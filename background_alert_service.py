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
        """Check for upcoming economic calendar events and send pre-event alerts"""
        try:
            logger.info("📅 Checking economic calendar for upcoming events...")
            
            # Get economic calendar
            response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to get calendar: {response.status_code}")
                return
            
            calendar_data = response.json()
            events = calendar_data.get('events', [])
            
            # Find upcoming high-impact events (next 2 hours)
            now = datetime.now()
            upcoming_high_impact = []
            
            for event in events:
                if event.get('impact') == 'high':
                    try:
                        # Parse event time
                        event_time_str = event.get('time', '')
                        if event_time_str:
                            # Simple time parsing (you might need to adjust based on your format)
                            event_time = datetime.strptime(event_time_str, '%H:%M UTC')
                            event_time = event_time.replace(year=now.year, month=now.month, day=now.day)
                            
                            # Check if event is in next 2 hours
                            time_diff = event_time - now
                            if timedelta(0) <= time_diff <= timedelta(hours=2):
                                upcoming_high_impact.append(event)
                    except:
                        continue
            
            if upcoming_high_impact:
                logger.info(f"Found {len(upcoming_high_impact)} upcoming high-impact events")
                
                # Send pre-event alerts
                from services.news_alert_trigger import news_alert_trigger
                
                for event in upcoming_high_impact[:2]:  # Send alerts for first 2 events
                    title = event.get('title', 'Unknown')
                    event_time = event.get('time', 'Unknown')
                    
                    # Create pre-event alert
                    pre_event_alert = {
                        'title': f'📅 UPCOMING ECONOMIC EVENT: {title}',
                        'summary': f'High-impact economic event scheduled for {event_time}. Prepare for potential market volatility.',
                        'source': 'Economic Calendar',
                        'impact': 'high',
                        'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
                        'published_at': datetime.now().isoformat()
                    }
                    
                    user_data = {
                        'user_id': self.user_id,
                        'chat_id': self.chat_id,
                        'settings': self.user_settings
                    }
                    
                    success = news_alert_trigger._send_alert_to_user(user_data, pre_event_alert, False)
                    if success:
                        logger.info(f"✅ Pre-event alert sent: {title[:50]}...")
                    else:
                        logger.warning(f"❌ Failed to send pre-event alert: {title[:50]}...")
                    
                    time.sleep(2)  # Wait between alerts
            else:
                logger.info("No upcoming high-impact events found")
                
        except Exception as e:
            logger.error(f"Error checking economic calendar: {e}")

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
