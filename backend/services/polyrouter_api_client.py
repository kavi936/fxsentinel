#!/usr/bin/env python3
"""
PolyRouter API Client
Unified API aggregating prediction markets from Polymarket, Kalshi, Manifold, Limitless, etc.
"""

import logging
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class PolyRouterAPIClient:
    """Client for PolyRouter unified prediction markets API"""
    
    BASE_URL = "https://api-v2.polyrouter.io"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize PolyRouter API client
        
        Args:
            api_key: PolyRouter API key (defaults to POLYROUTER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('POLYROUTER_API_KEY')
        if not self.api_key:
            logger.warning("POLYROUTER_API_KEY not set. PolyRouter API will not be available.")
            self.available = False
        else:
            self.available = True
            logger.info("PolyRouter API client initialized")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make authenticated request to PolyRouter API
        
        Args:
            endpoint: API endpoint (e.g., '/v2/markets')
            params: Query parameters
            
        Returns:
            JSON response or None on error
        """
        if not self.available:
            return None
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"PolyRouter API request failed: {e}")
            return None
    
    def get_markets(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_raw: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch markets from PolyRouter
        
        Args:
            status: Market status filter - NOT USED (PolyRouter doesn't support this parameter)
            platform: Platform filter ('polymarket', 'kalshi', 'manifold', 'limitless', etc.) - optional
            limit: Maximum number of markets to return
            offset: Pagination offset
            include_raw: Include raw platform-specific data
        
        Returns:
            List of market dictionaries
        """
        params = {}
        
        # Only add limit if specified (PolyRouter may have defaults)
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        # NOTE: PolyRouter API doesn't support status parameter - filter client-side instead
        # if status:
        #     params["status"] = status
        if platform:
            params["platform"] = platform
        if include_raw:
            params["include_raw"] = "true"
        
        # PolyRouter endpoint is /markets
        endpoint = "/markets"
        data = self._make_request(endpoint, params)
        
        if data:
            # PolyRouter returns data in {"markets": [...]} format
            if isinstance(data, dict) and "markets" in data:
                return data["markets"]
            elif isinstance(data, list):
                return data
            elif isinstance(data, dict) and "id" in data:
                # Single market
                return [data]
        
        return []
    
    def get_market_by_id(self, market_id: str, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific market by ID
        
        Args:
            market_id: Market ID
            platform: Platform name (optional, helps with endpoint selection)
        
        Returns:
            Market dictionary or None if not found
        """
        # PolyRouter endpoint for single market: /markets/{market_id}
        endpoint = f"/markets/{market_id}"
        
        params = {}
        if platform:
            params["platform"] = platform
        
        data = self._make_request(endpoint, params)
        
        if data:
            # PolyRouter may return single market or wrapped in "market" key
            if isinstance(data, dict):
                if "market" in data:
                    return data["market"]
                elif "id" in data or "title" in data:
                    return data
        
        return None
    
    def get_price_history(
        self,
        market_ids: List[str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: str = "1h"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch price history (OHLC) for markets
        
        Args:
            market_ids: List of market IDs
            start_time: Start time for history
            end_time: End time for history
            interval: Time interval ('1m', '5m', '15m', '1h', '1d', etc.)
        
        Returns:
            Dictionary mapping market_id to list of OHLC data points
        """
        if not market_ids:
            return {}
        
        params = {
            "market_ids": ",".join(market_ids),
            "interval": interval
        }
        
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        
        # Try v2 endpoint first
        endpoints = ["/v2/price-history", "/v1/price-history", "/price-history"]
        
        for endpoint in endpoints:
            data = self._make_request(endpoint, params)
            if data:
                # PolyRouter returns price history in different formats
                if isinstance(data, dict):
                    # Check if it's a mapping of market_id to history
                    if all(isinstance(k, str) and isinstance(v, list) for k, v in data.items()):
                        return data
                    # Or if it's wrapped in a 'data' or 'history' key
                    elif "data" in data:
                        return data["data"]
                    elif "history" in data:
                        return data["history"]
        
        return {}
    
    def normalize_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize PolyRouter market data to our internal format
        
        Args:
            market: Raw market data from PolyRouter API
            
        Returns:
            Normalized market dictionary
        """
        # Extract question/title
        question = market.get("question") or market.get("title") or market.get("name", "")
        
        # Extract prices from current_prices structure (PolyRouter format)
        current_prices = market.get("current_prices", {})
        yes_price = None
        no_price = None
        
        if current_prices:
            # PolyRouter uses current_prices with outcome IDs as keys
            # Each outcome has {"price": 0.65, "bid": 0, "ask": 0}
            # CRITICAL: Price of 0 or 1 might mean "no data" or "resolved", not actual probability
            # Only accept prices in valid probability range (0 < price < 1) OR exactly 0.5 (50/50)
            for outcome_id, price_data in current_prices.items():
                if isinstance(price_data, dict):
                    price = price_data.get("price")
                    bid = price_data.get("bid", 0)
                    ask = price_data.get("ask", 0)
                    
                    # Check if we have valid price data
                    # Price of 0 with bid=0 and ask=0 and no volume likely means "no data"
                    # Price of 1.0 or 0.0 might mean resolved or extreme probability - accept if there's volume
                    if price is not None:
                        try:
                            price_float = float(price)
                            # Get volume to validate
                            volume = market.get("volume_24h") or market.get("volume_total") or market.get("volume") or 0
                            
                            # Accept price if:
                            # 1. It's in valid range (0 < price < 1), OR
                            # 2. It's exactly 0.5 (50/50), OR
                            # 3. It's 0 or 1 but we have bid/ask data (indicates real market), OR
                            # 4. It's 0 or 1 but market has volume (indicates real trading, even if extreme)
                            has_market_data = (
                                (bid > 0 or ask > 0) or 
                                (0 < price_float < 1) or 
                                price_float == 0.5 or
                                (volume > 0 and (price_float == 0 or price_float == 1))
                            )
                            
                            if has_market_data:
                                outcome_lower = str(outcome_id).lower()
                                
                                # Map common outcome names to yes/no
                                if outcome_lower in ["yes", "up", "true", "1"]:
                                    yes_price = price_float
                                elif outcome_lower in ["no", "down", "false", "0"]:
                                    no_price = price_float
                                # For binary markets, first outcome is typically "yes", second is "no"
                                elif yes_price is None:
                                    yes_price = price_float
                                elif no_price is None:
                                    no_price = price_float
                        except (ValueError, TypeError):
                            pass
        
        # Fallback: try outcomes array
        if yes_price is None and no_price is None:
            outcomes = market.get("outcomes", [])
            if outcomes:
                for outcome in outcomes:
                    name = str(outcome.get("name", "")).lower()
                    probability = outcome.get("probability") or outcome.get("price")
                    
                    if probability is not None:
                        try:
                            prob_float = float(probability)
                            if "yes" in name or name == "yes" or name == "up":
                                yes_price = prob_float
                            elif "no" in name or name == "no" or name == "down":
                                no_price = prob_float
                        except (ValueError, TypeError):
                            pass
        
        # Final fallback: try direct fields
        if yes_price is None and no_price is None:
            yes_price = market.get("yes_price") or market.get("yesPrice")
            no_price = market.get("no_price") or market.get("noPrice")
        
        # Extract platform/source
        platform = market.get("platform") or market.get("source", "polyrouter")
        
        # Extract status
        status = market.get("status", "").lower()
        is_resolved = status == "resolved" or market.get("resolved", False)
        is_closed = status == "closed" or market.get("closed", False)
        
        # Extract dates
        resolution_date = None
        if market.get("resolution_date"):
            resolution_date = market.get("resolution_date")
        elif market.get("end_date"):
            resolution_date = market.get("end_date")
        elif market.get("endDate"):
            resolution_date = market.get("endDate")
        elif market.get("endTime"):
            resolution_date = market.get("endTime")
        
        # Extract volume and liquidity (PolyRouter uses volume_24h, volume_total, liquidity)
        volume = market.get("volume_24h") or market.get("volume_total") or market.get("volume") or 0
        liquidity = market.get("liquidity") or market.get("liquidity_total") or None
        
        # Validate prices: If we have 0/1 prices with no volume AND no bid/ask, mark as invalid
        # This indicates a market with no real trading data
        # But if there's volume, 0/1 prices are valid (extreme probability or resolved)
        has_bid_ask = False
        if current_prices:
            for price_data in current_prices.values():
                if isinstance(price_data, dict):
                    if price_data.get("bid", 0) > 0 or price_data.get("ask", 0) > 0:
                        has_bid_ask = True
                        break
        
        if (yes_price == 0 or yes_price is None) and (no_price == 1 or (no_price is None and yes_price == 0)) and volume == 0 and not has_bid_ask:
            # Market has no real price data - set to None to indicate invalid
            yes_price = None
            no_price = None
        
        # Extract market ID
        market_id = market.get("id") or market.get("market_id") or market.get("condition_id")
        
        # Extract URL - PolyRouter uses source_url field
        source_url = market.get("source_url") or market.get("url") or market.get("link")
        
        normalized = {
            "id": market_id,
            "platform": platform,
            "source": "polyrouter",
            "question": question,
            "yes_price": yes_price,
            "no_price": no_price,
            "volume": volume,
            "liquidity": liquidity,
            "status": status,
            "is_resolved": is_resolved,
            "closed": is_closed,
            "resolution_date": resolution_date,
            "category": market.get("category"),
            "url": source_url,  # FIXED: Use source_url
            "raw_data": market  # Keep raw data for debugging
        }
        
        return normalized

