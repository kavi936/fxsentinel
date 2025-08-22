#!/usr/bin/env python3
"""
FXSentinel Background Alert Service
Continuously monitors for news and sends alerts automatically
"""

import time
import sys
import signal
import logging
from datetime import datetime, timedelta
import requests

# Add backend to path
sys.path.append('backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alert_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackgroundAlertService:
    def __init__(self):
        self.running = False
        self.check_interval = 300  # Check every 5 minutes
        self.last_news_check = None
        self.last_calendar_check = None
        self.processed_news_ids = set()
        
        # Economic calendar tracking to prevent duplicates
        self.sent_economic_events = {}  # Track sent events with timing
        self.economic_alert_times = [120, 60, 10]  # 2 hours, 1 hour, 10 minutes before
        
        # Your user configuration
        self.user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
        self.chat_id = "8008493413"
        
        # User settings
        self.user_settings = {
            'telegram_enabled': True,
            'alert_types': ['liveNews', 'economicCalendar'],
            'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
            'impact_levels': ['high', 'medium'],
            'notification_frequency': 'immediate'
        }
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self):
        """Start the background alert service"""
        logger.info("🚀 Starting FXSentinel Background Alert Service")
        logger.info(f"📱 Monitoring for user: {self.user_id}")
        logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        
        self.running = True
        
        try:
            while self.running:
                try:
                    # Check for new news alerts
                    self.check_news_alerts()
                    
                    # Check for economic calendar alerts
                    self.check_economic_calendar_alerts()
                    
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
        logger.info("🛑 Stopping FXSentinel Background Alert Service")
        self.running = False
    
    def check_news_alerts(self):
        """Check for new high-impact news and send alerts"""
        try:
            logger.info("📰 Checking for new high-impact news...")
            
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
            
            # Process news for alerts
            from services.news_alert_trigger import news_alert_trigger
            
            alerts_sent = 0
            for news_item in high_impact[:5]:  # Process first 5 high-impact items
                news_id = str(news_item.get('id', ''))
                
                # Skip if already processed
                if news_id in self.processed_news_ids:
                    continue
                
                # Check if forex high impact
                if not news_alert_trigger.is_forex_high_impact(news_item):
                    continue
                
                # Create user data
                user_data = {
                    'user_id': self.user_id,
                    'chat_id': self.chat_id,
                    'settings': self.user_settings
                }
                
                # Determine if AI analysis is needed
                needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
                
                # Send the alert
                success = news_alert_trigger._send_alert_to_user(user_data, news_item, needs_ai_analysis)
                
                if success:
                    alerts_sent += 1
                    logger.info(f"✅ Alert sent: {news_item.get('title', '')[:50]}...")
                    
                    # Mark as processed
                    self.processed_news_ids.add(news_id)
                    
                    # Keep only last 1000 processed IDs
                    if len(self.processed_news_ids) > 1000:
                        self.processed_news_ids = set(list(self.processed_news_ids)[-500:])
                
                # Wait a bit between alerts
                time.sleep(2)
            
            if alerts_sent > 0:
                logger.info(f"📨 Sent {alerts_sent} news alerts")
            else:
                logger.info("No new alerts sent")
                
        except Exception as e:
            logger.error(f"Error checking news alerts: {e}")
    
    def check_economic_calendar_alerts(self):
        """Check for upcoming economic calendar events and send pre-event alerts with proper timing"""
        try:
            logger.info("📅 Checking economic calendar for upcoming events...")
            
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
                                    # Send the alert
                                    self._send_economic_calendar_alert(event, alert_minutes)
                                    self.sent_economic_events[alert_key] = now
                                    alerts_sent += 1
                                    logger.info(f"✅ Economic calendar alert sent: {event.get('title', 'Unknown')} ({alert_minutes} min before)")
                                    break
                        
                    except Exception as e:
                        logger.error(f"Error processing event {event_id}: {e}")
                        continue
            
            if alerts_sent > 0:
                logger.info(f"📨 Sent {alerts_sent} economic calendar alerts")
            else:
                logger.info("No new economic calendar alerts to send")
                
        except Exception as e:
            logger.error(f"Error checking economic calendar: {e}")
    
    def _send_economic_calendar_alert(self, event, minutes_before):
        """Send a properly formatted economic calendar alert"""
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
                'chat_id': self.chat_id,
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
                
                firebase_storage.log_alert_history(self.user_id, alert_data)
                return True
            else:
                logger.error(f"Failed to send economic calendar alert: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending economic calendar alert: {e}")
            return False

def main():
    """Main function to start the background service"""
    service = BackgroundAlertService()
    
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
