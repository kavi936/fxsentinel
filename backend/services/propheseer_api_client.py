#!/usr/bin/env python3
"""
PropheSeer API Client
Unified API aggregating prediction markets from Polymarket, Kalshi, Gemini, etc.
"""

import logging
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class PropheSeerAPIClient:
    """Client for PropheSeer unified prediction markets API"""
    
    BASE_URL = "https://api.propheseer.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize PropheSeer API client
        
        Args:
            api_key: PropheSeer API key (defaults to PROPHESEER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('PROPHESEER_API_KEY')
        if not self.api_key:
            logger.warning("PROPHESEER_API_KEY not set. PropheSeer API will not be available.")
            self.available = False
        else:
            self.available = True
            logger.info("PropheSeer API client initialized")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make authenticated request to PropheSeer API
        
        Args:
            endpoint: API endpoint (e.g., '/v1/markets')
            params: Query parameters
            
        Returns:
            JSON response or None on error
        """
        if not self.available:
            return None
        
        url = f"{self.BASE_URL}{endpoint}"
        
        # PropheSeer uses Bearer token authentication
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"PropheSeer API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}, body: {e.response.text[:200]}")
            return None
    
    def get_markets(
        self,
        status: Optional[str] = "open",
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch markets from PropheSeer
        
        Args:
            status: Market status filter ('open', 'closed', 'resolved')
            category: Category filter (optional)
            limit: Maximum number of markets to return
            offset: Pagination offset
            platform: Platform filter ('polymarket', 'kalshi', 'gemini', etc.)
        
        Returns:
            List of market dictionaries
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        if platform:
            params["platform"] = platform
        
        # PropheSeer endpoint is /markets (base URL already includes /v1)
        endpoint = "/markets"
        data = self._make_request(endpoint, params)
        
        if data:
            # PropheSeer returns data in {"data": [...], "meta": {...}} format
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            elif isinstance(data, list):
                return data
            elif isinstance(data, dict) and "id" in data:
                # Single market
                return [data]
        
        return []
    
    def normalize_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize PropheSeer market data to our internal format
        
        Args:
            market: Raw market data from PropheSeer API
            
        Returns:
            Normalized market dictionary
        """
        # Extract question/title
        question = market.get("question") or market.get("title") or market.get("name", "")
        
        # Extract outcomes and probabilities
        outcomes = market.get("outcomes", [])
        yes_price = None
        no_price = None
        
        if outcomes:
            # PropheSeer uses normalized outcomes array
            for outcome in outcomes:
                name = str(outcome.get("name", "")).lower()
                probability = outcome.get("probability") or outcome.get("price")
                
                if probability is not None:
                    try:
                        prob_float = float(probability)
                        if "yes" in name or name == "yes":
                            yes_price = prob_float
                        elif "no" in name or name == "no":
                            no_price = prob_float
                    except (ValueError, TypeError):
                        pass
        
        # If no outcomes found, try alternative fields
        if yes_price is None and no_price is None:
            yes_price = market.get("yes_price") or market.get("yesPrice")
            no_price = market.get("no_price") or market.get("noPrice")
        
        # Extract platform/source
        platform = market.get("platform") or market.get("source", "propheseer")
        
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
        
        # Extract volume and liquidity
        volume = market.get("volume") or market.get("volume_total") or 0
        liquidity = market.get("liquidity") or market.get("liquidity_total") or None
        
        # Extract market ID
        market_id = market.get("id") or market.get("market_id") or market.get("condition_id")
        
        normalized = {
            "id": market_id,
            "platform": platform,
            "source": "propheseer",
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
            "url": market.get("url") or market.get("link"),
            "raw_data": market  # Keep raw data for debugging
        }
        
        return normalized

