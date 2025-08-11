#!/usr/bin/env python3
"""
News caching system to store and serve real news data
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NewsCache:
    def __init__(self, cache_file: str = 'news_cache.json', max_age_hours: int = 2):  # Reduced from 24 to 2 hours
        self.cache_file = cache_file
        self.max_age_hours = max_age_hours
        self.cache_dir = os.path.dirname(cache_file)
        
        # Ensure cache directory exists
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def save_news(self, news_items: List[Dict[str, Any]]) -> bool:
        """Save news items to cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'news_count': len(news_items),
                'news': news_items
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached {len(news_items)} news items")
            return True
            
        except Exception as e:
            logger.error(f"Error saving news to cache: {e}")
            return False
    
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

# Global instance
news_cache = NewsCache()
