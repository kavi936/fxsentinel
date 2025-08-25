#!/usr/bin/env python3
"""
Background Alert Worker for Flask App
Integrates alert checking into the main web application
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests

logger = logging.getLogger(__name__)

class BackgroundAlertWorker:
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        self.check_interval = 300  # Check every 5 minutes
        self.last_news_check = None
        self.last_calendar_check = None
        self.processed_news_ids = set()
        
        # Economic calendar tracking
        self.sent_economic_events = {}
        self.economic_alert_times = [120, 60, 10]  # 2 hours, 1 hour, 10 minutes before
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the worker with Flask app"""
        self.app = app
        
        # Start the background thread when app starts
        with app.app_context():
            self.start()
    
    def start(self):
        """Start the background alert worker"""
        if self.running:
            logger.info("Background alert worker already running")
            return
        
        logger.info("🚀 Starting Background Alert Worker")
        self.running = True
        self.thread = threading.Thread(target=self._run_worker, daemon=True)
        self.thread.start()
        logger.info("✅ Background alert worker started")
    
    def stop(self):
        """Stop the background alert worker"""
        logger.info("🛑 Stopping Background Alert Worker")
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("✅ Background alert worker stopped")
    
    def _run_worker(self):
        """Main worker loop"""
        logger.info("🔄 Background alert worker loop started")
        
        while self.running:
            try:
                with self.app.app_context():
                    # Check for news alerts
                    self._check_news_alerts()
                    
                    # Check for economic calendar alerts
                    self._check_economic_calendar_alerts()
                
                # Wait before next check
                logger.info(f"⏳ Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in background worker: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _check_news_alerts(self):
        """Check for new high-impact news and send alerts"""
        try:
            logger.info("📰 Checking for new high-impact news...")
            
            # Get current news from the API
            response = requests.get("http://localhost:5001/api/news", timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to get news: {response.status_code}")
                return
            
            news_data = response.json()
            news_items = news_data.get('news', [])
            high_impact = [n for n in news_items if n.get('impact') == 'high']
            
            if not high_impact:
                logger.info("No high-impact news found")
                return
            
            logger.info(f"Found {len(high_impact)} high-impact news items")
            
            # Get all connected users
            users = self._get_all_connected_users()
            if not users:
                logger.info("No connected users found")
                return
            
            # Process news for alerts
            from .news_alert_trigger import news_alert_trigger
            
            alerts_sent = 0
            for news_item in high_impact[:5]:  # Process first 5 high-impact items
                news_id = str(news_item.get('id', ''))
                
                # Skip if already processed
                if news_id in self.processed_news_ids:
                    continue
                
                # Check if forex high impact
                if not news_alert_trigger.is_forex_high_impact(news_item):
                    continue
                
                # Send to all connected users
                for user in users:
                    try:
                        # Create user data
                        user_data = {
                            'user_id': user['user_id'],
                            'chat_id': user['chat_id'],
                            'settings': user['settings']
                        }
                        
                        # Determine if AI analysis is needed
                        needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
                        
                        # Send the alert
                        import asyncio
                        success = asyncio.run(news_alert_trigger._send_alert_to_user(user_data, news_item, needs_ai_analysis))
                        
                        if success:
                            alerts_sent += 1
                            logger.info(f"✅ Alert sent to user {user['user_id']}: {news_item.get('title', '')[:50]}...")
                        
                        # Wait a bit between users
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error sending alert to user {user['user_id']}: {e}")
                
                # Mark as processed
                self.processed_news_ids.add(news_id)
                
                # Keep only last 1000 processed IDs
                if len(self.processed_news_ids) > 1000:
                    self.processed_news_ids = set(list(self.processed_news_ids)[-500:])
                
                # Wait a bit between news items
                time.sleep(2)
            
            if alerts_sent > 0:
                logger.info(f"📨 Sent {alerts_sent} news alerts")
            else:
                logger.info("No new alerts sent")
                
        except Exception as e:
            logger.error(f"Error checking news alerts: {e}")
    
    def _check_economic_calendar_alerts(self):
        """Check for upcoming economic calendar events"""
        try:
            logger.info("📅 Checking economic calendar for upcoming events...")
            
            # Get economic calendar
            response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to get calendar: {response.status_code}")
                return
            
            calendar_data = response.json()
            events = calendar_data.get('events', [])
            
            if not events:
                logger.info("No economic calendar events found")
                return
            
            logger.info(f"📊 Processing {len(events)} events from calendar")
            
            # Get all connected users
            users = self._get_all_connected_users()
            if not users:
                logger.info("No connected users found for calendar alerts")
                return
            
            # Find upcoming high-impact events
            now = datetime.now()
            alerts_sent = 0
            
            for event in events:
                if event.get('impact') == 'high':
                    event_id = event.get('id', event.get('title', 'unknown'))
                    event_time_str = event.get('time', '')
                    
                    if not event_time_str:
                        continue
                    
                    try:
                        # Parse event time
                        event_time = datetime.strptime(event_time_str, '%H:%M UTC')
                        event_time = event_time.replace(year=now.year, month=now.month, day=now.day)
                        
                        # Calculate time until event
                        time_until_event = event_time - now
                        minutes_until_event = time_until_event.total_seconds() / 60
                        
                        # Check if we should send an alert
                        for alert_minutes in self.economic_alert_times:
                            if 0 <= minutes_until_event <= alert_minutes and minutes_until_event >= alert_minutes - 5:
                                # Check if we already sent this alert
                                alert_key = f"{event_id}_{alert_minutes}"
                                if alert_key not in self.sent_economic_events:
                                    # Send to all connected users
                                    for user in users:
                                        try:
                                            self._send_economic_calendar_alert(event, alert_minutes, user)
                                            alerts_sent += 1
                                            time.sleep(0.5)
                                        except Exception as e:
                                            logger.error(f"Error sending calendar alert to user {user['user_id']}: {e}")
                                    
                                    self.sent_economic_events[alert_key] = now
                                    break
                        
                    except Exception as e:
                        logger.error(f"Error processing event {event_id}: {e}")
            
            if alerts_sent > 0:
                logger.info(f"📅 Sent {alerts_sent} economic calendar alerts")
            else:
                logger.info("No new calendar alerts sent")
                
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}")
    
    def _get_all_connected_users(self) -> List[Dict[str, Any]]:
        """Get all users who have connected to the system"""
        try:
            from .firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            
            # Get all users with alert settings
            users = firebase_storage.get_all_users_with_alerts()
            
            if not users:
                logger.warning("No users found with alert settings")
                return []
            
            # Process users to ensure they have the correct structure
            processed_users = []
            for user in users:
                user_id = user.get('user_id')
                settings = user.get('settings', {})
                chat_id = user.get('telegram_chat_id')
                
                # Get chat ID from mapping if not in user data
                if not chat_id:
                    chat_id = firebase_storage.get_telegram_chat_id(user_id)
                
                if chat_id and settings:
                    processed_users.append({
                        'user_id': user_id,
                        'chat_id': chat_id,
                        'settings': settings
                    })
            
            logger.info(f"Found {len(processed_users)} users with alert settings and chat IDs")
            return processed_users
            
        except Exception as e:
            logger.error(f"Error getting connected users: {e}")
            return []
    
    def _send_economic_calendar_alert(self, event: Dict[str, Any], minutes_before: int, user: Dict[str, Any]):
        """Send economic calendar alert to a specific user"""
        try:
            from .economic_calendar_alerts import economic_calendar_alerts
            
            # Create user data
            user_data = {
                'user_id': user['user_id'],
                'chat_id': user['chat_id'],
                'settings': user['settings']
            }
            
            # Send the alert
            import asyncio
            success = asyncio.run(economic_calendar_alerts._send_calendar_alert_to_user(user_data, event, minutes_before))
            
            if success:
                logger.info(f"✅ Calendar alert sent to user {user['user_id']}")
            else:
                logger.warning(f"❌ Calendar alert failed for user {user['user_id']}")
                
        except Exception as e:
            logger.error(f"Error sending calendar alert: {e}")

# Global instance
background_alert_worker = BackgroundAlertWorker()
