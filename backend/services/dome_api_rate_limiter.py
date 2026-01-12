#!/usr/bin/env python3
"""
Dome API Rate Limiter
Handles rate limiting for Dome API free tier (1 request per second, 10 requests per 10 seconds)
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
    Rate limiter for Dome API free tier
    - 1 request per second (QPS)
    - 10 requests per 10 seconds (rolling window)
    Uses a token bucket-like approach with request queuing
    Implements exponential backoff on rate limit errors
    """
    
    def __init__(self, requests_per_second: float = 1.0, requests_per_10_seconds: int = 10):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Maximum requests per second (default: 1.0 for free tier)
            requests_per_10_seconds: Maximum requests per 10 seconds (default: 10 for free tier)
        """
        self.requests_per_second = requests_per_second
        self.requests_per_10_seconds = requests_per_10_seconds
        self.min_interval = 1.0 / requests_per_second  # Minimum time between requests
        self.window_seconds = 10.0  # Rolling window size
        
        # Thread-safe request tracking
        self.lock = threading.Lock()
        self.last_request_time = None
        self.request_times = deque(maxlen=100)  # Track last 100 requests for statistics
        
        # Rolling 10-second window tracking
        self.window_request_times = deque()  # Track request times in rolling window
        
        # Exponential backoff tracking
        self.consecutive_rate_limits = 0
        self.last_rate_limit_time = None
        self.backoff_multiplier = 1.0  # Start with 1x wait time
        self.max_backoff_seconds = 60  # Maximum backoff time
        
        # Statistics
        self.total_requests = 0
        self.rate_limit_hits = 0
        self.total_wait_time = 0.0
        self.window_limit_hits = 0  # Track how many times we hit the 10-per-10-seconds limit
    
    def _clean_old_requests(self, now: float):
        """Remove request times older than the rolling window"""
        cutoff_time = now - self.window_seconds
        while self.window_request_times and self.window_request_times[0] < cutoff_time:
            self.window_request_times.popleft()
    
    def _count_requests_in_window(self, now: float) -> int:
        """Count requests in the last 10 seconds"""
        self._clean_old_requests(now)
        return len(self.window_request_times)
    
    def _get_time_until_window_available(self, now: float) -> float:
        """
        Calculate time until we can make another request without exceeding 10-per-10-seconds limit
        Returns 0 if we can make a request now
        """
        self._clean_old_requests(now)
        current_count = len(self.window_request_times)
        
        if current_count < self.requests_per_10_seconds:
            return 0.0
        
        # We're at the limit, need to wait until oldest request falls out of window
        oldest_request_time = self.window_request_times[0]
        time_until_available = (oldest_request_time + self.window_seconds) - now
        
        return max(0.0, time_until_available)
    
    def wait_if_needed(self) -> float:
        """
        Wait if necessary to respect rate limits
        Enforces both 1 QPS and 10 queries per 10 seconds limits
        Includes exponential backoff if we've been hitting rate limits
        Returns the time waited in seconds
        """
        with self.lock:
            now = time.time()
            wait_time = 0.0
            
            # Clean old requests from rolling window
            self._clean_old_requests(now)
            
            # Check 10-per-10-seconds limit first
            requests_in_window = len(self.window_request_times)
            if requests_in_window >= self.requests_per_10_seconds:
                # We're at the limit, calculate wait time until oldest request expires
                time_until_available = self._get_time_until_window_available(now)
                if time_until_available > 0:
                    window_wait = time_until_available
                    logger.debug(f"Rate limiter: 10-per-10-seconds limit reached ({requests_in_window}/{self.requests_per_10_seconds}), "
                               f"waiting {window_wait:.2f}s until window clears")
                    time.sleep(window_wait)
                    wait_time += window_wait
                    self.total_wait_time += window_wait
                    # Update now after waiting
                    now = time.time()
                    self._clean_old_requests(now)
            
            # Apply exponential backoff if we've been hitting rate limits
            base_wait = self.min_interval
            backoff_additional_wait = 0.0
            if self.consecutive_rate_limits > 0:
                # Exponential backoff: wait longer after each rate limit hit
                backoff_time = base_wait * self.backoff_multiplier
                backoff_time = min(backoff_time, self.max_backoff_seconds)
                
                # If we recently hit a rate limit, add extra wait time
                if self.last_rate_limit_time:
                    time_since_rate_limit = now - self.last_rate_limit_time
                    if time_since_rate_limit < 10:  # Within 10 seconds of rate limit
                        backoff_additional_wait = max(0, backoff_time - time_since_rate_limit)
            
            # Check 1 QPS limit (recalculate after any window wait)
            if self.last_request_time is not None:
                time_since_last = now - self.last_request_time
                
                # Calculate required wait for 1 QPS (base interval + backoff)
                required_qps_wait = base_wait + backoff_additional_wait
                if time_since_last < required_qps_wait:
                    qps_wait = required_qps_wait - time_since_last
                    if qps_wait > 0:
                        logger.debug(f"Rate limiter: waiting {qps_wait:.2f}s for 1 QPS limit (backoff: {self.backoff_multiplier}x)")
                        time.sleep(qps_wait)
                        wait_time += qps_wait
                        self.total_wait_time += qps_wait
                        # Update now after waiting
                        now = time.time()
            elif backoff_additional_wait > 0:
                # No previous request, but we need to wait for backoff
                logger.debug(f"Rate limiter: waiting {backoff_additional_wait:.2f}s for backoff")
                time.sleep(backoff_additional_wait)
                wait_time += backoff_additional_wait
                self.total_wait_time += backoff_additional_wait
                now = time.time()
            
            # Record this request
            request_time = time.time()
            self.last_request_time = request_time
            self.request_times.append(request_time)
            self.window_request_times.append(request_time)
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
        Checks both 1 QPS and 10-per-10-seconds limits
        """
        with self.lock:
            now = time.time()
            
            # Check 1 QPS limit
            if self.last_request_time is not None:
                time_since_last = now - self.last_request_time
                if time_since_last < self.min_interval:
                    return False
            
            # Check 10-per-10-seconds limit
            self._clean_old_requests(now)
            requests_in_window = len(self.window_request_times)
            if requests_in_window >= self.requests_per_10_seconds:
                return False
            
            return True
    
    def get_time_until_next_request(self) -> float:
        """
        Get seconds until next request can be made
        Returns 0 if request can be made now
        Considers both 1 QPS and 10-per-10-seconds limits
        """
        with self.lock:
            now = time.time()
            
            # Check 10-per-10-seconds limit first (usually the longer wait)
            time_until_window = self._get_time_until_window_available(now)
            
            # Check 1 QPS limit
            time_until_qps = 0.0
            if self.last_request_time is not None:
                time_since_last = now - self.last_request_time
                if time_since_last < self.min_interval:
                    time_until_qps = self.min_interval - time_since_last
            
            # Return the longer of the two wait times
            return max(time_until_window, time_until_qps)
    
    def record_rate_limit_hit(self):
        """Record that we hit a rate limit and apply exponential backoff"""
        with self.lock:
            now = time.time()
            self.rate_limit_hits += 1
            self.consecutive_rate_limits += 1
            self.last_rate_limit_time = now
            
            # Check if this was likely a 10-per-10-seconds limit hit
            requests_in_window = self._count_requests_in_window(now)
            if requests_in_window >= self.requests_per_10_seconds:
                self.window_limit_hits += 1
                logger.warning(f"Rate limit hit - likely 10-per-10-seconds limit "
                            f"({requests_in_window}/{self.requests_per_10_seconds} requests in window)")
            else:
                logger.warning(f"Rate limit hit - likely 1 QPS limit")
            
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
            now = time.time()
            self._clean_old_requests(now)
            requests_in_window = len(self.window_request_times)
            
            return {
                "total_requests": self.total_requests,
                "rate_limit_hits": self.rate_limit_hits,
                "window_limit_hits": self.window_limit_hits,
                "total_wait_time": self.total_wait_time,
                "avg_wait_time": self.total_wait_time / max(self.total_requests, 1),
                "requests_per_second": self.requests_per_second,
                "requests_per_10_seconds": self.requests_per_10_seconds,
                "requests_in_current_window": requests_in_window,
                "consecutive_rate_limits": self.consecutive_rate_limits,
                "backoff_multiplier": self.backoff_multiplier
            }
    
    def reset_stats(self):
        """Reset statistics (keeps rate limiting state)"""
        with self.lock:
            self.total_requests = 0
            self.rate_limit_hits = 0
            self.window_limit_hits = 0
            self.total_wait_time = 0.0
            self.consecutive_rate_limits = 0
            self.backoff_multiplier = 1.0
            self.last_rate_limit_time = None
            # Note: window_request_times is kept to maintain rate limiting behavior

# Global instance for Dome API
# Free tier: 1 QPS, 10 queries per 10 seconds
dome_rate_limiter = DomeAPIRateLimiter(requests_per_second=1.0, requests_per_10_seconds=10)

