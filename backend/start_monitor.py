#!/usr/bin/env python3
"""
FXSentinel Process Monitor Startup Script
Starts the process monitoring service alongside the main application
"""

import os
import sys
import asyncio
import logging
import signal
import threading
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProcessMonitorRunner:
    def __init__(self):
        self.running = False
        self.monitor_task = None
        
    async def start_monitor(self):
        """Start the process monitoring service"""
        try:
            from services.process_monitor import process_monitor
            logger.info("Starting FXSentinel Process Monitor...")
            
            self.running = True
            await process_monitor.start_monitoring()
            
        except Exception as e:
            logger.error(f"Error in process monitor: {e}")
            self.running = False
    
    def stop_monitor(self):
        """Stop the process monitoring service"""
        logger.info("Stopping FXSentinel Process Monitor...")
        self.running = False
    
    def run_monitor(self):
        """Run the monitor in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.start_monitor())
        except KeyboardInterrupt:
            logger.info("Process monitor interrupted")
        finally:
            loop.close()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main function to start the process monitor"""
    logger.info("=" * 60)
    logger.info("FXSentinel Process Monitor Starting")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the monitor
    monitor_runner = ProcessMonitorRunner()
    
    # Run monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor_runner.run_monitor, daemon=True)
    monitor_thread.start()
    
    logger.info("Process monitor started successfully")
    logger.info("Monitoring all FXSentinel background services...")
    
    try:
        # Keep the main thread alive
        while monitor_runner.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down process monitor...")
        monitor_runner.stop_monitor()
    
    logger.info("Process monitor stopped")

if __name__ == "__main__":
    main()
