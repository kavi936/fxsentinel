#!/usr/bin/env python3
"""
Unified Alert Deduplication Service
Centralizes deduplication logic to prevent duplicate alerts across all services
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AlertRecord:
    """Record of a sent alert"""
    alert_id: str
    alert_type: str  # 'news', 'economic', 'test'
    user_id: str
    sent_at: datetime
    content_hash: str
    expires_at: datetime

class UnifiedAlertDeduplication:
    """
    Centralized deduplication service that prevents duplicate alerts
    across all alert services (news, economic calendar, etc.)
    """
    
    def __init__(self):
        # Track sent alerts with expiration
        self.sent_alerts: Dict[str, AlertRecord] = {}
        
        # Track processed content to prevent duplicates
        self.processed_content_hashes: Set[str] = set()
        
        # Configuration
        self.alert_ttl_hours = 24  # How long to remember sent alerts
        self.max_records = 10000   # Maximum number of records to keep
        self.cleanup_interval = 100  # Cleanup every N operations
        
        # Performance tracking
        self.operations_count = 0
        self.duplicates_prevented = 0
        self.cleanups_performed = 0
        
        logger.info("Unified Alert Deduplication Service initialized")
    
    def _generate_alert_id(self, alert_type: str, content: str, user_id: str) -> str:
        """Generate unique alert ID"""
        # Create a hash based on type, content, and user
        content_str = f"{alert_type}:{content}:{user_id}"
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash of alert content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _cleanup_expired_records(self):
        """Remove expired alert records"""
        now = datetime.now()
        expired_keys = []
        
        for alert_id, record in self.sent_alerts.items():
            if now >= record.expires_at:
                expired_keys.append(alert_id)
        
        for key in expired_keys:
            del self.sent_alerts[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired alert records")
            self.cleanups_performed += 1
    
    def should_send_alert(self, alert_type: str, content: str, user_id: str) -> bool:
        """
        Check if alert should be sent (not a duplicate)
        Returns: True if alert should be sent, False if it's a duplicate
        """
        try:
            self.operations_count += 1
            
            # Cleanup expired records periodically
            if self.operations_count % self.cleanup_interval == 0:
                self._cleanup_expired_records()
            
            # Generate alert ID and content hash
            alert_id = self._generate_alert_id(alert_type, content, user_id)
            content_hash = self._generate_content_hash(content)
            
            # Check if we've already sent this exact alert to this user
            if alert_id in self.sent_alerts:
                record = self.sent_alerts[alert_id]
                if datetime.now() < record.expires_at:
                    self.duplicates_prevented += 1
                    logger.debug(f"Duplicate alert prevented for user {user_id}: {alert_type}")
                    return False
            
            # Check if we've processed this content recently (global deduplication)
            if content_hash in self.processed_content_hashes:
                self.duplicates_prevented += 1
                logger.debug(f"Duplicate content prevented: {alert_type}")
                return False
            
            # This is a new alert
            return True
            
        except Exception as e:
            logger.error(f"Error checking alert deduplication: {e}")
            return True  # Allow alert if deduplication fails
    
    def mark_alert_sent(self, alert_type: str, content: str, user_id: str):
        """Mark an alert as sent to prevent duplicates"""
        try:
            alert_id = self._generate_alert_id(alert_type, content, user_id)
            content_hash = self._generate_content_hash(content)
            
            # Create alert record
            now = datetime.now()
            expires_at = now + timedelta(hours=self.alert_ttl_hours)
            
            record = AlertRecord(
                alert_id=alert_id,
                alert_type=alert_type,
                user_id=user_id,
                sent_at=now,
                content_hash=content_hash,
                expires_at=expires_at
            )
            
            # Store the record
            self.sent_alerts[alert_id] = record
            self.processed_content_hashes.add(content_hash)
            
            # Limit the number of records
            if len(self.sent_alerts) > self.max_records:
                # Remove oldest records
                sorted_records = sorted(
                    self.sent_alerts.items(),
                    key=lambda x: x[1].sent_at
                )
                records_to_remove = len(sorted_records) - self.max_records
                for i in range(records_to_remove):
                    del self.sent_alerts[sorted_records[i][0]]
                
                logger.debug(f"Removed {records_to_remove} old alert records")
            
            # Limit content hash set size
            if len(self.processed_content_hashes) > self.max_records:
                # Convert to list, keep only recent ones
                hash_list = list(self.processed_content_hashes)
                self.processed_content_hashes = set(hash_list[-self.max_records:])
            
        except Exception as e:
            logger.error(f"Error marking alert as sent: {e}")
    
    def is_news_duplicate(self, news_item: Dict[str, Any], user_id: str) -> bool:
        """Check if news item is a duplicate for a specific user"""
        try:
            # Create content from news item
            title = news_item.get('title', '')
            source = news_item.get('source', '')
            url = news_item.get('url', '')
            
            # Create content string for deduplication
            content = f"{title}|{source}|{url}"
            
            # Check if this is a duplicate
            should_send = self.should_send_alert('news', content, user_id)
            
            if should_send:
                # Mark as sent
                self.mark_alert_sent('news', content, user_id)
                return False
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error checking news duplicate: {e}")
            return False  # Allow alert if check fails
    
    def is_economic_event_duplicate(self, event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
        """Check if economic event alert is a duplicate"""
        try:
            # Create content from event
            title = event.get('title', '')
            event_time = event.get('time', '')
            event_date = event.get('date', '')
            
            # Include timing in content to allow multiple alerts for same event
            content = f"{title}|{event_time}|{event_date}|{alert_timing}"
            
            # Check if this is a duplicate
            should_send = self.should_send_alert('economic', content, user_id)
            
            if should_send:
                # Mark as sent
                self.mark_alert_sent('economic', content, user_id)
                return False
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error checking economic event duplicate: {e}")
            return False  # Allow alert if check fails
    
    def clear_user_alerts(self, user_id: str):
        """Clear all alert records for a specific user"""
        try:
            keys_to_remove = []
            for alert_id, record in self.sent_alerts.items():
                if record.user_id == user_id:
                    keys_to_remove.append(alert_id)
            
            for key in keys_to_remove:
                del self.sent_alerts[key]
            
            logger.info(f"Cleared {len(keys_to_remove)} alert records for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing user alerts: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        return {
            'total_records': len(self.sent_alerts),
            'content_hashes': len(self.processed_content_hashes),
            'operations_count': self.operations_count,
            'duplicates_prevented': self.duplicates_prevented,
            'cleanups_performed': self.cleanups_performed,
            'max_records': self.max_records,
            'alert_ttl_hours': self.alert_ttl_hours
        }
    
    def clear_all(self):
        """Clear all deduplication records"""
        self.sent_alerts.clear()
        self.processed_content_hashes.clear()
        self.operations_count = 0
        self.duplicates_prevented = 0
        self.cleanups_performed = 0
        logger.info("Cleared all deduplication records")

# Global instance
unified_deduplication = UnifiedAlertDeduplication()

# Convenience functions
def should_send_news_alert(news_item: Dict[str, Any], user_id: str) -> bool:
    """Check if news alert should be sent (not a duplicate)"""
    return not unified_deduplication.is_news_duplicate(news_item, user_id)

def should_send_economic_alert(event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
    """Check if economic alert should be sent (not a duplicate)"""
    return not unified_deduplication.is_economic_event_duplicate(event, user_id, alert_timing)

def get_deduplication_stats() -> Dict[str, Any]:
    """Get deduplication statistics"""
    return unified_deduplication.get_stats()

def clear_user_deduplication(user_id: str):
    """Clear deduplication records for a user"""
    unified_deduplication.clear_user_alerts(user_id)

def clear_all_deduplication():
    """Clear all deduplication records"""
    unified_deduplication.clear_all()
