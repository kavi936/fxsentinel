#!/usr/bin/env python3
"""
Persistent News Cache Service
Stores news cache and history in Firebase Realtime Database
Survives app restarts and deployments (unlike local JSON files)
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .firebase_realtime_storage import FirebaseRealtimeStorage

logger = logging.getLogger(__name__)

class PersistentNewsCache:
    """
    Persistent news cache service that stores state in Firebase Realtime Database
    This ensures news cache survives restarts and works across multiple instances
    """
    
    def __init__(self, max_age_hours: float = 24.0):
        """
        Initialize persistent news cache
        
        Args:
            max_age_hours: How long cache is valid (default 24 hours, vs 0.25 for file cache)
        """
        self.firebase = FirebaseRealtimeStorage()
        self.max_age_hours = max_age_hours
        self.max_history_items = 500  # Keep more history than file cache (was 100)
        
        logger.info(f"Persistent News Cache Service initialized (TTL: {max_age_hours}h)")
    
    def _get_cache_path(self) -> str:
        """Get Firebase path for current news cache"""
        return "news_cache/current"
    
    def _get_history_path(self) -> str:
        """Get Firebase path for news history"""
        return "news_cache/history"
    
    def _get_history_item_path(self, news_id: str) -> str:
        """Get Firebase path for specific history item"""
        return f"news_cache/history/{news_id}"
    
    def save_news(self, news_items: List[Dict[str, Any]]) -> bool:
        """Save news items to cache and add to history"""
        try:
            # Prepare cache data
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'news_count': len(news_items),
                'news': news_items,
                'max_age_hours': self.max_age_hours
            }
            
            # Save to Firebase
            cache_path = self._get_cache_path()
            result = self.firebase._make_request('PUT', cache_path, cache_data)
            
            # Firebase _make_request returns {} on error, or the written data on success
            # For PUT requests, Firebase returns the data that was written
            # Check if result is empty dict (error) or missing expected fields
            if not result or not isinstance(result, dict) or 'news' not in result:
                logger.warning("Failed to save news cache to Firebase (empty or invalid response)")
                return False
            
            # Add to history
            self._add_to_history(news_items)
            
            logger.info(f"Cached {len(news_items)} news items to Firebase and updated history")
            return True
            
        except Exception as e:
            logger.error(f"Error saving news to persistent cache: {e}")
            return False
    
    def _add_to_history(self, news_items: List[Dict[str, Any]]):
        """Add news items to history in Firebase"""
        try:
            # Get existing history to check for duplicates
            existing_history = self.load_history()
            existing_ids = {str(item.get('id', '')) for item in existing_history}
            
            # Add new items
            new_items_count = 0
            for item in news_items:
                news_id = str(item.get('id', ''))
                if not news_id or news_id in existing_ids:
                    continue  # Skip duplicates
                
                history_item = {
                    'id': news_id,
                    'title': item.get('title', ''),
                    'summary': item.get('summary', ''),
                    'source': item.get('source', ''),
                    'url': item.get('url', ''),
                    'published_at': item.get('published_at', ''),
                    'added_to_feed_at': item.get('added_to_feed_at', ''),
                    'impact': item.get('impact', 'medium'),
                    'currency_pairs': item.get('currency_pairs', []),
                    'cached_at': datetime.now().isoformat(),
                    'type': item.get('type', 'RSS_FEED')
                }
                
                # Save to Firebase
                history_path = self._get_history_item_path(news_id)
                self.firebase._make_request('PUT', history_path, history_item)
                existing_ids.add(news_id)
                new_items_count += 1
            
            # Cleanup old history items if needed
            if len(existing_history) + new_items_count > self.max_history_items:
                self._cleanup_old_history()
            
            if new_items_count > 0:
                logger.info(f"Added {new_items_count} new items to history")
                
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
    
    def _cleanup_old_history(self):
        """Remove oldest history items to stay within limit"""
        try:
            history = self.load_history()
            
            if len(history) <= self.max_history_items:
                return
            
            # Sort by cached_at (oldest first)
            history.sort(key=lambda x: x.get('cached_at', ''))
            
            # Remove oldest items
            items_to_remove = history[:-self.max_history_items]
            
            for item in items_to_remove:
                news_id = str(item.get('id', ''))
                if news_id:
                    history_path = self._get_history_item_path(news_id)
                    self.firebase._make_request('DELETE', history_path)
            
            logger.info(f"Cleaned up {len(items_to_remove)} old history items")
            
        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")
    
    def load_news(self) -> Optional[List[Dict[str, Any]]]:
        """Load news items from cache if they're not too old"""
        try:
            cache_path = self._get_cache_path()
            cache_data = self.firebase._make_request('GET', cache_path)
            
            if not cache_data or not isinstance(cache_data, dict):
                logger.info("No cache found in Firebase")
                return None
            
            # Check if cache is too old
            timestamp_str = cache_data.get('timestamp')
            if not timestamp_str:
                logger.info("Cache has no timestamp")
                return None
            
            try:
                cache_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                age = datetime.now() - cache_timestamp
                
                if age > timedelta(hours=self.max_age_hours):
                    logger.info(f"Cache is too old ({age}), ignoring")
                    return None
                
                news_items = cache_data.get('news', [])
                logger.info(f"Loaded {len(news_items)} news items from Firebase cache (age: {age})")
                return news_items
                
            except Exception as e:
                logger.warning(f"Error parsing cache timestamp: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error loading news from persistent cache: {e}")
            return None
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Load news history from Firebase"""
        try:
            history_path = self._get_history_path()
            history_data = self.firebase._make_request('GET', history_path)
            
            if not history_data or not isinstance(history_data, dict):
                return []
            
            # Convert Firebase object format to list
            history = []
            for news_id, item_data in history_data.items():
                if isinstance(item_data, dict):
                    history.append(item_data)
            
            # Sort by cached_at (newest first)
            history.sort(key=lambda x: x.get('cached_at', ''), reverse=True)
            
            logger.info(f"Loaded {len(history)} items from news history")
            return history
            
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []
    
    def get_recent_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get news history from the last N hours"""
        try:
            history = self.load_history()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_items = []
            for item in history:
                try:
                    cached_at_str = item.get('cached_at', '')
                    if cached_at_str:
                        cached_at = datetime.fromisoformat(cached_at_str.replace('Z', '+00:00'))
                        if cached_at >= cutoff_time:
                            recent_items.append(item)
                except Exception as e:
                    # If date parsing fails, include the item (better safe than sorry)
                    logger.debug(f"Error parsing cached_at for item {item.get('id')}: {e}")
                    recent_items.append(item)
            
            return recent_items
            
        except Exception as e:
            logger.error(f"Error getting recent history: {e}")
            return []
    
    def get_news_by_id(self, news_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific news item by ID from cache or history"""
        try:
            # First check current cache
            cached_news = self.load_news()
            if cached_news:
                news_item = next((item for item in cached_news if str(item.get('id')) == str(news_id)), None)
                if news_item:
                    return news_item
            
            # If not in cache, check history
            history = self.load_history()
            history_item = next((item for item in history if str(item.get('id')) == str(news_id)), None)
            if history_item:
                return history_item
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting news by ID: {e}")
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
                    'news_count': 0,
                    'is_valid': False
                }
            
            timestamp_str = cache_data.get('timestamp')
            if not timestamp_str:
                return {
                    'exists': True,
                    'age': None,
                    'news_count': cache_data.get('news_count', 0),
                    'is_valid': False
                }
            
            try:
                cache_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                age = datetime.now() - cache_timestamp
                is_valid = age <= timedelta(hours=self.max_age_hours)
                
                return {
                    'exists': True,
                    'age': str(age),
                    'news_count': cache_data.get('news_count', 0),
                    'is_valid': is_valid,
                    'last_updated': timestamp_str
                }
            except Exception as e:
                return {
                    'exists': True,
                    'age': None,
                    'news_count': cache_data.get('news_count', 0),
                    'is_valid': False,
                    'error': str(e)
                }
            
        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {
                'exists': False,
                'age': None,
                'news_count': 0,
                'is_valid': False,
                'error': str(e)
            }
    
    def get_history_status(self) -> Dict[str, Any]:
        """Get information about the history status"""
        try:
            history = self.load_history()
            
            if not history:
                return {
                    'total_items': 0,
                    'oldest_item': None,
                    'newest_item': None
                }
            
            # Sort by cached_at
            sorted_history = sorted(history, key=lambda x: x.get('cached_at', ''))
            
            return {
                'total_items': len(history),
                'oldest_item': sorted_history[0].get('cached_at') if sorted_history else None,
                'newest_item': sorted_history[-1].get('cached_at') if sorted_history else None
            }
        except Exception as e:
            logger.error(f"Error getting history status: {e}")
            return {
                'total_items': 0,
                'oldest_item': None,
                'newest_item': None,
                'error': str(e)
            }
    
    def clear_cache(self) -> bool:
        """Clear the cache in Firebase"""
        try:
            cache_path = self._get_cache_path()
            self.firebase._make_request('DELETE', cache_path)
            logger.info("Cache cleared in Firebase")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def clear_history(self) -> bool:
        """Clear the history in Firebase"""
        try:
            history_path = self._get_history_path()
            # Get all history items first
            history_data = self.firebase._make_request('GET', history_path)
            
            if history_data and isinstance(history_data, dict):
                # Delete each item
                for news_id in history_data.keys():
                    item_path = self._get_history_item_path(news_id)
                    self.firebase._make_request('DELETE', item_path)
            
            logger.info("History cleared in Firebase")
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return False

# Global singleton instance
_persistent_news_cache = None

def get_persistent_news_cache() -> PersistentNewsCache:
    """Get the global persistent news cache instance"""
    global _persistent_news_cache
    if _persistent_news_cache is None:
        _persistent_news_cache = PersistentNewsCache()
    return _persistent_news_cache

# For backward compatibility - create alias
persistent_news_cache = get_persistent_news_cache()

