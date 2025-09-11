#!/usr/bin/env python3
"""
Independent Background Worker for FXSentinel
Works independently without relying on main app API calls
"""

import os
import sys
import time
import logging
import threading
import requests
from datetime import datetime
from flask import Flask, jsonify

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Railway captures stdout/stderr
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app for health checks
app = Flask(__name__)

# Global worker reference
background_worker = None

@app.route('/')
def root():
    """Root endpoint"""
    return "FXSentinel Independent Background Worker is running", 200

@app.route('/api/health')
def health():
    """Health check endpoint for Railway"""
    global background_worker
    
    status = {
        "status": "healthy",
        "service": "independent-background-worker",
        "worker_running": background_worker is not None and background_worker.get('running', False),
        "timestamp": time.time(),
        "version": "1.0.0"
    }
    
    return jsonify(status), 200

class IndependentBackgroundWorker:
    """Independent background worker that works without main app API"""
    
    def __init__(self):
        """Initialize the independent worker"""
        self.running = False
        self.thread = None
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.last_check = None
        self.last_news_check = None
        self.last_calendar_check = None
        
        logger.info("IndependentBackgroundWorker initialized")
    
    def start(self):
        """Start the background worker"""
        if self.running:
            logger.warning("IndependentBackgroundWorker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_worker, daemon=True)
        self.thread.start()
        logger.info("IndependentBackgroundWorker started")
    
    def stop(self):
        """Stop the background worker"""
        self.running = False
        logger.info("IndependentBackgroundWorker stopped")
    
    def get_status(self):
        """Get worker status"""
        return {
            'running': self.running,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'telegram_configured': bool(self.telegram_token)
        }
    
    def _run_worker(self):
        """Main worker loop"""
        logger.info("IndependentBackgroundWorker main loop started")
        
        while self.running:
            try:
                logger.info("🔄 Running independent alert check...")
                
                # Check for news alerts
                self._check_news_alerts()
                
                # Check for economic calendar alerts
                self._check_economic_calendar_alerts()
                
                self.last_check = datetime.now()
                logger.info(f"✅ Independent alert check completed at {self.last_check}")
                
                # Wait 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in independent worker: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _check_news_alerts(self):
        """Check for news alerts using direct service calls"""
        try:
            logger.info("Checking for news alerts...")
            
            # Import news aggregator directly
            from services.news_aggregator import news_aggregator
            
            # Get recent news
            news_items = news_aggregator.get_recent_news(hours=1)  # Last hour only
            
            if not news_items:
                logger.info("No recent news found")
                return
            
            # Filter for high-impact news
            high_impact = [n for n in news_items if n.get('impact') == 'high']
            
            if not high_impact:
                logger.info("No high-impact news found")
                return
            
            logger.info(f"Found {len(high_impact)} high-impact news items")
            
            # Send alerts for high-impact news
            for news_item in high_impact[:3]:  # Process first 3 items
                self._send_telegram_alert("news", news_item)
                
        except Exception as e:
            logger.error(f"Error checking news alerts: {e}")
    
    def _check_economic_calendar_alerts(self):
        """Check for economic calendar alerts using direct service calls"""
        try:
            logger.info("Checking for economic calendar alerts...")
            
            # Import finnhub calendar directly
            from services.finnhub_calendar import finnhub_calendar
            
            # Get economic calendar events
            events = finnhub_calendar.get_economic_calendar()
            
            if not events:
                logger.info("No economic events found")
                return
            
            # Process upcoming high-impact events
            now = datetime.now()
            for event in events:
                if event.get('impact') == 'high':
                    # Check timing for alerts (2h, 1h, 10min before)
                    try:
                        time_str = event.get('time', '')
                        date_str = event.get('date', '')
                        
                        if time_str and date_str:
                            # Parse event datetime
                            datetime_str = f"{date_str} {time_str}"
                            event_datetime = datetime.strptime(datetime_str, "%a, %b %d %H:%M UTC")
                            event_datetime = event_datetime.replace(year=datetime.now().year)
                            
                            minutes_until_event = (event_datetime - now).total_seconds() / 60
                            
                            # Send alerts at strategic times
                            if (8 <= minutes_until_event <= 10 or      # 10min before
                                55 <= minutes_until_event <= 60 or    # 1h before
                                115 <= minutes_until_event <= 120):   # 2h before
                                
                                logger.info(f"🎯 Sending economic alert for: {event.get('title', 'Unknown')} ({minutes_until_event:.1f} minutes away)")
                                self._send_telegram_alert("calendar", event)
                                
                    except Exception as e:
                        logger.error(f"Error checking event timing: {e}")
                        continue
                    
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}")
    
    def _send_telegram_alert(self, alert_type, data):
        """Send Telegram alert directly"""
        try:
            if not self.telegram_token:
                logger.warning("No Telegram bot token configured")
                return
            
            # Import telegram service directly
            from services.robust_telegram_service import RobustTelegramService
            
            telegram_service = RobustTelegramService()
            
            if alert_type == "news":
                message = f"🚨 HIGH IMPACT NEWS ALERT 🚨\n\n"
                message += f"📰 {data.get('title', 'Breaking News')}\n"
                message += f"📊 Impact: {data.get('impact', 'High')}\n"
                message += f"🌐 Source: {data.get('source', 'Unknown')}\n"
                if data.get('url'):
                    message += f"🔗 Read more: {data['url']}\n"
                message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
                
            elif alert_type == "calendar":
                message = f"📅 ECONOMIC CALENDAR ALERT 📅\n\n"
                message += f"🎯 {data.get('title', 'Economic Event')}\n"
                message += f"📊 Impact: {data.get('impact', 'High')}\n"
                message += f"⏰ Time: {data.get('date', '')} {data.get('time', '')} UTC\n"
                message += f"🇺🇸 Country: {data.get('country', 'US')}\n"
                message += f"\n⏰ Alert sent: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
            
            # Send to all users (you'll need to implement user list retrieval)
            # For now, let's log the message
            logger.info(f"📱 Telegram Alert Ready:\n{message}")
            
            # TODO: Implement actual Telegram sending to user list
            # telegram_service.send_to_all_users(message)
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")

def main():
    """Main function to start the independent background worker"""
    try:
        logger.info("🚀 Starting FXSentinel Independent Background Worker v1.0.0 on Railway")
        
        # Check required environment variables
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token:
            logger.info(f"✅ TELEGRAM_BOT_TOKEN configured (length: {len(telegram_token)})")
        else:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not configured")
        
        logger.info("✅ Environment variables checked")
        
        # Start the independent background worker
        global background_worker
        worker = IndependentBackgroundWorker()
        worker.start()
        background_worker = worker.get_status()
        
        logger.info("✅ Independent background worker started successfully")
        logger.info("🔄 Worker is now monitoring independently...")
        
        # Start Flask app
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"🌐 Starting Flask app on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
                
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
    finally:
        logger.info("🔄 Independent background worker process ending")

if __name__ == "__main__":
    main()
