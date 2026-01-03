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
            'recent_failures': [],  # Last 100 failures
            'chat_id_lookup_failures': 0,  # Track chat ID lookup failures
            'deduplication_stats': {
                'cache_size': 0,
                'duplicates_prevented': 0,
                'operations_count': 0
            },
            'circuit_breaker_stats': {
                'state': 'closed',
                'total_rejections': 0,
                'state_changes': 0
            },
            'dead_letter_queue_size': 0
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
    
    def record_chat_id_lookup_failure(self, user_id: str):
        """Record a chat ID lookup failure"""
        try:
            with self._lock:
                self._metrics['chat_id_lookup_failures'] += 1
                logger.warning(f"Chat ID lookup failed for user {user_id}")
        except Exception as e:
            logger.error(f"Error recording chat ID lookup failure: {e}")
    
    def update_deduplication_stats(self, cache_size: int, duplicates_prevented: int, operations_count: int):
        """Update deduplication statistics"""
        try:
            with self._lock:
                self._metrics['deduplication_stats'] = {
                    'cache_size': cache_size,
                    'duplicates_prevented': duplicates_prevented,
                    'operations_count': operations_count,
                    'last_updated': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error updating deduplication stats: {e}")
    
    def update_circuit_breaker_stats(self, state: str, total_rejections: int, state_changes: int):
        """Update circuit breaker statistics"""
        try:
            with self._lock:
                self._metrics['circuit_breaker_stats'] = {
                    'state': state,
                    'total_rejections': total_rejections,
                    'state_changes': state_changes,
                    'last_updated': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error updating circuit breaker stats: {e}")
    
    def update_dead_letter_queue_size(self, size: int):
        """Update dead letter queue size"""
        try:
            with self._lock:
                self._metrics['dead_letter_queue_size'] = size
        except Exception as e:
            logger.error(f"Error updating dead letter queue size: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current alert metrics"""
        with self._lock:
            # Get deduplication stats
            try:
                from .persistent_alert_deduplication import get_deduplication_stats
                dedup_stats = get_deduplication_stats()
                self._metrics['deduplication_stats'].update({
                    'total_records': dedup_stats.get('total_records', 0),
                    'duplicates_prevented': dedup_stats.get('duplicates_prevented', 0),
                    'operations_count': dedup_stats.get('operations_count', 0)
                })
            except Exception as e:
                logger.debug(f"Error getting deduplication stats: {e}")
            
            # Get circuit breaker stats
            try:
                from .circuit_breaker import get_telegram_circuit_breaker
                cb_stats = get_telegram_circuit_breaker().get_stats()
                self._metrics['circuit_breaker_stats'].update({
                    'state': cb_stats.get('state', 'unknown'),
                    'total_rejections': cb_stats.get('total_rejections', 0),
                    'state_changes': cb_stats.get('state_changes', 0)
                })
            except Exception as e:
                logger.debug(f"Error getting circuit breaker stats: {e}")
            
            # Get dead letter queue size
            try:
                from .dead_letter_queue import get_dead_letter_queue
                dlq_stats = get_dead_letter_queue().get_stats()
                self._metrics['dead_letter_queue_size'] = dlq_stats.get('total_failed_alerts', 0)
            except Exception as e:
                logger.debug(f"Error getting dead letter queue stats: {e}")
            
            return {
                'total_sent': self._metrics['total_sent'],
                'total_failed': self._metrics['total_failed'],
                'success_rate': self._get_success_rate(),
                'by_user': dict(self._metrics['by_user']),
                'by_type': dict(self._metrics['by_type']),
                'recent_failures_count': len(self._metrics['recent_failures']),
                'recent_failures': self._metrics['recent_failures'][-10:],  # Last 10
                'chat_id_lookup_failures': self._metrics['chat_id_lookup_failures'],
                'deduplication_stats': self._metrics['deduplication_stats'],
                'circuit_breaker_stats': self._metrics['circuit_breaker_stats'],
                'dead_letter_queue_size': self._metrics['dead_letter_queue_size']
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

