#!/usr/bin/env python3
"""
Alert Monitoring Service
Tracks alert success/failure rates and provides metrics
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
from .firebase_realtime_storage import FirebaseRealtimeStorage

logger = logging.getLogger(__name__)

class AlertMonitoring:
    """
    Monitors alert delivery success/failure rates
    Stores metrics in Firebase for persistence
    """
    
    def __init__(self):
        self.firebase = FirebaseRealtimeStorage()
        self._lock = threading.Lock()
        
        # In-memory metrics (for fast access)
        self._metrics = {
            'total_sent': 0,
            'total_failed': 0,
            'by_user': defaultdict(lambda: {'sent': 0, 'failed': 0}),
            'by_type': defaultdict(lambda: {'sent': 0, 'failed': 0}),
            'recent_failures': []  # Last 100 failures
        }
        
        logger.info("Alert Monitoring Service initialized")
    
    def record_success(self, user_id: str, alert_type: str, alert_title: str = None):
        """Record a successful alert delivery"""
        try:
            with self._lock:
                self._metrics['total_sent'] += 1
                self._metrics['by_user'][user_id]['sent'] += 1
                self._metrics['by_type'][alert_type]['sent'] += 1
                
                # Persist to Firebase (async, non-blocking)
                self._persist_metrics_async()
                
        except Exception as e:
            logger.error(f"Error recording alert success: {e}")
    
    def record_failure(self, user_id: str, alert_type: str, error: str, alert_title: str = None):
        """Record a failed alert delivery"""
        try:
            with self._lock:
                self._metrics['total_failed'] += 1
                self._metrics['by_user'][user_id]['failed'] += 1
                self._metrics['by_type'][alert_type]['failed'] += 1
                
                # Track recent failures (keep last 100)
                failure_record = {
                    'user_id': user_id,
                    'alert_type': alert_type,
                    'error': error,
                    'alert_title': alert_title,
                    'timestamp': datetime.now().isoformat()
                }
                self._metrics['recent_failures'].append(failure_record)
                if len(self._metrics['recent_failures']) > 100:
                    self._metrics['recent_failures'].pop(0)
                
                # Persist to Firebase (async, non-blocking)
                self._persist_metrics_async()
                
                logger.warning(f"Alert failure recorded: user={user_id}, type={alert_type}, error={error}")
                
        except Exception as e:
            logger.error(f"Error recording alert failure: {e}")
    
    def _persist_metrics_async(self):
        """Persist metrics to Firebase (non-blocking)"""
        try:
            # Store summary metrics
            metrics_path = "alert_monitoring/metrics"
            summary = {
                'total_sent': self._metrics['total_sent'],
                'total_failed': self._metrics['total_failed'],
                'success_rate': self._get_success_rate(),
                'last_updated': datetime.now().isoformat()
            }
            self.firebase._make_request('PUT', metrics_path, summary)
            
        except Exception as e:
            logger.debug(f"Error persisting metrics (non-critical): {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current alert metrics"""
        with self._lock:
            return {
                'total_sent': self._metrics['total_sent'],
                'total_failed': self._metrics['total_failed'],
                'success_rate': self._get_success_rate(),
                'by_user': dict(self._metrics['by_user']),
                'by_type': dict(self._metrics['by_type']),
                'recent_failures_count': len(self._metrics['recent_failures']),
                'recent_failures': self._metrics['recent_failures'][-10:]  # Last 10
            }
    
    def _get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        total = self._metrics['total_sent'] + self._metrics['total_failed']
        if total == 0:
            return 0.0
        return (self._metrics['total_sent'] / total) * 100
    
    def get_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get metrics for a specific user"""
        with self._lock:
            user_metrics = self._metrics['by_user'].get(user_id, {'sent': 0, 'failed': 0})
            total = user_metrics['sent'] + user_metrics['failed']
            success_rate = (user_metrics['sent'] / total * 100) if total > 0 else 0.0
            
            return {
                'user_id': user_id,
                'sent': user_metrics['sent'],
                'failed': user_metrics['failed'],
                'total': total,
                'success_rate': success_rate
            }
    
    def get_recent_failures(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alert failures"""
        with self._lock:
            return self._metrics['recent_failures'][-limit:]

# Singleton instance
_alert_monitoring = None
_monitoring_lock = threading.Lock()

def get_alert_monitoring() -> AlertMonitoring:
    """Get singleton alert monitoring instance"""
    global _alert_monitoring
    if _alert_monitoring is None:
        with _monitoring_lock:
            if _alert_monitoring is None:
                _alert_monitoring = AlertMonitoring()
    return _alert_monitoring

