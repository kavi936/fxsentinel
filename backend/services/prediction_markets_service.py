#!/usr/bin/env python3
"""
Prediction Markets Service for FXSentinel
Fetches and filters prediction market data from Polymarket via Dome API
"""

import json
import logging
import re
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Import curated markets
try:
    from services.curated_prediction_markets import (
        CURATED_MARKETS,
        get_curated_keywords,
        get_market_priority,
        get_affected_pairs_for_keywords
    )
    CURATED_MARKETS_AVAILABLE = True
except ImportError:
    CURATED_MARKETS_AVAILABLE = False
    logger.warning("Curated markets not available. Using default keywords.")

# Try to import Dome API SDK, fallback to requests if not available
try:
    from dome_api_sdk import DomeClient
    DOME_SDK_AVAILABLE = True
except ImportError:
    DOME_SDK_AVAILABLE = False
    import requests

# Import Dome API rate limiter
try:
    from services.dome_api_rate_limiter import dome_rate_limiter
except ImportError:
    # Fallback: create a simple rate limiter
    class SimpleRateLimiter:
        def __init__(self):
            self.last_request = 0
            self.lock = threading.Lock()
        def wait_if_needed(self):
            with self.lock:
                now = time.time()
                elapsed = now - self.last_request
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)
                self.last_request = time.time()
    import threading
    dome_rate_limiter = SimpleRateLimiter()

logger = logging.getLogger(__name__)

# Import persistent cache service
try:
    from services.persistent_prediction_markets_cache import get_persistent_prediction_markets_cache
    PERSISTENT_CACHE_AVAILABLE = True
except ImportError:
    PERSISTENT_CACHE_AVAILABLE = False
    logger.warning("Persistent prediction markets cache not available. Using file-based cache.")

# Import PolyRouter API client
try:
    from services.polyrouter_api_client import PolyRouterAPIClient
    POLYROUTER_AVAILABLE = True
except ImportError:
    POLYROUTER_AVAILABLE = False
    logger.warning("PolyRouter API client not available. Install dependencies if needed.")

if not DOME_SDK_AVAILABLE:
    logger.warning("dome-api-sdk not installed. Install with: pip install dome-api-sdk")

# Configuration constants for free tier optimization
FREE_TIER_MAX_PAGES_PER_PLATFORM = 2  # Reduced from 5/3 to 2/2 to stay within 10 queries per 10 seconds
FREE_TIER_EARLY_STOP_THRESHOLD = 400  # Stop when we have 400 raw markets (increased from 200 to get more variety)
FREE_TIER_CACHE_EXPIRATION_MINUTES = 30  # Increased from 10 to reduce refresh frequency
FREE_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES = 20  # Refresh every 20 minutes in background

# Paid tier defaults
PAID_TIER_MAX_PAGES_POLYMARKET = 5
PAID_TIER_MAX_PAGES_KALSHI = 3
PAID_TIER_EARLY_STOP_THRESHOLD = 150
PAID_TIER_CACHE_EXPIRATION_MINUTES = 10
PAID_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES = 5

# Market filtering limits
MAX_FILTERED_MARKETS = 50  # Maximum markets to return after filtering (increased from 30)
# Note: We return up to 50 markets, but frontend may display fewer based on UI constraints
FREE_TIER_MAX_PRICE_FETCH_MARKETS = 5  # Max markets to fetch prices for on free tier
PAID_TIER_MAX_PRICE_FETCH_MARKETS = 20  # Max markets to fetch prices for on paid tier

# Date thresholds
RECENTLY_RESOLVED_DAYS = 30  # Markets resolved within this many days are "recent"
CLOSED_MARKET_GRACE_PERIOD_DAYS = 30  # Allow closed markets within this period (increased from 7 to show more markets)

