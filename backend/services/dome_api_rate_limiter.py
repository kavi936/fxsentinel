#!/usr/bin/env python3
"""
Dome API Rate Limiter
Handles rate limiting for Dome API free tier (1 request per second)
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)

class DomeAPIRateLimiter:
    """
    Rate limiter for Dome API free tier (1 QPS)
    Uses a token bucket-like approach with request queuing
    Implements exponential backoff on rate limit errors
    """
    
    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Maximum requests per second (default: 1.0 for free tier)
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second  # Minimum time between requests
        
        # Thread-safe request tracking
        self.lock = threading.Lock()
        self.last_request_time = None
        self.request_times = deque(maxlen=100)  # Track last 100 requests
        
        # Exponential backoff tracking
        self.consecutive_rate_limits = 0
        self.last_rate_limit_time = None
        self.backoff_multiplier = 1.0  # Start with 1x wait time
        self.max_backoff_seconds = 60  # Maximum backoff time
        
        # Statistics
        self.total_requests = 0
        self.rate_limit_hits = 0
        self.total_wait_time = 0.0
    
    def wait_if_needed(self) -> float:
        """
        Wait if necessary to respect rate limits
        Includes exponential backoff if we've been hitting rate limits
        Returns the time waited in seconds
        """
        with self.lock:
            now = time.time()
            wait_time = 0.0
            
            # Apply exponential backoff if we've been hitting rate limits
            base_wait = self.min_interval
            if self.consecutive_rate_limits > 0:
                # Exponential backoff: wait longer after each rate limit hit
                backoff_time = base_wait * self.backoff_multiplier
                backoff_time = min(backoff_time, self.max_backoff_seconds)
                
                # If we recently hit a rate limit, add extra wait time
                if self.last_rate_limit_time:
                    time_since_rate_limit = now - self.last_rate_limit_time
                    if time_since_rate_limit < 10:  # Within 10 seconds of rate limit
                        wait_time = max(wait_time, backoff_time - time_since_rate_limit)
            
            if self.last_request_time is not None:
                time_since_last = now - self.last_request_time
                
                # Wait for base interval plus any backoff
                required_wait = base_wait + wait_time
                if time_since_last < required_wait:
                    wait_time = required_wait - time_since_last
                    if wait_time > 0:
                        logger.debug(f"Rate limiter: waiting {wait_time:.2f}s (backoff: {self.backoff_multiplier}x)")
                        time.sleep(wait_time)
                        self.total_wait_time += wait_time
            
            self.last_request_time = time.time()
            self.request_times.append(self.last_request_time)
            self.total_requests += 1
            
            # Reset backoff if we successfully made a request after waiting
            if wait_time > 0 and self.consecutive_rate_limits > 0:
                # Gradually reduce backoff after successful requests
                self.consecutive_rate_limits = max(0, self.consecutive_rate_limits - 1)
                if self.consecutive_rate_limits == 0:
                    self.backoff_multiplier = 1.0
            
            return wait_time
    
    def can_make_request(self) -> bool:
        """
        Check if we can make a request now (non-blocking)
        Returns True if we can make request immediately
        """
        with self.lock:
            if self.last_request_time is None:
                return True
            
            time_since_last = time.time() - self.last_request_time
            return time_since_last >= self.min_interval
    
    def get_time_until_next_request(self) -> float:
        """
        Get seconds until next request can be made
        Returns 0 if request can be made now
        """
        with self.lock:
            if self.last_request_time is None:
                return 0.0
            
            time_since_last = time.time() - self.last_request_time
            if time_since_last >= self.min_interval:
                return 0.0
            
            return self.min_interval - time_since_last
    
    def record_rate_limit_hit(self):
        """Record that we hit a rate limit and apply exponential backoff"""
        with self.lock:
            self.rate_limit_hits += 1
            self.consecutive_rate_limits += 1
            self.last_rate_limit_time = time.time()
            
            # Exponential backoff: double the wait time after each rate limit
            # Cap at max_backoff_seconds
            self.backoff_multiplier = min(2.0 ** self.consecutive_rate_limits, self.max_backoff_seconds / self.min_interval)
            
            logger.warning(f"Rate limit hit (#{self.consecutive_rate_limits}). "
                         f"Backoff multiplier: {self.backoff_multiplier:.2f}x "
                         f"(will wait up to {self.min_interval * self.backoff_multiplier:.2f}s between requests)")
            
            # Wait extra time immediately after rate limit hit
            extra_wait = self.min_interval * self.backoff_multiplier
            logger.info(f"Waiting {extra_wait:.2f}s after rate limit hit")
            time.sleep(extra_wait)
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        with self.lock:
            return {
                "total_requests": self.total_requests,
                "rate_limit_hits": self.rate_limit_hits,
                "total_wait_time": self.total_wait_time,
                "avg_wait_time": self.total_wait_time / max(self.total_requests, 1),
                "requests_per_second": self.requests_per_second,
                "consecutive_rate_limits": self.consecutive_rate_limits,
                "backoff_multiplier": self.backoff_multiplier
            }
    
    def reset_stats(self):
        """Reset statistics (keeps rate limiting state)"""
        with self.lock:
            self.total_requests = 0
            self.rate_limit_hits = 0
            self.total_wait_time = 0.0
            self.consecutive_rate_limits = 0
            self.backoff_multiplier = 1.0
            self.last_rate_limit_time = None

# Global instance for Dome API
dome_rate_limiter = DomeAPIRateLimiter(requests_per_second=1.0)

