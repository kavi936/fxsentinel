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
        self.cache_expiration_minutes = 10  # Refresh every 10 minutes
        
        # Request deduplication: prevent concurrent refresh requests
        self._refresh_lock = threading.Lock()
        self._refresh_in_progress = False
        self._refresh_future = None
        self._refresh_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="prediction_markets_refresh")
        
        # Background refresh tracking
        self._last_background_refresh = None
        self._background_refresh_interval_minutes = 5  # Refresh in background every 5 minutes
        
        # Dome API configuration
        self.dome_api_key = os.getenv('DOME_API_KEY')
        
        if not self.dome_api_key:
            logger.warning("DOME_API_KEY not set. Prediction markets will not be available.")
            self.dome_client = None
        elif DOME_SDK_AVAILABLE:
            try:
                self.dome_client = DomeClient({"api_key": self.dome_api_key})
                logger.info("Dome API SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Dome API SDK: {e}")
                self.dome_client = None
        else:
            logger.warning("Dome API SDK not available. Install with: pip install dome-api-sdk")
            self.dome_client = None
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
            
            # Geopolitical Events (affect forex)
            "geopolitics", "sanctions", "war", "conflict", "crisis",
            "brexit", "european union", "eu", "nato",
            
            # Economic Indicators
            "pmi", "purchasing managers index", "ism", "manufacturing",
            "consumer confidence", "business confidence", "housing", "real estate"
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
    
    def _fetch_kalshi_markets(self, early_stop_threshold: int = 50) -> List[Dict]:
        """Fetch markets from Kalshi via Dome API using SDK
        
        Args:
            early_stop_threshold: Stop fetching if we have this many markets (saves API calls)
        """
        if not self.dome_api_key:
            logger.error("DOME_API_KEY not configured")
            return []
        
        markets = []
        limit = 100  # Dome API limit per page
        max_pages = 3  # Reduced to 3 pages (300 markets) to avoid rate limits - Kalshi has good economic markets early
        
        try:
            if self.dome_client and DOME_SDK_AVAILABLE:
                # Use SDK
                offset = 0
                import time
            for page in range(max_pages):
                    try:
                        # Add delay between requests to respect rate limits
                        if page > 0:
                            time.sleep(1.1)
                        
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
    
    def _fetch_polymarket_markets(self, early_stop_threshold: int = 50) -> List[Dict]:
        """Fetch markets from Polymarket via Dome API using SDK
        
        Args:
            early_stop_threshold: Stop fetching if we have this many markets (saves API calls)
        """
        if not self.dome_api_key:
            logger.error("DOME_API_KEY not configured")
            return []
        
        markets = []
        limit = 100  # Dome API limit per page
        max_pages = 5  # Reduced to 5 pages (500 markets) to avoid rate limits - enough to find economic markets
        
        try:
            if self.dome_client and DOME_SDK_AVAILABLE:
                # Use SDK
                offset = 0
                for page in range(max_pages):
                    try:
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
            
            # Don't skip closed markets yet - we'll filter them after checking relevance
            # We want to include recently resolved markets and highly relevant historical ones
            
            # Track whether market is accepting orders (open markets are accepting orders)
            accepting_orders = is_open
            
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
            price_patterns = ["price of", "price be", "will the price", "price above", "price below", "price less than"]
            
            if any(crypto in text_lower for crypto in crypto_keywords):
                # If it's about crypto AND price, exclude it
                if any(pattern in text_lower for pattern in price_patterns) or "up or down" in text_lower:
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
            
            # Only include markets that match economic keywords
            # Tags alone are not enough - we need actual economic content
            if not matched_keywords:
                skipped_no_keywords += 1
                continue
            
            # Economic tags can boost relevance but aren't required
            if has_economic_tag and relevance == "low":
                        relevance = "medium"
            
            # Filter closed markets: include if recently resolved OR relevant (medium or high)
            # This ensures we show more markets even if they're closed
            if is_closed:
                # Include if recently resolved (within 30 days) OR medium/high relevance
                if not is_recently_resolved and relevance not in ["high", "medium"]:
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
        # 1. Markets accepting orders (highest priority - most "live" on Polymarket)
        # 2. Future markets (upcoming)
        # 3. Recently resolved (for context)
        # 4. By relevance score (high > medium > low)
        # 5. By number of matched keywords
        # 6. By resolution date (closer first)
        relevant_markets.sort(
            key=lambda x: (
                x.get("accepting_orders", False),  # Markets accepting orders first
                x.get("is_future", False),  # Then future markets
                x.get("is_recently_resolved", False),  # Then recently resolved
                x["relevance"] == "high",  # Then by relevance: high
                x.get("relevance") == "medium",  # Then: medium
                -len(x.get("matched_keywords", [])),  # More matched keywords = higher priority
                -x.get("days_until_resolution", 999) if x.get("days_until_resolution") else 999,  # Closer dates first
            ),
            reverse=True
        )
        
        # Return top 20 markets (increased to show more diverse options)
        # Note: Deduplication by market_id already prevents duplicates from appearing
        return relevant_markets[:20]
    
    def _fetch_token_price(self, token_id: str) -> Optional[float]:
        """Fetch price for a specific token from Dome API
        
        Note: This method attempts to fetch prices using the SDK or direct API calls.
        If prices cannot be fetched, the system will use fallback logic based on market status.
        
        IMPORTANT: Price fetching is disabled by default to avoid rate limits.
        Enable by setting FETCH_MARKET_PRICES=true in environment.
        """
        # Skip price fetching by default to avoid rate limits
        # Prices will use fallback logic (50/50 for open markets, winning_side for resolved)
        if not os.getenv('FETCH_MARKET_PRICES', 'false').lower() == 'true':
            return None
        
        if not self.dome_api_key or not token_id:
            return None
        
        try:
            # Use rate limiter before making price request
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
                # Use rate limiter before making price request
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
    
    def _extract_prices_from_dome_market(self, market: Dict) -> tuple:
        """Extract yes/no prices from Dome API market structure (Polymarket or Kalshi)"""
        yes_price = None
        no_price = None
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
                elif result.lower() == "no":
                    yes_price = 0.0
                    no_price = 1.0
            elif last_price is not None:
                # Convert Kalshi price (0-100) to probability (0-1)
                # Kalshi price represents Yes probability
                yes_price = float(last_price) / 100.0
                no_price = 1.0 - yes_price
            else:
                # No price available - use fallback
                status = _safe_get(market, "status", "").lower()
                if status == "open":
                    yes_price = 0.5
                    no_price = 0.5
        else:
            # Polymarket uses side_a and side_b with token IDs
            side_a = _safe_get(market, "side_a", {})
            side_b = _safe_get(market, "side_b", {})
            
            # Handle both dict and object formats for side_a and side_b
            if not isinstance(side_a, dict):
                side_a = {"id": _safe_get(side_a, "id"), "label": _safe_get(side_a, "label", "")}
            if not isinstance(side_b, dict):
                side_b = {"id": _safe_get(side_b, "id"), "label": _safe_get(side_b, "label", "")}
            
            side_a_id = side_a.get("id") if isinstance(side_a, dict) else None
            side_b_id = side_b.get("id") if isinstance(side_b, dict) else None
            side_a_label = (side_a.get("label", "") if isinstance(side_a, dict) else "").lower()
            side_b_label = (side_b.get("label", "") if isinstance(side_b, dict) else "").lower()
            
            # Try to fetch prices for both sides
            price_a = self._fetch_token_price(side_a_id) if side_a_id else None
            price_b = self._fetch_token_price(side_b_id) if side_b_id else None
            
            # Determine which side is Yes and which is No based on labels
            if "yes" in side_a_label or "will" in side_a_label or "up" in side_a_label:
                yes_price = price_a
                no_price = price_b
            elif "yes" in side_b_label or "will" in side_b_label or "up" in side_b_label:
                yes_price = price_b
                no_price = price_a
            else:
                # Default: first side is Yes, second is No
                yes_price = price_a
                no_price = price_b
            
            # If we couldn't fetch prices, use a fallback: check if market is resolved
            winning_side = _safe_get(market, "winning_side")
            if winning_side is not None:
                # Market is resolved
                if winning_side == side_a_id:
                    yes_price = 1.0
                    no_price = 0.0
                elif winning_side == side_b_id:
                    yes_price = 0.0
                    no_price = 1.0
            
            # If still no prices and market is open, estimate 50/50 as fallback
            if yes_price is None and no_price is None:
                status = _safe_get(market, "status", "").lower()
                if status == "open":
                    yes_price = 0.5
                    no_price = 0.5
        
        # Normalize to ensure they sum to 1 (if we have both)
        if yes_price is not None and no_price is not None:
            total = yes_price + no_price
            if total > 0:
                yes_price = yes_price / total
                no_price = no_price / total
        
        return yes_price, no_price
    
    def _normalize_market_data(self, market: Dict) -> Dict:
        """Normalize Dome API market data to our format (handles both Polymarket and Kalshi)"""
        platform = market.get("platform", "polymarket")
        
        # Extract prices from Dome API structure
        yes_price, no_price = self._extract_prices_from_dome_market(market)
        
        # Check if market is resolved
        is_resolved = (yes_price == 1.0 and no_price == 0.0) or (yes_price == 0.0 and no_price == 1.0)
        if not is_resolved:
            # Check platform-specific resolved indicators
            if platform == "kalshi":
                result = _safe_get(market, "result")
                is_resolved = result is not None
            else:
                winning_side = _safe_get(market, "winning_side")
                is_resolved = winning_side is not None
        
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
        
        return {
            "id": market_id,
            "platform": platform,
            "question": title,  # Use title as question for display
            "description": description,
            "category": category,
            "yes_price": yes_price,
            "no_price": no_price,
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
            
            # Use early stopping to reduce API calls - stop when we have enough raw markets
            # We need ~100-200 raw markets to filter down to 20 relevant ones
            early_stop_threshold = 150
            
            polymarket_markets = self._fetch_polymarket_markets(early_stop_threshold=early_stop_threshold)
            kalshi_markets = self._fetch_kalshi_markets(early_stop_threshold=early_stop_threshold)
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
            normalized_markets = [self._normalize_market_data(m) for m in filtered_markets]
            
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
        """
        try:
            # Fast path: use cache if valid and not forcing refresh
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

