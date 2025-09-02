#!/usr/bin/env python3
"""
FXSentinel Railway Background Worker
Runs the background alert service for production deployment
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add current directory to path
sys.path.append('.')

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Railway captures stdout/stderr
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the background worker"""
    try:
        logger.info("🚀 Starting FXSentinel Background Worker on Railway")
        
        # Log environment configuration
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        logger.info(f"🌐 API Base URL: {api_base_url}")
        
        # Check required environment variables
        required_vars = ['TELEGRAM_BOT_TOKEN']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.error("Please set these in your Railway environment variables")
            return
        
        logger.info("✅ Environment variables configured")
        
        # Import and start the background worker
        try:
            from services.background_alert_worker import start_background_worker, background_worker
            
            logger.info("📦 Background worker imported successfully")
            
            # Start the worker
            start_background_worker()
            
            logger.info("✅ Background worker started successfully")
            logger.info("🔄 Worker is now monitoring for alerts...")
            
            # Keep the process running
            while True:
                # Check if worker is still running
                if not background_worker.running:
                    logger.warning("⚠️ Background worker stopped, restarting...")
                    start_background_worker()
                
                # Log status every 5 minutes
                time.sleep(300)
                status = background_worker.get_status()
                logger.info(f"📊 Worker Status: {status}")
                
        except ImportError as e:
            logger.error(f"❌ Failed to import background worker: {e}")
            logger.error("Make sure all required services are available")
            return
        except Exception as e:
            logger.error(f"❌ Error starting background worker: {e}")
            return
            
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
    finally:
        logger.info("🔄 Background worker process ending")

if __name__ == "__main__":
    main()
