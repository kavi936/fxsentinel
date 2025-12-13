#!/usr/bin/env python3
"""
FXSentinel Multi-User Background Alert Service
Continuously monitors for news and sends alerts automatically for ALL connected users
"""

import time
import sys
import signal
import logging
from datetime import datetime, timedelta
import requests
import json

# Add backend to path
sys.path.append('backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alert_service_multi_user.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiUserBackgroundAlertService:
    def __init__(self):
        self.running = False
        self.check_interval = 300  # Check every 5 minutes
        self.last_news_check = None
        self.last_calendar_check = None
        self.processed_news_ids = set()
        
        # Economic calendar tracking to prevent duplicates
        self.sent_economic_events = {}  # Track sent events with timing
        self.economic_alert_times = [120, 60, 10]  # 2 hours, 1 hour, 10 minutes before
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def get_all_connected_users(self):
        """Get all users who have connected to the system"""
        try:
            # Get users from Firebase or your user database
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
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
                
                # Get chat ID from Firebase if not in user data
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
    
    def start(self):
        """Start the background alert service"""
        logger.info("🚀 Starting FXSentinel Multi-User Background Alert Service")
        logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        
        self.running = True
        
        try:
            while self.running:
                try:
                    # Get all connected users
                    users = self.get_all_connected_users()
                    
                    if users:
                        # Check for new news alerts for all users
                        self.check_news_alerts_for_all_users(users)
                        
                        # Check for economic calendar alerts for all users
                        self.check_economic_calendar_alerts_for_all_users(users)
                    else:
                        logger.info("No connected users found, waiting...")
                    
                    # Wait before next check
                    logger.info(f"⏳ Waiting {self.check_interval} seconds until next check...")
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Service interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(60)  # Wait 1 minute on error
                    
        except Exception as e:
            logger.error(f"Fatal error in background service: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the background service"""
        logger.info("🛑 Stopping FXSentinel Multi-User Background Alert Service")
        self.running = False
    
    def check_news_alerts_for_all_users(self, users):
        """Check for new high-impact news and send alerts to all users"""
        try:
            logger.info("📰 Checking for new high-impact news for all users...")
            
            # Get current news
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
            
            # Process news for alerts for each user
            from services.news_alert_trigger import news_alert_trigger
            
            total_alerts_sent = 0
            
            for user in users:
                user_id = user.get('user_id')
                user_settings = user.get('settings', {})
                
                # Check if user has Telegram enabled
                telegram_enabled = user_settings.get('telegram_enabled', False)
                if not telegram_enabled:
                    # Also check the nested structure
                    telegram_enabled = user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                    if not telegram_enabled:
                        continue
                
                user_alerts_sent = 0
                
                for news_item in high_impact[:5]:  # Process first 5 high-impact items
                    news_id = str(news_item.get('id', ''))
                    
                    # Skip if already processed for this user
                    user_news_key = f"{user_id}_{news_id}"
                    if user_news_key in self.processed_news_ids:
                        continue
                    
                    # Check if forex high impact
                    if not news_alert_trigger.is_forex_high_impact(news_item):
                        continue
                    
                    # Check user's currency preferences
                    user_currencies = user_settings.get('currency_pairs', [])
                    if not user_currencies:
                        # Also check the nested structure
                        user_currencies = user_settings.get('preferences', {}).get('currencyPairs', [])
                    
                    if user_currencies and not self._news_matches_user_currencies(news_item, user_currencies):
                        continue
                    
                    # Create user data
                    user_data = {
                        'user_id': user_id,
                        'chat_id': user.get('chat_id'),
                        'settings': user_settings
                    }
                    
                    # Determine if AI analysis is needed
                    needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
                    
                    # Send the alert
                    success = news_alert_trigger._send_alert_to_user(user_data, news_item, needs_ai_analysis)
                    
                    if success:
                        user_alerts_sent += 1
                        total_alerts_sent += 1
                        logger.info(f"✅ Alert sent to user {user_id}: {news_item.get('title', '')[:50]}...")
                        
                        # Mark as processed for this user
                        self.processed_news_ids.add(user_news_key)
                    
                    # Wait a bit between alerts
                    time.sleep(1)
                
                if user_alerts_sent > 0:
                    logger.info(f"📨 Sent {user_alerts_sent} news alerts to user {user_id}")
                
                # Keep only last 1000 processed IDs per user
                if len(self.processed_news_ids) > 1000:
                    # Keep only recent entries
                    recent_ids = list(self.processed_news_ids)[-500:]
                    self.processed_news_ids = set(recent_ids)
            
            if total_alerts_sent > 0:
                logger.info(f"📨 Total: Sent {total_alerts_sent} news alerts to all users")
            else:
                logger.info("No new alerts sent to any users")
                
        except Exception as e:
            logger.error(f"Error checking news alerts for all users: {e}")
    
    def check_economic_calendar_alerts_for_all_users(self, users):
        """Check for upcoming economic calendar events and send pre-event alerts to all users"""
        try:
            logger.info("📅 Checking economic calendar for upcoming events for all users...")
            
            # Get economic calendar
            response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to get calendar: {response.status_code}")
                return
            
            calendar_data = response.json()
            
            # CRITICAL: Check data source to prevent false alerts from fallback/mock data
            data_source = calendar_data.get('source', 'unknown')
            if data_source in ['fallback_data', 'mock_data', 'test_data']:
                logger.warning(f"⚠️ Skipping economic calendar alerts - using {data_source} (potential false alerts)")
                return
            
            # Additional validation: Check if we have real events
            events = calendar_data.get('events', [])
            if not events:
                logger.warning("⚠️ No events found in calendar data")
                return
            
            # Log data source for monitoring
            logger.info(f"📊 Processing {len(events)} events from {data_source}")
            
            # Find upcoming high-impact events
            now = datetime.now()
            total_alerts_sent = 0
            
            for user in users:
                user_id = user.get('user_id')
                user_settings = user.get('settings', {})
                
                # Check if user has Telegram enabled
                telegram_enabled = user_settings.get('telegram_enabled', False)
                if not telegram_enabled:
                    # Also check the nested structure
                    telegram_enabled = user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                    if not telegram_enabled:
                        continue
                
                # Check if user wants economic calendar alerts
                alert_types = user_settings.get('alert_types', [])
                if not alert_types:
                    # Also check the nested structure
                    alert_types = user_settings.get('preferences', {}).get('alertTypes', {})
                    if isinstance(alert_types, dict):
                        # Convert dict to list format
                        alert_types = [k for k, v in alert_types.items() if v]
                
                if 'economicCalendar' not in alert_types and 'preNews' not in alert_types:
                    continue
                
                user_alerts_sent = 0
                
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
                                    # Check if we already sent this alert to this user
                                    alert_key = f"{user_id}_{event_id}_{alert_minutes}"
                                    if alert_key not in self.sent_economic_events:
                                        # Send the alert
                                        success = self._send_economic_calendar_alert_to_user(event, alert_minutes, user)
                                        if success:
                                            self.sent_economic_events[alert_key] = now
                                            user_alerts_sent += 1
                                            total_alerts_sent += 1
                                            logger.info(f"✅ Economic calendar alert sent to user {user_id}: {event.get('title', 'Unknown')} ({alert_minutes} min before)")
                                        break
                            
                        except Exception as e:
                            logger.error(f"Error processing event {event_id} for user {user_id}: {e}")
                            continue
                
                if user_alerts_sent > 0:
                    logger.info(f"📨 Sent {user_alerts_sent} economic calendar alerts to user {user_id}")
            
            if total_alerts_sent > 0:
                logger.info(f"📨 Total: Sent {total_alerts_sent} economic calendar alerts to all users")
            else:
                logger.info("No new economic calendar alerts to send to any users")
                
        except Exception as e:
            logger.error(f"Error checking economic calendar for all users: {e}")
    
    def _news_matches_user_currencies(self, news_item, user_currencies):
        """Check if news item matches user's currency preferences"""
        try:
            title = news_item.get('title', '').lower()
            summary = news_item.get('summary', '').lower()
            content = f"{title} {summary}"
            
            for currency_pair in user_currencies:
                # Convert currency pairs to search terms
                if '/' in currency_pair:
                    base, quote = currency_pair.split('/')
                    if base.lower() in content or quote.lower() in content:
                        return True
                else:
                    if currency_pair.lower() in content:
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking currency match: {e}")
            return True  # Default to sending if there's an error
    
    def _send_economic_calendar_alert_to_user(self, event, minutes_before, user):
        """Send a properly formatted economic calendar alert to a specific user"""
        try:
            title = event.get('title', 'Unknown Event')
            event_time = event.get('time', 'Unknown Time')
            currency = event.get('currency', 'USD')
            expected = event.get('expected', 'N/A')
            previous = event.get('previous', 'N/A')
            
            time_text = {
                120: "2 hours",
                60: "1 hour", 
                10: "10 minutes"
            }.get(minutes_before, f"{minutes_before} minutes")
            
            # Create properly formatted alert message
            alert_message = f"""📅 <b>UPCOMING ECONOMIC EVENT</b>

<b>{title}</b> - Event starts in {time_text}

📊 <b>Event Details:</b>
• Time: {event_time} UTC
• Currency: {currency}
• Expected: {expected}
• Previous: {previous}

💱 <b>Affected Pairs:</b> {currency}/USD, EUR/{currency}

🎯 <b>Prepare for Market Volatility!</b>
📱 Check dashboard for detailed analysis"""
            
            # Send via Telegram
            import os
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("Telegram bot token not configured")
                return False
            
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            telegram_data = {
                'chat_id': user.get('chat_id'),
                'text': alert_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(telegram_url, json=telegram_data, timeout=10)
            
            if response.status_code == 200:
                # Save to alert history
                from services.firebase_realtime_storage import FirebaseRealtimeStorage
                firebase_storage = FirebaseRealtimeStorage()
                
                alert_data = {
                    'alert_type': 'economic_calendar',
                    'title': f'Economic Calendar: {title}',
                    'content': alert_message,
                    'timestamp': datetime.now().isoformat(),
                    'sent_via': ['telegram'],
                    'status': 'sent'
                }
                
                firebase_storage.log_alert_history(user.get('user_id'), alert_data)
                return True
            else:
                logger.error(f"Failed to send economic calendar alert to user {user.get('user_id')}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending economic calendar alert to user {user.get('user_id')}: {e}")
            return False

def main():
    """Main function to start the background service"""
    service = MultiUserBackgroundAlertService()
    
    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        service.stop()

if __name__ == "__main__":
    main()
