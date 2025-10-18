#!/usr/bin/env python3
"""
FXSentinel Subscription Cache Service
Fixes async/sync race conditions and performance issues with subscription validation
"""

import asyncio
import threading
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SubscriptionStatus(Enum):
    """Subscription status enumeration (freemium model)"""
    FREE = "free"
    PREMIUM = "premium"
    PAST_DUE = "past_due"
    DEVELOPER = "developer"
    UNKNOWN = "unknown"

@dataclass
class CachedSubscription:
    """Cached subscription data"""
    user_id: str
    status: SubscriptionStatus
    cached_at: datetime
    expires_at: datetime
    stripe_data: Dict[str, Any]
    is_valid: bool

class SubscriptionCache:
    """
    Thread-safe subscription cache with async support
    Fixes race conditions and performance issues
    """
    
    def __init__(self, cache_ttl_minutes: int = 15):
        self.cache_ttl_minutes = cache_ttl_minutes
        self._cache: Dict[str, CachedSubscription] = {}
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.stripe_api_calls = 0
        self.errors = 0
        
        logger.info(f"Subscription cache initialized with {cache_ttl_minutes} minute TTL")
    
    def _is_cache_valid(self, cached_sub: CachedSubscription) -> bool:
        """Check if cached subscription is still valid"""
        return datetime.now() < cached_sub.expires_at
    
    def _get_valid_statuses(self) -> set:
        """Get set of valid subscription statuses (freemium model)"""
        return {
            SubscriptionStatus.FREE,
            SubscriptionStatus.PREMIUM,
            SubscriptionStatus.DEVELOPER
        }
    
    def _parse_stripe_status(self, stripe_data: Dict[str, Any]) -> Tuple[SubscriptionStatus, bool]:
        """Parse Stripe data and determine subscription status (freemium model)"""
        try:
            status = stripe_data.get('status', 'unknown').lower()
            
            # Map Stripe status to our enum (freemium model)
            status_map = {
                'free': SubscriptionStatus.FREE,
                'premium': SubscriptionStatus.PREMIUM,
                'active': SubscriptionStatus.PREMIUM,  # Legacy mapping
                'past_due': SubscriptionStatus.PAST_DUE,
                'developer': SubscriptionStatus.DEVELOPER
            }
            
            subscription_status = status_map.get(status, SubscriptionStatus.UNKNOWN)
            is_valid = subscription_status in self._get_valid_statuses()
            
            return subscription_status, is_valid
            
        except Exception as e:
            logger.error(f"Error parsing Stripe status: {e}")
            return SubscriptionStatus.UNKNOWN, False
    
    def get_cached_subscription(self, user_id: str) -> Optional[CachedSubscription]:
        """Get cached subscription (thread-safe)"""
        with self._lock:
            if user_id in self._cache:
                cached_sub = self._cache[user_id]
                if self._is_cache_valid(cached_sub):
                    self.cache_hits += 1
                    return cached_sub
                else:
                    # Remove expired cache entry
                    del self._cache[user_id]
            
            self.cache_misses += 1
            return None
    
    def set_cached_subscription(self, user_id: str, stripe_data: Dict[str, Any]) -> CachedSubscription:
        """Set cached subscription (thread-safe)"""
        with self._lock:
            status, is_valid = self._parse_stripe_status(stripe_data)
            
            cached_sub = CachedSubscription(
                user_id=user_id,
                status=status,
                cached_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=self.cache_ttl_minutes),
                stripe_data=stripe_data,
                is_valid=is_valid
            )
            
            self._cache[user_id] = cached_sub
            logger.debug(f"Cached subscription for user {user_id}: {status.value} (valid: {is_valid})")
            return cached_sub
    
    def invalidate_cache(self, user_id: str) -> None:
        """Invalidate cached subscription (thread-safe)"""
        with self._lock:
            if user_id in self._cache:
                del self._cache[user_id]
                logger.debug(f"Invalidated cache for user {user_id}")
    
    def clear_cache(self) -> None:
        """Clear all cached subscriptions (thread-safe)"""
        with self._lock:
            cache_size = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared subscription cache ({cache_size} entries)")
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries (thread-safe)"""
        with self._lock:
            expired_count = 0
            current_time = datetime.now()
            
            expired_keys = [
                user_id for user_id, cached_sub in self._cache.items()
                if current_time >= cached_sub.expires_at
            ]
            
            for user_id in expired_keys:
                del self._cache[user_id]
                expired_count += 1
            
            if expired_count > 0:
                logger.debug(f"Cleaned up {expired_count} expired cache entries")
            
            return expired_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_size': len(self._cache),
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'hit_rate_percent': round(hit_rate, 2),
                'stripe_api_calls': self.stripe_api_calls,
                'errors': self.errors,
                'cache_ttl_minutes': self.cache_ttl_minutes
            }
    
    async def get_subscription_status_async(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Get subscription status asynchronously with caching
        Returns: (is_valid, error_message)
        """
        try:
            # Check cache first
            cached_sub = self.get_cached_subscription(user_id)
            if cached_sub:
                return cached_sub.is_valid, None
            
            # Cache miss - fetch from Stripe
            async with self._async_lock:
                # Double-check cache after acquiring lock
                cached_sub = self.get_cached_subscription(user_id)
                if cached_sub:
                    return cached_sub.is_valid, None
                
                # Fetch from Stripe
                stripe_data = await self._fetch_stripe_subscription_async(user_id)
                if stripe_data is None:
                    self.errors += 1
                    return False, "Failed to fetch subscription data"
                
                # Cache the result
                cached_sub = self.set_cached_subscription(user_id, stripe_data)
                return cached_sub.is_valid, None
                
        except Exception as e:
            self.errors += 1
            error_msg = f"Error checking subscription: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_subscription_status_sync(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Get subscription status synchronously with caching
        Returns: (is_valid, error_message)
        """
        try:
            # Check cache first
            cached_sub = self.get_cached_subscription(user_id)
            if cached_sub:
                return cached_sub.is_valid, None
            
            # Cache miss - fetch from Stripe
            with self._lock:
                # Double-check cache after acquiring lock
                cached_sub = self.get_cached_subscription(user_id)
                if cached_sub:
                    return cached_sub.is_valid, None
                
                # Fetch from Stripe
                stripe_data = self._fetch_stripe_subscription_sync(user_id)
                if stripe_data is None:
                    self.errors += 1
                    return False, "Failed to fetch subscription data"
                
                # Cache the result
                cached_sub = self.set_cached_subscription(user_id, stripe_data)
                return cached_sub.is_valid, None
                
        except Exception as e:
            self.errors += 1
            error_msg = f"Error checking subscription: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def _fetch_stripe_subscription_async(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch subscription data from Stripe asynchronously"""
        try:
            from services.stripe_service import StripeService
            stripe_service = StripeService()
            
            # Use asyncio to run the sync Stripe call
            loop = asyncio.get_event_loop()
            stripe_data = await loop.run_in_executor(
                None, 
                stripe_service.get_subscription_status, 
                user_id
            )
            
            self.stripe_api_calls += 1
            return stripe_data
            
        except Exception as e:
            logger.error(f"Error fetching Stripe subscription for {user_id}: {e}")
            return None
    
    def _fetch_stripe_subscription_sync(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch subscription data from Stripe synchronously"""
        try:
            from services.stripe_service import StripeService
            stripe_service = StripeService()
            
            stripe_data = stripe_service.get_subscription_status(user_id)
            self.stripe_api_calls += 1
            return stripe_data
            
        except Exception as e:
            logger.error(f"Error fetching Stripe subscription for {user_id}: {e}")
            return None

# Global cache instance
subscription_cache = SubscriptionCache()

# Convenience functions for easy access
async def get_subscription_status_async(user_id: str) -> Tuple[bool, Optional[str]]:
    """Get subscription status asynchronously"""
    return await subscription_cache.get_subscription_status_async(user_id)

def get_subscription_status_sync(user_id: str) -> Tuple[bool, Optional[str]]:
    """Get subscription status synchronously"""
    return subscription_cache.get_subscription_status_sync(user_id)

def invalidate_subscription_cache(user_id: str) -> None:
    """Invalidate cached subscription"""
    subscription_cache.invalidate_cache(user_id)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return subscription_cache.get_cache_stats()

def clear_subscription_cache() -> None:
    """Clear all cached subscriptions"""
    subscription_cache.clear_cache()
