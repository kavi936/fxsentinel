#!/usr/bin/env python3
"""
FXSentinel Robust Alert Service
A production-ready alert service with auto-restart, health monitoring, and error isolation
"""

import time
import sys
import signal
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import requests
import json
import os
from collections import deque
import psutil
import gc

# Add backend to path
sys.path.append('backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('robust_alert_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RESTARTING = "restarting"

@dataclass
class ServiceHealth:
    """Service health metrics"""
    status: ServiceStatus
    uptime: timedelta
    memory_usage_mb: float
    cpu_usage_percent: float
    error_count: int
    last_error: Optional[str] = None
    last_successful_check: Optional[datetime] = None
    alerts_sent_today: int = 0
    alerts_failed_today: int = 0
    users_processed: int = 0
    last_check_duration_ms: float = 0.0

@dataclass
class AlertMetrics:
    """Alert delivery metrics"""
    total_sent: int = 0
    total_failed: int = 0
    success_rate: float = 0.0
    average_delivery_time_ms: float = 0.0
    last_delivery_time: Optional[datetime] = None
    errors_by_type: Dict[str, int] = field(default_factory=dict)

class RobustAlertService:
    """
    Production-ready alert service with:
    - Auto-restart capability
    - Health monitoring
    - Memory management
    - Error isolation
    - Performance metrics
    - Graceful shutdown
    """
    
    def __init__(self):
        self.running = False
        self.status = ServiceStatus.STOPPED
        self.start_time = None
        self.health = ServiceHealth(
            status=ServiceStatus.STOPPED,
            uptime=timedelta(0),
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0,
            error_count=0
        )
        self.metrics = AlertMetrics()
        
        # Configuration
        self.check_interval = int(os.getenv('ALERT_CHECK_INTERVAL', 300))  # 5 minutes
        self.max_retries = int(os.getenv('ALERT_MAX_RETRIES', 3))
        self.retry_delay = int(os.getenv('ALERT_RETRY_DELAY', 60))  # 1 minute
        self.max_memory_mb = int(os.getenv('ALERT_MAX_MEMORY_MB', 500))
        self.max_errors_before_restart = int(os.getenv('ALERT_MAX_ERRORS', 10))
        self.health_check_interval = int(os.getenv('ALERT_HEALTH_CHECK_INTERVAL', 60))  # 1 minute
        
        # Memory management
        self.processed_news_ids: Set[str] = set()
        self.max_processed_ids = 10000  # Increased from 1000
        self.cleanup_interval = 3600  # Cleanup every hour
        
        # Error tracking
        self.error_history = deque(maxlen=100)  # Keep last 100 errors
        self.consecutive_errors = 0
        self.last_successful_run = None
        
        # Performance tracking
        self.check_durations = deque(maxlen=100)  # Keep last 100 check durations
        
        # Threading
        self.main_thread = None
        self.health_thread = None
        self.shutdown_event = threading.Event()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Robust Alert Service initialized")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
        self.stop()
    
    def start(self):
        """Start the robust alert service"""
        if self.running:
            logger.warning("Service is already running")
            return
        
        logger.info("🚀 Starting FXSentinel Robust Alert Service")
        logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        logger.info(f"🔄 Max retries: {self.max_retries}")
        logger.info(f"💾 Max memory: {self.max_memory_mb}MB")
        logger.info(f"⚠️ Max errors before restart: {self.max_errors_before_restart}")
        
        self.running = True
        self.status = ServiceStatus.STARTING
        self.start_time = datetime.now()
        self.shutdown_event.clear()
        
        # Start main service thread
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        # Start health monitoring thread
        self.health_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self.health_thread.start()
        
        self.status = ServiceStatus.RUNNING
        logger.info("✅ Robust Alert Service started successfully")
    
    def stop(self):
        """Stop the service gracefully"""
        logger.info("🛑 Stopping Robust Alert Service...")
        self.running = False
        self.status = ServiceStatus.STOPPING
        self.shutdown_event.set()
        
        # Wait for threads to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=30)
        
        if self.health_thread and self.health_thread.is_alive():
            self.health_thread.join(timeout=10)
        
        self.status = ServiceStatus.STOPPED
        logger.info("✅ Robust Alert Service stopped")
    
    def restart(self):
        """Restart the service"""
        logger.info("🔄 Restarting Robust Alert Service...")
        self.status = ServiceStatus.RESTARTING
        self.stop()
        time.sleep(5)  # Wait before restart
        self.start()
    
    def _main_loop(self):
        """Main service loop with error handling and auto-restart"""
        while self.running and not self.shutdown_event.is_set():
            try:
                start_time = datetime.now()
                
                # Check if we should restart due to too many errors
                if self.consecutive_errors >= self.max_errors_before_restart:
                    logger.error(f"Too many consecutive errors ({self.consecutive_errors}), restarting service")
                    self.restart()
                    break
                
                # Perform health check
                if not self._health_check():
                    logger.error("Health check failed, restarting service")
                    self.restart()
                    break
                
                # Check memory usage
                if not self._memory_check():
                    logger.warning("Memory usage high, performing cleanup")
                    self._cleanup_memory()
                
                # Process alerts
                success = self._process_alerts()
                
                # Update metrics
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                self.check_durations.append(duration_ms)
                self.health.last_check_duration_ms = duration_ms
                
                if success:
                    self.consecutive_errors = 0
                    self.last_successful_run = datetime.now()
                    self.health.last_successful_check = datetime.now()
                    logger.info(f"✅ Alert check completed successfully in {duration_ms:.1f}ms")
                else:
                    self.consecutive_errors += 1
                    logger.error(f"❌ Alert check failed (consecutive errors: {self.consecutive_errors})")
                
                # Wait for next check
                self.shutdown_event.wait(self.check_interval)
                
            except Exception as e:
                self.consecutive_errors += 1
                error_msg = f"Critical error in main loop: {e}"
                logger.error(error_msg)
                self.error_history.append({
                    'timestamp': datetime.now(),
                    'error': str(e),
                    'consecutive_errors': self.consecutive_errors
                })
                
                # Wait before retry
                time.sleep(self.retry_delay)
    
    def _health_monitor_loop(self):
        """Health monitoring loop"""
        while self.running and not self.shutdown_event.is_set():
            try:
                self._update_health_metrics()
                self.shutdown_event.wait(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                time.sleep(10)
    
    def _health_check(self) -> bool:
        """Perform health check"""
        try:
            # Check if Flask app is running
            response = requests.get("http://localhost:5001/api/health", timeout=5)
            if response.status_code != 200:
                logger.error(f"Flask app health check failed: {response.status_code}")
                return False
            
            # Check memory usage
            if self.health.memory_usage_mb > self.max_memory_mb:
                logger.error(f"Memory usage too high: {self.health.memory_usage_mb}MB")
                return False
            
            # Check if main thread is alive
            if self.main_thread and not self.main_thread.is_alive():
                logger.error("Main thread is not alive")
                return False
            
            return True
            
        except requests.exceptions.ConnectionError:
            # Flask app might not be ready yet, don't restart immediately
            logger.warning("Flask app not ready yet, will retry")
            return True  # Don't restart, just wait
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def _memory_check(self) -> bool:
        """Check if memory usage is acceptable"""
        return self.health.memory_usage_mb < (self.max_memory_mb * 0.8)
    
    def _cleanup_memory(self):
        """Clean up memory usage"""
        try:
            # Trim processed news IDs
            if len(self.processed_news_ids) > self.max_processed_ids:
                # Keep only recent IDs
                ids_list = list(self.processed_news_ids)
                self.processed_news_ids = set(ids_list[-self.max_processed_ids//2:])
                logger.info(f"Cleaned up processed news IDs: {len(self.processed_news_ids)} remaining")
            
            # Clear old error history
            if len(self.error_history) > 50:
                # Keep only recent errors
                recent_errors = list(self.error_history)[-50:]
                self.error_history.clear()
                self.error_history.extend(recent_errors)
            
            # Clear old check durations
            if len(self.check_durations) > 50:
                recent_durations = list(self.check_durations)[-50:]
                self.check_durations.clear()
                self.check_durations.extend(recent_durations)
            
            # Force garbage collection
            gc.collect()
            
            logger.info("Memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
    
    def _update_health_metrics(self):
        """Update health metrics"""
        try:
            process = psutil.Process()
            
            # Update uptime
            if self.start_time:
                self.health.uptime = datetime.now() - self.start_time
            
            # Update memory usage
            memory_info = process.memory_info()
            self.health.memory_usage_mb = memory_info.rss / 1024 / 1024
            
            # Update CPU usage
            self.health.cpu_usage_percent = process.cpu_percent()
            
            # Update error count
            self.health.error_count = self.consecutive_errors
            
            # Update last error
            if self.error_history:
                self.health.last_error = self.error_history[-1]['error']
            
            # Update success rate
            total_attempts = self.metrics.total_sent + self.metrics.total_failed
            if total_attempts > 0:
                self.metrics.success_rate = (self.metrics.total_sent / total_attempts) * 100
            
            # Update average delivery time
            if self.check_durations:
                self.metrics.average_delivery_time_ms = sum(self.check_durations) / len(self.check_durations)
            
        except Exception as e:
            logger.error(f"Error updating health metrics: {e}")
    
    def _process_alerts(self) -> bool:
        """Process alerts with error isolation"""
        try:
            # Get all connected users
            users = self._get_all_connected_users()
            if not users:
                logger.info("No connected users found")
                return True
            
            # Process news alerts
            news_success = self._process_news_alerts(users)
            
            # Process economic calendar alerts
            calendar_success = self._process_economic_calendar_alerts(users)
            
            # Update user count
            self.health.users_processed = len(users)
            
            return news_success and calendar_success
            
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
            return False
    
    def _get_all_connected_users(self) -> List[Dict[str, Any]]:
        """Get all connected users with error isolation"""
        try:
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            
            users = firebase_storage.get_all_users_with_alerts()
            
            if not users:
                return []
            
            # Process users with error isolation
            processed_users = []
            for user in users:
                try:
                    user_id = user.get('user_id')
                    settings = user.get('settings', {})
                    chat_id = user.get('telegram_chat_id')
                    
                    if not chat_id:
                        chat_id = firebase_storage.get_telegram_chat_id(user_id)
                    
                    if chat_id and settings:
                        processed_users.append({
                            'user_id': user_id,
                            'chat_id': chat_id,
                            'settings': settings
                        })
                except Exception as e:
                    logger.error(f"Error processing user {user.get('user_id', 'unknown')}: {e}")
                    continue
            
            return processed_users
            
        except Exception as e:
            logger.error(f"Error getting connected users: {e}")
            return []
    
    def _process_news_alerts(self, users: List[Dict[str, Any]]) -> bool:
        """Process news alerts with error isolation per user"""
        try:
            logger.info("📰 Processing news alerts...")
            
            # Get current news
            response = requests.get("http://localhost:5001/api/news", timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to get news: {response.status_code}")
                return False
            
            news_data = response.json()
            news_items = news_data.get('news', [])
            high_impact = [n for n in news_items if n.get('impact') == 'high']
            
            if not high_impact:
                logger.info("No high-impact news found")
                return True
            
            total_alerts_sent = 0
            
            # Process each user with error isolation
            for user in users:
                try:
                    user_id = user['user_id']
                    user_alerts_sent = 0
                    
                    for news_item in high_impact[:5]:  # Limit to 5 items per user
                        news_id = str(news_item.get('id', ''))
                        user_news_key = f"{user_id}_{news_id}"
                        
                        # Check if already processed
                        if user_news_key in self.processed_news_ids:
                            continue
                        
                        # Send alert with retry logic
                        success = self._send_alert_with_retry(user, news_item, 'news')
                        
                        if success:
                            user_alerts_sent += 1
                            total_alerts_sent += 1
                            self.processed_news_ids.add(user_news_key)
                            self.metrics.total_sent += 1
                            self.metrics.last_delivery_time = datetime.now()
                        
                        # Small delay between alerts
                        time.sleep(0.1)
                    
                    if user_alerts_sent > 0:
                        logger.info(f"📨 Sent {user_alerts_sent} news alerts to user {user_id}")
                
                except Exception as e:
                    logger.error(f"Error processing alerts for user {user.get('user_id', 'unknown')}: {e}")
                    self.metrics.total_failed += 1
                    continue
            
            if total_alerts_sent > 0:
                logger.info(f"📨 Total: Sent {total_alerts_sent} news alerts")
                self.health.alerts_sent_today += total_alerts_sent
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing news alerts: {e}")
            return False
    
    def _process_economic_calendar_alerts(self, users: List[Dict[str, Any]]) -> bool:
        """Process economic calendar alerts with error isolation"""
        try:
            logger.info("📅 Processing economic calendar alerts...")
            
            # Get economic calendar
            response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to get calendar: {response.status_code}")
                return False
            
            calendar_data = response.json()
            events = calendar_data.get('events', [])
            
            if not events:
                logger.info("No economic events found")
                return True
            
            # Process upcoming high-impact events
            now = datetime.now()
            total_alerts_sent = 0
            
            for user in users:
                try:
                    user_id = user['user_id']
                    user_alerts_sent = 0
                    
                    # Check if user wants economic calendar alerts
                    alert_types = user['settings'].get('alert_types', [])
                    if 'economicCalendar' not in alert_types:
                        continue
                    
                    for event in events:
                        if event.get('impact') == 'high':
                            # Send alert with retry logic
                            success = self._send_alert_with_retry(user, event, 'economic')
                            
                            if success:
                                user_alerts_sent += 1
                                total_alerts_sent += 1
                                self.metrics.total_sent += 1
                                self.metrics.last_delivery_time = datetime.now()
                            
                            # Small delay between alerts
                            time.sleep(0.1)
                    
                    if user_alerts_sent > 0:
                        logger.info(f"📨 Sent {user_alerts_sent} economic alerts to user {user_id}")
                
                except Exception as e:
                    logger.error(f"Error processing economic alerts for user {user.get('user_id', 'unknown')}: {e}")
                    self.metrics.total_failed += 1
                    continue
            
            if total_alerts_sent > 0:
                logger.info(f"📨 Total: Sent {total_alerts_sent} economic alerts")
                self.health.alerts_sent_today += total_alerts_sent
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing economic calendar alerts: {e}")
            return False
    
    def _send_alert_with_retry(self, user: Dict[str, Any], content: Dict[str, Any], alert_type: str) -> bool:
        """Send alert with retry logic and error isolation"""
        for attempt in range(self.max_retries):
            try:
                # Use the existing alert service
                from services.alert_service import get_alert_service
                alert_service = get_alert_service()
                
                # Create alert data
                alert_data = {
                    'title': content.get('title', 'Alert'),
                    'content': content.get('summary', 'No content available'),
                    'type': alert_type,
                    'impact_level': content.get('impact', 'medium'),
                    'source': content.get('source', 'Unknown')
                }
                
                # Send alert
                success = asyncio.run(alert_service.process_alert(
                    alert_data, 
                    user['settings'], 
                    user['user_id']
                ))
                
                if success:
                    return True
                else:
                    logger.warning(f"Alert service returned False for user {user['user_id']}")
                    return False
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for user {user['user_id']}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    self.metrics.total_failed += 1
                    self.health.alerts_failed_today += 1
                    return False
        
        return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            'status': self.status.value,
            'uptime_seconds': self.health.uptime.total_seconds(),
            'memory_usage_mb': round(self.health.memory_usage_mb, 2),
            'cpu_usage_percent': round(self.health.cpu_usage_percent, 2),
            'error_count': self.health.error_count,
            'consecutive_errors': self.consecutive_errors,
            'last_error': self.health.last_error,
            'last_successful_check': self.health.last_successful_check.isoformat() if self.health.last_successful_check else None,
            'alerts_sent_today': self.health.alerts_sent_today,
            'alerts_failed_today': self.health.alerts_failed_today,
            'users_processed': self.health.users_processed,
            'last_check_duration_ms': round(self.health.last_check_duration_ms, 2),
            'metrics': {
                'total_sent': self.metrics.total_sent,
                'total_failed': self.metrics.total_failed,
                'success_rate': round(self.metrics.success_rate, 2),
                'average_delivery_time_ms': round(self.metrics.average_delivery_time_ms, 2),
                'last_delivery_time': self.metrics.last_delivery_time.isoformat() if self.metrics.last_delivery_time else None
            },
            'processed_news_ids_count': len(self.processed_news_ids),
            'error_history_count': len(self.error_history)
        }

# Global instance
robust_alert_service = RobustAlertService()

def start_robust_alert_service():
    """Start the robust alert service"""
    robust_alert_service.start()

def stop_robust_alert_service():
    """Stop the robust alert service"""
    robust_alert_service.stop()

def get_service_health():
    """Get service health status"""
    return robust_alert_service.get_health_status()

if __name__ == "__main__":
    try:
        start_robust_alert_service()
        
        # Keep the main thread alive
        while robust_alert_service.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        stop_robust_alert_service()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        stop_robust_alert_service()
        sys.exit(1)
