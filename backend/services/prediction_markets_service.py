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

if not DOME_SDK_AVAILABLE:
    logger.warning("dome-api-sdk not installed. Install with: pip install dome-api-sdk")

# Configuration constants for free tier optimization
FREE_TIER_MAX_PAGES_PER_PLATFORM = 2  # Reduced from 5/3 to 2/2 to stay within 10 queries per 10 seconds
FREE_TIER_EARLY_STOP_THRESHOLD = 200  # Stop when we have 200 raw markets (enough to filter to 30+)
FREE_TIER_CACHE_EXPIRATION_MINUTES = 30  # Increased from 10 to reduce refresh frequency
FREE_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES = 20  # Refresh every 20 minutes in background

# Paid tier defaults
PAID_TIER_MAX_PAGES_POLYMARKET = 5
PAID_TIER_MAX_PAGES_KALSHI = 3
PAID_TIER_EARLY_STOP_THRESHOLD = 150
PAID_TIER_CACHE_EXPIRATION_MINUTES = 10
PAID_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES = 5

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
        # Cache file in backend directory to match other services
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "prediction_markets_cache.json")
        self.cache_file = os.path.normpath(self.cache_file)
        self.cached_markets = None
        self.cache_timestamp = None
        
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
        
        # Request deduplication: prevent concurrent refresh requests
        self._refresh_lock = threading.Lock()
        self._refresh_in_progress = False
        self._refresh_future = None
        self._refresh_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="prediction_markets_refresh")
        
        # Background refresh tracking
        self._last_background_refresh = None
        
        # API call budget tracking (for free tier 10-per-10-seconds limit)
        self._api_calls_last_10_seconds = []
        self._api_call_lock = threading.Lock()
        
        # Dome API configuration
        self.dome_api_key = os.getenv('DOME_API_KEY')
        self.api_available = False
        
        if not self.dome_api_key:
            logger.warning("DOME_API_KEY not set. Prediction markets will not be available.")
            self.dome_client = None
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
            # Fallback to direct HTTP requests
            self.dome_api_base_url = "https://api.domeapi.io/v1/polymarket"
        
        # Economic keywords for filtering - expanded to include forex-relevant markets
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
            "stimulus", "austerity", "spending", "tax", "taxes", "revenue"
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
        
        self._load_cache()
    
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
        """Load cached markets data"""
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
        """Save markets to cache"""
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
    
    def _fetch_polymarket_markets(self, early_stop_threshold: int = None) -> List[Dict]:
        """Fetch markets from Polymarket via Dome API using SDK
        
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
                # Detect platform from dict structure
                if "market_ticker" in market or "event_ticker" in market:
                    market["platform"] = "kalshi"
                else:
                    market["platform"] = market.get("platform", "polymarket")
            
            # Deduplicate by market identifier
            if market.get("platform") == "kalshi":
                market_id = _safe_get(market, "market_ticker") or _safe_get(market, "event_ticker")
            else:
                market_id = _safe_get(market, "condition_id")
            
            if not market_id or market_id in seen_ids:
                continue
            seen_ids.add(market_id)
            
            # Check if market is resolved - exclude all resolved markets
            platform = market.get("platform", "polymarket")
            is_resolved = False
            if platform == "kalshi":
                # Kalshi: market is resolved if result field is not None
                result = _safe_get(market, "result")
                is_resolved = result is not None
            else:
                # Polymarket: market is resolved if winning_side is not None
                winning_side = _safe_get(market, "winning_side")
                is_resolved = winning_side is not None
            
            # Skip all resolved markets
            if is_resolved:
                skipped_closed += 1
                continue
            
            # Get title (both platforms use "title")
            title = _safe_get(market, "title", "").lower()
            
            # Handle tags (Polymarket has tags array, Kalshi might not)
            tags_list = _safe_get(market, "tags", [])
            if not tags_list:
                tags_list = []
            tags = [tag.lower() if isinstance(tag, str) else str(tag).lower() for tag in tags_list]
            text = f"{title} {' '.join(tags)}"
            
            # Check if market has economic tags
            has_economic_tag = any(econ_tag in tags for econ_tag in self.economic_tags)
            
            # Status field (both platforms use "status")
            status = _safe_get(market, "status", "").lower()
            is_open = status == "open"
            is_closed = status == "closed"
            
            # Note: Resolved markets are already filtered out above
            # We'll filter closed markets after checking relevance (only open/active markets are shown)
            
            # Track whether market is accepting orders (open markets are accepting orders)
            accepting_orders = is_open
            
            # NEW: Check if market has embedded price data (prioritize these on free tier)
            has_embedded_price = False
            
            if platform == "kalshi":
                has_embedded_price = _safe_get(market, "last_price") is not None
            else:
                # Polymarket: Check if side_a or side_b have prices
                side_a = _safe_get(market, "side_a", {})
                side_b = _safe_get(market, "side_b", {})
                
                if isinstance(side_a, dict):
                    has_embedded_price = any(
                        _safe_get(side_a, key) is not None 
                        for key in ["price", "current_price", "last_price", "token_price"]
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
            
            # Store price availability flag
            market["has_embedded_price"] = has_embedded_price
            
            # Check if market has future resolution date
            # Both platforms use Unix timestamps: end_time, close_time (Kalshi), completed_time (Polymarket)
            end_time = _safe_get(market, "end_time")
            close_time = _safe_get(market, "close_time")  # Kalshi uses close_time
            completed_time = _safe_get(market, "completed_time")  # Polymarket uses completed_time
            
            is_future = False
            days_until_resolution = None
            
            resolution_time = end_time or close_time
            if resolution_time:
                try:
                    # Convert Unix timestamp to datetime
                    end_date = datetime.fromtimestamp(resolution_time, tz=timezone.utc)
                    is_future = end_date > now
                    days_until_resolution = (end_date - now).days
                except (ValueError, TypeError):
                    pass
            
            # Track recently resolved markets (within last 30 days)
            is_recently_resolved = False
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
            # Relaxed: Allow markets with economic tags even without keyword matches
            if not matched_keywords:
                # Allow markets with economic tags (more lenient than before)
                # This includes: politics, geopolitics, economics, finance, policy, elections, presidential
                if has_economic_tag:
                    # Market has economic tag but no keyword match - assign low relevance
                    relevance = "low"
                    matched_keywords = ["economic_tag"]  # Placeholder to allow through
                else:
                    # No keywords AND no economic tags - exclude
                    skipped_no_keywords += 1
                    continue
            
            # NEW: Stricter geopolitics filtering - geopolitics tag alone isn't enough
            # Must have forex-relevant keywords (currency, trade, sanctions affecting forex, etc.)
            if has_economic_tag and "geopolitics" in tags:
                # Check if it has actual forex-relevant keywords
                forex_relevant_geopolitics_keywords = [
                    "trade", "tariff", "sanctions", "currency", "forex", "fx", "exchange rate",
                    "dollar", "euro", "pound", "yen", "yuan", "brexit", "trade war", "trade deal",
                    "usd", "eur", "gbp", "jpy", "cny", "economic", "economy"
                ]
                has_forex_relevant_geo = any(keyword in text_lower for keyword in forex_relevant_geopolitics_keywords)
                
                if not has_forex_relevant_geo:
                    # Geopolitics tag but no forex relevance - exclude
                    skipped_no_keywords += 1
                    continue
            
            # Economic tags can boost relevance but aren't required
            if has_economic_tag and relevance == "low":
                        relevance = "medium"
            
            # Filter closed markets: exclude closed markets UNLESS they're recently closed (within last 7 days)
            # This allows us to show more markets while still prioritizing active ones
            # Note: Resolved markets are already filtered out above
            if is_closed:
                # Allow recently closed markets (within 7 days) to show more results
                if completion_time:
                    try:
                        completed_date = datetime.fromtimestamp(completion_time, tz=timezone.utc)
                        days_since_closed = (now - completed_date).days
                        if days_since_closed > 7:
                            skipped_closed += 1
                            continue
                        # Market closed within last 7 days - allow it but mark as closed
                    except (ValueError, TypeError):
                        # Can't parse date, exclude closed market
                        skipped_closed += 1
                        continue
                else:
                    # Closed but no completion time - exclude
                    skipped_closed += 1
                    continue
            
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
                
                # Store Dome API specific fields for later use
                market["relevance"] = relevance
                market["related_event"] = related_event
                market["matched_keywords"] = matched_keywords
                market["accepting_orders"] = accepting_orders
                market["is_future"] = is_future
                market["days_until_resolution"] = days_until_resolution
                market["is_recently_resolved"] = is_recently_resolved
                market["is_historical"] = is_historical
                market["is_open"] = is_open
                market["is_closed"] = is_closed
                relevant_markets.append(market)
                included_markets += 1
        
        # Log filtering statistics
        logger.info(f"Filtering stats: checked={total_checked}, included={included_markets}, "
                   f"skipped_closed={skipped_closed}, skipped_exclude={skipped_exclude}, "
                   f"skipped_no_keywords={skipped_no_keywords}")
        
        # Sort by priority:
        # 1. Markets accepting orders (highest priority - most "live")
        # 2. Markets with embedded prices (important on free tier to avoid API calls)
        # 3. Future markets (upcoming)
        # 4. By relevance score (high > medium > low)
        # 5. By number of matched keywords
        # 6. By resolution date (closer first)
        relevant_markets.sort(
            key=lambda x: (
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
        
        # Return top 30 markets (increased to show more options)
        # Note: Deduplication by market_id already prevents duplicates from appearing
        return relevant_markets[:30]
    
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
                    logger.info(f"✅ Found market-level prices: yes={side_a_price}, no={side_b_price}")
                except (ValueError, TypeError):
                    logger.debug(f"⚠️ Market-level price values invalid: yes={market_yes_price}, no={market_no_price}")
                    market_yes_price = None
                    market_no_price = None
            
            # Handle both dict and object formats for side_a and side_b
            # Only process if we didn't find market-level prices
            if side_a_price is None or side_b_price is None:
                # Improved object handling - try multiple methods to extract data
                if not isinstance(side_a_raw, dict):
                    # Try to convert object to dict
                    if hasattr(side_a_raw, '__dict__'):
                        side_a = side_a_raw.__dict__.copy()
                    elif hasattr(side_a_raw, '__getitem__'):
                        # Try to access as dict-like
                        try:
                            side_a = {k: side_a_raw[k] for k in ['id', 'label', 'price', 'current_price', 'last_price', 'token_price'] if hasattr(side_a_raw, k) or (hasattr(side_a_raw, '__getitem__') and k in side_a_raw)}
                        except:
                            side_a = {"id": _safe_get(side_a_raw, "id"), "label": _safe_get(side_a_raw, "label", "")}
                    else:
                        side_a = {"id": _safe_get(side_a_raw, "id"), "label": _safe_get(side_a_raw, "label", "")}
                else:
                    side_a = side_a_raw.copy() if isinstance(side_a_raw, dict) else {}
                
                # Same for side_b
                if not isinstance(side_b_raw, dict):
                    if hasattr(side_b_raw, '__dict__'):
                        side_b = side_b_raw.__dict__.copy()
                    elif hasattr(side_b_raw, '__getitem__'):
                        try:
                            side_b = {k: side_b_raw[k] for k in ['id', 'label', 'price', 'current_price', 'last_price', 'token_price'] if hasattr(side_b_raw, k) or (hasattr(side_b_raw, '__getitem__') and k in side_b_raw)}
                        except:
                            side_b = {"id": _safe_get(side_b_raw, "id"), "label": _safe_get(side_b_raw, "label", "")}
                    else:
                        side_b = {"id": _safe_get(side_b_raw, "id"), "label": _safe_get(side_b_raw, "label", "")}
                else:
                    side_b = side_b_raw.copy() if isinstance(side_b_raw, dict) else {}
                
                side_a_id = side_a.get("id") if isinstance(side_a, dict) else None
                side_b_id = side_b.get("id") if isinstance(side_b, dict) else None
                side_a_label = (side_a.get("label", "") if isinstance(side_a, dict) else "").lower()
                side_b_label = (side_b.get("label", "") if isinstance(side_b, dict) else "").lower()
                
                # Check if prices are included directly in side_a/side_b (Dome API may include this)
                if isinstance(side_a, dict):
                    # Check multiple possible price field names
                    side_a_price_candidate = (_safe_get(side_a, "price") or 
                                           _safe_get(side_a, "current_price") or 
                                           _safe_get(side_a, "last_price") or
                                           _safe_get(side_a, "token_price") or
                                           _safe_get(side_a, "yes_price") or
                                           _safe_get(side_a, "no_price"))
                    if side_a_price_candidate is not None:
                        try:
                            side_a_price = float(side_a_price_candidate)
                            if price_source != "embedded":
                                price_source = "embedded"
                            logger.info(f"✅ Found side_a price in response: {side_a_price}")
                        except (ValueError, TypeError):
                            logger.debug(f"⚠️ side_a price value invalid: {side_a_price_candidate}")
                            side_a_price = None
                    else:
                        logger.debug(f"⚠️ No price found in side_a. Available fields: {list(side_a.keys()) if isinstance(side_a, dict) else 'N/A'}")
                
                if isinstance(side_b, dict):
                    # Check multiple possible price field names
                    side_b_price_candidate = (_safe_get(side_b, "price") or 
                                           _safe_get(side_b, "current_price") or 
                                           _safe_get(side_b, "last_price") or
                                           _safe_get(side_b, "token_price") or
                                           _safe_get(side_b, "yes_price") or
                                           _safe_get(side_b, "no_price"))
                    if side_b_price_candidate is not None:
                        try:
                            side_b_price = float(side_b_price_candidate)
                            if price_source != "embedded":
                                price_source = "embedded"
                            logger.info(f"✅ Found side_b price in response: {side_b_price}")
                        except (ValueError, TypeError):
                            logger.debug(f"⚠️ side_b price value invalid: {side_b_price_candidate}")
                            side_b_price = None
                    else:
                        logger.debug(f"⚠️ No price found in side_b. Available fields: {list(side_b.keys()) if isinstance(side_b, dict) else 'N/A'}")
            else:
                # We already have prices from market-level, but we still need side labels for Yes/No determination
                if not isinstance(side_a_raw, dict):
                    if hasattr(side_a_raw, '__dict__'):
                        side_a = side_a_raw.__dict__.copy()
                    else:
                        side_a = {"id": _safe_get(side_a_raw, "id"), "label": _safe_get(side_a_raw, "label", "")}
                else:
                    side_a = side_a_raw.copy() if isinstance(side_a_raw, dict) else {}
                
                if not isinstance(side_b_raw, dict):
                    if hasattr(side_b_raw, '__dict__'):
                        side_b = side_b_raw.__dict__.copy()
                    else:
                        side_b = {"id": _safe_get(side_b_raw, "id"), "label": _safe_get(side_b_raw, "label", "")}
                else:
                    side_b = side_b_raw.copy() if isinstance(side_b_raw, dict) else {}
                
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
                                logger.debug(f"✅ Fetched yes_price (side_a): {price_a}")
                                price_source = "api"
                        elif side_b_is_yes and side_b_id:
                            price_b = self._fetch_token_price(side_b_id, use_rate_limiter=True)
                            yes_price_temp = price_b
                            if price_b is not None:
                                logger.debug(f"✅ Fetched yes_price (side_b): {price_b}")
                                price_source = "api"
                        elif side_a_id:  # Fallback: assume side_a is Yes if we can't determine
                            price_a = self._fetch_token_price(side_a_id, use_rate_limiter=True)
                            yes_price_temp = price_a
                            if price_a is not None:
                                logger.debug(f"✅ Fetched yes_price (side_a, fallback): {price_a}")
                                price_source = "api"
                    
                    # Second price fetch - rate limiter will ensure 1 second delay
                    if no_price_temp is None:
                        if side_b_is_yes and side_b_id and yes_price_temp is not None:
                            # side_b is Yes, so side_a must be No
                            if side_a_id:
                                price_a = self._fetch_token_price(side_a_id, use_rate_limiter=True)
                                no_price_temp = price_a
                                if price_a is not None:
                                    logger.debug(f"✅ Fetched no_price (side_a): {price_a}")
                                    if price_source != "api":
                                        price_source = "api"
                        elif side_a_is_yes and side_a_id and yes_price_temp is not None:
                            # side_a is Yes, so side_b must be No
                            if side_b_id:
                                price_b = self._fetch_token_price(side_b_id, use_rate_limiter=True)
                                no_price_temp = price_b
                                if price_b is not None:
                                    logger.debug(f"✅ Fetched no_price (side_b): {price_b}")
                                    if price_source != "api":
                                        price_source = "api"
                        elif side_b_id and yes_price_temp is not None:  # Fallback: assume side_b is No
                            price_b = self._fetch_token_price(side_b_id, use_rate_limiter=True)
                            no_price_temp = price_b
                            if price_b is not None:
                                logger.debug(f"✅ Fetched no_price (side_b, fallback): {price_b}")
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
            
            # If still no prices and market is open, estimate 50/50 as fallback
            if yes_price is None and no_price is None:
                status = _safe_get(market, "status", "").lower()
                market_title = market.get('title', 'unknown')[:50]
                if status == "open":
                    yes_price = 0.5
                    no_price = 0.5
                    price_source = "fallback"
                    if self.is_free_tier:
                        logger.debug(f"Free tier: No embedded price for '{market_title}...' - using 50/50 fallback")
                    else:
                        logger.warning(f"⚠️ No price data found for open market '{market_title}...' - using 50/50 fallback. "
                                     f"Platform: {platform}, side_a fields: {list(side_a.keys()) if isinstance(side_a, dict) else 'N/A'}, "
                                     f"side_b fields: {list(side_b.keys()) if isinstance(side_b, dict) else 'N/A'}")
                else:
                    # For closed markets without prices, log a warning
                    logger.debug(f"No price data available for closed market {market_title}...")
        
        # Normalize to ensure they sum to 1 (if we have both)
        if yes_price is not None and no_price is not None:
            total = yes_price + no_price
            if total > 0:
                yes_price = yes_price / total
                no_price = no_price / total
        
        return yes_price, no_price, price_source
    
    def _normalize_market_data(self, market: Dict, fetch_price: bool = False) -> Dict:
        """Normalize Dome API market data to our format (handles both Polymarket and Kalshi)
        
        Args:
            market: Raw market data from API
            fetch_price: Whether to fetch prices via API (default: False, always False on free tier)
        """
        platform = market.get("platform", "polymarket")
        
        # Extract prices from Dome API structure
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
        
        # Also check if prices indicate resolution (but only if we have actual prices, not fallback)
        # Don't mark as resolved if prices are fallback (50/50) - those are just estimates
        if not is_resolved and price_source != "fallback" and yes_price is not None and no_price is not None:
            if (yes_price == 1.0 and no_price == 0.0) or (yes_price == 0.0 and no_price == 1.0):
                is_resolved = True
        
        # Extract volume data (platform-specific)
        if platform == "kalshi":
            volume = _safe_get(market, "volume") or _safe_get(market, "volume_24h")
        else:
            volume = _safe_get(market, "volume_total") or _safe_get(market, "volume_1_week")
        liquidity = None  # Dome API doesn't provide liquidity directly
        
        # Convert resolution date from Unix timestamp to ISO format
        resolution_date = None
        end_time = _safe_get(market, "end_time")
        close_time = _safe_get(market, "close_time")  # Kalshi uses close_time
        resolution_time = end_time or close_time
        
        if resolution_time:
            try:
                end_date = datetime.fromtimestamp(resolution_time, tz=timezone.utc)
                resolution_date = end_date.isoformat()
            except (ValueError, TypeError):
                pass
        
        # Get title (both platforms use "title")
        title = _safe_get(market, "title", "")
        
        # Get description (Dome API may not have description, use title)
        description = _safe_get(market, "description", title)
        if description:
            description = description[:300]
        
        # Get tags safely (Polymarket has tags, Kalshi might not)
        tags = _safe_get(market, "tags", [])
        category = tags[0] if tags and len(tags) > 0 else None
        
        # Get market ID (platform-specific)
        if platform == "kalshi":
            market_id = _safe_get(market, "market_ticker") or _safe_get(market, "event_ticker", "")
        else:
            market_id = _safe_get(market, "condition_id", "")
        
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
            "question": title,  # Use title as question for display
            "description": description,
            "category": category,
            "yes_price": yes_price,
            "no_price": no_price,
            "price_source": price_source,  # NEW: Track where price came from
            "price_quality": price_quality,  # NEW: Quality indicator (high/medium/low)
            "liquidity": liquidity,
            "volume": volume,
            "resolution_date": resolution_date,
            "active": _safe_get(market, "is_open", False),
            "closed": _safe_get(market, "is_closed", False),
            "accepting_orders": _safe_get(market, "accepting_orders", False),
            "is_resolved": is_resolved,
            "is_future": _safe_get(market, "is_future", False),
            "is_historical": _safe_get(market, "is_historical", False),
            "days_until_resolution": _safe_get(market, "days_until_resolution"),
            "relevance": _safe_get(market, "relevance", "low"),
            "related_event": _safe_get(market, "related_event")
        }
    
    def _do_refresh(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Internal method to perform the actual refresh (called with lock protection)"""
        try:
            # Fetch fresh data from both platforms
            logger.info("Fetching fresh prediction markets data from Dome API (Polymarket + Kalshi)")
            
            # Use instance-level early stopping threshold
            early_stop_threshold = self.early_stop_threshold
            
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
            
            all_markets = polymarket_markets + kalshi_markets
            logger.info(f"Fetched {len(polymarket_markets)} Polymarket + {len(kalshi_markets)} Kalshi = {len(all_markets)} total markets")
            
            if not all_markets:
                logger.warning("Dome API failed to return any markets")
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
                    "error": "Failed to fetch markets from Dome API. Please check DOME_API_KEY configuration.",
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
            # On free tier, fetch prices for top markets only (within rate limit budget)
            # Free tier: 10 queries per 10 seconds
            # - 4 queries used for fetching markets (2 pages each platform)
            # - 6 queries remaining for price fetching
            # - Each Polymarket market needs 2 queries (yes + no prices)
            # - So we can fetch prices for top 3 Polymarket markets
            # - Or top 5 markets (some might be Kalshi with embedded prices)
            
            if self.is_free_tier:
                # On free tier, fetch prices for top 5 markets only
                max_price_fetch_markets = 5
                fetch_prices_enabled = True
                logger.info(f"Free tier: Will fetch prices for top {max_price_fetch_markets} markets (within rate limit)")
            else:
                # On paid tier, respect FETCH_MARKET_PRICES env var
                fetch_prices_enabled = os.getenv('FETCH_MARKET_PRICES', 'false').lower() == 'true'
                max_price_fetch_markets = 20  # Paid tier can fetch more
            
            if fetch_prices_enabled and not self.is_free_tier:
                # Count Polymarket markets that need price fetching
                polymarket_count = sum(1 for m in filtered_markets if m.get("platform", "polymarket") == "polymarket")
                total_price_queries_needed = polymarket_count * 2  # 2 prices per Polymarket market
                logger.info(f"💰 Price fetching enabled: Will fetch prices for {polymarket_count} Polymarket markets "
                          f"({total_price_queries_needed} queries, ~{total_price_queries_needed} seconds)")
            
            for idx, m in enumerate(filtered_markets):
                # Log first market structure for debugging (only once per refresh)
                if len(normalized_markets) == 0:
                    import json
                    logger.info(f"🔍 Sample market structure from Dome API - Top-level keys: {list(m.keys())[:30]}")
                    if "side_a" in m:
                        side_a_sample = m.get("side_a")
                        if isinstance(side_a_sample, dict):
                            logger.info(f"🔍 Sample side_a fields: {list(side_a_sample.keys())}")
                            logger.info(f"🔍 Sample side_a values: {json.dumps({k: v for k, v in list(side_a_sample.items())[:10]}, default=str)}")
                        else:
                            logger.info(f"🔍 Sample side_a type: {type(side_a_sample)}, value: {str(side_a_sample)[:200]}")
                    if "side_b" in m:
                        side_b_sample = m.get("side_b")
                        if isinstance(side_b_sample, dict):
                            logger.info(f"🔍 Sample side_b fields: {list(side_b_sample.keys())}")
                            logger.info(f"🔍 Sample side_b values: {json.dumps({k: v for k, v in list(side_b_sample.items())[:10]}, default=str)}")
                    # Check for any price-related fields at market level
                    price_fields = [k for k in m.keys() if 'price' in k.lower() or 'yes' in k.lower() or 'no' in k.lower()]
                    if price_fields:
                        logger.info(f"🔍 Found price-related fields at market level: {price_fields}")
                
                # On free tier, only fetch prices for top N markets to stay within rate limits
                # On paid tier, fetch prices for all markets if enabled
                should_fetch_price = fetch_prices_enabled and (
                    not self.is_free_tier or idx < max_price_fetch_markets
                )
                
                # Normalize market data (fetch prices for top markets on free tier)
                normalized_markets.append(self._normalize_market_data(m, fetch_price=should_fetch_price))
                
                # Log progress for markets with price fetching
                if should_fetch_price and m.get("platform", "polymarket") == "polymarket":
                    progress = idx + 1
                    if self.is_free_tier:
                        logger.info(f"💰 Free tier: Fetching prices for market {progress}/{max_price_fetch_markets}")
                    else:
                        polymarket_count = sum(1 for m in filtered_markets if m.get("platform", "polymarket") == "polymarket")
                        logger.info(f"💰 Price fetching progress: {progress}/{polymarket_count} Polymarket markets processed")
            
            # Filter out any resolved markets that may have slipped through (safety check)
            # Log how many are being filtered out for debugging
            before_filter = len(normalized_markets)
            resolved_markets = [m for m in normalized_markets if m.get("is_resolved", False)]
            normalized_markets = [m for m in normalized_markets if not m.get("is_resolved", False)]
            after_filter = len(normalized_markets)
            if before_filter != after_filter:
                logger.info(f"Filtered out {before_filter - after_filter} resolved markets after normalization ({before_filter} -> {after_filter})")
                for resolved in resolved_markets[:3]:  # Log first 3 for debugging
                    logger.debug(f"  - Resolved market: {resolved.get('question', 'unknown')[:50]} (is_resolved={resolved.get('is_resolved')})")
            
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
        
        Strategy:
        1. If cache is valid and not forcing refresh, return cached data immediately
        2. If refresh is needed, check if one is already in progress (deduplication)
        3. If refresh in progress, return stale cache immediately (don't wait)
        4. If no refresh in progress, start background refresh and return stale cache
        5. Only block and wait if force_refresh=True AND no refresh in progress
        
        On free tier, be more conservative with refreshes to avoid hitting rate limits.
        """
        try:
            # On free tier, be more conservative with refreshes
            if self.is_free_tier and not force_refresh:
                # Check if cache is still valid (30 minutes)
                if self._is_cache_valid():
                    logger.info("Using cached prediction markets data (free tier)")
                    return {
                        "status": "success",
                        "markets": self.cached_markets,
                        "cached": True,
                        "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
                    }
                
                # On free tier, only refresh if cache is very stale (>30 min)
                if self.cache_timestamp:
                    cache_age = datetime.now(timezone.utc) - self.cache_timestamp.replace(tzinfo=timezone.utc)
                    cache_age_minutes = cache_age.total_seconds() / 60
                    
                    if cache_age_minutes < self.cache_expiration_minutes:
                        logger.info(f"Cache still fresh ({cache_age_minutes:.1f} min old), using cached data (free tier)")
                        return {
                            "status": "success",
                            "markets": self.cached_markets,
                            "cached": True,
                            "stale": False,
                            "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
                        }
            
            # Fast path: use cache if valid and not forcing refresh (paid tier or force refresh)
            if not force_refresh and self._is_cache_valid():
                logger.info("Using cached prediction markets data")
                
                # Trigger background refresh if cache is getting stale (but don't wait)
                cache_age = datetime.now(timezone.utc) - self.cache_timestamp.replace(tzinfo=timezone.utc)
                cache_age_minutes = cache_age.total_seconds() / 60
                
                # If cache is older than background refresh interval, trigger background refresh
                if cache_age_minutes >= self._background_refresh_interval_minutes:
                    self._trigger_background_refresh()
                
                return {
                    "status": "success",
                    "markets": self.cached_markets,
                    "cached": True,
                    "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
                }
            
            # Need to refresh - check if refresh is already in progress
            with self._refresh_lock:
                if self._refresh_in_progress:
                    # Another request is already refreshing - return stale cache immediately
                    logger.info("Refresh already in progress, returning stale cache")
                    if self.cached_markets:
                        return {
                            "status": "success",
                            "markets": self.cached_markets,
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
            
            # Perform refresh
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

