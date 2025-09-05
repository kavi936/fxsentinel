#!/usr/bin/env python3
"""
Simple startup script for Railway background worker
This script avoids any token access during import/build time
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the background worker"""
    try:
        logger.info("🚀 Starting FXSentinel Background Worker on Railway")
        
        # Check if TELEGRAM_BOT_TOKEN is available
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set")
            logger.error("Please set TELEGRAM_BOT_TOKEN in your Railway environment variables")
            return
        
        logger.info("✅ TELEGRAM_BOT_TOKEN is available")
        
        # Now import and run the railway worker
        from railway_worker import main as railway_main
        railway_main()
        
    except Exception as e:
        logger.error(f"❌ Error starting background worker: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
