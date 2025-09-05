#!/usr/bin/env python3
"""
Simple Background Worker for Railway
Minimal implementation that avoids all build-time token access
"""

import os
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

@app.route('/')
def root():
    """Root endpoint"""
    return "FXSentinel Background Worker is running", 200

@app.route('/api/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({
        "status": "healthy",
        "service": "background-worker",
        "timestamp": time.time()
    }), 200

def start_worker():
    """Start the background worker"""
    try:
        logger.info("🚀 Starting FXSentinel Background Worker")
        
        # Check if token is available
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set - worker will run in monitoring mode")
            return
        
        logger.info("✅ Environment variables configured")
        
        # Import and start the actual worker only when token is available
        try:
            from services.background_alert_worker import BackgroundAlertWorker
            worker = BackgroundAlertWorker()
            worker.start()
            logger.info("✅ Background worker started successfully")
        except Exception as e:
            logger.error(f"❌ Error starting background worker: {e}")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    # Start the worker
    start_worker()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
