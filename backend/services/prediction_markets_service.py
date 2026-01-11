#!/usr/bin/env python3
"""
Prediction Markets Service for FXSentinel
Fetches and filters prediction market data from Polymarket
"""

import json
import logging
import requests
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PredictionMarketsService:
    """Main prediction markets service"""
    
    def __init__(self):
        import os
        # Cache file in backend directory to match other services
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "prediction_markets_cache.json")
        self.cache_file = os.path.normpath(self.cache_file)
        self.cached_markets = None
        self.cache_timestamp = None
        self.cache_expiration_minutes = 10  # Refresh every 10 minutes
        
        # Economic keywords for filtering (refined to avoid false positives)
        self.economic_keywords = [
            "federal reserve", "fed", "fomc", "interest rate", "rate hike", "rate cut",
            "inflation", "cpi", "consumer price index",
            "gdp", "gross domestic product",
            "employment", "non-farm payrolls", "nfp", "unemployment",
            "ecb", "european central bank",
            "bank of england", "boe", "british pound",
            "bank of japan", "boj", "yen",
            "central bank", "monetary policy", "policy decision"
        ]
        
        # Keywords to exclude (reduce false positives)
        self.exclude_keywords = [
            "academy", "oscar", "award", "movie", "film", "actor", "actress",
            "sports", "nba", "nfl", "ncaab", "football", "basketball"
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
    
    def _fetch_polymarket_markets(self) -> List[Dict]:
        """Fetch markets from Polymarket CLOB API"""
        markets = []
        cursor = None
        max_pages = 5  # Fetch 5 pages (5000 markets) to find enough economic ones
        
        try:
            for page in range(max_pages):
                url = "https://clob.polymarket.com/markets"
                params = {"limit": 1000}
                if cursor:
                    params["cursor"] = cursor
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code != 200:
                    logger.error(f"Polymarket API error: {response.status_code}")
                    break
                
                data = response.json()
                page_markets = data.get("data", [])
                markets.extend(page_markets)
                
                cursor = data.get("next_cursor")
                if not cursor:
                    break
                
                logger.info(f"Fetched page {page + 1}: {len(page_markets)} markets")
        
        except Exception as e:
            logger.error(f"Error fetching Polymarket data: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        return markets
    
    def _filter_economic_markets(self, markets: List[Dict]) -> List[Dict]:
        """Filter markets for economic/forex relevance"""
        relevant_markets = []
        seen_ids = set()  # Track seen market IDs to prevent duplicates
        now = datetime.now(timezone.utc)
        
        for market in markets:
            # Deduplicate by condition_id or question_id
            market_id = market.get("condition_id") or market.get("question_id")
            if not market_id or market_id in seen_ids:
                continue
            seen_ids.add(market_id)
            
            question = market.get("question", "").lower()
            description = market.get("description", "").lower()
            text = f"{question} {description}"
            
            # Skip if market is not active
            if not market.get("active"):
                continue
            
            # Skip only if archived (very old markets)
            if market.get("archived"):
                continue
            
            # Track whether market is accepting orders (key indicator of "live" market on Polymarket)
            accepting_orders = market.get("accepting_orders", False)
            
            # Check if market has future resolution date
            end_date_str = market.get("end_date_iso") or market.get("game_start_time")
            is_future = False
            days_until_resolution = None
            
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    end_date = end_date.replace(tzinfo=timezone.utc)
                    is_future = end_date > now
                    days_until_resolution = (end_date - now).days
                except:
                    pass
            
            # Track recently resolved markets (within last 30 days)
            is_recently_resolved = False
            if market.get("closed") and end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    end_date = end_date.replace(tzinfo=timezone.utc)
                    days_since_resolution = (now - end_date).days
                    is_recently_resolved = 0 <= days_since_resolution <= 30
                except:
                    pass
            
            # Mark historical markets (closed and old) - but these are common on Polymarket
            # On Polymarket, most markets are historical, so we don't filter them out
            is_historical = market.get("closed") and not is_future and not is_recently_resolved
            
            # Skip if contains exclude keywords
            if any(exclude in text for exclude in self.exclude_keywords):
                continue
            
            # Check for economic keywords
            relevance = "low"
            matched_keywords = []
            
            for keyword in self.economic_keywords:
                # Use word boundaries for "fed" to avoid matching "federal" in unrelated contexts
                if keyword == "fed":
                    # Match "fed" as whole word, or "federal reserve", but not just "federal"
                    if re.search(r'\bfed\b', text) or "federal reserve" in text or "fomc" in text:
                        matched_keywords.append(keyword)
                        relevance = "high"
                elif keyword.lower() in text:
                    matched_keywords.append(keyword)
                    # High relevance for Fed, inflation, employment
                    if keyword in ["federal reserve", "fomc", "interest rate", "rate hike", "rate cut"]:
                        relevance = "high"
                    elif keyword in ["inflation", "cpi", "consumer price index"]:
                        relevance = "high"
                    elif keyword in ["employment", "non-farm payrolls", "nfp", "unemployment"]:
                        relevance = "high"
                    elif keyword in ["ecb", "european central bank", "bank of england", "boe", "bank of japan", "boj"]:
                        relevance = "high"
                    elif relevance == "low":
                        relevance = "medium"
            
            if matched_keywords:
                # Determine related event
                related_event = None
                if any(k in matched_keywords for k in ["fed", "federal reserve", "fomc", "interest rate"]):
                    related_event = "FOMC Meeting"
                elif "inflation" in matched_keywords or "cpi" in matched_keywords:
                    related_event = "CPI Release"
                elif "gdp" in matched_keywords:
                    related_event = "GDP Release"
                elif any(k in matched_keywords for k in ["employment", "nfp", "non-farm payrolls"]):
                    related_event = "Employment Report"
                elif "ecb" in matched_keywords:
                    related_event = "ECB Meeting"
                elif "boe" in matched_keywords or "bank of england" in matched_keywords:
                    related_event = "BOE Meeting"
                elif "boj" in matched_keywords or "bank of japan" in matched_keywords:
                    related_event = "BOJ Meeting"
                
                # Include all economically relevant markets - we prioritize by sorting, not filtering
                # This ensures we get the best available data from Polymarket even if mostly historical
                market["relevance"] = relevance
                market["related_event"] = related_event
                market["matched_keywords"] = matched_keywords
                market["accepting_orders"] = accepting_orders
                market["is_future"] = is_future
                market["days_until_resolution"] = days_until_resolution
                market["is_recently_resolved"] = is_recently_resolved
                market["is_historical"] = is_historical
                relevant_markets.append(market)
        
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
        
        # Return top 10 markets (increased from original to show more options)
        # Note: Deduplication by market_id already prevents duplicates from appearing
        return relevant_markets[:10]
    
    def _extract_prices_from_tokens(self, tokens: List[Dict]) -> tuple:
        """Extract yes/no prices from tokens array"""
        yes_price = None
        no_price = None
        
        if not tokens or len(tokens) < 2:
            return yes_price, no_price
        
        # Polymarket tokens have outcomes and prices
        # Prices represent probability (0-1)
        # For binary markets, we typically have two outcomes
        for token in tokens:
            outcome = token.get("outcome", "").lower()
            price = token.get("price")
            
            if price is not None:
                # Try to identify yes/no outcomes
                if "yes" in outcome or "will" in outcome or outcome == "true":
                    yes_price = float(price)
                elif "no" in outcome or outcome == "false":
                    no_price = float(price)
        
        # If we couldn't identify yes/no, use first two tokens
        if yes_price is None and no_price is None and len(tokens) >= 2:
            yes_price = float(tokens[0].get("price", 0))
            no_price = float(tokens[1].get("price", 0))
        
        # Normalize to ensure they sum to 1 (if we have both)
        if yes_price is not None and no_price is not None:
            total = yes_price + no_price
            if total > 0:
                yes_price = yes_price / total
                no_price = no_price / total
        
        return yes_price, no_price
    
    def _normalize_market_data(self, market: Dict) -> Dict:
        """Normalize Polymarket data to our format"""
        tokens = market.get("tokens", [])
        yes_price, no_price = self._extract_prices_from_tokens(tokens)
        
        # Check if market is resolved (prices are exactly 0.0 or 1.0)
        is_resolved = (yes_price == 1.0 and no_price == 0.0) or (yes_price == 0.0 and no_price == 1.0)
        
        # Calculate volume/liquidity (if available)
        # Note: Polymarket CLOB API may not provide these directly
        # We'll use placeholder values or calculate from tokens if possible
        liquidity = None
        volume = None
        
        resolution_date = market.get("end_date_iso") or market.get("game_start_time")
        
        return {
            "id": market.get("condition_id") or market.get("question_id", ""),
            "platform": "polymarket",
            "question": market.get("question", ""),
            "description": market.get("description", "")[:300],  # Truncate long descriptions
            "category": market.get("tags", [])[0] if market.get("tags") else None,
            "yes_price": yes_price,
            "no_price": no_price,
            "liquidity": liquidity,
            "volume": volume,
            "resolution_date": resolution_date,
            "active": market.get("active", False),
            "closed": market.get("closed", False),
            "accepting_orders": market.get("accepting_orders", False),
            "is_resolved": is_resolved,
            "is_future": market.get("is_future", False),
            "is_historical": market.get("is_historical", False),
            "days_until_resolution": market.get("days_until_resolution"),
            "relevance": market.get("relevance", "low"),
            "related_event": market.get("related_event")
        }
    
    def get_prediction_markets(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get filtered prediction markets"""
        try:
            # Use cache if valid and not forcing refresh
            if not force_refresh and self._is_cache_valid():
                logger.info("Using cached prediction markets data")
                return {
                    "status": "success",
                    "markets": self.cached_markets,
                    "cached": True,
                    "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
                }
            
            # Fetch fresh data
            logger.info("Fetching fresh prediction markets data from Polymarket")
            all_markets = self._fetch_polymarket_markets()
            
            if not all_markets:
                logger.warning("API failed to return any markets")
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
                    "error": "Failed to fetch markets from Polymarket API",
                    "markets": []
                }
            
            # Filter for economic relevance
            filtered_markets = self._filter_economic_markets(all_markets)
            
            if not filtered_markets:
                logger.warning(f"No economic markets found after filtering (checked {len(all_markets)} total markets)")
                # If filtering produced nothing, still prefer fresh filtered results over stale cache
                # This indicates the Polymarket API returned markets but none matched our criteria
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
            logger.error(f"Error getting prediction markets: {e}")
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

# Singleton instance
prediction_markets_service = PredictionMarketsService()

