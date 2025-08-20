#!/usr/bin/env python3
"""
Enhanced News caching system to store and serve real news data with history
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NewsCache:
    def __init__(self, cache_file: str = 'news_cache.json', max_age_hours: int = 0.25, history_file: str = 'news_history.json'):  # 15 minutes cache
        self.cache_file = cache_file
        self.history_file = history_file
        self.max_age_hours = max_age_hours
        self.cache_dir = os.path.dirname(cache_file)
        
        # Ensure cache directory exists
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def save_news(self, news_items: List[Dict[str, Any]]) -> bool:
        """Save news items to cache and add to history"""
        try:
            # Save current news to cache
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'news_count': len(news_items),
                'news': news_items
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # Add to history (keep last 100 news items)
            self._add_to_history(news_items)
            
            logger.info(f"Cached {len(news_items)} news items and updated history")
            return True
            
        except Exception as e:
            logger.error(f"Error saving news to cache: {e}")
            return False
    
    def _add_to_history(self, news_items: List[Dict[str, Any]]):
        """Add news items to history file"""
        try:
            history = self.load_history()
            
            # Add new items with timestamp
            for item in news_items:
                history_item = {
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'summary': item.get('summary'),
                    'source': item.get('source'),
                    'url': item.get('url'),
                    'published_at': item.get('published_at'),
                    'impact': item.get('impact'),
                    'currency_pairs': item.get('currency_pairs', []),
                    'cached_at': datetime.now().isoformat(),
                    'type': item.get('type', 'RSS_FEED')
                }
                history.append(history_item)
            
            # Keep only last 100 items to prevent file from growing too large
            if len(history) > 100:
                history = history[-100:]
            
            # Save updated history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Load news history"""
        try:
            if not os.path.exists(self.history_file):
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            return history
            
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []
    
    def get_news_by_id(self, news_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific news item by ID from cache or history"""
        try:
            # First check current cache
            cached_news = self.load_news()
            if cached_news:
                news_item = next((item for item in cached_news if item.get('id') == news_id), None)
                if news_item:
                    return news_item
            
            # If not in cache, check history
            history = self.load_history()
            history_item = next((item for item in history if item.get('id') == news_id), None)
            if history_item:
                return history_item
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting news by ID: {e}")
            return None
    
    def get_recent_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get news history from the last N hours"""
        try:
            history = self.load_history()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_items = []
            for item in history:
                try:
                    cached_at = datetime.fromisoformat(item.get('cached_at', '').replace('Z', '+00:00'))
                    if cached_at >= cutoff_time:
                        recent_items.append(item)
                except:
                    # If date parsing fails, include the item
                    recent_items.append(item)
            
            return recent_items
            
        except Exception as e:
            logger.error(f"Error getting recent history: {e}")
            return []
    
    def load_news(self) -> Optional[List[Dict[str, Any]]]:
        """Load news items from cache if they're not too old"""
        try:
            if not os.path.exists(self.cache_file):
                logger.info("No cache file found")
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is too old
            cache_timestamp = datetime.fromisoformat(cache_data['timestamp'])
            age = datetime.now() - cache_timestamp
            
            if age > timedelta(hours=self.max_age_hours):
                logger.info(f"Cache is too old ({age}), ignoring")
                return None
            
            news_items = cache_data.get('news', [])
            logger.info(f"Loaded {len(news_items)} news items from cache (age: {age})")
            return news_items
            
        except Exception as e:
            logger.error(f"Error loading news from cache: {e}")
            return None
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get information about the cache status"""
        try:
            if not os.path.exists(self.cache_file):
                return {
                    'exists': False,
                    'age': None,
                    'news_count': 0,
                    'is_valid': False
                }
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_timestamp = datetime.fromisoformat(cache_data['timestamp'])
            age = datetime.now() - cache_timestamp
            is_valid = age <= timedelta(hours=self.max_age_hours)
            
            return {
                'exists': True,
                'age': str(age),
                'news_count': cache_data.get('news_count', 0),
                'is_valid': is_valid,
                'last_updated': cache_data['timestamp']
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
            return {
                'total_items': len(history),
                'oldest_item': history[0].get('cached_at') if history else None,
                'newest_item': history[-1].get('cached_at') if history else None
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
        """Clear the cache file"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def clear_history(self) -> bool:
        """Clear the history file"""
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
                logger.info("History cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return False

# Global instance
news_cache = NewsCache()
