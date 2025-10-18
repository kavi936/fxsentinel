#!/usr/bin/env python3
"""
Production Alert Worker Runner
Starts and monitors the production alert worker
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('production_worker.log')
    ]
)
logger = logging.getLogger(__name__)

# Import worker
from services.production_alert_worker import get_production_worker

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    worker = get_production_worker()
    worker.stop()
    sys.exit(0)

def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("FXSentinel Production Alert Worker")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now()}")
    logger.info(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")
    logger.info(f"API Base URL: {os.getenv('API_BASE_URL', 'http://localhost:5001')}")
    logger.info("=" * 60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Get and start worker
        worker = get_production_worker()
        worker.start()
        
        logger.info("✅ Worker started successfully")
        logger.info("Press Ctrl+C to stop")
        
        # Keep alive and monitor
        while True:
            time.sleep(60)
            
            # Log status every hour
            status = worker.get_status()
            if status['total_checks'] % 60 == 0:
                logger.info(f"Status: Uptime {status['uptime_seconds']:.0f}s, "
                          f"Alerts: {status['alerts_sent']}, "
                          f"Errors: {status['errors_count']}")
            
            # Check health
            health = worker.get_health()
            if not health['healthy']:
                logger.error("⚠️  Worker is unhealthy!")
                logger.error(f"Health details: {health}")
                
                # Attempt restart
                logger.info("Attempting to restart worker...")
                worker.stop()
                time.sleep(5)
                worker.start()
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        worker = get_production_worker()
        worker.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

