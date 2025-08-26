#!/usr/bin/env python3
"""
Background Alert Worker for Flask App
Integrates alert checking into the main web application
"""

import threading
import time
import asyncio
import requests
from datetime import datetime
import logging
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

class BackgroundAlertWorker:
    """Background worker for checking and sending alerts"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_check = None
        self.check_interval = 300  # 5 minutes
        self.api_base_url = "https://fxsentinel-production.up.railway.app"
        
    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        logger.info("BackgroundAlertWorker initialized with Flask app")
    
    def start(self):
        """Start the background worker"""
        if self.running:
            logger.warning("BackgroundAlertWorker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_worker, daemon=True)
        self.thread.start()
        logger.info("BackgroundAlertWorker started")
    
    def stop(self):
        """Stop the background worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("BackgroundAlertWorker stopped")
    
    def _run_worker(self):
        """Main worker loop"""
        logger.info("BackgroundAlertWorker main loop started")
        
        while self.running:
            try:
                # Run alert checks
                self._check_news_alerts()
                self._check_economic_calendar_alerts()
                
                self.last_check = datetime.now()
                logger.info(f"Alert check completed at {self.last_check}")
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in background worker: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _check_news_alerts(self):
        """Check for new news alerts"""
        try:
            logger.info("Checking for news alerts...")
            
            # Get latest news from API
            response = requests.get(f"{self.api_base_url}/api/news", timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get news: {response.status_code}")
                return
            
            news_data = response.json()
            news_items = news_data.get('news', [])
            
            # Filter high-impact news
            high_impact = [n for n in news_items if n.get('impact') == 'high']
            
            if not high_impact:
                logger.info("No high-impact news found")
                return
            
            logger.info(f"Found {len(high_impact)} high-impact news items")
            
            # Send alerts for high-impact news
            for news_item in high_impact[:3]:  # Process first 3 items
                self._send_news_alert(news_item)
                
        except Exception as e:
            logger.error(f"Error checking news alerts: {e}")
    
    def _check_economic_calendar_alerts(self):
        """Check for economic calendar alerts"""
        try:
            logger.info("Checking for economic calendar alerts...")
            
            # Get economic calendar from API
            response = requests.get(f"{self.api_base_url}/api/economic-calendar", timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get economic calendar: {response.status_code}")
                return
            
            calendar_data = response.json()
            events = calendar_data.get('events', [])
            
            # Filter high-impact upcoming events
            high_impact_upcoming = [
                event for event in events 
                if event.get('impact') == 'high' and 
                self._is_upcoming_event(event)
            ]
            
            if not high_impact_upcoming:
                logger.info("No high-impact upcoming events found")
                return
            
            logger.info(f"Found {len(high_impact_upcoming)} high-impact upcoming events")
            
            # Send alerts for upcoming events
            for event in high_impact_upcoming[:2]:  # Process first 2 items
                self._send_calendar_alert(event)
                
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}")
    
    def _is_upcoming_event(self, event: Dict[str, Any]) -> bool:
        """Check if event is upcoming (within next 24 hours)"""
        try:
            event_time = event.get('time')
            if not event_time:
                return False
            
            # Parse event time and check if it's within next 24 hours
            # This is a simplified check - you might want to improve this
            return True  # For now, assume all events are upcoming
        except:
            return False
    
    def _send_news_alert(self, news_item: Dict[str, Any]):
        """Send news alert to all connected users"""
        try:
            # Call the alert trigger endpoint
            alert_data = {
                'type': 'news',
                'data': news_item
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/alerts/trigger",
                json=alert_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"News alert sent successfully: {news_item.get('title', '')[:50]}")
            else:
                logger.error(f"Failed to send news alert: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending news alert: {e}")
    
    def _send_calendar_alert(self, event: Dict[str, Any]):
        """Send calendar alert to all connected users"""
        try:
            # Call the alert trigger endpoint
            alert_data = {
                'type': 'calendar',
                'data': event
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/alerts/trigger",
                json=alert_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Calendar alert sent successfully: {event.get('title', '')[:50]}")
            else:
                logger.error(f"Failed to send calendar alert: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending calendar alert: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get worker status"""
        return {
            'running': self.running,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'check_interval': self.check_interval
        }

# Global instance
background_alert_worker = BackgroundAlertWorker()
