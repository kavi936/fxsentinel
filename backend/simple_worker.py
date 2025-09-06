#!/usr/bin/env python3
"""
Simple Background Worker for FXSentinel
A simplified version that can start without complex dependencies
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
    return "FXSentinel Simple Background Worker is running", 200

@app.route('/api/health')
def health():
    """Health check endpoint for Railway"""
    global background_worker
    
    status = {
        "status": "healthy",
        "service": "simple-background-worker",
        "worker_running": background_worker is not None and background_worker.get('running', False),
        "timestamp": time.time(),
        "version": "1.0.0"
    }
    
    return jsonify(status), 200

class SimpleBackgroundWorker:
    """Simple background worker that can start without complex dependencies"""
    
    def __init__(self):
        """Initialize the simple worker"""
        self.running = False
        self.thread = None
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.last_check = None
        
        logger.info("SimpleBackgroundWorker initialized")
    
    def start(self):
        """Start the background worker"""
        if self.running:
            logger.warning("SimpleBackgroundWorker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_worker, daemon=True)
        self.thread.start()
        logger.info("SimpleBackgroundWorker started")
    
    def stop(self):
        """Stop the background worker"""
        self.running = False
        logger.info("SimpleBackgroundWorker stopped")
    
    def get_status(self):
        """Get worker status"""
        return {
            'running': self.running,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'api_base_url': self.api_base_url,
            'telegram_configured': bool(self.telegram_token)
        }
    
    def _run_worker(self):
        """Main worker loop"""
        logger.info("SimpleBackgroundWorker main loop started")
        
        while self.running:
            try:
                logger.info("🔄 Running simple alert check...")
                
                # Try to connect to main app
                try:
                    response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ Main app is reachable")
                    else:
                        logger.warning(f"⚠️ Main app returned status {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Cannot reach main app: {e}")
                
                # Check if we have Telegram token
                if self.telegram_token:
                    logger.info("✅ Telegram bot token is configured")
                else:
                    logger.warning("⚠️ No Telegram bot token configured")
                
                self.last_check = datetime.now()
                logger.info(f"✅ Simple alert check completed at {self.last_check}")
                
                # Wait 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in simple worker: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    """Main function to start the simple background worker"""
    try:
        logger.info("🚀 Starting FXSentinel Simple Background Worker v1.0.0 on Railway")
        
        # Log environment configuration
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        logger.info(f"🌐 API Base URL: {api_base_url}")
        
        # Check required environment variables
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token:
            logger.info(f"✅ TELEGRAM_BOT_TOKEN configured (length: {len(telegram_token)})")
        else:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not configured")
        
        logger.info("✅ Environment variables checked")
        
        # Start the simple background worker
        global background_worker
        worker = SimpleBackgroundWorker()
        worker.start()
        background_worker = worker.get_status()
        
        logger.info("✅ Simple background worker started successfully")
        logger.info("🔄 Worker is now monitoring...")
        
        # Start Flask app
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"🌐 Starting Flask app on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
                
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
    finally:
        logger.info("🔄 Simple background worker process ending")

if __name__ == "__main__":
    main()
