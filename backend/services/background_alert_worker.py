#!/usr/bin/env python3
"""
Background Alert Worker
Processes alerts and post-news analysis in the background
"""

import time
import logging
import threading
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundAlertWorker:
    """Background worker for checking and sending alerts"""
    
    def __init__(self, check_interval: int = 60):
        """Initialize the background worker"""
        self.check_interval = check_interval  # seconds
        self.running = False
        self.thread = None
        self.last_check = None
        self.api_base_url = 'http://localhost:5001'
        
        # Post-news analysis processing
        self.post_news_interval = 300  # 5 minutes
        self.last_post_news_check = None
        
        logger.info("BackgroundAlertWorker initialized")
    
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
        if not self.running:
            return
        
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
                
                # Process post-news analysis
                self._process_post_news_analysis()
                
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
            
            # Get economic calendar
            response = requests.get(f"{self.api_base_url}/api/economic-calendar", timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get calendar: {response.status_code}")
                return
            
            calendar_data = response.json()
            events = calendar_data.get('events', [])
            
            if not events:
                logger.info("No economic events found")
                return
            
            # Process upcoming high-impact events
            now = datetime.now()
            for event in events:
                if event.get('impact') == 'high':
                    self._send_economic_alert(event)
                    
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}")
    
    def _process_post_news_analysis(self):
        """Process post-news analysis queue"""
        try:
            # Check if it's time to process post-news analysis
            current_time = datetime.now()
            if (self.last_post_news_check and 
                (current_time - self.last_post_news_check).total_seconds() < self.post_news_interval):
                return
            
            logger.info("Processing post-news analysis queue...")
            
            # Import the news alert trigger
            from services.news_alert_trigger import news_alert_trigger
            
            # Process post-news analysis asynchronously
            try:
                # Create event loop for async processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Process post-news analysis
                loop.run_until_complete(news_alert_trigger.process_post_news_analysis())
                
                # Clean up old history
                news_alert_trigger.cleanup_old_history()
                
                loop.close()
                
                self.last_post_news_check = current_time
                logger.info("Post-news analysis processing completed")
                
            except Exception as e:
                logger.error(f"Error in async post-news processing: {e}")
                
        except Exception as e:
            logger.error(f"Error processing post-news analysis: {e}")
    
    def _send_news_alert(self, news_item: Dict[str, Any]):
        """Send news alert"""
        try:
            # Trigger alert via API
            alert_data = {
                'type': 'news',
                'data': news_item
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/alerts/trigger",
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"News alert triggered: {result.get('alerts_sent', 0)} alerts sent")
            else:
                logger.error(f"Failed to trigger news alert: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending news alert: {e}")
    
    def _send_economic_alert(self, event: Dict[str, Any]):
        """Send economic calendar alert"""
        try:
            # Trigger alert via API
            alert_data = {
                'type': 'calendar',
                'data': event
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/alerts/trigger",
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Economic alert triggered: {result.get('alerts_sent', 0)} alerts sent")
            else:
                logger.error(f"Failed to trigger economic alert: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending economic alert: {e}")

# Global instance
background_worker = BackgroundAlertWorker()

def start_background_worker():
    """Start the background alert worker"""
    background_worker.start()

def stop_background_worker():
    """Stop the background alert worker"""
    background_worker.stop()

if __name__ == "__main__":
    # Test the background worker
    try:
        start_background_worker()
        print("Background worker started. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping background worker...")
        stop_background_worker()
        print("Background worker stopped.")
