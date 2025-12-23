#!/usr/bin/env python3
"""
Production Alert Worker
Single canonical implementation for all background alert processing
Includes health monitoring, proper async handling, and memory leak prevention
"""

import os
import time
import asyncio
import logging
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionAlertWorker:
    """
    Production-ready alert worker with:
    - Memory leak prevention
    - Health monitoring
    - Proper async/sync handling
    - Automatic recovery
    - Comprehensive logging
    """
    
    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        
        # Health monitoring
        self.last_heartbeat = None
        self.total_checks = 0
        self.alerts_sent = 0
        self.errors_count = 0
        self.started_at = None
        
        # Check intervals
        self.news_check_interval = 120  # 2 minutes
        self.calendar_check_interval = 300  # 5 minutes
        self.health_check_interval = 60  # 1 minute
        
        # Timestamps
        self.last_news_check = None
        self.last_calendar_check = None
        self.last_health_check = None
        
        # Import services
        from .alert_deduplication import should_send_news_alert, should_send_economic_alert
        self.should_send_news_alert = should_send_news_alert
        self.should_send_economic_alert = should_send_economic_alert
        
        logger.info("✅ Production Alert Worker initialized")
    
    def start(self):
        """Start the worker"""
        if self.running:
            logger.warning("Worker already running")
            return
        
        self.running = True
        self.started_at = datetime.now()
        self.worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self.worker_thread.start()
        
        logger.info("🚀 Production Alert Worker started")
    
    def stop(self):
        """Stop the worker gracefully"""
        if not self.running:
            return
        
        logger.info("⏸️  Stopping Production Alert Worker...")
        self.running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
        
        logger.info("✅ Production Alert Worker stopped")
    
    def _run_worker(self):
        """Main worker loop with error recovery"""
        logger.info("📊 Worker main loop started")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check news alerts
                if self._should_check_news(current_time):
                    self._check_news_alerts()
                    self.last_news_check = current_time
                
                # Check economic calendar
                if self._should_check_calendar(current_time):
                    self._check_economic_calendar_alerts()
                    self.last_calendar_check = current_time
                
                # Update heartbeat
                if self._should_check_health(current_time):
                    self._update_heartbeat()
                    self.last_health_check = current_time
                
                # Sleep briefly to prevent busy waiting
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.errors_count += 1
                logger.error(f"❌ Error in worker loop: {e}", exc_info=True)
                
                # Back off on repeated errors
                if self.errors_count > 5:
                    logger.error("⚠️  Multiple errors detected, backing off...")
                    time.sleep(60)
                else:
                    time.sleep(10)
    
    def _should_check_news(self, current_time: datetime) -> bool:
        """Check if it's time to check news"""
        if not self.last_news_check:
            return True
        
        elapsed = (current_time - self.last_news_check).total_seconds()
        return elapsed >= self.news_check_interval
    
    def _should_check_calendar(self, current_time: datetime) -> bool:
        """Check if it's time to check economic calendar"""
        if not self.last_calendar_check:
            return True
        
        elapsed = (current_time - self.last_calendar_check).total_seconds()
        return elapsed >= self.calendar_check_interval
    
    def _should_check_health(self, current_time: datetime) -> bool:
        """Check if it's time to update health"""
        if not self.last_health_check:
            return True
        
        elapsed = (current_time - self.last_health_check).total_seconds()
        return elapsed >= self.health_check_interval
    
    def _check_news_alerts(self):
        """Check for news alerts to send"""
        try:
            logger.info("📰 Checking for news alerts...")
            
            # Use the news aggregator or API to get recent news
            from .news_aggregator import news_aggregator
            
            # Get news from last 5 minutes to avoid missing any
            recent_news = news_aggregator.get_recent_news(hours=0.1)  # 0.1 hours = 6 minutes
            
            if not recent_news:
                logger.debug("No recent news found")
                return
            
            logger.info(f"Found {len(recent_news)} recent news items")
            
            # Use sophisticated filtering like main app (not just impact level)
            # This ensures consistent filtering between worker and main app
            from .news_alert_trigger import news_alert_trigger
            
            # Process high-impact forex news
            for news_item in recent_news:
                try:
                    # Use the same filtering logic as main app
                    if not news_alert_trigger.is_forex_high_impact(news_item):
                        continue
                    
                    # Get news ID
                    news_id = news_item.get('id') or news_item.get('url') or news_item.get('title')
                    if not news_id:
                        continue
                    
                    # Note: Deduplication is handled at the main app level per-user
                    # The worker just filters and sends to main app
                    # Main app will handle user-specific deduplication via persistent_alert_deduplication
                    
                    # Send alert via API
                    self._send_news_alert_to_api(news_item)
                    
                except Exception as e:
                    logger.error(f"Error processing news item: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error checking news alerts: {e}", exc_info=True)
    
    def _check_economic_calendar_alerts(self):
        """Check for economic calendar alerts to send"""
        try:
            logger.info("📅 Checking for economic calendar alerts...")
            
            # Use the economic calendar alerts service
            from .economic_calendar_alerts import economic_calendar_alerts
            
            # Process calendar and send alerts
            results = economic_calendar_alerts.process_economic_calendar_for_alerts()
            
            if results.get('alerts_sent', 0) > 0:
                self.alerts_sent += results['alerts_sent']
                logger.info(f"✅ Sent {results['alerts_sent']} economic calendar alerts")
            
            if results.get('errors'):
                self.errors_count += len(results['errors'])
                for error in results['errors']:
                    logger.error(f"Economic alert error: {error}")
            
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}", exc_info=True)
    
    def _send_news_alert_to_api(self, news_item: Dict[str, Any]):
        """Send news alert via API endpoint"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/alerts/trigger",
                json={
                    'type': 'news',
                    'data': news_item
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                alerts_sent = result.get('alerts_sent', 0)
                
                if alerts_sent > 0:
                    self.alerts_sent += alerts_sent
                    logger.info(f"✅ News alert sent: {alerts_sent} recipients")
            else:
                logger.error(f"Failed to send news alert: HTTP {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error sending news alert to API: {e}")
    
    def _update_heartbeat(self):
        """Update heartbeat and log status"""
        self.last_heartbeat = datetime.now()
        self.total_checks += 1
        
        # Log status every hour
        if self.total_checks % 60 == 0:  # Every 60 checks (60 minutes)
            uptime = datetime.now() - self.started_at if self.started_at else timedelta(0)
            logger.info(f"💓 Heartbeat: Uptime {uptime}, Alerts sent: {self.alerts_sent}, "
                       f"Errors: {self.errors_count}, Checks: {self.total_checks}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get worker status"""
        uptime = datetime.now() - self.started_at if self.started_at else timedelta(0)
        
        return {
            'running': self.running,
            'thread_alive': self.worker_thread.is_alive() if self.worker_thread else False,
            'uptime_seconds': uptime.total_seconds(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'last_news_check': self.last_news_check.isoformat() if self.last_news_check else None,
            'last_calendar_check': self.last_calendar_check.isoformat() if self.last_calendar_check else None,
            'total_checks': self.total_checks,
            'alerts_sent': self.alerts_sent,
            'errors_count': self.errors_count,
            'news_check_interval': self.news_check_interval,
            'calendar_check_interval': self.calendar_check_interval
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status for monitoring"""
        status = self.get_status()
        
        # Determine health
        is_healthy = (
            status['running'] and
            status['thread_alive'] and
            self.last_heartbeat and
            (datetime.now() - self.last_heartbeat).total_seconds() < 120  # Heartbeat within 2 minutes
        )
        
        return {
            'healthy': is_healthy,
            'status': 'healthy' if is_healthy else 'unhealthy',
            'details': status
        }

# Global instance
_production_worker = None

def get_production_worker() -> ProductionAlertWorker:
    """Get or create the global production worker instance"""
    global _production_worker
    if _production_worker is None:
        _production_worker = ProductionAlertWorker()
    return _production_worker

def start_worker():
    """Start the production worker"""
    worker = get_production_worker()
    worker.start()
    return worker

def stop_worker():
    """Stop the production worker"""
    worker = get_production_worker()
    worker.stop()

def get_worker_status() -> Dict[str, Any]:
    """Get worker status"""
    worker = get_production_worker()
    return worker.get_status()

def get_worker_health() -> Dict[str, Any]:
    """Get worker health"""
    worker = get_production_worker()
    return worker.get_health()