def _safe_get(obj, key, default=None):
    """Safely get attribute from object or dict"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    else:
        # Try attribute access first, then fallback to getattr
        return getattr(obj, key, default)

class PredictionMarketsService:
    """Main prediction markets service"""
    
    def __init__(self):
        # Detect API tier (default to free tier for safety)
        self.is_free_tier = os.getenv('DOME_API_TIER', 'free').lower() == 'free'
        
        # Set configuration based on tier
        if self.is_free_tier:
            self.max_pages_polymarket = FREE_TIER_MAX_PAGES_PER_PLATFORM
            self.max_pages_kalshi = FREE_TIER_MAX_PAGES_PER_PLATFORM
            self.early_stop_threshold = FREE_TIER_EARLY_STOP_THRESHOLD
            self.cache_expiration_minutes = FREE_TIER_CACHE_EXPIRATION_MINUTES
            self._background_refresh_interval_minutes = FREE_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES
            logger.info("Running in FREE TIER mode: Max 2 pages per platform, 30min cache, no price fetching")
        else:
            self.max_pages_polymarket = PAID_TIER_MAX_PAGES_POLYMARKET
            self.max_pages_kalshi = PAID_TIER_MAX_PAGES_KALSHI
            self.early_stop_threshold = PAID_TIER_EARLY_STOP_THRESHOLD
            self.cache_expiration_minutes = PAID_TIER_CACHE_EXPIRATION_MINUTES
            self._background_refresh_interval_minutes = PAID_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES
            logger.info("Running in PAID TIER mode: Max 5/3 pages per platform, 10min cache")
        
        # Initialize threading locks and refresh state (needed regardless of cache type)
        self._refresh_lock = threading.Lock()
        self._refresh_in_progress = False
        self._refresh_future = None
        self._refresh_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="prediction_markets_refresh")
        self._last_background_refresh = None
        
        # API call budget tracking (for free tier 10-per-10-seconds limit)
        self._api_calls_last_10_seconds = []
        self._api_call_lock = threading.Lock()
        
        # Configuration: Use direct CLOB API for Polymarket (better rate limits, more data)
        self.use_direct_clob = os.getenv('USE_DIRECT_CLOB', 'true').lower() == 'true'
        self.clob_max_pages = int(os.getenv('CLOB_MAX_PAGES', '3'))  # Default: 3 pages = 3,000 markets
        self.clob_request_delay = float(os.getenv('CLOB_REQUEST_DELAY', '0.5'))  # Delay between requests (seconds)
        
        # Initialize Dome API configuration (needed for Kalshi and Polymarket fallback)
        self.dome_api_key = os.getenv('DOME_API_KEY')
        self.api_available = False
        self.dome_client = None
        self.dome_api_base_url = "https://api.domeapi.io/v1/polymarket"
        
        if not self.dome_api_key:
            logger.warning("DOME_API_KEY not set. Kalshi markets will not be available.")
            self.api_available = False
        elif DOME_SDK_AVAILABLE:
            try:
                self.dome_client = DomeClient({"api_key": self.dome_api_key})
                logger.info("Dome API SDK initialized successfully")
                self.api_available = True
            except Exception as e:
                logger.error(f"Failed to initialize Dome API SDK: {e}")
                self.dome_client = None
                self.api_available = False
        else:
            logger.warning("Dome API SDK not available. Install with: pip install dome-api-sdk")
            self.dome_client = None
            self.api_available = False
        
        # Log configuration
        if self.use_direct_clob:
            logger.info(f"Using direct Polymarket CLOB API (max {self.clob_max_pages} pages = {self.clob_max_pages * 1000} markets)")
        else:
            logger.info("Using DOME API for Polymarket (fallback mode)")
        
        # Initialize filtering keywords and tags (needed regardless of cache type)
        self.economic_keywords = [
            # Federal Reserve & US Rates
            "federal reserve", "fed", "fomc", "interest rate", "rate hike", "rate cut", "rates",
            "jerome powell", "powell", "federal funds", "fed rate",
            
            # Inflation & Economic Data
            "inflation", "cpi", "consumer price index", "ppi", "producer price index",
            "gdp", "gross domestic product", "employment", "non-farm payrolls", "nfp", 
            "unemployment", "jobs report", "retail sales",
            
            # Central Banks & Governors
            "ecb", "european central bank", "christine lagarde", "lagarde",
            "bank of england", "boe", "andrew bailey", "bailey",
            "bank of japan", "boj", "kazuo ueda", "ueda", "kuroda",
            "central bank", "monetary policy", "policy decision", "policy meeting",
            
            # Forex Pairs & Currencies
            "eur/usd", "euro", "eurozone", "euro zone",
            "gbp/usd", "british pound", "sterling", "pound",
            "usd/jpy", "japanese yen", "yen",
            "usd/chf", "swiss franc", "franc",
            "aud/usd", "australian dollar", "aussie",
            "nzd/usd", "new zealand dollar", "kiwi",
            "usd/cad", "canadian dollar", "loonie",
            "forex", "fx", "currency", "exchange rate",
            
            # Trade & Tariffs
            "tariff", "tariffs", "trade war", "trade policy", "trade deal",
            "economic policy", "fiscal policy", "trade deficit", "trade surplus",
            
            # Key Politicians & Leaders (affect forex)
            "trump", "donald trump", "biden", "joe biden",
            "president", "presidential", "election", "elections",
            "congress", "senate", "house of representatives",
            
            # Political Events & Legislation (affect forex)
            "act", "law", "bill", "legislation", "signed", "passed", "congressional",
            "charged", "indictment", "trial", "court", "legal", "lawsuit",
            "policy", "policies", "reform", "regulation", "regulatory",
            
            # Geopolitical Events (affect forex)
            "geopolitics", "sanctions", "war", "conflict", "crisis",
            "brexit", "european union", "eu", "nato",
            "diplomatic", "diplomacy", "treaty", "agreement", "deal",
            
            # Economic Indicators
            "pmi", "purchasing managers index", "ism", "manufacturing",
            "consumer confidence", "business confidence", "housing", "real estate",
            "retail sales", "industrial production", "durable goods",
            
            # Government & Fiscal Policy
            "government", "fiscal", "budget", "deficit", "surplus", "debt",
            "stimulus", "austerity", "spending", "tax", "taxes", "revenue",
            
            # General Economic Terms (broader matching)
            "economic", "economy", "market", "financial", "markets", "finance",
            "business", "corporate", "company", "companies", "sector", "industry",
            "growth", "recession", "recovery", "expansion", "contraction",
            "indicator", "data", "report", "release", "announcement", "statement",
            "meeting", "conference", "speech", "testimony", "hearing"
        ]
        
        # Economic tags that indicate relevant markets
        self.economic_tags = [
            "politics", "geopolitics", "economics", "finance", "policy",
            "elections", "presidential"
        ]
        
        # Keywords to exclude (reduce false positives)
        self.exclude_keywords = [
            "academy", "oscar", "award", "movie", "film", "actor", "actress",
            "sports", "nba", "nfl", "ncaab", "football", "basketball",
            "dota", "counter-strike", "esports", "gaming", "game",
            "hawks", "warriors", "lakers", "celtics", "vs.", "o/u", "over/under",
            "bitcoin up or down", "ethereum up or down", "crypto up or down",
            "up or down -", "up or down:",  # Exclude recurring crypto price markets
            "15m", "30m", "1h", "4h"  # Exclude short-term crypto price movements
        ]
        
        # Initialize cache file path (needed for fallback even when using persistent cache)
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "prediction_markets_cache.json")
        self.cache_file = os.path.normpath(self.cache_file)
        
        # Initialize persistent cache attributes (will be set if available)
        self.persistent_cache = None
        self.use_persistent_cache = False
        
        # Initialize persistent cache (Firebase) or fallback to file cache
        if PERSISTENT_CACHE_AVAILABLE:
            try:
                self.persistent_cache = get_persistent_prediction_markets_cache(max_age_minutes=self.cache_expiration_minutes)
                self.use_persistent_cache = True
                logger.info("Using Firebase persistent cache for prediction markets")
            except Exception as e:
                logger.warning(f"Failed to initialize persistent cache, falling back to file cache: {e}")
                self.use_persistent_cache = False
        else:
            self.use_persistent_cache = False
        
        # Initialize PolyRouter API client
        self.use_polyrouter = os.getenv('USE_POLYROUTER', 'true').lower() == 'true'
        
        self.polyrouter_client = None
        if POLYROUTER_AVAILABLE and self.use_polyrouter:
            try:
                self.polyrouter_client = PolyRouterAPIClient()
                if self.polyrouter_client.available:
                    logger.info("PolyRouter API client initialized and available")
                else:
                    logger.warning("PolyRouter API key not configured")
            except Exception as e:
                logger.warning(f"Failed to initialize PolyRouter client: {e}")
        
        # Initialize cached data
        self.cached_markets = None
        self.cache_timestamp = None
        self._load_cache()
    
    def _init_file_cache(self):
        """Initialize file-based cache (fallback)"""
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "prediction_markets_cache.json")
        self.cache_file = os.path.normpath(self.cache_file)
        
        # Note: Threading locks, refresh state, Dome API configuration, and filtering keywords
        # are now initialized in __init__ to ensure they're always available regardless of cache type
    
    def _check_api_budget(self) -> bool:
        """Check if we have budget for another API call (free tier only)
        
        Returns:
            True if we can make another API call, False otherwise
        """
        if not self.is_free_tier:
            return True  # No limit on paid tiers
        
        with self._api_call_lock:
            now = time.time()
            # Remove calls older than 10 seconds
            self._api_calls_last_10_seconds = [
                call_time for call_time in self._api_calls_last_10_seconds
                if now - call_time < 10.0
            ]
            
            # Check if we can make another call (max 10 per 10 seconds)
            if len(self._api_calls_last_10_seconds) >= 10:
                return False
            
            # Record this call
            self._api_calls_last_10_seconds.append(now)
            return True
    
    def _wait_for_api_budget(self):
        """Wait until we have budget for an API call (free tier only)"""
        if not self.is_free_tier:
            return
        
        while not self._check_api_budget():
            # Calculate wait time until oldest call expires
            with self._api_call_lock:
                if self._api_calls_last_10_seconds:
                    oldest_call = min(self._api_calls_last_10_seconds)
                    wait_time = 10.0 - (time.time() - oldest_call) + 0.1  # Add small buffer
                    if wait_time > 0:
                        logger.info(f"API budget exhausted ({len(self._api_calls_last_10_seconds)}/10 calls in window), waiting {wait_time:.1f}s")
                        time.sleep(wait_time)
                    else:
                        # Clean up old calls
                        now = time.time()
                        self._api_calls_last_10_seconds = [
                            call_time for call_time in self._api_calls_last_10_seconds
                            if now - call_time < 10.0
                        ]
                else:
                    break
    
    def _load_cache(self):
        """Load cached markets data from Firebase or file cache"""
        if self.use_persistent_cache:
            try:
                cache_result = self.persistent_cache.load_markets(allow_stale=True, return_metadata=True)
                if cache_result and isinstance(cache_result, dict):
                    self.cached_markets = cache_result.get('markets', [])
                    last_fetch_str = cache_result.get('last_fetch')
                    if last_fetch_str:
                        try:
                            self.cache_timestamp = datetime.fromisoformat(last_fetch_str.replace('Z', '+00:00'))
                        except (ValueError, TypeError):
                            # Fallback to timestamp if last_fetch parsing fails
                            cache_data = self.persistent_cache.firebase._make_request('GET', self.persistent_cache._get_cache_path())
                            if cache_data and isinstance(cache_data, dict):
                                timestamp_str = cache_data.get('timestamp')
                                if timestamp_str:
                                    self.cache_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                elif cache_result:
                    # Backward compatibility: if return_metadata=False was used
                    self.cached_markets = cache_result
                    # Try to get timestamp from Firebase
                    cache_data = self.persistent_cache.firebase._make_request('GET', self.persistent_cache._get_cache_path())
                    if cache_data and isinstance(cache_data, dict):
                        timestamp_str = cache_data.get('timestamp')
                        if timestamp_str:
                            self.cache_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    self.cached_markets = None
                    self.cache_timestamp = None
            except Exception as e:
                logger.error(f"Error loading from persistent cache: {e}")
                self.cached_markets = None
                self.cache_timestamp = None
        else:
            # Fallback to file cache
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.cached_markets = data.get('markets', [])
                    timestamp_str = data.get('timestamp')
                    if timestamp_str:
                        self.cache_timestamp = datetime.fromisoformat(
                            timestamp_str.replace('Z', '+00:00')
                        )
            except (FileNotFoundError, json.JSONDecodeError, ValueError):
                self.cached_markets = None
                self.cache_timestamp = None
    
    def _save_cache(self, markets: List[Dict]):
        """Save markets to Firebase or file cache"""
        if self.use_persistent_cache:
            try:
                success = self.persistent_cache.save_markets(markets)
                if success:
                    # Update local cache timestamp
                    self.cache_timestamp = datetime.now(timezone.utc)
                    self.cached_markets = markets
                else:
                    logger.warning("Failed to save to persistent cache, but continuing")
            except Exception as e:
                logger.error(f"Error saving to persistent cache: {e}")
        else:
            # Fallback to file cache
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump({
                        'markets': markets,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save cache: {e}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.cached_markets or not self.cache_timestamp:
            return False
        
        age = datetime.now(timezone.utc) - self.cache_timestamp.replace(tzinfo=timezone.utc)
        return age.total_seconds() < (self.cache_expiration_minutes * 60)
    
    
    def _fetch_kalshi_markets(self, early_stop_threshold: int = None) -> List[Dict]:
        """Fetch markets from Kalshi via Dome API using SDK
        
        Args:
            early_stop_threshold: Stop fetching if we have this many markets (saves API calls)
                                  If None, uses instance-level threshold
        """
        if not self.api_available:
            logger.error("Dome API not available. Check DOME_API_KEY configuration.")
            return []
        
        # Use instance-level threshold if not provided
        if early_stop_threshold is None:
            early_stop_threshold = self.early_stop_threshold
        
        markets = []
        limit = 100  # Dome API limit per page
        max_pages = self.max_pages_kalshi  # Use instance-level config
        
        try:
            if self.dome_client and DOME_SDK_AVAILABLE:
                # Use SDK
                offset = 0
                import time
            for page in range(max_pages):
                    try:
                        # Check API budget before each call (free tier)
                        if self.is_free_tier:
                            self._wait_for_api_budget()
                        
                        # Use rate limiter to ensure exactly 1 request per second
                        wait_time = dome_rate_limiter.wait_if_needed()
                        if wait_time > 0 and page > 0:
                            logger.debug(f"Rate limiter: waited {wait_time:.2f}s before Kalshi page {page + 1}")
                        
                        result = self.dome_client.kalshi.markets.get_markets({
                            "limit": limit,
                            "offset": offset
                        })
                        
                        # Handle SDK response
                        if hasattr(result, 'markets'):
                            page_markets = result.markets
                            pagination = result.pagination if hasattr(result, 'pagination') else None
                        elif isinstance(result, dict):
                            page_markets = result.get("markets", [])
                            pagination = result.get("pagination", {})
                        else:
                            break
                        
                        if not page_markets:
                            break
                        
                        markets.extend(page_markets)
                        
                        # Early stopping: if we have enough markets, stop fetching to save API calls
                        if len(markets) >= early_stop_threshold:
                            logger.info(f"Early stopping Kalshi fetch: have {len(markets)} markets (threshold: {early_stop_threshold})")
                            break
                        
                        # Check pagination
                        if pagination:
                            has_more = _safe_get(pagination, "has_more", False)
                        else:
                            has_more = False
                        
                        if not has_more:
                            break
                        
                        offset += limit
                        logger.info(f"Fetched Kalshi page {page + 1}: {len(page_markets)} markets (total: {len(markets)})")
                        
                    except Exception as e:
                        logger.error(f"Error fetching Kalshi page {page + 1}: {e}")
                        break
            else:
                # Fallback to direct HTTP requests
                import requests
                offset = 0
                headers = {"Authorization": f"Bearer {self.dome_api_key}"}
                
                for page in range(max_pages):
                    # Check API budget before each call (free tier)
                    if self.is_free_tier:
                        self._wait_for_api_budget()
                    
                    # Use rate limiter to ensure exactly 1 request per second
                    wait_time = dome_rate_limiter.wait_if_needed()
                    if wait_time > 0 and page > 0:
                        logger.debug(f"Rate limiter: waited {wait_time:.2f}s before Kalshi page {page + 1}")
                    
                    url = "https://api.domeapi.io/v1/kalshi/markets"
                    params = {"limit": limit, "offset": offset}
                    
                    response = requests.get(url, params=params, headers=headers, timeout=15)
                    if response.status_code == 429:
                        dome_rate_limiter.record_rate_limit_hit()
                        logger.warning(f"Rate limit hit on Kalshi page {page + 1}, stopping pagination")
                        break
                    elif response.status_code != 200:
                        logger.error(f"Kalshi API error: {response.status_code}")
                        break
                    
                    data = response.json()
                    page_markets = data.get("markets", [])
                    markets.extend(page_markets)
                    
                    # Early stopping: if we have enough markets, stop fetching to save API calls
                    if len(markets) >= early_stop_threshold:
                        logger.info(f"Early stopping Kalshi fetch: have {len(markets)} markets (threshold: {early_stop_threshold})")
                        break
                    
                    pagination = data.get("pagination", {})
                    has_more = pagination.get("has_more", False)
                    
                    if not has_more or len(page_markets) == 0:
                        break
                    
                    offset += limit
                    logger.info(f"Fetched Kalshi page {page + 1}: {len(page_markets)} markets (total: {len(markets)})")
        
        except Exception as e:
            logger.error(f"Error fetching Kalshi data: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        logger.info(f"Total Kalshi markets fetched: {len(markets)}")
        return markets
    
    def _fetch_polymarket_clob_direct(self, early_stop_threshold: int = None) -> List[Dict]:
        """Fetch markets directly from Polymarket CLOB API
        
        Args:
            early_stop_threshold: Stop fetching if we have this many markets (saves API calls)
                                  If None, uses instance-level threshold
        
        Returns:
            List of market dictionaries from CLOB API
        """
        if early_stop_threshold is None:
            early_stop_threshold = self.early_stop_threshold
        
        markets = []
        cursor = None
        max_pages = self.clob_max_pages
        
        try:
            import requests
            
            logger.info(f"Fetching Polymarket markets directly from CLOB API (max {max_pages} pages)")
            
            for page in range(max_pages):
                url = "https://clob.polymarket.com/markets"
                params = {"limit": 1000}  # CLOB API supports up to 1000 per request
                
                if cursor:
                    params["cursor"] = cursor
                
                try:
                    # Add respectful delay between requests
                    if page > 0:
                        time.sleep(self.clob_request_delay)
                    
                    response = requests.get(url, params=params, timeout=15)
                    
                    if response.status_code == 429:
                        logger.warning(f"Rate limit hit on CLOB API page {page + 1}, stopping")
                        break
                    elif response.status_code != 200:
                        logger.error(f"CLOB API error: {response.status_code} - {response.text[:200]}")
                        break
                    
                    data = response.json()
                    page_markets = data.get("data", [])
                    
                    if not page_markets:
                        logger.info(f"No more markets available (empty page {page + 1})")
                        break
                    
                    # Mark markets as from CLOB API
                    for market in page_markets:
                        market["platform"] = "polymarket"
                        market["_source"] = "clob_direct"
                    
                    markets.extend(page_markets)
                    
                    # Early stopping: if we have enough markets, stop fetching
                    if len(markets) >= early_stop_threshold:
                        logger.info(f"Early stopping CLOB fetch: have {len(markets)} markets (threshold: {early_stop_threshold})")
                        break
                    
                    # Check pagination
                    cursor = data.get("next_cursor")
                    if not cursor:
                        logger.info(f"No more pages available (no next_cursor)")
                        break
                    
                    logger.info(f"Fetched CLOB page {page + 1}: {len(page_markets)} markets (total: {len(markets)})")
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching CLOB API page {page + 1}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error fetching CLOB API page {page + 1}: {e}")
                    import traceback
                    traceback.print_exc()
                    break
        
        except Exception as e:
            logger.error(f"Error fetching from CLOB API: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        logger.info(f"Total markets fetched from CLOB API: {len(markets)}")
        return markets
    
    def _fetch_polymarket_markets(self, early_stop_threshold: int = None) -> List[Dict]:
        """Fetch markets from Polymarket - uses direct CLOB API or DOME API fallback
        
        Args:
            early_stop_threshold: Stop fetching if we have this many markets (saves API calls)
                                  If None, uses instance-level threshold
        """
        # Use direct CLOB API if enabled (default), otherwise use DOME API
        if self.use_direct_clob:
            markets = self._fetch_polymarket_clob_direct(early_stop_threshold=early_stop_threshold)
            if markets:
                return markets
            else:
                logger.warning("CLOB API fetch failed, falling back to DOME API")
                # Fall through to DOME API
        
        # Fallback to DOME API
        if not self.api_available:
            logger.error("Dome API not available. Check DOME_API_KEY configuration.")
            return []
        
        # Use instance-level threshold if not provided
        if early_stop_threshold is None:
            early_stop_threshold = self.early_stop_threshold
        
        markets = []
        limit = 100  # Dome API limit per page
        max_pages = self.max_pages_polymarket  # Use instance-level config
        
        try:
            if self.dome_client and DOME_SDK_AVAILABLE:
                # Use SDK
                offset = 0
                for page in range(max_pages):
                    try:
                        # Check API budget before each call (free tier)
                        if self.is_free_tier:
                            self._wait_for_api_budget()
                        
                        # Use rate limiter to ensure exactly 1 request per second
                        wait_time = dome_rate_limiter.wait_if_needed()
                        if wait_time > 0 and page > 0:
                            logger.debug(f"Rate limiter: waited {wait_time:.2f}s before Polymarket page {page + 1}")
                        
                        result = self.dome_client.polymarket.markets.get_markets({
                            "limit": limit,
                            "offset": offset
                        })
                        
                        # SDK may return result object with attributes or a dict
                        # Handle both cases
                        if hasattr(result, 'markets'):
                            page_markets = result.markets
                            pagination = result.pagination if hasattr(result, 'pagination') else None
                        elif isinstance(result, dict):
                            page_markets = result.get("markets", [])
                            pagination = result.get("pagination", {})
                        else:
                            # Try to convert to dict if possible
                            try:
                                result_dict = dict(result) if hasattr(result, '__dict__') else {}
                                page_markets = result_dict.get("markets", [])
                                pagination = result_dict.get("pagination", {})
                            except:
                                logger.warning(f"Unexpected result format from SDK: {type(result)}")
                                break
                        
                        if not page_markets:
                            break
                        
                        markets.extend(page_markets)
                        
                        # Early stopping: if we have enough markets, stop fetching to save API calls
                        if len(markets) >= early_stop_threshold:
                            logger.info(f"Early stopping Polymarket fetch: have {len(markets)} markets (threshold: {early_stop_threshold})")
                            break
                        
                        # Check pagination - handle both object and dict formats
                        if pagination:
                            has_more = _safe_get(pagination, "has_more", False)
                        else:
                            has_more = False
                        
                        if not has_more:
                            break
                        
                        offset += limit
                        logger.info(f"Fetched page {page + 1}: {len(page_markets)} markets (total: {len(markets)})")
                        
                    except Exception as e:
                        error_str = str(e)
                        # Check if it's a rate limit error (429)
                        if "429" in error_str or "rate limit" in error_str.lower() or "Too Many Requests" in error_str:
                            dome_rate_limiter.record_rate_limit_hit()
                            logger.warning(f"Rate limit hit on Polymarket page {page + 1}, stopping pagination")
                            # Wait a bit before returning to let rate limit reset
                            time.sleep(2)
                            break
                        logger.error(f"Error fetching page {page + 1} via SDK: {e}")
                        import traceback
                        traceback.print_exc()
                        break
            else:
                # Fallback to direct HTTP requests
                import requests
                offset = 0
                headers = {
                    "Authorization": f"Bearer {self.dome_api_key}"
                }
                
                for page in range(max_pages):
                    # Check API budget before each call (free tier)
                    if self.is_free_tier:
                        self._wait_for_api_budget()
                    
                    # Use rate limiter to ensure exactly 1 request per second
                    wait_time = dome_rate_limiter.wait_if_needed()
                    if wait_time > 0 and page > 0:
                        logger.debug(f"Rate limiter: waited {wait_time:.2f}s before Polymarket page {page + 1}")
                    
                    url = f"{self.dome_api_base_url}/markets"
                    params = {
                        "limit": limit,
                        "offset": offset
                    }
                    
                    response = requests.get(url, params=params, headers=headers, timeout=15)
                    if response.status_code == 429:
                        dome_rate_limiter.record_rate_limit_hit()
                        logger.warning(f"Rate limit hit on Polymarket page {page + 1}, stopping pagination")
                        break
                    elif response.status_code != 200:
                        logger.error(f"Dome API error: {response.status_code} - {response.text}")
                        break
                    
                    data = response.json()
                    page_markets = data.get("markets", [])
                    markets.extend(page_markets)
                    
                    # Early stopping: if we have enough markets, stop fetching to save API calls
                    if len(markets) >= early_stop_threshold:
                        logger.info(f"Early stopping Polymarket fetch: have {len(markets)} markets (threshold: {early_stop_threshold})")
                        break
                    
                    pagination = data.get("pagination", {})
                    has_more = pagination.get("has_more", False)
                    
                    if not has_more or len(page_markets) == 0:
                        break
                    
                    offset += limit
                    logger.info(f"Fetched page {page + 1}: {len(page_markets)} markets (total: {len(markets)})")
        
        except Exception as e:
            logger.error(f"Error fetching Dome API data: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        logger.info(f"Total markets fetched from Dome API: {len(markets)}")
        return markets
    
    def _detect_platform(self, market: Dict[str, Any]) -> str:
        """Detect platform from market structure
        
        Args:
            market: Market dictionary
            
        Returns:
            Platform name: "kalshi" or "polymarket"
        """
        if "market_ticker" in market or "event_ticker" in market:
            return "kalshi"
        return market.get("platform", "polymarket")
    
    def _get_market_id(self, market: Dict[str, Any], platform: Optional[str] = None) -> Optional[str]:
        """Get unique market identifier based on platform
        
        Args:
            market: Market dictionary
            platform: Platform name (auto-detected if None)
        
        Returns:
            Market ID string or None
        """
        if platform is None:
            platform = self._detect_platform(market)
        
        if platform == "kalshi":
            return _safe_get(market, "market_ticker") or _safe_get(market, "event_ticker")
        else:
            return _safe_get(market, "condition_id")
    
    def _is_market_resolved(self, market: Dict[str, Any], platform: str) -> bool:
        """Check if market is resolved
        
        Args:
            market: Market dictionary
            platform: Platform name ("kalshi" or "polymarket")
        
        Returns:
            True if market is resolved, False otherwise
        """
        # Check source to determine structure
        source = market.get("_source", "dome")
        is_clob_structure = source == "clob_direct" or "question" in market
        
        if platform == "kalshi":
            # Kalshi: market is resolved if result field is not None
            result = _safe_get(market, "result")
            return result is not None
        elif is_clob_structure:
            # CLOB API: Check winning_side, closed status, or token prices
            winning_side = _safe_get(market, "winning_side")
            closed_val = _safe_get(market, "closed", False)
            # Handle string booleans from CLOB API
            closed = closed_val if isinstance(closed_val, bool) else str(closed_val).lower() == "true"
            
            # Also check if tokens show resolved state (100% or 0% prices)
            tokens = _safe_get(market, "tokens", [])
            if tokens:
                for token in tokens:
                    price = token.get("price")
                    winner = token.get("winner")
                    if winner is True or (price is not None and (price == 1 or price == 0)):
                        return True
                    if price is not None:
                        try:
                            price_float = float(price)
                            # If any token is 1.0 or 0.0, market is resolved
                            if price_float == 1.0 or price_float == 0.0:
                                return True
                        except (ValueError, TypeError):
                            pass
            
            return winning_side is not None or closed
        else:
            # DOME API Polymarket: market is resolved if winning_side is not None
            winning_side = _safe_get(market, "winning_side")
            return winning_side is not None
    
    def _get_affected_currency_pairs(self, market: Dict, matched_keywords: List[str], related_event: str) -> List[str]:
        """Determine which currency pairs are affected by this market
        
        Args:
            market: Market dictionary
            matched_keywords: List of matched economic keywords
            related_event: Related event type (e.g., "FOMC Meeting", "CPI Release")
        
        Returns:
            List of affected currency pairs (e.g., ["EUR/USD", "GBP/USD"])
        """
        pairs = []
        matched_lower = [k.lower() for k in matched_keywords]
        
        # Fed/FOMC affects USD pairs
        if any(k in matched_lower for k in ["fed", "federal reserve", "fomc", "interest rate", "rate hike", "rate cut", "rates", "powell", "jerome powell"]):
            pairs.extend(["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD"])
        
        # ECB affects EUR pairs
        if any(k in matched_lower for k in ["ecb", "european central bank", "lagarde", "christine lagarde"]):
            pairs.extend(["EUR/USD", "EUR/GBP", "EUR/JPY", "EUR/CHF"])
        
        # BOE affects GBP pairs
        if any(k in matched_lower for k in ["boe", "bank of england", "bailey", "andrew bailey"]):
            pairs.extend(["GBP/USD", "EUR/GBP", "GBP/JPY", "GBP/CHF"])
        
        # BOJ affects JPY pairs
        if any(k in matched_lower for k in ["boj", "bank of japan", "ueda", "kazuo ueda", "kuroda"]):
            pairs.extend(["USD/JPY", "EUR/JPY", "GBP/JPY", "AUD/JPY"])
        
        # RBA affects AUD pairs
        if any(k in matched_lower for k in ["rba", "reserve bank of australia"]):
            pairs.extend(["AUD/USD", "AUD/JPY", "AUD/NZD", "AUD/CAD"])
        
        # RBNZ affects NZD pairs
        if any(k in matched_lower for k in ["rbnz", "reserve bank of new zealand"]):
            pairs.extend(["NZD/USD", "NZD/JPY", "AUD/NZD"])
        
        # BOC affects CAD pairs
        if any(k in matched_lower for k in ["boc", "bank of canada"]):
            pairs.extend(["USD/CAD", "EUR/CAD", "GBP/CAD"])
        
        # SNB affects CHF pairs
        if any(k in matched_lower for k in ["snb", "swiss national bank"]):
            pairs.extend(["USD/CHF", "EUR/CHF", "GBP/CHF"])
        
        # US economic data (CPI, GDP, NFP) affects USD pairs
        if any(k in matched_lower for k in ["cpi", "consumer price index", "inflation", "ppi", "gdp", "gross domestic product", 
                                             "employment", "nfp", "non-farm payrolls", "jobs report", "unemployment"]):
            # Check if it's specifically US data (default assumption for these keywords)
            pairs.extend(["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD"])
        
        # Specific forex pair mentions
        if any(k in matched_lower for k in ["eur/usd", "euro", "eurozone", "euro zone"]):
            if "EUR/USD" not in pairs:
                pairs.append("EUR/USD")
        if any(k in matched_lower for k in ["gbp/usd", "british pound", "sterling", "pound"]):
            if "GBP/USD" not in pairs:
                pairs.append("GBP/USD")
        if any(k in matched_lower for k in ["usd/jpy", "japanese yen", "yen"]):
            if "USD/JPY" not in pairs:
                pairs.append("USD/JPY")
        if any(k in matched_lower for k in ["usd/chf", "swiss franc", "franc"]):
            if "USD/CHF" not in pairs:
                pairs.append("USD/CHF")
        if any(k in matched_lower for k in ["aud/usd", "australian dollar", "aussie"]):
            if "AUD/USD" not in pairs:
                pairs.append("AUD/USD")
        if any(k in matched_lower for k in ["nzd/usd", "new zealand dollar", "kiwi"]):
            if "NZD/USD" not in pairs:
                pairs.append("NZD/USD")
        if any(k in matched_lower for k in ["usd/cad", "canadian dollar", "loonie"]):
            if "USD/CAD" not in pairs:
                pairs.append("USD/CAD")
        
        # Remove duplicates and return
        return list(set(pairs))
    
    def _filter_economic_markets(self, markets: List[Dict]) -> List[Dict]:
        """Filter markets for economic/forex relevance"""
        relevant_markets = []
        seen_ids = set()  # Track seen market IDs to prevent duplicates
        now = datetime.now(timezone.utc)
        
        # Debug counters
        total_checked = 0
        skipped_closed = 0
        skipped_exclude = 0
        skipped_no_keywords = 0
        included_markets = 0
        
        for market_obj in markets:
            total_checked += 1
            # Convert Market object to dict if needed for consistent access
            if not isinstance(market_obj, dict):
                # Check if it's Kalshi (has event_ticker) or Polymarket (has condition_id)
                is_kalshi = hasattr(market_obj, "event_ticker") or hasattr(market_obj, "market_ticker")
                
                if is_kalshi:
                    # Kalshi structure
                    market = {
                        "market_ticker": _safe_get(market_obj, "market_ticker"),
                        "event_ticker": _safe_get(market_obj, "event_ticker"),
                        "title": _safe_get(market_obj, "title", ""),
                        "status": _safe_get(market_obj, "status", ""),
                        "start_time": _safe_get(market_obj, "start_time"),
                        "end_time": _safe_get(market_obj, "end_time"),
                        "close_time": _safe_get(market_obj, "close_time"),
                        "last_price": _safe_get(market_obj, "last_price"),
                        "volume": _safe_get(market_obj, "volume"),
                        "volume_24h": _safe_get(market_obj, "volume_24h"),
                        "result": _safe_get(market_obj, "result"),
                        "platform": "kalshi"
                    }
                else:
                    # Polymarket structure
                    market = {
                        "condition_id": _safe_get(market_obj, "condition_id"),
                        "title": _safe_get(market_obj, "title", ""),
                        "tags": _safe_get(market_obj, "tags", []),
                        "status": _safe_get(market_obj, "status", ""),
                        "end_time": _safe_get(market_obj, "end_time"),
                        "completed_time": _safe_get(market_obj, "completed_time"),
                        "side_a": _safe_get(market_obj, "side_a"),
                        "side_b": _safe_get(market_obj, "side_b"),
                        "winning_side": _safe_get(market_obj, "winning_side"),
                        "volume_total": _safe_get(market_obj, "volume_total"),
                        "volume_1_week": _safe_get(market_obj, "volume_1_week"),
                        "platform": "polymarket"
                    }
            else:
                market = market_obj
                # Detect platform from dict structure using helper method
                market["platform"] = self._detect_platform(market)
            
            # Deduplicate by market identifier using helper method
            platform = market.get("platform", "polymarket")
            market_id = self._get_market_id(market, platform)
            
            if not market_id or market_id in seen_ids:
                continue
            seen_ids.add(market_id)
            
            # Get title/question - CLOB uses "question", DOME uses "title"
            source = market.get("_source", "dome")
            is_clob_structure = source == "clob_direct" or "question" in market
            
            if is_clob_structure:
                title_raw = _safe_get(market, "question", "")
                # Remove "arch" prefix if present (archived markets in CLOB API)
                if title_raw.startswith("arch"):
                    title_raw = title_raw[4:]  # Remove "arch" prefix
                title = title_raw.lower()
            else:
                title = _safe_get(market, "title", "").lower()
            
            # Check if market is archived (CLOB API marks archived markets)
            if is_clob_structure:
                archived_val = _safe_get(market, "archived", False)
                archived = archived_val if isinstance(archived_val, bool) else str(archived_val).lower() == "true"
                # Also check if original question starts with "arch" (another indicator)
                question_raw = _safe_get(market, "question", "")
                if archived or (question_raw and question_raw.lower().startswith("arch")):
                    skipped_closed += 1
                    continue
            
            # Check if market is resolved - filter out ALL resolved markets per user requirement
            is_resolved = self._is_market_resolved(market, platform)
            
            # Skip ALL resolved markets (no exceptions)
            if is_resolved:
                skipped_closed += 1
                continue
            
            # Handle tags (Polymarket has tags array, Kalshi might not)
            tags_list = _safe_get(market, "tags", [])
            if not tags_list:
                tags_list = []
            tags = [tag.lower() if isinstance(tag, str) else str(tag).lower() for tag in tags_list]
            text = f"{title} {' '.join(tags)}"
            
            # Check if market has economic tags
            has_economic_tag = any(econ_tag in tags for econ_tag in self.economic_tags)
            
            # Status field - handle both CLOB (booleans/strings) and DOME (status string)
            if is_clob_structure:
                # CLOB API may return strings "True"/"False" or actual booleans
                active_val = _safe_get(market, "active", False)
                closed_val = _safe_get(market, "closed", False)
                accepting_orders_val = _safe_get(market, "accepting_orders", False)
                
                # Convert string booleans to actual booleans
                is_open = active_val if isinstance(active_val, bool) else str(active_val).lower() == "true"
                is_closed = closed_val if isinstance(closed_val, bool) else str(closed_val).lower() == "true"
                accepting_orders = accepting_orders_val if isinstance(accepting_orders_val, bool) else str(accepting_orders_val).lower() == "true"
            else:
                status = _safe_get(market, "status", "").lower()
                is_open = status == "open"
                is_closed = status == "closed"
                accepting_orders = _safe_get(market, "accepting_orders", False) or is_open
            
            # Filter out closed markets (per user requirement - no resolved/closed markets)
            if is_closed:
                skipped_closed += 1
                continue
            
            # NEW: Check if market has embedded price data (prioritize these on free tier)
            # Also validate that prices are meaningful (not 0/1 with no volume)
            has_embedded_price = False
            has_valid_prices = False
            
            # Get volume for validation
            if platform == "kalshi":
                volume = _safe_get(market, "volume") or _safe_get(market, "volume_24h") or 0
            elif is_clob_structure:
                volume = _safe_get(market, "volume") or _safe_get(market, "volume_total") or 0
            else:
                volume = _safe_get(market, "volume_total") or _safe_get(market, "volume_1_week") or 0
            
            if platform == "kalshi":
                last_price = _safe_get(market, "last_price")
                has_embedded_price = last_price is not None
                # Valid if price is in range (0, 1) or market has volume
                has_valid_prices = (last_price is not None and 0 < last_price < 1) or volume > 0
            elif is_clob_structure:
                # CLOB API: Check if tokens array has prices
                tokens = _safe_get(market, "tokens", [])
                if tokens:
                    has_embedded_price = any(
                        token.get("price") is not None 
                        for token in tokens
                    )
                    # Check if prices are valid (not all 0 with no volume)
                    valid_prices = [
                        float(t.get("price", 0)) 
                        for t in tokens 
                        if t.get("price") is not None
                    ]
                    has_valid_prices = any(0 < p < 1 for p in valid_prices) or volume > 0
            else:
                # DOME API Polymarket: Check if side_a or side_b have prices
                side_a = _safe_get(market, "side_a", {})
                side_b = _safe_get(market, "side_b", {})
                
                if isinstance(side_a, dict):
                    has_embedded_price = any(
                        _safe_get(side_a, key) is not None 
                        for key in ["price", "current_price", "last_price", "token_price"]
                    )
                    # Check if prices are valid
                    price_a = _safe_get(side_a, "price") or _safe_get(side_a, "current_price")
                    price_b = _safe_get(side_b, "price") or _safe_get(side_b, "current_price") if isinstance(side_b, dict) else None
                    has_valid_prices = (
                        (price_a is not None and 0 < price_a < 1) or 
                        (price_b is not None and 0 < price_b < 1) or 
                        volume > 0
                    )
                
                if not has_embedded_price and isinstance(side_b, dict):
                    has_embedded_price = any(
                        _safe_get(side_b, key) is not None 
                        for key in ["price", "current_price", "last_price", "token_price"]
                    )
                
                # Also check market-level prices
                if not has_embedded_price:
                    has_embedded_price = (
                        _safe_get(market, "yes_price") is not None or
                        _safe_get(market, "no_price") is not None
                    )
            
            # Skip markets with invalid prices (0/1 with no volume = no real data)
            if has_embedded_price and not has_valid_prices and volume == 0:
                # Market has price data but it's invalid (likely 0/1 with no volume)
                skipped_closed += 1
                continue
            
            # Store price availability flags
            market["has_embedded_price"] = has_embedded_price
            market["has_valid_prices"] = has_valid_prices
            
            # Check if market has future resolution date
            # CLOB uses ISO string (end_date_iso), DOME uses Unix timestamps
            # IMPORTANT: Filter out markets with past resolution dates (past due)
            is_future = False
            days_until_resolution = None
            resolution_date_obj = None
            
            if is_clob_structure:
                # CLOB API uses ISO string format
                end_date_iso = _safe_get(market, "end_date_iso")
                if end_date_iso:
                    try:
                        resolution_date_obj = datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
                        is_future = resolution_date_obj > now
                        days_until_resolution = (resolution_date_obj - now).days
                        days_since_resolution = (now - resolution_date_obj).days
                        
                        # Allow markets with future dates OR recently resolved (within last 90 days)
                        # Extended grace period to show more markets - many markets might be slightly old but still relevant
                        if not is_future:
                            # Market is in the past - only show if resolved recently (within 90 days)
                            # This is more lenient to ensure we show some markets
                            if days_since_resolution > 90:
                                skipped_closed += 1
                                continue
                            # Market resolved recently - treat as "recently resolved" for display
                            is_future = False
                            days_until_resolution = None
                    except (ValueError, TypeError):
                        # If we can't parse the date, allow the market (might be valid without date)
                        is_future = None  # Unknown
                        days_until_resolution = None
                else:
                    # No resolution date - allow the market (some markets don't have clear dates)
                    is_future = None  # Unknown
                    days_until_resolution = None
            else:
                # DOME API uses Unix timestamps
                end_time = _safe_get(market, "end_time")
                close_time = _safe_get(market, "close_time")  # Kalshi uses close_time
                resolution_time = end_time or close_time
                if resolution_time:
                    try:
                        # Convert Unix timestamp to datetime
                        resolution_date_obj = datetime.fromtimestamp(resolution_time, tz=timezone.utc)
                        is_future = resolution_date_obj > now
                        days_until_resolution = (resolution_date_obj - now).days
                        days_since_resolution = (now - resolution_date_obj).days
                        
                        # Allow markets with future dates OR recently resolved (within last 90 days)
                        # Extended grace period to show more markets - many markets might be slightly old but still relevant
                        if not is_future:
                            # Market is in the past - only show if resolved recently (within 90 days)
                            # This is more lenient to ensure we show some markets
                            if days_since_resolution > 90:
                                skipped_closed += 1
                                continue
                            # Market resolved recently - treat as "recently resolved" for display
                            is_future = False
                            days_until_resolution = None
                    except (ValueError, TypeError):
                        # If we can't parse the date, allow the market (might be valid without date)
                        is_future = None  # Unknown
                        days_until_resolution = None
                else:
                    # No resolution date - allow the market (some markets don't have clear dates)
                    is_future = None  # Unknown
                    days_until_resolution = None
            
            # Track recently resolved markets (within last 90 days - matches grace period)
            is_recently_resolved = False
            if is_clob_structure:
                # CLOB API - check completed_time or end_date_iso if closed
                if is_closed:
                    completed_time_iso = _safe_get(market, "completed_time")  # May be ISO string or timestamp
                    end_date_iso = _safe_get(market, "end_date_iso")
                    
                    try:
                        if completed_time_iso:
                            # Try ISO format first
                            try:
                                completed_date = datetime.fromisoformat(str(completed_time_iso).replace('Z', '+00:00'))
                            except:
                                # Fallback to timestamp
                                completed_date = datetime.fromtimestamp(completed_time_iso, tz=timezone.utc)
                        elif end_date_iso:
                            completed_date = datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
                        else:
                            completed_date = None
                        
                        if completed_date:
                            days_since_resolution = (now - completed_date).days
                            is_recently_resolved = 0 <= days_since_resolution <= 90  # Extended to 90 days
                    except (ValueError, TypeError):
                        pass
            else:
                # DOME API uses Unix timestamps
                completed_time = _safe_get(market, "completed_time")
                close_time = _safe_get(market, "close_time")
                completion_time = completed_time or close_time
                if is_closed and completion_time:
                    try:
                        completed_date = datetime.fromtimestamp(completion_time, tz=timezone.utc)
                        days_since_resolution = (now - completed_date).days
                        is_recently_resolved = 0 <= days_since_resolution <= 30
                    except (ValueError, TypeError):
                        pass
            
            # Mark historical markets (closed and old)
            is_historical = is_closed and not is_future and not is_recently_resolved
            
            # Skip if contains exclude keywords (check both title and tags)
            # Use case-insensitive matching
            text_lower = text.lower()
            if any(exclude.lower() in text_lower for exclude in self.exclude_keywords):
                skipped_exclude += 1
                continue
            
            # Additional exclusion: Skip crypto price markets
            crypto_keywords = ["bitcoin", "ethereum", "btc", "eth", "crypto", "solana", "cardano", "dogecoin"]
            # Expanded price patterns to catch more variations
            price_patterns = [
                "price of", "price be", "will the price", "price above", "price below", "price less than",
                "dip to", "drop to", "reach", "hit", "fall to", "rise to", "climb to", "surge to",
                "plunge to", "crash to", "soar to", "jump to", "spike to", "tumble to",
                "above $", "below $", "over $", "under $", "at least $", "at most $",
                "will be $", "will reach $", "will hit $", "will touch $"
            ]
            
            if any(crypto in text_lower for crypto in crypto_keywords):
                # If it's about crypto AND mentions a price/dollar amount, exclude it
                if any(pattern in text_lower for pattern in price_patterns) or "$" in text_lower or "up or down" in text_lower:
                    skipped_exclude += 1
                    continue
            
            # Skip sports betting markets (O/U, spread, etc.)
            if any(sports_indicator in text_lower for sports_indicator in ["o/u", "over/under", "spread", "total points"]):
                skipped_exclude += 1
                continue
            
            # Check for economic keywords
            relevance = "low"
            matched_keywords = []
            
            for keyword in self.economic_keywords:
                keyword_lower = keyword.lower()
                
                # Use word boundaries for "fed" to avoid matching "federal" in unrelated contexts
                if keyword == "fed":
                    # Match "fed" as whole word, or "federal reserve", but not just "federal"
                    if re.search(r'\bfed\b', text) or "federal reserve" in text or "fomc" in text:
                        matched_keywords.append(keyword)
                        relevance = "high"
                elif keyword_lower in text:
                    matched_keywords.append(keyword)
                    
                    # High relevance for key economic indicators and central banks
                    high_relevance_keywords = [
                        "federal reserve", "fomc", "interest rate", "rate hike", "rate cut", "rates",
                        "jerome powell", "powell", "fed rate",
                        "inflation", "cpi", "consumer price index", "ppi",
                        "employment", "non-farm payrolls", "nfp", "unemployment", "jobs report",
                        "ecb", "european central bank", "christine lagarde",
                        "bank of england", "boe", "andrew bailey",
                        "bank of japan", "boj", "kazuo ueda", "kuroda",
                        "gdp", "gross domestic product",
                        "eur/usd", "gbp/usd", "usd/jpy", "forex", "fx", "currency"
                    ]
                    
                    medium_relevance_keywords = [
                        "trump", "biden", "president", "presidential", "election",
                        "trade", "tariff", "tariffs", "trade war",
                        "geopolitics", "sanctions", "brexit",
                        "euro", "pound", "yen", "dollar",
                        "central bank", "monetary policy", "policy decision"
                    ]
                    
                    if keyword_lower in high_relevance_keywords:
                        relevance = "high"
                    elif keyword_lower in medium_relevance_keywords and relevance == "low":
                        relevance = "medium"
                    elif relevance == "low":
                        relevance = "medium"  # Default to medium for other economic keywords
            
            # Only include markets that match economic keywords OR have economic tags
            # More lenient: Allow markets with economic tags OR general economic terms
            if not matched_keywords:
                # Check for general economic terms that might not be in keyword list
                general_economic_terms = [
                    "economic", "economy", "market", "financial", "finance", "business",
                    "policy", "government", "regulation", "legislation", "law", "bill",
                    "announcement", "statement", "meeting", "decision", "report", "data"
                ]
                has_general_term = any(term in text_lower for term in general_economic_terms)
                
                # Allow markets with economic tags OR general economic terms
                if has_economic_tag or has_general_term:
                    # Market has economic tag or general term but no specific keyword match
                    relevance = "low"
                    matched_keywords = ["economic_tag"] if has_economic_tag else ["general_economic_term"]
                else:
                    # No keywords, no economic tags, and no general terms - exclude
                    skipped_no_keywords += 1
                    continue
            
            # Relaxed geopolitics filtering - allow if it has economic tag or general terms
            # Only exclude pure geopolitics without any economic connection
            if has_economic_tag and "geopolitics" in tags:
                # Check if it has any economic connection (broader than before)
                economic_connection_keywords = [
                    "trade", "tariff", "sanctions", "currency", "forex", "fx", "exchange rate",
                    "dollar", "euro", "pound", "yen", "yuan", "brexit", "trade war", "trade deal",
                    "usd", "eur", "gbp", "jpy", "cny", "economic", "economy", "market",
                    "financial", "policy", "government", "regulation"
                ]
                has_economic_connection = any(keyword in text_lower for keyword in economic_connection_keywords)
                
                # Only exclude if it's pure geopolitics with no economic connection
                if not has_economic_connection and not matched_keywords:
                    skipped_no_keywords += 1
                    continue
            
            # Economic tags can boost relevance but aren't required
            if has_economic_tag and relevance == "low":
                        relevance = "medium"
            
            if matched_keywords:
                # Determine related event
                related_event = None
                matched_lower = [k.lower() for k in matched_keywords]
                
                if any(k in matched_lower for k in ["fed", "federal reserve", "fomc", "interest rate", "rate hike", "rate cut", "rates", "powell"]):
                    related_event = "FOMC Meeting"
                elif any(k in matched_lower for k in ["inflation", "cpi", "consumer price index", "ppi"]):
                    related_event = "CPI Release"
                elif any(k in matched_lower for k in ["gdp", "gross domestic product"]):
                    related_event = "GDP Release"
                elif any(k in matched_lower for k in ["employment", "nfp", "non-farm payrolls", "jobs report", "unemployment"]):
                    related_event = "Employment Report"
                elif any(k in matched_lower for k in ["ecb", "european central bank", "lagarde"]):
                    related_event = "ECB Meeting"
                elif any(k in matched_lower for k in ["boe", "bank of england", "bailey"]):
                    related_event = "BOE Meeting"
                elif any(k in matched_lower for k in ["boj", "bank of japan", "ueda", "kuroda"]):
                    related_event = "BOJ Meeting"
                elif any(k in matched_lower for k in ["trump", "biden", "president", "presidential", "election"]):
                    related_event = "Election/Politics"
                elif any(k in matched_lower for k in ["trade", "tariff", "tariffs", "trade war"]):
                    related_event = "Trade Policy"
                elif any(k in matched_lower for k in ["eur/usd", "euro", "eurozone"]):
                    related_event = "EUR/USD"
                elif any(k in matched_lower for k in ["gbp/usd", "british pound", "sterling", "pound"]):
                    related_event = "GBP/USD"
                elif any(k in matched_lower for k in ["usd/jpy", "japanese yen", "yen"]):
                    related_event = "USD/JPY"
                elif any(k in matched_lower for k in ["forex", "fx", "currency", "exchange rate"]):
                    related_event = "Forex"
                elif any(k in matched_lower for k in ["geopolitics", "sanctions", "brexit"]):
                    related_event = "Geopolitics"
                else:
                    related_event = "Economic Event"
                
                # Get affected currency pairs - use curated markets if available
                if CURATED_MARKETS_AVAILABLE:
                    affected_pairs = get_affected_pairs_for_keywords(matched_keywords)
                    if not affected_pairs:
                        # Fallback to original method
                        affected_pairs = self._get_affected_currency_pairs(market, matched_keywords, related_event)
                    # Calculate priority score for curated markets
                    priority_score = get_market_priority(matched_keywords)
                else:
                    affected_pairs = self._get_affected_currency_pairs(market, matched_keywords, related_event)
                    priority_score = 0
                
                # IMPORTANT: Filter out resolved markets - do not include them
                # BUT: Allow recently resolved markets (within grace period) for context
                if is_resolved and not is_recently_resolved:
                    skipped_closed += 1
                    continue
                
                # Store Dome API specific fields for later use
                market["relevance"] = relevance
                market["related_event"] = related_event
                market["matched_keywords"] = matched_keywords
                market["affected_currency_pairs"] = affected_pairs
                market["accepting_orders"] = accepting_orders
                market["is_future"] = is_future
                market["days_until_resolution"] = days_until_resolution
                market["is_recently_resolved"] = is_recently_resolved
                market["is_historical"] = is_historical
                market["is_open"] = is_open
                market["is_closed"] = is_closed
                market["priority_score"] = priority_score  # Add priority score for sorting
                relevant_markets.append(market)
                included_markets += 1
        
        # Log filtering statistics with more detail
        logger.info(f"Filtering stats: checked={total_checked}, included={included_markets}, "
                   f"skipped_closed={skipped_closed}, skipped_exclude={skipped_exclude}, "
                   f"skipped_no_keywords={skipped_no_keywords}")
        logger.info(f"Filtering result: {included_markets} markets passed filtering (target: {MAX_FILTERED_MARKETS})")
        
        # Sort by priority (simplified for curated markets):
        # 1. Priority score (curated markets first - higher priority)
        # 2. Markets accepting orders (active trading)
        # 3. Future markets (not resolved yet)
        # 4. Relevance score (high to low)
        # 5. Number of matched keywords (more keywords = more relevant)
        # 6. Resolution date (sooner = more urgent)
        # Note: Volume-based sorting will be done in frontend (highest to lowest)
        relevant_markets.sort(
            key=lambda x: (
                -x.get("priority_score", 0),  # Curated markets first (higher priority score)
                x.get("accepting_orders", False),  # Markets accepting orders first
                x.get("has_embedded_price", False),  # Then markets with embedded prices (free tier optimization)
                x.get("is_future", False),  # Then future markets
                x["relevance"] == "high",  # Then by relevance: high
                x.get("relevance") == "medium",  # Then: medium
                -len(x.get("matched_keywords", [])),  # More matched keywords = higher priority
                -x.get("days_until_resolution", 999) if x.get("days_until_resolution") else 999,  # Closer dates first
            ),
            reverse=True
        )
        
        # Limit to top markets (prioritize quality over quantity)
        max_markets = min(MAX_FILTERED_MARKETS, len(relevant_markets))
        relevant_markets = relevant_markets[:max_markets]
        
        # Return top markets (limited by MAX_FILTERED_MARKETS)
        # Note: Deduplication by market_id already prevents duplicates from appearing
        return relevant_markets[:MAX_FILTERED_MARKETS]
    
    def _fetch_token_price(self, token_id: str, use_rate_limiter: bool = True) -> Optional[float]:
        """Fetch price for a specific token from Dome API
        
        Note: This method attempts to fetch prices using the SDK or direct API calls.
        If prices cannot be fetched, the system will use fallback logic based on market status.
        
        IMPORTANT: Price fetching is disabled by default to avoid rate limits.
        Enable by setting FETCH_MARKET_PRICES=true in environment.
        
        Args:
            token_id: The token ID to fetch price for
            use_rate_limiter: Whether to use rate limiter (default: True). Set to False if 
                            rate limiting is handled externally (e.g., sequential fetching)
        """
        # Skip price fetching by default to avoid rate limits
        # Prices will use fallback logic (50/50 for open markets, winning_side for resolved)
        if not os.getenv('FETCH_MARKET_PRICES', 'false').lower() == 'true':
            return None
        
        if not self.dome_api_key or not token_id:
            return None
        
        try:
            # Use rate limiter before making price request (if enabled)
            if use_rate_limiter:
                dome_rate_limiter.wait_if_needed()
            
            if self.dome_client and DOME_SDK_AVAILABLE:
                # Try using SDK for price fetching
                try:
                    result = self.dome_client.polymarket.markets.get_market_price({
                        "token_id": token_id
                    })
                    
                    # SDK may return price directly or in a nested structure
                    price = None
                    if hasattr(result, 'price'):
                        price = result.price
                    elif isinstance(result, dict):
                        price = result.get("price") or result.get("last_price") or result.get("current_price")
                    
                    if price is not None:
                        return float(price)
                except Exception as e:
                    logger.debug(f"SDK price fetch failed for token {token_id[:20]}...: {e}")
            
            # Fallback to direct HTTP request
            if not DOME_SDK_AVAILABLE or not self.dome_client:
                import requests
                # Use rate limiter before making price request (if enabled)
                if use_rate_limiter:
                    dome_rate_limiter.wait_if_needed()
                
                url = f"{self.dome_api_base_url}/markets/market-price"
                headers = {"Authorization": f"Bearer {self.dome_api_key}"}
                params = {"token_id": token_id}
                
                response = requests.get(url, params=params, headers=headers, timeout=5)
                
                # Handle rate limit errors
                if response.status_code == 429:
                    dome_rate_limiter.record_rate_limit_hit()
                    logger.warning(f"Rate limit hit when fetching price for token {token_id[:20]}...")
                    return None
                if response.status_code == 200:
                    data = response.json()
                    price = data.get("price") or data.get("last_price") or data.get("current_price")
                    if price is not None:
                        return float(price)
        except Exception as e:
            logger.debug(f"Could not fetch price for token {token_id[:20]}...: {e}")
        
        return None
    
    def _normalize_side_object(self, side_raw: Any) -> Dict[str, Any]:
        """Normalize side_a or side_b object to dictionary format
        
        Handles multiple input formats: dict, object with __dict__, or object with __getitem__.
        This eliminates code duplication when processing side_a and side_b.
        
        Args:
            side_raw: Can be dict, object with __dict__, or object with __getitem__
        
        Returns:
            Dictionary with id, label, and any price fields
        """
        if isinstance(side_raw, dict):
            return side_raw.copy()
        
        if hasattr(side_raw, '__dict__'):
            return side_raw.__dict__.copy()
        
        if hasattr(side_raw, '__getitem__'):
            try:
                # Try to extract common fields
                return {
                    k: side_raw[k] 
                    for k in ['id', 'label', 'price', 'current_price', 'last_price', 'token_price', 'yes_price', 'no_price']
                    if k in side_raw or hasattr(side_raw, k)
                }
            except (KeyError, TypeError):
                pass
        
        # Fallback: extract what we can
        return {
            "id": _safe_get(side_raw, "id"),
            "label": _safe_get(side_raw, "label", "")
        }
    
    def _extract_price_from_side(self, side: Dict[str, Any], side_name: str = "side") -> Optional[float]:
        """Extract price from a normalized side dictionary
        
        Checks multiple possible price field names to handle different API response formats.
        
        Args:
            side: Normalized side dictionary
            side_name: Name for logging (e.g., "side_a", "side_b")
        
        Returns:
            Price as float, or None if not found
        """
        if not isinstance(side, dict):
            return None
        
        price_candidate = (
            _safe_get(side, "price") or 
            _safe_get(side, "current_price") or 
            _safe_get(side, "last_price") or
            _safe_get(side, "token_price") or
            _safe_get(side, "yes_price") or
            _safe_get(side, "no_price")
        )
        
        if price_candidate is not None:
            try:
                return float(price_candidate)
            except (ValueError, TypeError):
                logger.debug(f"Price value invalid for {side_name}: {price_candidate}")
                return None
        
        return None
    
    def _extract_prices_from_dome_market(self, market: Dict, fetch_price: bool = False) -> tuple:
        """Extract yes/no prices from Dome API market structure (Polymarket or Kalshi)
        
        Args:
            market: Market data from API
            fetch_price: Whether to fetch prices via API (ALWAYS False on free tier)
        
        Returns:
            Tuple of (yes_price, no_price, price_source)
            price_source: "resolved", "embedded", "api", or "fallback"
        """
        # On free tier, only fetch prices if explicitly requested (for top markets)
        # The fetch_price parameter is controlled by the caller based on market priority
        # We respect the fetch_price parameter even on free tier for top markets
        
        yes_price = None
        no_price = None
        price_source = "fallback"
        platform = market.get("platform", "polymarket")
        
        if platform == "kalshi":
            # Kalshi uses last_price directly (0-100, represents Yes probability)
            last_price = _safe_get(market, "last_price")
            result = _safe_get(market, "result")
            
            if result is not None:
                # Market is resolved - result is "yes" or "no"
                if result.lower() == "yes":
                    yes_price = 1.0
                    no_price = 0.0
                    price_source = "resolved"
                elif result.lower() == "no":
                    yes_price = 0.0
                    no_price = 1.0
                    price_source = "resolved"
            elif last_price is not None:
                # Convert Kalshi price (0-100) to probability (0-1)
                # Kalshi price represents Yes probability
                yes_price = float(last_price) / 100.0
                no_price = 1.0 - yes_price
                price_source = "embedded"
            else:
                # No price available - use fallback
                status = _safe_get(market, "status", "").lower()
                if status == "open":
                    yes_price = 0.5
                    no_price = 0.5
                    price_source = "fallback"
        else:
            # Polymarket uses side_a and side_b with token IDs
            side_a_raw = _safe_get(market, "side_a", {})
            side_b_raw = _safe_get(market, "side_b", {})
            
            # Check for market-level price fields FIRST (some APIs provide this directly)
            # This is checked before side_a/side_b because it's more reliable
            market_yes_price = (_safe_get(market, "yes_price") or 
                               _safe_get(market, "yesPrice") or 
                               _safe_get(market, "yes_price_usd") or
                               _safe_get(market, "current_yes_price"))
            market_no_price = (_safe_get(market, "no_price") or 
                              _safe_get(market, "noPrice") or 
                              _safe_get(market, "no_price_usd") or
                              _safe_get(market, "current_no_price"))
            
            side_a_price = None
            side_b_price = None
            side_a_id = None
            side_b_id = None
            side_a_label = ""
            side_b_label = ""
            
            if market_yes_price is not None and market_no_price is not None:
                try:
                    side_a_price = float(market_yes_price)
                    side_b_price = float(market_no_price)
                    price_source = "embedded"
                    logger.info(f"Found market-level prices: yes={side_a_price}, no={side_b_price}")
                except (ValueError, TypeError):
                    logger.debug(f"Market-level price values invalid: yes={market_yes_price}, no={market_no_price}")
                    market_yes_price = None
                    market_no_price = None
            
            # Handle both dict and object formats for side_a and side_b
            # Only process if we didn't find market-level prices
            if side_a_price is None or side_b_price is None:
                # Normalize side objects to dictionaries using helper method
                side_a = self._normalize_side_object(side_a_raw)
                side_b = self._normalize_side_object(side_b_raw)
                
                side_a_id = side_a.get("id") if isinstance(side_a, dict) else None
                side_b_id = side_b.get("id") if isinstance(side_b, dict) else None
                side_a_label = (side_a.get("label", "") if isinstance(side_a, dict) else "").lower()
                side_b_label = (side_b.get("label", "") if isinstance(side_b, dict) else "").lower()
                
                # Extract prices from sides using helper method
                if side_a_price is None:
                    extracted_price = self._extract_price_from_side(side_a, "side_a")
                    if extracted_price is not None:
                        side_a_price = extracted_price
                        if price_source != "embedded":
                            price_source = "embedded"
                        logger.info(f"Found side_a price in response: {side_a_price}")
                    else:
                        logger.debug(f"No price found in side_a. Available fields: {list(side_a.keys()) if isinstance(side_a, dict) else 'N/A'}")
                
                if side_b_price is None:
                    extracted_price = self._extract_price_from_side(side_b, "side_b")
                    if extracted_price is not None:
                        side_b_price = extracted_price
                        if price_source != "embedded":
                            price_source = "embedded"
                        logger.info(f"Found side_b price in response: {side_b_price}")
                    else:
                        logger.debug(f"No price found in side_b. Available fields: {list(side_b.keys()) if isinstance(side_b, dict) else 'N/A'}")
            else:
                # We already have prices from market-level, but we still need side labels for Yes/No determination
                # Normalize side objects to get labels
                side_a = self._normalize_side_object(side_a_raw)
                side_b = self._normalize_side_object(side_b_raw)
                
                side_a_id = side_a.get("id") if isinstance(side_a, dict) else None
                side_b_id = side_b.get("id") if isinstance(side_b, dict) else None
                side_a_label = (side_a.get("label", "") if isinstance(side_a, dict) else "").lower()
                side_b_label = (side_b.get("label", "") if isinstance(side_b, dict) else "").lower()
            
            # Ensure side_a_label and side_b_label are defined (needed for Yes/No determination)
            if 'side_a_label' not in locals():
                side_a_label = (side_a.get("label", "") if isinstance(side_a, dict) else "").lower() if 'side_a' in locals() else ""
            if 'side_b_label' not in locals():
                side_b_label = (side_b.get("label", "") if isinstance(side_b, dict) else "").lower() if 'side_b' in locals() else ""
            
            # Determine which side is Yes and which is No based on labels
            # This needs to happen before API fetching so we know which side to fetch prices for
            if "yes" in side_a_label or "will" in side_a_label or "up" in side_a_label:
                yes_price_temp = side_a_price
                no_price_temp = side_b_price
            elif "yes" in side_b_label or "will" in side_b_label or "up" in side_b_label:
                yes_price_temp = side_b_price
                no_price_temp = side_a_price
            else:
                # Default: first side is Yes, second is No
                yes_price_temp = side_a_price
                no_price_temp = side_b_price
            
            # If prices not found in response, try fetching via API
            # On free tier, only fetch if fetch_price=True (set for top markets only)
            # On paid tier, respect FETCH_MARKET_PRICES env var
            if yes_price_temp is None or no_price_temp is None:
                # Fetch prices if fetch_price parameter is True
                # On free tier, this is only True for top markets
                # On paid tier, this respects FETCH_MARKET_PRICES env var
                fetch_prices_enabled = fetch_price
                
                if fetch_prices_enabled:
                    # Fetch prices sequentially (one per second) to respect rate limits
                    # Rate limiter ensures 1 query per second automatically
                    # Determine which side is Yes based on labels (if available)
                    side_a_is_yes = side_a_label and ("yes" in side_a_label or "will" in side_a_label or "up" in side_a_label)
                    side_b_is_yes = side_b_label and ("yes" in side_b_label or "will" in side_b_label or "up" in side_b_label)
                    
                    # Fetch Yes price first
                    if yes_price_temp is None:
                        if side_a_is_yes and side_a_id:
                            price_a = self._fetch_token_price(side_a_id, use_rate_limiter=True)
                            yes_price_temp = price_a
                            if price_a is not None:
                                logger.debug(f"Fetched yes_price (side_a): {price_a}")
                                price_source = "api"
                        elif side_b_is_yes and side_b_id:
                            price_b = self._fetch_token_price(side_b_id, use_rate_limiter=True)
                            yes_price_temp = price_b
                            if price_b is not None:
                                logger.debug(f"Fetched yes_price (side_b): {price_b}")
                                price_source = "api"
                        elif side_a_id:  # Fallback: assume side_a is Yes if we can't determine
                            price_a = self._fetch_token_price(side_a_id, use_rate_limiter=True)
                            yes_price_temp = price_a
                            if price_a is not None:
                                logger.debug(f"Fetched yes_price (side_a, fallback): {price_a}")
                                price_source = "api"
                    
                    # Second price fetch - rate limiter will ensure 1 second delay
                    if no_price_temp is None:
                        if side_b_is_yes and side_b_id and yes_price_temp is not None:
                            # side_b is Yes, so side_a must be No
                            if side_a_id:
                                price_a = self._fetch_token_price(side_a_id, use_rate_limiter=True)
                                no_price_temp = price_a
                                if price_a is not None:
                                    logger.debug(f"Fetched no_price (side_a): {price_a}")
                                    if price_source != "api":
                                        price_source = "api"
                        elif side_a_is_yes and side_a_id and yes_price_temp is not None:
                            # side_a is Yes, so side_b must be No
                            if side_b_id:
                                price_b = self._fetch_token_price(side_b_id, use_rate_limiter=True)
                                no_price_temp = price_b
                                if price_b is not None:
                                    logger.debug(f"Fetched no_price (side_b): {price_b}")
                                    if price_source != "api":
                                        price_source = "api"
                        elif side_b_id and yes_price_temp is not None:  # Fallback: assume side_b is No
                            price_b = self._fetch_token_price(side_b_id, use_rate_limiter=True)
                            no_price_temp = price_b
                            if price_b is not None:
                                logger.debug(f"Fetched no_price (side_b, fallback): {price_b}")
                                if price_source != "api":
                                    price_source = "api"
                else:
                    # Price fetching disabled or free tier - prices remain None and will fall back
                    if price_source == "fallback":
                        pass  # Already set to fallback
            
            # Assign final prices
            yes_price = yes_price_temp
            no_price = no_price_temp
            
            # If we couldn't fetch prices, use a fallback: check if market is resolved
            winning_side = _safe_get(market, "winning_side")
            if winning_side is not None:
                # Market is resolved
                if winning_side == side_a_id:
                    yes_price = 1.0
                    no_price = 0.0
                    price_source = "resolved"
                elif winning_side == side_b_id:
                    yes_price = 0.0
                    no_price = 1.0
                    price_source = "resolved"
            
            # Validate prices: If we have 0/1 prices with no volume, mark as invalid
            # This indicates a market with no real trading data
            market_volume = _safe_get(market, "volume") or _safe_get(market, "volume_total") or _safe_get(market, "volume_24h") or 0
            if (yes_price == 0 or yes_price is None) and (no_price == 1 or (no_price is None and yes_price == 0)) and market_volume == 0:
                # Market has no real price data - set to None
                yes_price = None
                no_price = None
                price_source = "invalid"
            
            # Ensure prices always sum to 1 - handle missing prices
            if yes_price is None and no_price is None:
                # Both missing - use 50/50 fallback only if market has volume (indicates it's active)
                status = _safe_get(market, "status", "").lower()
                market_title = market.get('title', 'unknown')[:50]
                if status == "open" and market_volume > 0:
                    # Only use 50/50 fallback for active markets with volume
                    yes_price = 0.5
                    no_price = 0.5
                    price_source = "fallback"
                    if self.is_free_tier:
                        logger.debug(f"Free tier: No embedded price for '{market_title}...' - using 50/50 fallback")
                    else:
                        logger.warning(f"No price data found for open market '{market_title}...' - using 50/50 fallback. "
                                     f"Platform: {platform}, side_a fields: {list(side_a.keys()) if isinstance(side_a, dict) else 'N/A'}, "
                                     f"side_b fields: {list(side_b.keys()) if isinstance(side_b, dict) else 'N/A'}")
                else:
                    # For markets with no volume or closed markets, don't use fallback - leave as None
                    # This will cause the market to be filtered out
                    yes_price = None
                    no_price = None
                    price_source = "invalid"
                    logger.debug(f"No price data and no volume for market {market_title}... - marking as invalid")
            elif yes_price is None and no_price is not None:
                # YES missing - calculate from NO
                yes_price = max(0.0, 1.0 - no_price)
                logger.debug(f"YES price missing, calculated from NO: {yes_price}")
            elif no_price is None and yes_price is not None:
                # NO missing - calculate from YES
                no_price = max(0.0, 1.0 - yes_price)
                logger.debug(f"NO price missing, calculated from YES: {no_price}")
        
        # Normalize to ensure they sum to 1 (if we have both)
        if yes_price is not None and no_price is not None:
            total = yes_price + no_price
            if total > 0:
                yes_price = yes_price / total
                no_price = no_price / total
            else:
                # Both are 0 or negative - fallback to 50/50
                yes_price = 0.5
                no_price = 0.5
        
        return yes_price, no_price, price_source
    
    def _extract_prices_from_clob_market(self, market: Dict) -> tuple:
        """Extract Yes/No prices from CLOB API market structure
        
        Args:
            market: Market dictionary from CLOB API
            
        Returns:
            Tuple of (yes_price, no_price, price_source)
        """
        tokens = market.get("tokens", [])
        
        if not tokens or len(tokens) < 2:
            return None, None, "fallback"
        
        yes_price = None
        no_price = None
        
        # Extract prices from tokens array
        # CLOB API tokens have "outcome" field (e.g., "Yes", "No", "Arizona State", etc.)
        # CRITICAL: Price of 0 might mean "no data" not "0% probability"
        # Check for volume/liquidity to validate prices
        market_volume = market.get("volume") or market.get("volume_total") or 0
        
        for token in tokens:
            outcome = str(token.get("outcome", "")).lower()
            price = token.get("price")
            
            if price is not None:
                try:
                    price_float = float(price)
                    # Only accept price if:
                    # 1. It's in valid range (0 < price < 1), OR
                    # 2. It's exactly 0.5 (50/50), OR
                    # 3. Market has volume (indicates real trading)
                    is_valid_price = (0 < price_float < 1) or price_float == 0.5 or market_volume > 0
                    
                    if is_valid_price:
                        # Check for Yes/No outcomes
                        if outcome == "yes" or (outcome.startswith("yes") and len(outcome) <= 5):
                            yes_price = price_float
                        elif outcome == "no" or (outcome.startswith("no") and len(outcome) <= 4):
                            no_price = price_float
                        # Also check for "will" patterns (e.g., "Will X happen" -> Yes)
                        elif "yes" in outcome or outcome.startswith("will"):
                            if yes_price is None:
                                yes_price = price_float
                except (ValueError, TypeError):
                    pass
        
        # Fallback: use first two tokens if Yes/No not found
        # This handles markets with custom outcomes (e.g., "Arizona State" vs "Nevada")
        # Only use if prices are valid (not both 0 with no volume)
        if yes_price is None and no_price is None and len(tokens) >= 2:
            try:
                price0 = tokens[0].get("price")
                price1 = tokens[1].get("price")
                if price0 is not None and price1 is not None:
                    price0_float = float(price0)
                    price1_float = float(price1)
                    # Only use if at least one price is valid OR market has volume
                    if (0 < price0_float < 1 or 0 < price1_float < 1 or price0_float == 0.5 or price1_float == 0.5) or market_volume > 0:
                        yes_price = price0_float
                        no_price = price1_float
            except (ValueError, TypeError):
                pass
        
        # Normalize to sum to 1.0
        if yes_price is not None and no_price is not None:
            total = yes_price + no_price
            if total > 0:
                yes_price = yes_price / total
                no_price = no_price / total
                # Check if market is resolved (prices are 1.0/0.0 or 0.0/1.0)
                if (yes_price == 1.0 and no_price == 0.0) or (yes_price == 0.0 and no_price == 1.0):
                    return yes_price, no_price, "resolved"
                return yes_price, no_price, "embedded"
            else:
                return 0.5, 0.5, "fallback"
        
        return None, None, "fallback"
    
    def _normalize_market_data(self, market: Dict, fetch_price: bool = False) -> Dict:
        """Normalize market data to our format (handles CLOB API, DOME API, PolyRouter, Polymarket, and Kalshi)
        
        Args:
            market: Raw market data from API
            fetch_price: Whether to fetch prices via API (default: False, always False on free tier)
        """
        platform = market.get("platform", "polymarket")
        source = market.get("_source", "dome")  # "clob_direct", "dome", or "polyrouter"
        
        # Detect if this is PolyRouter data (already normalized by PolyRouter client)
        is_polyrouter = source == "polyrouter"
        
        # Detect if this is CLOB API data structure
        is_clob_structure = source == "clob_direct" or ("question" in market and "tokens" in market)
        
        # Extract prices based on data source
        if is_polyrouter:
            # PolyRouter markets are already normalized by the client, prices are in yes_price/no_price
            yes_price = market.get("yes_price")
            no_price = market.get("no_price")
            # Check if prices are valid (not None and not invalid 0/1 with no volume)
            volume = market.get("volume") or 0
            if (yes_price == 0 and no_price == 1 and volume == 0) or (yes_price is None and no_price is None):
                price_source = "invalid"
            else:
                price_source = "embedded" if (yes_price is not None or no_price is not None) else "fallback"
        elif is_clob_structure:
            yes_price, no_price, price_source = self._extract_prices_from_clob_market(market)
        else:
            # Extract prices from DOME API structure
            yes_price, no_price, price_source = self._extract_prices_from_dome_market(market, fetch_price=fetch_price)
        
        # Check if market is resolved
        # First check platform-specific resolved indicators (most reliable)
        is_resolved = False
        if platform == "kalshi":
            result = _safe_get(market, "result")
            is_resolved = result is not None
        else:
            winning_side = _safe_get(market, "winning_side")
            is_resolved = winning_side is not None
        
        # Don't mark as resolved based on prices alone - prices can be 0%/100% without market being resolved
        # Only trust platform-specific resolved indicators (result, winning_side, closed status)
        # Prices of 0%/100% can just mean very low/high probability, not actual resolution
        
        # Extract volume data (platform-specific)
        if platform == "kalshi":
            volume = _safe_get(market, "volume") or _safe_get(market, "volume_24h")
        else:
            volume = _safe_get(market, "volume_total") or _safe_get(market, "volume_1_week")
        liquidity = None  # Dome API doesn't provide liquidity directly
        
        # Convert resolution date - handle both CLOB (ISO string) and DOME (Unix timestamp)
        resolution_date = None
        if is_clob_structure:
            # CLOB API uses ISO string format
            end_date_iso = _safe_get(market, "end_date_iso")
            if end_date_iso:
                try:
                    # Parse ISO format string
                    resolution_date = end_date_iso
                    # Validate it's a valid ISO format
                    datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    pass
        else:
            # DOME API uses Unix timestamp
            end_time = _safe_get(market, "end_time")
            close_time = _safe_get(market, "close_time")  # Kalshi uses close_time
            resolution_time = end_time or close_time
            
            if resolution_time:
                try:
                    end_date = datetime.fromtimestamp(resolution_time, tz=timezone.utc)
                    resolution_date = end_date.isoformat()
                except (ValueError, TypeError):
                    pass
        
        # Get title/question - CLOB uses "question", DOME/PolyRouter use "title"
        if is_polyrouter:
            # PolyRouter markets already have question field set by normalize_market
            title = _safe_get(market, "question") or _safe_get(market, "title", "")
        elif is_clob_structure:
            title_raw = _safe_get(market, "question", "")
            # Remove "arch" prefix if present (archived markets in CLOB API)
            if title_raw.startswith("arch"):
                title_raw = title_raw[4:]  # Remove "arch" prefix
            title = title_raw
        else:
            title = _safe_get(market, "title", "")
        
        # Get description (Dome API may not have description, use title)
        description = _safe_get(market, "description", title)
        if description:
            description = description[:300]
        
        # Get tags safely (Polymarket has tags, Kalshi might not)
        tags = _safe_get(market, "tags", [])
        category = tags[0] if tags and len(tags) > 0 else None
        
        # Extract URL (platform-specific)
        market_url = None
        if is_polyrouter:
            # PolyRouter uses source_url
            market_url = market.get("url") or market.get("source_url")
        elif is_clob_structure:
            # CLOB API: Construct Polymarket URL from condition_id or slug
            condition_id = _safe_get(market, "condition_id")
            slug = _safe_get(market, "slug") or _safe_get(market, "market_slug")
            if slug:
                market_url = f"https://polymarket.com/event/{slug}"
            elif condition_id:
                # Fallback: use condition_id to construct URL (may not work for all markets)
                market_url = f"https://polymarket.com/condition/{condition_id}"
        else:
            # DOME API: May have url field, or construct from platform
            market_url = _safe_get(market, "url")
            if not market_url and platform == "kalshi":
                # Try to construct Kalshi URL from market_ticker
                market_ticker = _safe_get(market, "market_ticker")
                event_ticker = _safe_get(market, "event_ticker")
                if market_ticker and event_ticker:
                    # Kalshi URL format: /markets/{event_ticker}/{market_ticker}
                    market_url = f"https://kalshi.com/markets/{event_ticker}/{market_ticker}"
        
        # Get market ID (platform-specific)
        if platform == "kalshi":
            market_id = _safe_get(market, "market_ticker") or _safe_get(market, "event_ticker", "")
        else:
            market_id = _safe_get(market, "condition_id", "")
        
        # Determine active/closed status - handle both CLOB (booleans/strings) and DOME (status string)
        if is_clob_structure:
            # CLOB API may return strings "True"/"False" or actual booleans
            active_val = _safe_get(market, "active", False)
            closed_val = _safe_get(market, "closed", False)
            accepting_orders_val = _safe_get(market, "accepting_orders", False)
            
            # Convert string booleans to actual booleans
            active = active_val if isinstance(active_val, bool) else str(active_val).lower() == "true"
            closed = closed_val if isinstance(closed_val, bool) else str(closed_val).lower() == "true"
            accepting_orders = accepting_orders_val if isinstance(accepting_orders_val, bool) else str(accepting_orders_val).lower() == "true"
        else:
            # DOME API uses status string
            status = _safe_get(market, "status", "").lower()
            active = status == "open"
            closed = status == "closed"
            accepting_orders = _safe_get(market, "accepting_orders", False) or active
        
        # Don't filter out markets with invalid prices here - let them through
        # The frontend will handle displaying "No price data" for these markets
        # Only filter out if BOTH prices are None AND market is closed/resolved (truly invalid)
        if price_source == "invalid" and (yes_price is None and no_price is None):
            # Only filter if market is also closed/resolved (double-check)
            if is_resolved or closed:
                # Return None to indicate this market should be filtered out
                return None
            # Otherwise, allow through with None prices (frontend will show "No data")
        
        # Determine price quality based on source
        price_quality_map = {
            "resolved": "high",
            "api": "high",
            "embedded": "medium",
            "fallback": "low"
        }
        price_quality = price_quality_map.get(price_source, "low")
        
        return {
            "id": market_id,
            "platform": platform,
            "question": title,  # Use title/question as question for display
            "description": description,
            "category": category,
            "yes_price": yes_price,
            "no_price": no_price,
            "price_source": price_source,  # Track where price came from
            "price_quality": price_quality,  # Quality indicator (high/medium/low)
            "liquidity": liquidity,
            "volume": volume,
            "resolution_date": resolution_date,
            "active": active,
            "closed": closed,
            "accepting_orders": accepting_orders,
            "is_resolved": is_resolved,
            "is_future": _safe_get(market, "is_future", False),
            "is_historical": _safe_get(market, "is_historical", False),
            "days_until_resolution": _safe_get(market, "days_until_resolution"),
            "relevance": _safe_get(market, "relevance", "low"),
            "related_event": _safe_get(market, "related_event"),
            "affected_currency_pairs": _safe_get(market, "affected_currency_pairs", []),  # Currency pairs affected by this market
            "url": market_url  # URL to view market on original platform
        }
    
    def _do_refresh(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Internal method to perform the actual refresh (called with lock protection)"""
        try:
            # Fetch fresh data from both platforms
            logger.info("Fetching fresh prediction markets data from Dome API (Polymarket + Kalshi)")
            
            # Use instance-level early stopping threshold
            early_stop_threshold = self.early_stop_threshold
            
            # Fetch from all available sources
            all_markets = []
            
            # Fetch from PolyRouter API (provides normalized data with prices)
            polyrouter_markets = []
            
            if self.polyrouter_client and self.polyrouter_client.available:
                # Fetch from both Polymarket and Kalshi via PolyRouter
                polymarket_markets_pr = self.polyrouter_client.get_markets(platform="polymarket", limit=100)
                kalshi_markets_pr = self.polyrouter_client.get_markets(platform="kalshi", limit=100)
                
                # Normalize and add source marker
                for market in polymarket_markets_pr + kalshi_markets_pr:
                    try:
                        normalized = self.polyrouter_client.normalize_market(market)
                        normalized["_source"] = "polyrouter"
                        all_markets.append(normalized)
                    except Exception as e:
                        logger.warning(f"Failed to normalize PolyRouter market: {e}")
                        continue
                
                logger.info(f"Fetched {len(polymarket_markets_pr)} Polymarket + {len(kalshi_markets_pr)} Kalshi markets from PolyRouter")
            
            # Fetch from direct APIs (CLOB and DOME) as fallback/supplement
            # On free tier, fetch platforms sequentially with delays to stay within 10-per-10-seconds limit
            # On paid tier, can fetch in parallel
            if self.is_free_tier:
                # Fetch Polymarket first (2 API calls max)
                logger.info(f"Fetching Polymarket markets (free tier: max {self.max_pages_polymarket} pages)")
                polymarket_markets = self._fetch_polymarket_markets(early_stop_threshold=early_stop_threshold)
                
                # Wait to ensure we don't exceed 10-per-10-seconds limit
                # We've used 2 calls, wait 2 seconds before next platform
                if len(polymarket_markets) > 0:
                    logger.info("Waiting 2 seconds before fetching Kalshi markets (free tier rate limit)")
                    time.sleep(2)
                
                # Fetch Kalshi (2 API calls max)
                logger.info(f"Fetching Kalshi markets (free tier: max {self.max_pages_kalshi} pages)")
                kalshi_markets = self._fetch_kalshi_markets(early_stop_threshold=early_stop_threshold)
                
                # Total: 4 API calls, well within 10-per-10-seconds limit
                all_markets.extend(polymarket_markets)
                all_markets.extend(kalshi_markets)
            else:
                # On paid tier, can fetch in parallel
                with ThreadPoolExecutor(max_workers=2) as executor:
                    polymarket_future = executor.submit(
                        self._fetch_polymarket_markets, 
                        early_stop_threshold=early_stop_threshold
                    )
                    kalshi_future = executor.submit(
                        self._fetch_kalshi_markets,
                        early_stop_threshold=early_stop_threshold
                    )
                    polymarket_markets = polymarket_future.result()
                    kalshi_markets = kalshi_future.result()
                    all_markets.extend(polymarket_markets)
                    all_markets.extend(kalshi_markets)
            
            # Count markets from each source (handle both dict and object types)
            polyrouter_count = sum(1 for m in all_markets if (
                isinstance(m, dict) and m.get("_source") == "polyrouter"
            ) or (hasattr(m, "_source") and getattr(m, "_source", None) == "polyrouter"))
            polymarket_count = len(polymarket_markets) if 'polymarket_markets' in locals() else 0
            kalshi_count = len(kalshi_markets) if 'kalshi_markets' in locals() else 0
            
            logger.info(f"Fetched {polyrouter_count} PolyRouter + "
                       f"{polymarket_count} Polymarket + {kalshi_count} Kalshi = {len(all_markets)} total markets")
            
            if not all_markets:
                logger.warning("Failed to fetch any markets from APIs")
                # Only return cached data if we have absolutely nothing else
                if self.cached_markets:
                    logger.info("Falling back to cached data due to API failure")
                    return {
                        "status": "success",
                        "markets": self.cached_markets,
                        "cached": True,
                        "stale": True,
                        "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
                    }
                return {
                    "status": "error",
                    "error": "Failed to fetch markets. Check API configuration (DOME_API_KEY for Kalshi, CLOB API for Polymarket).",
                    "markets": []
                }
            
            # Filter for economic relevance
            filtered_markets = self._filter_economic_markets(all_markets)
            
            if not filtered_markets:
                logger.warning(f"No economic markets found after filtering (checked {len(all_markets)} total markets)")
                # If filtering produced nothing, still prefer fresh filtered results over stale cache
                # This indicates the Dome API returned markets but none matched our criteria
                return {
                    "status": "success",
                    "markets": [],
                    "cached": False,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Normalize data
            normalized_markets = []
            
            # Optimize price fetching: prioritize markets with embedded prices (Kalshi markets)
            # Sort markets to prioritize those with embedded prices (avoids API calls)
            filtered_markets.sort(
                key=lambda x: (
                    x.get("has_embedded_price", False),  # Markets with embedded prices first
                    x.get("relevance") == "high",  # Then by relevance
                    x.get("relevance") == "medium",
                ),
                reverse=True
            )
            
            if self.is_free_tier:
                # On free tier, fetch prices for top markets only
                # Prioritize Kalshi markets (have embedded prices) to minimize API calls
                max_price_fetch_markets = FREE_TIER_MAX_PRICE_FETCH_MARKETS
                fetch_prices_enabled = True
                
                # Count how many markets need price fetching (Polymarket markets without embedded prices)
                markets_needing_price_fetch = [
                    m for m in filtered_markets[:max_price_fetch_markets]
                    if m.get("platform", "polymarket") == "polymarket" and not m.get("has_embedded_price", False)
                ]
                price_queries_needed = len(markets_needing_price_fetch) * 2  # 2 queries per market
                
                logger.info(f"Free tier: Will fetch prices for {len(markets_needing_price_fetch)} Polymarket markets "
                          f"({price_queries_needed} queries, ~{price_queries_needed} seconds). "
                          f"Kalshi markets have embedded prices (no API calls needed).")
            else:
                # On paid tier, respect FETCH_MARKET_PRICES env var
                fetch_prices_enabled = os.getenv('FETCH_MARKET_PRICES', 'false').lower() == 'true'
                max_price_fetch_markets = PAID_TIER_MAX_PRICE_FETCH_MARKETS  # Paid tier can fetch more
                
                if fetch_prices_enabled:
                    # Count Polymarket markets that need price fetching
                    polymarket_count = sum(1 for m in filtered_markets if m.get("platform", "polymarket") == "polymarket")
                    total_price_queries_needed = polymarket_count * 2  # 2 prices per Polymarket market
                    logger.info(f"Price fetching enabled: Will fetch prices for {polymarket_count} Polymarket markets "
                              f"({total_price_queries_needed} queries, ~{total_price_queries_needed} seconds)")
            
            for idx, m in enumerate(filtered_markets):
                # Log first market structure for debugging (only once per refresh)
                if len(normalized_markets) == 0:
                    import json
                    logger.info(f"Sample market structure from Dome API - Top-level keys: {list(m.keys())[:30]}")
                    if "side_a" in m:
                        side_a_sample = m.get("side_a")
                        if isinstance(side_a_sample, dict):
                            logger.info(f"Sample side_a fields: {list(side_a_sample.keys())}")
                            logger.info(f"Sample side_a values: {json.dumps({k: v for k, v in list(side_a_sample.items())[:10]}, default=str)}")
                        else:
                            logger.info(f"Sample side_a type: {type(side_a_sample)}, value: {str(side_a_sample)[:200]}")
                    if "side_b" in m:
                        side_b_sample = m.get("side_b")
                        if isinstance(side_b_sample, dict):
                            logger.info(f"Sample side_b fields: {list(side_b_sample.keys())}")
                            logger.info(f"Sample side_b values: {json.dumps({k: v for k, v in list(side_b_sample.items())[:10]}, default=str)}")
                    # Check for any price-related fields at market level
                    price_fields = [k for k in m.keys() if 'price' in k.lower() or 'yes' in k.lower() or 'no' in k.lower()]
                    if price_fields:
                        logger.info(f"Found price-related fields at market level: {price_fields}")
                
                # On free tier, only fetch prices for Polymarket markets without embedded prices
                # Kalshi markets have embedded prices, so skip API calls for them
                if self.is_free_tier:
                    # Only fetch prices for Polymarket markets without embedded prices
                    is_polymarket = m.get("platform", "polymarket") == "polymarket"
                    has_embedded = m.get("has_embedded_price", False)
                    should_fetch_price = fetch_prices_enabled and is_polymarket and not has_embedded and idx < max_price_fetch_markets
                else:
                    # On paid tier, fetch prices for all markets if enabled
                    should_fetch_price = fetch_prices_enabled and (
                        not self.is_free_tier or idx < max_price_fetch_markets
                    )
                
                # Normalize market data (fetch prices for top markets on free tier)
                normalized = self._normalize_market_data(m, fetch_price=should_fetch_price)
                # Only add if normalization returned valid market (not None - indicates invalid prices)
                if normalized is not None:
                    normalized_markets.append(normalized)
                
                # Log progress for markets with price fetching
                if should_fetch_price and m.get("platform", "polymarket") == "polymarket":
                    progress = idx + 1
                    if self.is_free_tier:
                        logger.info(f"Free tier: Fetching prices for market {progress}/{max_price_fetch_markets}")
                    else:
                        polymarket_count = sum(1 for m in filtered_markets if m.get("platform", "polymarket") == "polymarket")
                        logger.info(f"Price fetching progress: {progress}/{polymarket_count} Polymarket markets processed")
            
            # Note: We no longer filter out resolved markets here because we already filter them
            # in _filter_economic_markets (except for recently resolved ones within grace period)
            # This allows recently resolved markets to be displayed
            
            # Save to cache
            self._save_cache(normalized_markets)
            self.cached_markets = normalized_markets
            self.cache_timestamp = datetime.now(timezone.utc)
            
            logger.info(f"Successfully fetched and cached {len(normalized_markets)} prediction markets")
            return {
                "status": "success",
                "markets": normalized_markets,
                "cached": False,
                "timestamp": self.cache_timestamp.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error refreshing prediction markets: {e}")
            import traceback
            traceback.print_exc()
            
            # Only return cached data if API throws an exception
            if self.cached_markets:
                logger.info("Returning cached data due to exception")
                return {
                    "status": "success",
                    "markets": self.cached_markets,
                    "cached": True,
                    "stale": True,
                    "error": str(e)
                }
            
            return {
                "status": "error",
                "error": str(e),
                "markets": []
            }
    
    def get_prediction_markets(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get filtered prediction markets with rate limiting workarounds
        
        Strategy (similar to news feed):
        1. Load cache (even if stale) for fast UI response
        2. Check if should fetch new markets (based on last_fetch interval)
        3. If cache exists and not forcing refresh, return stale cache immediately
        4. If should fetch new, trigger background refresh (don't wait)
        5. Only block and wait if force_refresh=True AND no refresh in progress
        
        On free tier, be more conservative with refreshes to avoid hitting rate limits.
        """
        try:
            # Load cache (even if stale) for fast UI response - similar to news feed pattern
            cached_markets = None
            last_fetch = None
            
            if self.use_persistent_cache:
                # Use persistent cache with metadata batching
                cache_result = self.persistent_cache.load_markets(allow_stale=True, return_metadata=True)
                if cache_result and isinstance(cache_result, dict):
                    cached_markets = cache_result.get('markets', [])
                    last_fetch = cache_result.get('last_fetch')
                    if cached_markets:
                        # Update local cache state
                        self.cached_markets = cached_markets
                        if last_fetch:
                            try:
                                self.cache_timestamp = datetime.fromisoformat(last_fetch.replace('Z', '+00:00'))
                            except (ValueError, TypeError):
                                pass
                elif cache_result:
                    cached_markets = cache_result
                    self.cached_markets = cached_markets
            else:
                # Fallback: use existing cache loading
                if self.cached_markets:
                    cached_markets = self.cached_markets
            
            # Check if should fetch new markets (similar to news feed)
            should_fetch_new = False
            if not force_refresh:
                if self.use_persistent_cache:
                    # Use batched metadata to avoid extra Firebase call
                    should_fetch_new = self.persistent_cache.should_fetch_new_markets(
                        fetch_interval_minutes=self._background_refresh_interval_minutes,
                        last_fetch=last_fetch
                    )
                else:
                    # Fallback: check cache age
                    if self.cache_timestamp:
                        cache_age = datetime.now(timezone.utc) - self.cache_timestamp.replace(tzinfo=timezone.utc)
                        cache_age_minutes = cache_age.total_seconds() / 60
                        should_fetch_new = cache_age_minutes >= self._background_refresh_interval_minutes
                    else:
                        should_fetch_new = True
            else:
                should_fetch_new = True
            
            # If cache exists and not forcing refresh, return stale cache immediately (fast UI)
            if cached_markets and not force_refresh:
                logger.info(f"Returning cached prediction markets ({len(cached_markets)} markets) for fast UI loading")
                
                # Trigger background refresh if should fetch new (but don't wait)
                if should_fetch_new:
                    logger.info("Cache is stale, triggering background refresh")
                    self._trigger_background_refresh()
                
                return {
                    "status": "success",
                    "markets": cached_markets,
                    "cached": True,
                    "stale": should_fetch_new,  # Mark as stale if refresh is needed
                    "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
                }
            
            # Need to refresh - check if refresh is already in progress
            with self._refresh_lock:
                if self._refresh_in_progress:
                    # Another request is already refreshing - return stale cache immediately
                    logger.info("Refresh already in progress, returning stale cache")
                    if cached_markets:
                        return {
                            "status": "success",
                            "markets": cached_markets,
                            "cached": True,
                            "stale": True,
                            "refresh_in_progress": True,
                            "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
                        }
                    # No cache available, wait for in-progress refresh
                    logger.info("No cache available, waiting for in-progress refresh")
                    self._refresh_in_progress = False  # Reset flag to allow waiting
                
                # Mark refresh as in progress
                self._refresh_in_progress = True
            
            # Perform refresh (only blocks if force_refresh=True)
            try:
                result = self._do_refresh(force_refresh=force_refresh)
                return result
            finally:
                # Always clear the refresh flag
                with self._refresh_lock:
                    self._refresh_in_progress = False
        
        except Exception as e:
            logger.error(f"Error getting prediction markets: {e}")
            import traceback
            traceback.print_exc()
            
            # Clear refresh flag on error
            with self._refresh_lock:
                self._refresh_in_progress = False
            
            # Only return cached data if API throws an exception
            if self.cached_markets:
                logger.info("Returning cached data due to exception")
                return {
                    "status": "success",
                    "markets": self.cached_markets,
                    "cached": True,
                    "stale": True,
                    "error": str(e)
                }
            
            return {
                "status": "error",
                "error": str(e),
                "markets": []
            }
    
    def _trigger_background_refresh(self):
        """Trigger a background refresh without blocking the current request"""
        with self._refresh_lock:
            # Don't trigger if refresh already in progress
            if self._refresh_in_progress:
                return
            
            # Don't trigger if we just refreshed recently
            if self._last_background_refresh:
                time_since_refresh = (datetime.now(timezone.utc) - self._last_background_refresh).total_seconds() / 60
                if time_since_refresh < self._background_refresh_interval_minutes:
                    return
            
            # Mark refresh as in progress
            self._refresh_in_progress = True
            
            # Submit background refresh task
            def background_refresh():
                try:
                    logger.info("Starting background refresh of prediction markets")
                    self._do_refresh(force_refresh=False)
                    self._last_background_refresh = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(f"Background refresh failed: {e}")
                finally:
                    with self._refresh_lock:
                        self._refresh_in_progress = False
            
            self._refresh_future = self._refresh_executor.submit(background_refresh)
            logger.info("Background refresh triggered")

# Singleton instance
prediction_markets_service = PredictionMarketsService()

