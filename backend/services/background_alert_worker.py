#!/usr/bin/env python3
"""
Background Alert Worker
Processes alerts and post-news analysis in the background
"""

import os
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
        # Use environment variable for production, fallback to localhost for development
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        
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
    
    def get_status(self):
        """Get the current status of the background worker"""
        return {
            'running': self.running,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'check_interval': self.check_interval,
            'post_news_interval': self.post_news_interval,
            'last_post_news_check': self.last_post_news_check.isoformat() if self.last_post_news_check else None
        }
    
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
            
            # Try to use local function first (if running as part of main app)
            news_items = self._get_news_local()
            if news_items is None:
                # Fallback to HTTP API call
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
    
    def _get_news_local(self):
        """Try to get news using local function (if running as part of main app)"""
        try:
            # Try to import and use the local news function
            from flask import current_app
            with current_app.app_context():
                # Import the news aggregator directly
                from .news_aggregator import news_aggregator
                news_items = news_aggregator.get_latest_news()
                return news_items
        except Exception as e:
            logger.debug(f"Could not get news locally: {e}")
            return None
    
    def _check_economic_calendar_alerts(self):
        """Check for economic calendar alerts"""
        try:
            logger.info("Checking for economic calendar alerts...")
            
            # Try to use local function first (if running as part of main app)
            events = self._get_economic_calendar_local()
            if events is None:
                # Fallback to HTTP API call
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
                # Only process high-impact events that are upcoming
                if (event.get('impact') == 'high' and 
                    event.get('status', '').upper() in ['UPCOMING', 'IMMINENT']):
                    
                    # Check if event is within alert timing windows (2h, 1h, 10min before)
                    try:
                        # datetime is already imported at the top of the file
                        time_str = event.get('time', '')
                        date_str = event.get('date', '')
                        
                        if time_str and date_str:
                            # Parse event datetime with proper year handling
                            datetime_str = f"{date_str} {time_str}"
                            event_datetime = datetime.strptime(datetime_str, "%a, %b %d %H:%M UTC")
                            
                            # CRITICAL FIX: Always use current year for economic calendar events
                            # The date format doesn't include year, so we need to add it
                            current_year = datetime.now().year
                            event_datetime = event_datetime.replace(year=current_year)
                            
                            # Additional validation: If the event date is in the past relative to current date,
                            # it might be from next year (e.g., if we're in December and event is in January)
                            current_date = datetime.now().date()
                            event_date = event_datetime.date()
                            
                            # If event date is more than 30 days in the past, assume it's next year
                            if (current_date - event_date).days > 30:
                                event_datetime = event_datetime.replace(year=current_year + 1)
                                logger.debug(f"Adjusted event year to next year: {event.get('title', 'Unknown')} -> {event_datetime}")
                            
                            time_until_event = event_datetime - now
                            minutes_until_event = time_until_event.total_seconds() / 60
                            
                            # Add detailed logging for debugging
                            logger.debug(f"Event: {event.get('title', 'Unknown')} | Parsed: {event_datetime} | Minutes until: {minutes_until_event:.1f}")
                            
                            # Only send alerts if within timing windows
                            if (8 <= minutes_until_event <= 10 or      # 10min before
                                55 <= minutes_until_event <= 60 or    # 1h before
                                115 <= minutes_until_event <= 120):   # 2h before
                                logger.info(f"🎯 Sending economic alert for: {event.get('title', 'Unknown')} ({minutes_until_event:.1f} minutes away)")
                                self._send_economic_alert(event)
                            else:
                                if minutes_until_event > 0:  # Only log future events
                                    logger.debug(f"Event {event.get('title', 'Unknown')} not within alert timing windows ({minutes_until_event:.1f} minutes away)")
                                else:
                                    logger.debug(f"Event {event.get('title', 'Unknown')} is in the past ({minutes_until_event:.1f} minutes ago)")
                    except Exception as e:
                        logger.error(f"Error checking event timing: {e}")
                        continue
                    
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}")
    
    def _get_economic_calendar_local(self):
        """Try to get economic calendar using local function (if running as part of main app)"""
        try:
            # Try to import and use the local economic calendar function
            from flask import current_app
            with current_app.app_context():
                # Import the finnhub calendar directly
                from .finnhub_calendar import finnhub_calendar
                events = finnhub_calendar.get_economic_calendar()
                return events
        except Exception as e:
            logger.debug(f"Could not get economic calendar locally: {e}")
            return None
    
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

# Global instance - lazy initialization
_background_worker = None

def get_background_worker():
    """Get the background worker instance (lazy initialization)"""
    global _background_worker
    if _background_worker is None:
        _background_worker = BackgroundAlertWorker()
    return _background_worker

def start_background_worker():
    """Start the background alert worker"""
    worker = get_background_worker()
    worker.start()

def stop_background_worker():
    """Stop the background alert worker"""
    worker = get_background_worker()
    worker.stop()

# For backward compatibility - this will be created when first accessed
class _LazyBackgroundWorker:
    def __getattr__(self, name):
        return getattr(get_background_worker(), name)

background_worker = _LazyBackgroundWorker()

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
