#!/usr/bin/env python3
"""
Alert Metrics Collection Service
Phase 2 improvement: Centralized metrics collection for alert system
Tracks success/failure rates, deduplication hits, and system health
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class AlertMetrics:
    """
    Thread-safe metrics collection for alert system
    Tracks various metrics for monitoring and debugging
    """
    
    def __init__(self):
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Counters
        self.metrics = {
            'alerts_sent': 0,
            'alerts_failed': 0,
            'alerts_blocked_deduplication': 0,
            'alerts_blocked_global_hash': 0,
            'chat_id_lookup_failures': 0,
            'circuit_breaker_opens': 0,
            'dead_letter_queue_additions': 0,
            'settings_normalization_count': 0,
            'chat_id_migrations': 0,
        }
        
        # Error tracking by type
        self.error_counts = defaultdict(int)
        
        # Timing metrics (last N operations)
        self.recent_operations = []
        self.max_recent_operations = 100
        
        # Time-based metrics (last hour)
        self.hourly_metrics = {
            'start_time': datetime.now(),
            'alerts_sent': 0,
            'alerts_failed': 0,
        }
        
        logger.info("Alert Metrics Service initialized")
    
    def record_alert_sent(self, alert_type: str = 'unknown'):
        """Record successful alert delivery"""
        with self._lock:
            self.metrics['alerts_sent'] += 1
            self.hourly_metrics['alerts_sent'] += 1
            self._add_recent_operation('sent', alert_type)
    
    def record_alert_failed(self, alert_type: str = 'unknown', error: str = 'unknown'):
        """Record failed alert delivery"""
        with self._lock:
            self.metrics['alerts_failed'] += 1
            self.hourly_metrics['alerts_failed'] += 1
            self.error_counts[error] += 1
            self._add_recent_operation('failed', alert_type, error)
    
    def record_deduplication_block(self, block_type: str = 'per_user'):
        """Record alert blocked by deduplication"""
        with self._lock:
            if block_type == 'global_hash':
                self.metrics['alerts_blocked_global_hash'] += 1
            else:
                self.metrics['alerts_blocked_deduplication'] += 1
            self._add_recent_operation('blocked', block_type)
    
    def record_chat_id_lookup_failure(self):
        """Record chat ID lookup failure"""
        with self._lock:
            self.metrics['chat_id_lookup_failures'] += 1
    
    def record_circuit_breaker_open(self):
        """Record circuit breaker opening"""
        with self._lock:
            self.metrics['circuit_breaker_opens'] += 1
    
    def record_dead_letter_queue_addition(self):
        """Record addition to dead letter queue"""
        with self._lock:
            self.metrics['dead_letter_queue_additions'] += 1
    
    def record_settings_normalization(self):
        """Record settings normalization"""
        with self._lock:
            self.metrics['settings_normalization_count'] += 1
    
    def record_chat_id_migration(self):
        """Record chat ID migration"""
        with self._lock:
            self.metrics['chat_id_migrations'] += 1
    
    def _add_recent_operation(self, status: str, alert_type: str, error: Optional[str] = None):
        """Add recent operation to tracking list"""
        operation = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'alert_type': alert_type,
            'error': error
        }
        self.recent_operations.append(operation)
        
        # Keep only recent operations
        if len(self.recent_operations) > self.max_recent_operations:
            self.recent_operations.pop(0)
    
    def _reset_hourly_metrics_if_needed(self):
        """Reset hourly metrics if an hour has passed"""
        now = datetime.now()
        if (now - self.hourly_metrics['start_time']) >= timedelta(hours=1):
            self.hourly_metrics = {
                'start_time': now,
                'alerts_sent': 0,
                'alerts_failed': 0,
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot
        Returns comprehensive metrics dictionary
        """
        with self._lock:
            self._reset_hourly_metrics_if_needed()
            
            total_alerts = self.metrics['alerts_sent'] + self.metrics['alerts_failed']
            success_rate = (
                self.metrics['alerts_sent'] / total_alerts 
                if total_alerts > 0 else 0.0
            )
            
            hourly_total = (
                self.hourly_metrics['alerts_sent'] + 
                self.hourly_metrics['alerts_failed']
            )
            hourly_success_rate = (
                self.hourly_metrics['alerts_sent'] / hourly_total
                if hourly_total > 0 else 0.0
            )
            
            return {
                # Overall metrics
                'total_alerts_sent': self.metrics['alerts_sent'],
                'total_alerts_failed': self.metrics['alerts_failed'],
                'total_alerts': total_alerts,
                'success_rate': round(success_rate * 100, 2),
                
                # Deduplication metrics
                'alerts_blocked_deduplication': self.metrics['alerts_blocked_deduplication'],
                'alerts_blocked_global_hash': self.metrics['alerts_blocked_global_hash'],
                'total_blocked': (
                    self.metrics['alerts_blocked_deduplication'] + 
                    self.metrics['alerts_blocked_global_hash']
                ),
                
                # System health metrics
                'chat_id_lookup_failures': self.metrics['chat_id_lookup_failures'],
                'circuit_breaker_opens': self.metrics['circuit_breaker_opens'],
                'dead_letter_queue_additions': self.metrics['dead_letter_queue_additions'],
                
                # Migration metrics
                'settings_normalization_count': self.metrics['settings_normalization_count'],
                'chat_id_migrations': self.metrics['chat_id_migrations'],
                
                # Hourly metrics
                'hourly_alerts_sent': self.hourly_metrics['alerts_sent'],
                'hourly_alerts_failed': self.hourly_metrics['alerts_failed'],
                'hourly_success_rate': round(hourly_success_rate * 100, 2),
                
                # Error breakdown
                'error_counts': dict(self.error_counts),
                
                # Recent operations (last 10)
                'recent_operations': self.recent_operations[-10:],
                
                # Timestamp
                'last_updated': datetime.now().isoformat(),
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get brief summary of key metrics"""
        metrics = self.get_metrics()
        return {
            'success_rate': metrics['success_rate'],
            'total_alerts': metrics['total_alerts'],
            'hourly_success_rate': metrics['hourly_success_rate'],
            'circuit_breaker_opens': metrics['circuit_breaker_opens'],
            'chat_id_lookup_failures': metrics['chat_id_lookup_failures'],
        }
    
    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        with self._lock:
            self.metrics = {
                'alerts_sent': 0,
                'alerts_failed': 0,
                'alerts_blocked_deduplication': 0,
                'alerts_blocked_global_hash': 0,
                'chat_id_lookup_failures': 0,
                'circuit_breaker_opens': 0,
                'dead_letter_queue_additions': 0,
                'settings_normalization_count': 0,
                'chat_id_migrations': 0,
            }
            self.error_counts.clear()
            self.recent_operations.clear()
            self.hourly_metrics = {
                'start_time': datetime.now(),
                'alerts_sent': 0,
                'alerts_failed': 0,
            }

# Global singleton instance
_alert_metrics_instance = None
_metrics_lock = threading.Lock()

def get_alert_metrics() -> AlertMetrics:
    """Get the global AlertMetrics instance"""
    global _alert_metrics_instance
    if _alert_metrics_instance is None:
        with _metrics_lock:
            if _alert_metrics_instance is None:
                _alert_metrics_instance = AlertMetrics()
    return _alert_metrics_instance

