#!/usr/bin/env python3
"""
FXSentinel API Rate Limiter
Manages API usage to prevent overusage and optimize performance
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests_per_minute: int
    max_requests_per_hour: int
    max_requests_per_day: int
    cooldown_period: int  # seconds to wait when limit exceeded

class APIRateLimiter:
    def __init__(self):
        """Initialize the API rate limiter"""
        self.request_history = {}
        self.rate_limits = {
            'health_checks': RateLimitConfig(
                max_requests_per_minute=2,   # Only 2 health checks per minute
                max_requests_per_hour=60,    # 60 per hour
                max_requests_per_day=1000,   # 1000 per day
                cooldown_period=30
            ),
            'news_fetch': RateLimitConfig(
                max_requests_per_minute=1,   # 1 news fetch per minute
                max_requests_per_hour=30,    # 30 per hour
                max_requests_per_day=500,    # 500 per day
                cooldown_period=60
            ),
            'forex_prices': RateLimitConfig(
                max_requests_per_minute=1,   # 1 price fetch per minute
                max_requests_per_hour=20,    # 20 per hour
                max_requests_per_day=300,    # 300 per day
                cooldown_period=120
            ),
            'ai_analysis': RateLimitConfig(
                max_requests_per_minute=5,   # 5 AI calls per minute
                max_requests_per_hour=100,   # 100 per hour
                max_requests_per_day=1000,   # 1000 per day
                cooldown_period=60
            ),
            'telegram_monitor': RateLimitConfig(
                max_requests_per_minute=2,   # 2 telegram checks per minute
                max_requests_per_hour=50,    # 50 per hour
                max_requests_per_day=800,    # 800 per day
                cooldown_period=30
            ),
            'economic_calendar': RateLimitConfig(
                max_requests_per_minute=1,   # 1 calendar check per minute
                max_requests_per_hour=15,    # 15 per hour
                max_requests_per_day=200,    # 200 per day
                cooldown_period=300
            )
        }
        
        # Cache configuration
        self.cache_durations = {
            'health_checks': 300,      # 5 minutes
            'news_fetch': 120,         # 2 minutes
            'forex_prices': 300,       # 5 minutes
            'ai_analysis': 3600,       # 1 hour
            'telegram_monitor': 60,    # 1 minute
            'economic_calendar': 1800  # 30 minutes
        }
        
        # Cache storage
        self.cache = {}
    
    def can_make_request(self, request_type: str, identifier: str = "default") -> bool:
        """Check if a request can be made based on rate limits"""
        try:
            if request_type not in self.rate_limits:
                logger.warning(f"Unknown request type: {request_type}")
                return True  # Allow unknown types
            
            config = self.rate_limits[request_type]
            key = f"{request_type}:{identifier}"
            
            # Initialize history if not exists
            if key not in self.request_history:
                self.request_history[key] = []
            
            now = datetime.now()
            history = self.request_history[key]
            
            # Clean old entries
            history = [req_time for req_time in history if 
                      (now - req_time).total_seconds() < 86400]  # Keep last 24 hours
            self.request_history[key] = history
            
            # Check minute limit
            minute_ago = now - timedelta(minutes=1)
            minute_requests = len([req_time for req_time in history if req_time > minute_ago])
            
            if minute_requests >= config.max_requests_per_minute:
                logger.warning(f"Rate limit exceeded for {request_type}: {minute_requests}/{config.max_requests_per_minute} per minute")
                return False
            
            # Check hour limit
            hour_ago = now - timedelta(hours=1)
            hour_requests = len([req_time for req_time in history if req_time > hour_ago])
            
            if hour_requests >= config.max_requests_per_hour:
                logger.warning(f"Rate limit exceeded for {request_type}: {hour_requests}/{config.max_requests_per_hour} per hour")
                return False
            
            # Check day limit
            day_ago = now - timedelta(days=1)
            day_requests = len([req_time for req_time in history if req_time > day_ago])
            
            if day_requests >= config.max_requests_per_day:
                logger.warning(f"Rate limit exceeded for {request_type}: {day_requests}/{config.max_requests_per_day} per day")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {request_type}: {e}")
            return True  # Allow on error
    
    def record_request(self, request_type: str, identifier: str = "default"):
        """Record a request for rate limiting"""
        try:
            key = f"{request_type}:{identifier}"
            if key not in self.request_history:
                self.request_history[key] = []
            
            self.request_history[key].append(datetime.now())
            
        except Exception as e:
            logger.error(f"Error recording request for {request_type}: {e}")
    
    def get_cached_data(self, request_type: str, identifier: str = "default") -> Optional[Dict[str, Any]]:
        """Get cached data if available and not expired"""
        try:
            key = f"{request_type}:{identifier}"
            if key not in self.cache:
                return None
            
            cached_data = self.cache[key]
            cache_duration = self.cache_durations.get(request_type, 300)
            
            # Check if cache is still valid
            if (datetime.now() - cached_data['timestamp']).total_seconds() < cache_duration:
                logger.info(f"Cache hit for {request_type}")
                return cached_data['data']
            else:
                # Remove expired cache
                del self.cache[key]
                return None
                
        except Exception as e:
            logger.error(f"Error getting cached data for {request_type}: {e}")
            return None
    
    def cache_data(self, request_type: str, data: Dict[str, Any], identifier: str = "default"):
        """Cache data for future use"""
        try:
            key = f"{request_type}:{identifier}"
            self.cache[key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            logger.info(f"Cached data for {request_type}")
            
        except Exception as e:
            logger.error(f"Error caching data for {request_type}: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        try:
            stats = {}
            now = datetime.now()
            
            for request_type in self.rate_limits:
                config = self.rate_limits[request_type]
                key = f"{request_type}:default"
                
                if key in self.request_history:
                    history = self.request_history[key]
                    
                    # Calculate usage for different time periods
                    minute_ago = now - timedelta(minutes=1)
                    hour_ago = now - timedelta(hours=1)
                    day_ago = now - timedelta(days=1)
                    
                    minute_requests = len([req_time for req_time in history if req_time > minute_ago])
                    hour_requests = len([req_time for req_time in history if req_time > hour_ago])
                    day_requests = len([req_time for req_time in history if req_time > day_ago])
                    
                    stats[request_type] = {
                        'minute_usage': f"{minute_requests}/{config.max_requests_per_minute}",
                        'hour_usage': f"{hour_requests}/{config.max_requests_per_hour}",
                        'day_usage': f"{day_requests}/{config.max_requests_per_day}",
                        'cache_hits': len([k for k in self.cache.keys() if k.startswith(request_type)])
                    }
                else:
                    stats[request_type] = {
                        'minute_usage': f"0/{config.max_requests_per_minute}",
                        'hour_usage': f"0/{config.max_requests_per_hour}",
                        'day_usage': f"0/{config.max_requests_per_day}",
                        'cache_hits': 0
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {}
    
    def should_use_cache(self, request_type: str) -> bool:
        """Determine if cache should be used instead of making a new request"""
        try:
            # Check if we have recent cached data
            cached_data = self.get_cached_data(request_type)
            if cached_data:
                return True
            
            # Check rate limits
            if not self.can_make_request(request_type):
                logger.warning(f"Rate limit exceeded for {request_type}, using cache if available")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking cache usage for {request_type}: {e}")
            return False
    
    def get_cooldown_period(self, request_type: str) -> int:
        """Get cooldown period for a request type"""
        return self.rate_limits.get(request_type, RateLimitConfig(1, 10, 100, 60)).cooldown_period
    
    def clear_cache(self, request_type: str = None):
        """Clear cache for specific type or all cache"""
        try:
            if request_type:
                keys_to_remove = [k for k in self.cache.keys() if k.startswith(request_type)]
                for key in keys_to_remove:
                    del self.cache[key]
                logger.info(f"Cleared cache for {request_type}")
            else:
                self.cache.clear()
                logger.info("Cleared all cache")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

# Global instance
api_rate_limiter = APIRateLimiter()
