#!/usr/bin/env python3
"""
Alert Deduplication Service
Prevents duplicate alerts with TTL-based cleanup to avoid memory leaks
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class AlertDeduplication:
    """
    Thread-safe alert deduplication with automatic TTL cleanup
    Prevents memory leaks by removing old entries
    """
    
    def __init__(self, ttl_hours: int = 24):
        self.ttl_hours = ttl_hours
        self.ttl_seconds = ttl_hours * 3600
        
        # Store: {alert_key: timestamp}
        self._processed_alerts: Dict[str, float] = {}
        
        # Store: {(event_id, user_id, timing): timestamp}
        self._economic_alerts: Dict[Tuple[str, str, str], float] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Metrics
        self.total_checks = 0
        self.duplicates_prevented = 0
        self.cleanups_run = 0
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info(f"Alert deduplication initialized with {ttl_hours}h TTL")
    
    def _start_cleanup_thread(self):
        """Start background thread for TTL cleanup"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    self.cleanup_expired()
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Cleanup thread started")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries (older than TTL)"""
        with self._lock:
            now = time.time()
            cutoff_time = now - self.ttl_seconds
            
            # Clean processed alerts
            expired_alerts = [
                key for key, timestamp in self._processed_alerts.items()
                if timestamp < cutoff_time
            ]
            for key in expired_alerts:
                del self._processed_alerts[key]
            
            # Clean economic alerts
            expired_economic = [
                key for key, timestamp in self._economic_alerts.items()
                if timestamp < cutoff_time
            ]
            for key in expired_economic:
                del self._economic_alerts[key]
            
            total_expired = len(expired_alerts) + len(expired_economic)
            
            if total_expired > 0:
                self.cleanups_run += 1
                logger.info(f"Cleaned up {total_expired} expired alert entries "
                          f"(alerts: {len(self._processed_alerts)}, "
                          f"economic: {len(self._economic_alerts)} remaining)")
            
            return total_expired
    
    def should_send_news_alert(self, news_id: str, user_id: str = None) -> bool:
        """
        Check if news alert should be sent
        Returns True if alert should be sent, False if duplicate
        """
        with self._lock:
            self.total_checks += 1
            
            # Create unique key
            if user_id:
                alert_key = f"news:{news_id}:{user_id}"
            else:
                alert_key = f"news:{news_id}:all"
            
            # Check if already processed
            if alert_key in self._processed_alerts:
                self.duplicates_prevented += 1
                logger.debug(f"Duplicate news alert prevented: {alert_key}")
                return False
            
            # Mark as processed
            self._processed_alerts[alert_key] = time.time()
            return True
    
    def should_send_economic_alert(self, event_id: str, user_id: str, timing: str) -> bool:
        """
        Check if economic calendar alert should be sent
        
        Args:
            event_id: Unique event identifier
            user_id: User to send alert to
            timing: Alert timing (2h_before, 1h_before, 10min_before)
        
        Returns:
            True if alert should be sent, False if duplicate
        """
        with self._lock:
            self.total_checks += 1
            
            # Create unique key
            alert_key = (event_id, user_id, timing)
            
            # Check if already processed
            if alert_key in self._economic_alerts:
                self.duplicates_prevented += 1
                logger.debug(f"Duplicate economic alert prevented: {event_id} for user {user_id} ({timing})")
                return False
            
            # Mark as processed
            self._economic_alerts[alert_key] = time.time()
            return True
    
    def mark_news_alert_sent(self, news_id: str, user_id: str = None):
        """Manually mark a news alert as sent"""
        with self._lock:
            if user_id:
                alert_key = f"news:{news_id}:{user_id}"
            else:
                alert_key = f"news:{news_id}:all"
            
            self._processed_alerts[alert_key] = time.time()
    
    def mark_economic_alert_sent(self, event_id: str, user_id: str, timing: str):
        """Manually mark an economic alert as sent"""
        with self._lock:
            alert_key = (event_id, user_id, timing)
            self._economic_alerts[alert_key] = time.time()
    
    def get_stats(self) -> Dict:
        """Get deduplication statistics"""
        with self._lock:
            return {
                'total_checks': self.total_checks,
                'duplicates_prevented': self.duplicates_prevented,
                'cleanups_run': self.cleanups_run,
                'processed_alerts_count': len(self._processed_alerts),
                'economic_alerts_count': len(self._economic_alerts),
                'ttl_hours': self.ttl_hours
            }
    
    def clear_all(self):
        """Clear all deduplication data (use with caution)"""
        with self._lock:
            self._processed_alerts.clear()
            self._economic_alerts.clear()
            logger.warning("All deduplication data cleared")

# Global instance
_deduplication_service = AlertDeduplication(ttl_hours=24)

# Convenience functions
def should_send_news_alert(news_id: str, user_id: str = None) -> bool:
    """Check if news alert should be sent"""
    return _deduplication_service.should_send_news_alert(news_id, user_id)

def should_send_economic_alert(event_id: str, user_id: str, timing: str) -> bool:
    """Check if economic alert should be sent"""
    return _deduplication_service.should_send_economic_alert(event_id, user_id, timing)

def cleanup_expired_alerts() -> int:
    """Manually trigger cleanup of expired alerts"""
    return _deduplication_service.cleanup_expired()

def get_deduplication_stats() -> Dict:
    """Get deduplication statistics"""
    return _deduplication_service.get_stats()

def clear_deduplication_data():
    """Clear all deduplication data"""
    _deduplication_service.clear_all()

