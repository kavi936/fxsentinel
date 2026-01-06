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
    
    def __init__(self, max_age_hours: float = 0.25):
        """
        Initialize persistent news cache
        
        Args:
            max_age_hours: How long cache is valid (default 0.25 hours = 15 minutes, same as old file cache)
                           Cache still persists across restarts (main benefit), but fresh news fetched regularly
        """
        self.firebase = FirebaseRealtimeStorage()
        self.max_age_hours = max_age_hours
        self.max_history_items = 500  # Keep more history than file cache (was 100)
        
        logger.info(f"Persistent News Cache Service initialized (TTL: {max_age_hours}h = {max_age_hours * 60:.0f} minutes)")
    
    def _get_cache_path(self) -> str:
        """Get Firebase path for current news cache"""
        return "news_cache/current"
    
    def _get_history_path(self) -> str:
        """Get Firebase path for news history"""
        return "news_cache/history"
    
    def _get_history_item_path(self, news_id: str) -> str:
        """Get Firebase path for specific history item"""
        return f"news_cache/history/{news_id}"
    
    def save_news(self, news_items: List[Dict[str, Any]], append: bool = False) -> bool:
        """
        Save news items to cache and add to history
        
        Args:
            news_items: List of news items to save
            append: If True, merge with existing cache (new items on top). If False, replace cache.
        """
        try:
            if append:
                # Merge with existing cache - new items on top
                # IMPORTANT: Load with allow_stale=True to get all cached items, even if expired
                existing_news = self.load_news(allow_stale=True) or []
                
                # Create a map of existing items by ID and title+source to preserve added_to_feed_at
                existing_by_id = {str(item.get('id', '')): item for item in existing_news if item.get('id')}
                existing_by_key = {f"{item.get('title', '').lower()}_{item.get('source', '').lower()}": item 
                                   for item in existing_news if item.get('title')}
                
                # Create sets for deduplication
                existing_ids = set(existing_by_id.keys())
                existing_keys = set(existing_by_key.keys())
                
                # Add new items that don't already exist
                new_items = []
                current_time = datetime.now().isoformat()
                
                for item in news_items:
                    item_id = str(item.get('id', ''))
                    item_key = f"{item.get('title', '').lower()}_{item.get('source', '').lower()}"
                    
                    # Check if item is new (not in existing cache)
                    if item_id and item_id in existing_ids:
                        # Item exists in cache by ID - preserve its original added_to_feed_at
                        existing_item = existing_by_id[item_id]
                        if 'added_to_feed_at' in existing_item:
                            # Preserve the original timestamp - don't add to new_items (already in existing_news)
                            logger.debug(f"Preserving added_to_feed_at for existing item: {item.get('title', '')[:50]} (ID: {item_id})")
                            pass
                        else:
                            # Existing item doesn't have added_to_feed_at - add it from existing_news
                            pass
                    elif item_key in existing_keys:
                        # Item exists in cache by title+source - preserve its original added_to_feed_at
                        existing_item = existing_by_key[item_key]
                        if 'added_to_feed_at' in existing_item:
                            # Preserve the original timestamp - don't add to new_items (already in existing_news)
                            logger.debug(f"Preserving added_to_feed_at for existing item: {item.get('title', '')[:50]} (Key: {item_key})")
                            pass
                        else:
                            # Existing item doesn't have added_to_feed_at - add it from existing_news
                            pass
                    else:
                        # New item - set added_to_feed_at if not already set
                        if 'added_to_feed_at' not in item:
                            item['added_to_feed_at'] = current_time
                            logger.debug(f"Setting new added_to_feed_at for new item: {item.get('title', '')[:50]}")
                        new_items.append(item)
                        if item_id:
                            existing_ids.add(item_id)
                        existing_keys.add(item_key)
                
                # Preserve added_to_feed_at for all existing items (they already have it from load_news)
                # Combine: new items first, then existing items (preserving their original added_to_feed_at)
                merged_news = new_items + existing_news
                
                # Limit to reasonable size (keep first 200 items - newest first)
                if len(merged_news) > 200:
                    original_count = len(merged_news)
                    merged_news = merged_news[:200]
                    logger.info(f"Limited merged news to 200 items (was {original_count})")
                
                news_items = merged_news
                logger.info(f"Merged {len(new_items)} new items with {len(existing_news)} existing items = {len(news_items)} total")
            
            # Prepare cache data
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'news_count': len(news_items),
                'news': news_items,
                'max_age_hours': self.max_age_hours,
                'last_fetch': datetime.now().isoformat()  # Track when news was last fetched
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
            
            # Add to history (only new items if appending)
            if append:
                # Only add truly new items to history
                existing_history = self.load_history()
                existing_history_ids = {str(item.get('id', '')) for item in existing_history}
                new_items_for_history = [item for item in news_items if str(item.get('id', '')) not in existing_history_ids]
                if new_items_for_history:
                    self._add_to_history(new_items_for_history)
            else:
                # Replace mode - add all items to history
                self._add_to_history(news_items)
            
            logger.info(f"Cached {len(news_items)} news items to Firebase and updated history")
            return True
            
        except Exception as e:
            logger.error(f"Error saving news to persistent cache: {e}")
            return False
    
    def should_fetch_new_news(self, fetch_interval_minutes: int = 5, last_fetch: Optional[str] = None) -> bool:
        """
        Check if new news should be fetched based on last fetch time
        
        Args:
            fetch_interval_minutes: How often to fetch new news (default 5 minutes)
            last_fetch: Optional timestamp string from cache metadata (avoids extra Firebase call if provided)
        
        Returns:
            True if new news should be fetched, False otherwise
        """
        try:
            # If last_fetch is provided (from batched load_news call), use it to avoid extra Firebase call
            if last_fetch:
                try:
                    last_fetch_dt = datetime.fromisoformat(last_fetch.replace('Z', '+00:00'))
                    if last_fetch_dt.tzinfo:
                        last_fetch_dt = last_fetch_dt.replace(tzinfo=None)
                    time_since_fetch = datetime.now() - last_fetch_dt
                    
                    if time_since_fetch >= timedelta(minutes=fetch_interval_minutes):
                        logger.info(f"Last fetch was {time_since_fetch}, should fetch new news (interval: {fetch_interval_minutes} min)")
                        print(f"⏰ should_fetch_new_news: True (last fetch was {time_since_fetch} ago, >= {fetch_interval_minutes} min)")
                        return True
                    else:
                        logger.debug(f"Last fetch was {time_since_fetch}, skipping fetch (interval: {fetch_interval_minutes} min)")
                        print(f"⏰ should_fetch_new_news: False (last fetch was {time_since_fetch} ago, < {fetch_interval_minutes} min)")
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
                    logger.info(f"Last fetch was {time_since_fetch}, should fetch new news (interval: {fetch_interval_minutes} min)")
                    print(f"⏰ should_fetch_new_news: True (last fetch was {time_since_fetch} ago, >= {fetch_interval_minutes} min)")
                    return True
                else:
                    logger.debug(f"Last fetch was {time_since_fetch}, skipping fetch (interval: {fetch_interval_minutes} min)")
                    print(f"⏰ should_fetch_new_news: False (last fetch was {time_since_fetch} ago, < {fetch_interval_minutes} min)")
                    return False
            except Exception as e:
                logger.warning(f"Error parsing last_fetch timestamp: {e}")
                return True  # On error, fetch to be safe
            
        except Exception as e:
            logger.error(f"Error checking if should fetch new news: {e}")
            return True  # On error, fetch to be safe
    
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
    
    def load_news(self, allow_stale: bool = True, return_metadata: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        Load news items from cache
        
        Args:
            allow_stale: If True, return cache even if expired (for faster UI loading).
                        If False, only return cache if not expired (default: True for better UX)
            return_metadata: If True, return dict with 'news' and 'last_fetch' keys instead of just news list.
                           This allows batching with should_fetch_new_news() to avoid extra Firebase calls.
        
        Returns:
            List of news items or None if no cache exists.
            If return_metadata=True, returns dict with keys: 'news' (list) and 'last_fetch' (str or None)
        """
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
            
            # Extract metadata for batching
            last_fetch_str = cache_data.get('last_fetch')
            
            try:
                cache_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Handle timezone-aware vs naive datetimes
                now = datetime.now()
                if cache_timestamp.tzinfo:
                    # Convert to naive datetime for comparison
                    cache_timestamp = cache_timestamp.replace(tzinfo=None)
                age = now - cache_timestamp
                
                news_items = cache_data.get('news', [])
                
                if age > timedelta(hours=self.max_age_hours):
                    if allow_stale:
                        # Return stale cache for faster UI loading (fresh fetch will happen in background)
                        logger.info(f"Cache is stale ({age}), but returning it for faster UI loading")
                        if return_metadata:
                            return {'news': news_items, 'last_fetch': last_fetch_str}
                        return news_items
                    else:
                        logger.info(f"Cache is too old ({age}), ignoring")
                        return None
                
                logger.info(f"Loaded {len(news_items)} news items from Firebase cache (age: {age})")
                if return_metadata:
                    return {'news': news_items, 'last_fetch': last_fetch_str}
                return news_items
                
            except Exception as e:
                logger.warning(f"Error parsing cache timestamp: {e}")
                # If timestamp parsing fails, still return the news (better than nothing)
                news_items = cache_data.get('news', [])
                if news_items:
                    logger.info(f"Loaded {len(news_items)} news items from cache (timestamp parse error, but returning news)")
                    if return_metadata:
                        return {'news': news_items, 'last_fetch': last_fetch_str}
                    return news_items
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
    
    def remove_filtered_items(self, filter_phrase: str) -> Dict[str, Any]:
        """
        Remove news items from cache and history that match a filter phrase in their title
        
        Args:
            filter_phrase: Phrase to search for in news item titles (case-sensitive)
        
        Returns:
            Dict with counts of removed items from cache and history
        """
        removed_from_cache = 0
        removed_from_history = 0
        
        try:
            # Remove from cache
            cache_path = self._get_cache_path()
            cache_data = self.firebase._make_request('GET', cache_path)
            
            if cache_data and isinstance(cache_data, dict):
                news_items = cache_data.get('news', [])
                if news_items:
                    original_count = len(news_items)
                    # Filter out items matching the phrase
                    filtered_news = [item for item in news_items if filter_phrase not in item.get('title', '')]
                    removed_from_cache = original_count - len(filtered_news)
                    
                    if removed_from_cache > 0:
                        # Update cache with filtered items
                        cache_data['news'] = filtered_news
                        cache_data['news_count'] = len(filtered_news)
                        cache_data['timestamp'] = datetime.now().isoformat()
                        self.firebase._make_request('PUT', cache_path, cache_data)
                        logger.info(f"Removed {removed_from_cache} items from cache matching filter: {filter_phrase}")
            
            # Remove from history
            history_path = self._get_history_path()
            history_data = self.firebase._make_request('GET', history_path)
            
            if history_data and isinstance(history_data, dict):
                # Find items to remove
                items_to_remove = []
                for news_id, item_data in history_data.items():
                    if isinstance(item_data, dict):
                        title = item_data.get('title', '')
                        if filter_phrase in title:
                            items_to_remove.append(news_id)
                
                # Delete matching items
                for news_id in items_to_remove:
                    item_path = self._get_history_item_path(news_id)
                    self.firebase._make_request('DELETE', item_path)
                    removed_from_history += 1
                
                if removed_from_history > 0:
                    logger.info(f"Removed {removed_from_history} items from history matching filter: {filter_phrase}")
            
            return {
                'success': True,
                'removed_from_cache': removed_from_cache,
                'removed_from_history': removed_from_history,
                'total_removed': removed_from_cache + removed_from_history,
                'filter_phrase': filter_phrase
            }
            
        except Exception as e:
            logger.error(f"Error removing filtered items: {e}")
            return {
                'success': False,
                'error': str(e),
                'removed_from_cache': removed_from_cache,
                'removed_from_history': removed_from_history,
                'total_removed': removed_from_cache + removed_from_history
            }

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

