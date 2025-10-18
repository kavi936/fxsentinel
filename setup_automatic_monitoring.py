#!/usr/bin/env python3
"""
Set up automatic monitoring for the background worker
"""

import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_worker_alerts():
    """Trigger the worker to check for alerts"""
    try:
        # Try worker first
        worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
        response = requests.post(f"{worker_url}/api/trigger-alerts", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Worker trigger successful: {result}")
            return True
        else:
            logger.warning(f"⚠️ Worker trigger failed: {response.status_code}")
            
            # Fallback to main app
            main_app_url = "https://fxsentinel-production.up.railway.app"
            response = requests.post(f"{main_app_url}/api/trigger-alerts", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Main app trigger successful: {result}")
                return True
            else:
                logger.error(f"❌ Both triggers failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error triggering alerts: {e}")
        return False

def run_monitoring_loop():
    """Run the monitoring loop"""
    logger.info("🚀 Starting automatic monitoring loop")
    logger.info("🔄 Will check for alerts every 60 seconds")
    
    while True:
        try:
            logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking for alerts...")
            
            success = trigger_worker_alerts()
            
            if success:
                logger.info("✅ Alert check completed successfully")
            else:
                logger.warning("⚠️ Alert check failed")
            
            # Wait 60 seconds before next check
            logger.info("⏳ Waiting 60 seconds for next check...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring loop stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            logger.info("⏳ Waiting 60 seconds before retry...")
            time.sleep(60)

if __name__ == "__main__":
    print("🔄 FXSentinel Automatic Monitoring")
    print("=" * 50)
    print("This will trigger the worker to check for alerts every 60 seconds")
    print("Press Ctrl+C to stop")
    print()
    
    run_monitoring_loop()
