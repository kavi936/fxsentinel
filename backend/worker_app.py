#!/usr/bin/env python3
"""
FXSentinel Background Worker Flask App
Provides health check endpoints while running the background worker
"""

import os
import sys
import threading
import time
import logging
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global worker reference
background_worker = None
worker_thread = None

@app.route('/')
def root():
    """Root endpoint"""
    return "FXSentinel Background Worker is running", 200

@app.route('/api/health')
def health():
    """Health check endpoint for Railway"""
    global background_worker
    
    status = {
        "status": "healthy",
        "service": "background-worker",
        "worker_running": background_worker is not None and background_worker.running if background_worker else False,
        "timestamp": time.time()
    }
    
    return jsonify(status), 200

def start_background_worker():
    """Start the background worker in a separate thread"""
    global background_worker, worker_thread
    
    try:
        logger.info("🚀 Starting FXSentinel Background Worker on Railway")
        
        # Check required environment variables
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set")
            return
        
        logger.info("✅ Environment variables configured")
        
        # Import and start the background worker
        from services.background_alert_worker import BackgroundAlertWorker
        
        background_worker = BackgroundAlertWorker()
        background_worker.start()
        
        logger.info("✅ Background worker started successfully")
        logger.info("🔄 Worker is now monitoring for alerts...")
        
    except Exception as e:
        logger.error(f"❌ Error starting background worker: {e}")
        import traceback
        traceback.print_exc()

def run_worker_monitor():
    """Monitor the background worker and restart if needed"""
    global background_worker
    
    while True:
        try:
            if background_worker and not background_worker.running:
                logger.warning("⚠️ Background worker stopped, restarting...")
                background_worker.start()
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"❌ Error in worker monitor: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # Start the background worker
    start_background_worker()
    
    # Start worker monitor in a separate thread
    monitor_thread = threading.Thread(target=run_worker_monitor, daemon=True)
    monitor_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
