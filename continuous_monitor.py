#!/usr/bin/env python3
"""
Continuous monitoring script that runs in the background
"""

import requests
import time
import logging
import signal
import sys
from datetime import datetime

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousMonitor:
    def __init__(self):
        self.running = True
        self.worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
        self.main_app_url = "https://fxsentinel-production.up.railway.app"
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def trigger_alerts(self):
        """Trigger the worker to check for alerts"""
        try:
            # Try worker first
            response = requests.post(f"{self.worker_url}/api/trigger-alerts", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Alert check successful - News: {result.get('news_alerts_processed', False)}, Calendar: {result.get('calendar_alerts_processed', False)}")
                return True
            else:
                logger.warning(f"⚠️ Worker trigger failed: {response.status_code}")
                
                # Fallback to main app
                response = requests.post(f"{self.main_app_url}/api/trigger-alerts", timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Main app trigger successful - News: {result.get('news_alerts_processed', False)}")
                    return True
                else:
                    logger.error(f"❌ Both triggers failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error triggering alerts: {e}")
            return False
    
    def run(self):
        """Run the continuous monitoring loop"""
        logger.info("🚀 Starting FXSentinel Continuous Monitor")
        logger.info("🔄 Will check for alerts every 60 seconds")
        logger.info("📝 Logs will be saved to monitor.log")
        logger.info("🛑 Press Ctrl+C to stop")
        
        check_count = 0
        
        while self.running:
            try:
                check_count += 1
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"⏰ Check #{check_count} at {timestamp}")
                
                success = self.trigger_alerts()
                
                if success:
                    logger.info(f"✅ Check #{check_count} completed successfully")
                else:
                    logger.warning(f"⚠️ Check #{check_count} failed")
                
                # Wait 60 seconds before next check
                logger.info("⏳ Waiting 60 seconds for next check...")
                
                # Sleep in small increments to allow for graceful shutdown
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🛑 Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                logger.info("⏳ Waiting 60 seconds before retry...")
                time.sleep(60)
        
        logger.info("🔄 Continuous monitoring stopped")

def main():
    """Main function"""
    print("🔄 FXSentinel Continuous Monitor")
    print("=" * 50)
    print("This will run continuously in the background")
    print("Logs will be saved to monitor.log")
    print("Press Ctrl+C to stop")
    print()
    
    monitor = ContinuousMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
