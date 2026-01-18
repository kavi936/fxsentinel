#!/usr/bin/env python3
"""
Persistent Prediction Markets Cache Service
Stores prediction markets cache in Firebase Realtime Database
Survives app restarts and deployments (unlike local JSON files)
Similar to persistent_news_cache.py pattern
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from .firebase_realtime_storage import FirebaseRealtimeStorage

logger = logging.getLogger(__name__)

class PersistentPredictionMarketsCache:
    """
    Persistent prediction markets cache service that stores state in Firebase Realtime Database
    This ensures markets cache survives restarts and works across multiple instances
    """
    
    def __init__(self, max_age_minutes: float = 30.0):
        """
        Initialize persistent prediction markets cache
        
        Args:
            max_age_minutes: How long cache is valid (default 30 minutes for free tier)
                           Cache still persists across restarts (main benefit), but fresh markets fetched regularly
        """
        self.firebase = FirebaseRealtimeStorage()
        self.max_age_minutes = max_age_minutes
        
        logger.info(f"Persistent Prediction Markets Cache Service initialized (TTL: {max_age_minutes} minutes)")
    
    def _get_cache_path(self) -> str:
        """Get Firebase path for current markets cache"""
        return "prediction_markets_cache/current"
    
    def save_markets(self, markets: List[Dict[str, Any]], price_history: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save prediction markets to cache
        
        Args:
            markets: List of market dictionaries to save
            price_history: Optional dict mapping market_id to list of price snapshots
        """
        try:
            # Prepare cache data
            cache_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'markets_count': len(markets),
                'markets': markets,
                'max_age_minutes': self.max_age_minutes,
                'last_fetch': datetime.now(timezone.utc).isoformat()  # Track when markets were last fetched
            }
            
            # Add price history if provided
            if price_history:
                cache_data['price_history'] = price_history
            
            # Save to Firebase
            cache_path = self._get_cache_path()
            result = self.firebase._make_request('PUT', cache_path, cache_data)
            
            # Firebase _make_request returns {} on error, or the written data on success
            # For PUT requests, Firebase returns the data that was written
            # Check if result is empty dict (error) or missing expected fields
            if not result or not isinstance(result, dict) or 'markets' not in result:
                logger.warning("Failed to save prediction markets cache to Firebase (empty or invalid response)")
                return False
            
            logger.info(f"Cached {len(markets)} prediction markets to Firebase")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prediction markets to persistent cache: {e}")
            return False
    
    def should_fetch_new_markets(self, fetch_interval_minutes: int = 20, last_fetch: Optional[str] = None) -> bool:
        """
        Check if new markets should be fetched based on last fetch time
        
        Args:
            fetch_interval_minutes: How often to fetch new markets (default 20 minutes for free tier)
            last_fetch: Optional timestamp string from cache metadata (avoids extra Firebase call if provided)
        
        Returns:
            True if new markets should be fetched, False otherwise
        """
        try:
            # If last_fetch is provided (from batched load_markets call), use it to avoid extra Firebase call
            if last_fetch:
                try:
                    last_fetch_dt = datetime.fromisoformat(last_fetch.replace('Z', '+00:00'))
                    if last_fetch_dt.tzinfo:
                        last_fetch_dt = last_fetch_dt.replace(tzinfo=None)
                    time_since_fetch = datetime.now() - last_fetch_dt
                    
                    if time_since_fetch >= timedelta(minutes=fetch_interval_minutes):
                        logger.info(f"Last fetch was {time_since_fetch}, should fetch new markets (interval: {fetch_interval_minutes} min)")
                        return True
                    else:
                        logger.debug(f"Last fetch was {time_since_fetch}, skipping fetch (interval: {fetch_interval_minutes} min)")
                        return False
                except Exception as e:
                    logger.warning(f"Error parsing last_fetch timestamp: {e}")
                    return True  # On error, fetch to be safe
            
            # Fallback: Fetch from Firebase if last_fetch not provided (backward compatibility)
            cache_path = self._get_cache_path()
            cache_data = self.firebase._make_request('GET', cache_path)
            
            if not cache_data or not isinstance(cache_data, dict):
                # No cache exists, should fetch
                return True
            
            last_fetch_str = cache_data.get('last_fetch')
            if not last_fetch_str:
                # No last_fetch timestamp, should fetch
                return True
            
            try:
                last_fetch_dt = datetime.fromisoformat(last_fetch_str.replace('Z', '+00:00'))
                if last_fetch_dt.tzinfo:
                    last_fetch_dt = last_fetch_dt.replace(tzinfo=None)
                time_since_fetch = datetime.now() - last_fetch_dt
                
                if time_since_fetch >= timedelta(minutes=fetch_interval_minutes):
                    logger.info(f"Last fetch was {time_since_fetch}, should fetch new markets (interval: {fetch_interval_minutes} min)")
                    return True
                else:
                    logger.debug(f"Last fetch was {time_since_fetch}, skipping fetch (interval: {fetch_interval_minutes} min)")
                    return False
            except Exception as e:
                logger.warning(f"Error parsing last_fetch timestamp: {e}")
                return True  # On error, fetch to be safe
                
        except Exception as e:
            logger.error(f"Error checking if should fetch new markets: {e}")
            return True  # On error, fetch to be safe
    
    def load_markets(self, allow_stale: bool = True, return_metadata: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        Load prediction markets from cache
        
        Args:
            allow_stale: If True, return cache even if expired (for faster UI loading).
                        If False, only return cache if not expired (default: True for better UX)
            return_metadata: If True, return dict with 'markets' and 'last_fetch' keys instead of just markets list.
                           This allows batching with should_fetch_new_markets() to avoid extra Firebase calls.
        
        Returns:
            List of market dictionaries or None if no cache exists.
            If return_metadata=True, returns dict with keys: 'markets' (list) and 'last_fetch' (str or None)
        """
        try:
            cache_path = self._get_cache_path()
            cache_data = self.firebase._make_request('GET', cache_path)
            
            if not cache_data or not isinstance(cache_data, dict):
                logger.info("No prediction markets cache found in Firebase")
                return None
            
            # Check if cache is too old
            timestamp_str = cache_data.get('timestamp')
            if not timestamp_str:
                logger.info("Cache has no timestamp")
                return None
            
            # Extract metadata for batching
            last_fetch_str = cache_data.get('last_fetch')
            
            try:
                cache_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Handle timezone-aware vs naive datetimes
                now = datetime.now(timezone.utc)
                if cache_timestamp.tzinfo:
                    cache_timestamp = cache_timestamp.replace(tzinfo=timezone.utc)
                else:
                    cache_timestamp = cache_timestamp.replace(tzinfo=timezone.utc)
                
                age = now - cache_timestamp
                
                markets = cache_data.get('markets', [])
                
                if age > timedelta(minutes=self.max_age_minutes):
                    if allow_stale:
                        # Return stale cache for faster UI loading (fresh fetch will happen in background)
                        logger.info(f"Cache is stale ({age}), but returning it for faster UI loading")
                        price_history = cache_data.get('price_history', {})
                        if return_metadata:
                            result = {'markets': markets, 'last_fetch': last_fetch_str}
                            if price_history:
                                result['price_history'] = price_history
                            return result
                        return markets
                    else:
                        logger.info(f"Cache is too old ({age}), ignoring")
                        return None
                
                logger.info(f"Loaded {len(markets)} prediction markets from Firebase cache (age: {age})")
                # Extract price history if available
                price_history = cache_data.get('price_history', {})
                
                if return_metadata:
                    result = {'markets': markets, 'last_fetch': last_fetch_str}
                    if price_history:
                        result['price_history'] = price_history
                    return result
                return markets
                
            except Exception as e:
                logger.warning(f"Error parsing cache timestamp: {e}")
                # If timestamp parsing fails, still return the markets (better than nothing)
                markets = cache_data.get('markets', [])
                price_history = cache_data.get('price_history', {})
                if markets:
                    logger.info(f"Loaded {len(markets)} prediction markets from cache (timestamp parse error, but returning markets)")
                    if return_metadata:
                        result = {'markets': markets, 'last_fetch': last_fetch_str}
                        if price_history:
                            result['price_history'] = price_history
                        return result
                    return markets
                return None
            
        except Exception as e:
            logger.error(f"Error loading prediction markets from persistent cache: {e}")
            return None
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get information about the cache status"""
        try:
            cache_path = self._get_cache_path()
            cache_data = self.firebase._make_request('GET', cache_path)
            
            if not cache_data or not isinstance(cache_data, dict):
                return {
                    'exists': False,
                    'age': None,
                    'markets_count': 0,
                    'is_valid': False
                }
            
            timestamp_str = cache_data.get('timestamp')
            if not timestamp_str:
                return {
                    'exists': True,
                    'age': None,
                    'markets_count': cache_data.get('markets_count', 0),
                    'is_valid': False
                }
            
            try:
                cache_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if cache_timestamp.tzinfo:
                    cache_timestamp = cache_timestamp.replace(tzinfo=timezone.utc)
                else:
                    cache_timestamp = cache_timestamp.replace(tzinfo=timezone.utc)
                age = datetime.now(timezone.utc) - cache_timestamp
                is_valid = age <= timedelta(minutes=self.max_age_minutes)
                
                return {
                    'exists': True,
                    'age': str(age),
                    'markets_count': cache_data.get('markets_count', 0),
                    'is_valid': is_valid,
                    'last_updated': timestamp_str
                }
            except Exception as e:
                return {
                    'exists': True,
                    'age': None,
                    'markets_count': cache_data.get('markets_count', 0),
                    'is_valid': False,
                    'error': str(e)
                }
            
        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {
                'exists': False,
                'age': None,
                'markets_count': 0,
                'is_valid': False,
                'error': str(e)
            }
    
    def clear_cache(self) -> bool:
        """Clear the cache in Firebase"""
        try:
            cache_path = self._get_cache_path()
            self.firebase._make_request('DELETE', cache_path)
            logger.info("Prediction markets cache cleared in Firebase")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Global singleton instance
_persistent_prediction_markets_cache = None

def get_persistent_prediction_markets_cache(max_age_minutes: float = 30.0) -> PersistentPredictionMarketsCache:
    """Get the global persistent prediction markets cache instance"""
    global _persistent_prediction_markets_cache
    if _persistent_prediction_markets_cache is None:
        _persistent_prediction_markets_cache = PersistentPredictionMarketsCache(max_age_minutes=max_age_minutes)
    return _persistent_prediction_markets_cache

