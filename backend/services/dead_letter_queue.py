#!/usr/bin/env python3
"""
Dead Letter Queue for Failed Alerts
Stores alerts that failed to send after all retry attempts
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json
from .firebase_realtime_storage import FirebaseRealtimeStorage

logger = logging.getLogger(__name__)

@dataclass
class FailedAlert:
    """Represents a failed alert in the dead letter queue"""
    alert_id: str
    user_id: str
    chat_id: str
    alert_type: str
    title: str
    content: str
    error_message: str
    failed_at: str
    attempts: int
    alert_data: Dict[str, Any]

class DeadLetterQueue:
    """
    Dead letter queue for storing failed alerts
    Alerts that fail after all retry attempts are stored here for manual review/retry
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize dead letter queue
        
        Args:
            max_size: Maximum number of failed alerts to store
        """
        self.max_size = max_size
        self.firebase = FirebaseRealtimeStorage()
        self.queue_path = "alert_failures/dead_letter_queue"
    
    def add_failed_alert(
        self,
        user_id: str,
        chat_id: str,
        alert_type: str,
        title: str,
        content: str,
        error_message: str,
        attempts: int,
        alert_data: Dict[str, Any]
    ) -> bool:
        """
        Add a failed alert to the dead letter queue
        
        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Generate alert ID
            import hashlib
            alert_id = hashlib.md5(
                f"{user_id}:{chat_id}:{title}:{datetime.now().isoformat()}".encode()
            ).hexdigest()
            
            failed_alert = FailedAlert(
                alert_id=alert_id,
                user_id=user_id,
                chat_id=chat_id,
                alert_type=alert_type,
                title=title,
                content=content,
                error_message=error_message,
                failed_at=datetime.now().isoformat(),
                attempts=attempts,
                alert_data=alert_data
            )
            
            # Store in Firebase
            alert_path = f"{self.queue_path}/{alert_id}"
            result = self.firebase._make_request('PUT', alert_path, asdict(failed_alert))
            
            if result is not None:
                logger.warning(f"Added failed alert to dead letter queue: {alert_id} for user {user_id}")
                
                # Check queue size and remove oldest if needed
                self._enforce_max_size()
                
                return True
            else:
                logger.error(f"Failed to add alert to dead letter queue: {alert_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding failed alert to dead letter queue: {e}")
            return False
    
    def get_failed_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get failed alerts from dead letter queue
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of failed alert dictionaries
        """
        try:
            result = self.firebase._make_request('GET', self.queue_path)
            
            if not result or not isinstance(result, dict):
                return []
            
            # Convert to list and sort by failed_at (newest first)
            alerts = []
            for alert_id, alert_data in result.items():
                if isinstance(alert_data, dict):
                    alert_data['id'] = alert_id
                    alerts.append(alert_data)
            
            # Sort by failed_at (newest first)
            alerts.sort(key=lambda x: x.get('failed_at', ''), reverse=True)
            
            # Limit results
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Error getting failed alerts from dead letter queue: {e}")
            return []
    
    def remove_failed_alert(self, alert_id: str) -> bool:
        """
        Remove a failed alert from the dead letter queue
        
        Args:
            alert_id: ID of the alert to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            alert_path = f"{self.queue_path}/{alert_id}"
            result = self.firebase._make_request('DELETE', alert_path)
            
            if result is not None:
                logger.info(f"Removed failed alert from dead letter queue: {alert_id}")
                return True
            else:
                logger.warning(f"Failed to remove alert from dead letter queue: {alert_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing failed alert from dead letter queue: {e}")
            return False
    
    def retry_failed_alert(self, alert_id: str) -> bool:
        """
        Retry sending a failed alert
        
        Args:
            alert_id: ID of the alert to retry
            
        Returns:
            True if retry initiated successfully, False otherwise
        """
        try:
            # Get the failed alert
            alert_path = f"{self.queue_path}/{alert_id}"
            alert_data = self.firebase._make_request('GET', alert_path)
            
            if not alert_data or not isinstance(alert_data, dict):
                logger.error(f"Failed alert not found: {alert_id}")
                return False
            
            # Import alert service
            from .alert_service import get_alert_service
            alert_service = get_alert_service()
            
            # Reconstruct alert data
            user_id = alert_data.get('user_id')
            chat_id = alert_data.get('chat_id')
            alert_type = alert_data.get('alert_type', 'news')
            title = alert_data.get('title', 'Alert')
            content = alert_data.get('content', '')
            
            # Get user settings
            user_settings = self.firebase.get_user_alert_settings(user_id)
            if not user_settings:
                logger.error(f"User settings not found for user {user_id}")
                return False
            
            # Create alert data
            alert_data_dict = alert_data.get('alert_data', {})
            alert_data_dict.update({
                'title': title,
                'content': content,
                'type': alert_type
            })
            
            # Try to send again
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't use existing loop, create new one
                    success = asyncio.run(
                        alert_service.process_alert(
                            alert_data_dict,
                            user_settings,
                            user_id,
                            {'telegram_chat_id': chat_id}
                        )
                    )
                else:
                    success = loop.run_until_complete(
                        alert_service.process_alert(
                            alert_data_dict,
                            user_settings,
                            user_id,
                            {'telegram_chat_id': chat_id}
                        )
                    )
            except RuntimeError:
                success = asyncio.run(
                    alert_service.process_alert(
                        alert_data_dict,
                        user_settings,
                        user_id,
                        {'telegram_chat_id': chat_id}
                    )
                )
            
            if success:
                # Remove from dead letter queue
                self.remove_failed_alert(alert_id)
                logger.info(f"Successfully retried failed alert: {alert_id}")
                return True
            else:
                logger.warning(f"Retry failed for alert: {alert_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error retrying failed alert: {e}")
            return False
    
    def _enforce_max_size(self):
        """Remove oldest alerts if queue exceeds max size"""
        try:
            alerts = self.get_failed_alerts(limit=self.max_size + 100)
            
            if len(alerts) > self.max_size:
                # Remove oldest alerts
                alerts_to_remove = alerts[self.max_size:]
                for alert in alerts_to_remove:
                    alert_id = alert.get('id')
                    if alert_id:
                        self.remove_failed_alert(alert_id)
                
                logger.info(f"Removed {len(alerts_to_remove)} oldest alerts from dead letter queue")
                
        except Exception as e:
            logger.error(f"Error enforcing max size for dead letter queue: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dead letter queue statistics"""
        try:
            alerts = self.get_failed_alerts(limit=10000)  # Get all for stats
            
            # Group by alert type
            by_type = {}
            for alert in alerts:
                alert_type = alert.get('alert_type', 'unknown')
                by_type[alert_type] = by_type.get(alert_type, 0) + 1
            
            return {
                'total_failed_alerts': len(alerts),
                'by_type': by_type,
                'max_size': self.max_size
            }
            
        except Exception as e:
            logger.error(f"Error getting dead letter queue stats: {e}")
            return {
                'total_failed_alerts': 0,
                'by_type': {},
                'max_size': self.max_size
            }

# Global instance
_dead_letter_queue = None

def get_dead_letter_queue() -> DeadLetterQueue:
    """Get global dead letter queue instance"""
    global _dead_letter_queue
    if _dead_letter_queue is None:
        _dead_letter_queue = DeadLetterQueue()
    return _dead_letter_queue

