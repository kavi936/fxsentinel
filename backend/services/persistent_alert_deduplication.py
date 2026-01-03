#!/usr/bin/env python3
"""
Persistent Alert Deduplication Service
Single source of truth for alert deduplication using Firebase Realtime Database
Replaces all in-memory deduplication systems
"""

import logging
import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .firebase_realtime_storage import FirebaseRealtimeStorage

logger = logging.getLogger(__name__)

class PersistentAlertDeduplication:
    """
    Persistent deduplication service that stores state in Firebase Realtime Database
    This ensures deduplication survives restarts and works across multiple instances
    """
    
    def __init__(self):
        self.firebase = FirebaseRealtimeStorage()
        self.alert_ttl_hours = 2  # How long to remember sent alerts (reduced from 24h to 2h)
        self.cleanup_interval = 50  # Cleanup every N operations (increased frequency)
        self.operations_count = 0
        self.duplicates_prevented = 0
        
        # In-memory cache for content hashes (global deduplication)
        # Key: content_hash, Value: expires_at timestamp
        self._content_hash_cache: Dict[str, datetime] = {}
        self._cache_ttl_seconds = 300  # Cache for 5 minutes to reduce Firebase calls
        
        # Thread lock for cache operations
        self._cache_lock = threading.Lock()
        
        logger.info("Persistent Alert Deduplication Service initialized with caching")
    
    def _generate_alert_key(self, alert_type: str, content: str, user_id: str) -> str:
        """Generate unique alert key for deduplication"""
        # Create a hash based on type, content, and user
        content_str = f"{alert_type}:{content}:{user_id}"
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash of alert content for global deduplication"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_alert_path(self, alert_key: str) -> str:
        """Get Firebase path for alert record"""
        return f"alert_deduplication/alerts/{alert_key}"
    
    def _get_content_hash_path(self, content_hash: str) -> str:
        """Get Firebase path for content hash"""
        return f"alert_deduplication/content_hashes/{content_hash}"
    
    def should_send_alert(self, alert_type: str, content: str, user_id: str) -> bool:
        """
        Check if alert should be sent (not a duplicate)
        Returns: True if alert should be sent, False if it's a duplicate
        """
        try:
            self.operations_count += 1
            
            # Automatic cleanup of expired records (increased frequency)
            if self.operations_count % self.cleanup_interval == 0:
                self.cleanup_expired_alerts()
                self._cleanup_expired_content_hashes()
            
            # Generate keys
            alert_key = self._generate_alert_key(alert_type, content, user_id)
            content_hash = self._generate_content_hash(content)
            
            # Check if we've already sent this exact alert to this user
            alert_path = self._get_alert_path(alert_key)
            existing_alert = self.firebase._make_request('GET', alert_path)
            
            # Handle Firebase connection errors gracefully
            if existing_alert is None:
                # Firebase connection failed - log warning but allow alert (fail open)
                logger.warning(f"Firebase connection failed, allowing alert (fail-open mode)")
                return True
            
            if existing_alert and isinstance(existing_alert, dict):
                # Check if alert hasn't expired
                expires_at_str = existing_alert.get('expires_at')
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if datetime.now() < expires_at:
                            self.duplicates_prevented += 1
                            logger.debug(f"Duplicate alert prevented for user {user_id}: {alert_type}")
                            return False
                    except Exception as e:
                        logger.warning(f"Error parsing expires_at: {e}")
                        # If we can't parse, assume it's expired and allow alert
            
            # This is a new alert
            return True
            
        except Exception as e:
            logger.error(f"Error checking alert deduplication: {e}")
            # On error, allow alert to be sent (fail open)
            return True
    
    def mark_alert_sent(self, alert_type: str, content: str, user_id: str) -> bool:
        """Mark an alert as sent to prevent duplicates"""
        try:
            alert_key = self._generate_alert_key(alert_type, content, user_id)
            content_hash = self._generate_content_hash(content)
            
            # Create alert record
            now = datetime.now()
            expires_at = now + timedelta(hours=self.alert_ttl_hours)
            
            alert_record = {
                'alert_type': alert_type,
                'user_id': user_id,
                'content_hash': content_hash,
                'sent_at': now.isoformat(),
                'expires_at': expires_at.isoformat()
            }
            
            # Store in Firebase
            alert_path = self._get_alert_path(alert_key)
            result = self.firebase._make_request('PUT', alert_path, alert_record)
            
            if result is not None:
                logger.debug(f"Marked alert as sent: {alert_type} for user {user_id}")
                return True
            else:
                logger.warning(f"Failed to mark alert as sent in Firebase")
                return False
            
        except Exception as e:
            logger.error(f"Error marking alert as sent: {e}")
            return False
    
    def _get_news_content_hash(self, news_item: Dict[str, Any]) -> str:
        """Generate content hash for news item (for global deduplication)"""
        try:
            # Use news_id if available (most reliable)
            news_id = str(news_item.get('id', ''))
            if news_id:
                return hashlib.md5(f"news:{news_id}".encode()).hexdigest()
            
            # Fallback to title+source+url
            title = news_item.get('title', '')
            source = news_item.get('source', '')
            url = news_item.get('url', '')
            content_str = f"news:{title}|{source}|{url}"
            return hashlib.md5(content_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating news content hash: {e}")
            return ""
    
    def _check_global_content_hash(self, content_hash: str) -> bool:
        """
        Check if content hash has been sent globally (optimization)
        Returns: True if content is new, False if already sent
        """
        try:
            now = datetime.now()
            
            # Check in-memory cache first (thread-safe)
            with self._cache_lock:
                if content_hash in self._content_hash_cache:
                    expires_at = self._content_hash_cache[content_hash]
                    if now < expires_at:
                        # Content already sent globally
                        return False
                    else:
                        # Cache expired, remove it
                        del self._content_hash_cache[content_hash]
            
            # Check Firebase for global content hash
            content_hash_path = self._get_content_hash_path(content_hash)
            existing_hash = self.firebase._make_request('GET', content_hash_path)
            
            if existing_hash and isinstance(existing_hash, dict):
                expires_at_str = existing_hash.get('expires_at')
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if now < expires_at:
                            # Content already sent globally - cache it (thread-safe)
                            with self._cache_lock:
                                self._content_hash_cache[content_hash] = expires_at
                            return False
                    except Exception as e:
                        logger.warning(f"Error parsing expires_at for content hash: {e}")
            
            # Content is new
            return True
            
        except Exception as e:
            logger.error(f"Error checking global content hash: {e}")
            return True  # Allow alert if check fails
    
    def _mark_global_content_hash(self, content_hash: str):
        """Mark content hash as sent globally (optimization)"""
        try:
            now = datetime.now()
            expires_at = now + timedelta(hours=self.alert_ttl_hours)
            
            # Cache in memory (thread-safe)
            with self._cache_lock:
                self._content_hash_cache[content_hash] = expires_at
            
            # Store in Firebase
            content_hash_path = self._get_content_hash_path(content_hash)
            hash_record = {
                'content_hash': content_hash,
                'sent_at': now.isoformat(),
                'expires_at': expires_at.isoformat()
            }
            self.firebase._make_request('PUT', content_hash_path, hash_record)
            
        except Exception as e:
            logger.error(f"Error marking global content hash: {e}")
    
    def should_send_news_alert(self, news_item: Dict[str, Any], user_id: str) -> bool:
        """
        Check if news alert should be sent (not a duplicate)
        OPTIMIZED: First checks global content hash, then per-user
        """
        try:
            # Generate content hash for global deduplication
            content_hash = self._get_news_content_hash(news_item)
            
            if content_hash:
                # OPTIMIZATION: Check global content hash first (one check for all users)
                if not self._check_global_content_hash(content_hash):
                    # Content already sent globally - no need to check per-user
                    logger.debug(f"Global duplicate prevented: {news_item.get('title', '')[:30]}...")
                    return False
            
            # Create content string from news item for per-user check
            title = news_item.get('title', '')
            source = news_item.get('source', '')
            url = news_item.get('url', '')
            news_id = str(news_item.get('id', ''))
            
            # Use news_id if available, otherwise use title+source+url
            if news_id:
                content = f"news:{news_id}"
            else:
                content = f"news:{title}|{source}|{url}"
            
            # Check per-user deduplication (only if global check passed)
            should_send = self.should_send_alert('news', content, user_id)
            
            return should_send
            
        except Exception as e:
            logger.error(f"Error checking news alert deduplication: {e}")
            return True  # Allow alert if check fails
    
    def mark_news_alert_sent(self, news_item: Dict[str, Any], user_id: str) -> bool:
        """
        Mark a news alert as sent after successful delivery
        OPTIMIZED: Marks both global content hash and per-user alert
        """
        try:
            # Generate content hash for global deduplication
            content_hash = self._get_news_content_hash(news_item)
            
            if content_hash:
                # OPTIMIZATION: Mark global content hash (prevents sending to other users)
                self._mark_global_content_hash(content_hash)
            
            # Create content string from news item (same as should_send_news_alert)
            title = news_item.get('title', '')
            source = news_item.get('source', '')
            url = news_item.get('url', '')
            news_id = str(news_item.get('id', ''))
            
            # Use news_id if available, otherwise use title+source+url
            if news_id:
                content = f"news:{news_id}"
            else:
                content = f"news:{title}|{source}|{url}"
            
            # Mark per-user alert as sent
            return self.mark_alert_sent('news', content, user_id)
            
        except Exception as e:
            logger.error(f"Error marking news alert as sent: {e}")
            return False
    
    def should_send_economic_alert(self, event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
        """Check if economic alert should be sent (not a duplicate)"""
        try:
            # Create content string from event
            title = event.get('title', '')
            event_time = event.get('time', '')
            event_date = event.get('date', '')
            event_id = event.get('id', '')
            
            # Include timing in content to allow multiple alerts for same event at different times
            if event_id:
                content = f"economic:{event_id}:{alert_timing}"
            else:
                content = f"economic:{title}|{event_time}|{event_date}|{alert_timing}"
            
            # Check if should send
            should_send = self.should_send_alert('economic', content, user_id)
            
            if should_send:
                # Mark as sent immediately
                self.mark_alert_sent('economic', content, user_id)
            
            return should_send
            
        except Exception as e:
            logger.error(f"Error checking economic alert deduplication: {e}")
            return True  # Allow alert if check fails
    
    def cleanup_expired_alerts(self) -> int:
        """Clean up expired alert records from Firebase"""
        try:
            # Get all alerts
            alerts_path = "alert_deduplication/alerts"
            all_alerts = self.firebase._make_request('GET', alerts_path)
            
            if not all_alerts or not isinstance(all_alerts, dict):
                return 0
            
            now = datetime.now()
            expired_count = 0
            
            # Check each alert and delete expired ones
            for alert_key, alert_data in list(all_alerts.items()):
                if isinstance(alert_data, dict):
                    expires_at_str = alert_data.get('expires_at')
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if now >= expires_at:
                                # Delete expired alert
                                alert_path = self._get_alert_path(alert_key)
                                self.firebase._make_request('DELETE', alert_path)
                                expired_count += 1
                        except Exception as e:
                            logger.warning(f"Error parsing expires_at for alert {alert_key}: {e}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired alert records")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired alerts: {e}")
            return 0
    
    def _cleanup_expired_content_hashes(self) -> int:
        """Clean up expired global content hash records from Firebase"""
        try:
            # Get all content hashes
            content_hashes_path = "alert_deduplication/content_hashes"
            all_hashes = self.firebase._make_request('GET', content_hashes_path)
            
            if not all_hashes or not isinstance(all_hashes, dict):
                return 0
            
            now = datetime.now()
            expired_count = 0
            
            # Check each hash and delete expired ones
            for content_hash, hash_data in list(all_hashes.items()):
                if isinstance(hash_data, dict):
                    expires_at_str = hash_data.get('expires_at')
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if now >= expires_at:
                                # Delete expired hash
                                hash_path = self._get_content_hash_path(content_hash)
                                self.firebase._make_request('DELETE', hash_path)
                                # Also remove from in-memory cache
                                with self._cache_lock:
                                    self._content_hash_cache.pop(content_hash, None)
                                expired_count += 1
                        except Exception as e:
                            logger.warning(f"Error parsing expires_at for content hash {content_hash}: {e}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired content hash records")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired content hashes: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        try:
            alerts_path = "alert_deduplication/alerts"
            all_alerts = self.firebase._make_request('GET', alerts_path)
            total_records = len(all_alerts) if isinstance(all_alerts, dict) else 0
            
            return {
                'total_records': total_records,
                'operations_count': self.operations_count,
                'duplicates_prevented': self.duplicates_prevented,
                'alert_ttl_hours': self.alert_ttl_hours
            }
        except Exception as e:
            logger.error(f"Error getting deduplication stats: {e}")
            return {
                'total_records': 0,
                'operations_count': self.operations_count,
                'duplicates_prevented': self.duplicates_prevented,
                'alert_ttl_hours': self.alert_ttl_hours
            }
    
    def clear_user_alerts(self, user_id: str) -> int:
        """Clear all alert records for a specific user"""
        try:
            alerts_path = "alert_deduplication/alerts"
            all_alerts = self.firebase._make_request('GET', alerts_path)
            
            if not all_alerts or not isinstance(all_alerts, dict):
                return 0
            
            cleared_count = 0
            
            # Find and delete all alerts for this user
            for alert_key, alert_data in list(all_alerts.items()):
                if isinstance(alert_data, dict) and alert_data.get('user_id') == user_id:
                    alert_path = self._get_alert_path(alert_key)
                    self.firebase._make_request('DELETE', alert_path)
                    cleared_count += 1
            
            if cleared_count > 0:
                logger.info(f"Cleared {cleared_count} alert records for user {user_id}")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing user alerts: {e}")
            return 0

# Global singleton instance
_persistent_deduplication = None

def get_persistent_deduplication() -> PersistentAlertDeduplication:
    """Get the global persistent deduplication instance"""
    global _persistent_deduplication
    if _persistent_deduplication is None:
        _persistent_deduplication = PersistentAlertDeduplication()
    return _persistent_deduplication

# Convenience functions for backward compatibility
def should_send_news_alert(news_item: Dict[str, Any], user_id: str) -> bool:
    """Check if news alert should be sent (not a duplicate)"""
    dedup = get_persistent_deduplication()
    return dedup.should_send_news_alert(news_item, user_id)

def mark_news_alert_sent(news_item: Dict[str, Any], user_id: str) -> bool:
    """Mark a news alert as sent after successful delivery"""
    dedup = get_persistent_deduplication()
    return dedup.mark_news_alert_sent(news_item, user_id)

def should_send_economic_alert(event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
    """Check if economic alert should be sent (not a duplicate)"""
    dedup = get_persistent_deduplication()
    return dedup.should_send_economic_alert(event, user_id, alert_timing)

def get_deduplication_stats() -> Dict[str, Any]:
    """Get deduplication statistics"""
    dedup = get_persistent_deduplication()
    return dedup.get_stats()

def clear_user_deduplication(user_id: str) -> int:
    """Clear deduplication records for a user"""
    dedup = get_persistent_deduplication()
    return dedup.clear_user_alerts(user_id)

