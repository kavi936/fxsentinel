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
        
        # Debug: Log environment variable status (without exposing the actual token)
        token_exists = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        token_value = os.getenv('TELEGRAM_BOT_TOKEN')
        logger.info(f"🔍 TELEGRAM_BOT_TOKEN exists: {token_exists}")
        if token_value:
            logger.info(f"🔍 TELEGRAM_BOT_TOKEN length: {len(token_value)} characters")
            logger.info(f"🔍 TELEGRAM_BOT_TOKEN starts with: {token_value[:10]}...")
        else:
            logger.warning("🔍 TELEGRAM_BOT_TOKEN is None or empty")
        
        # Log other important environment variables
        api_base_url = os.getenv('API_BASE_URL', 'Not set')
        port = os.getenv('PORT', 'Not set')
        logger.info(f"🌐 API_BASE_URL: {api_base_url}")
        logger.info(f"🚪 PORT: {port}")
        
        # Log all environment variables that start with TELEGRAM or API
        telegram_vars = {k: v for k, v in os.environ.items() if k.startswith('TELEGRAM')}
        api_vars = {k: v for k, v in os.environ.items() if k.startswith('API')}
        logger.info(f"🔍 TELEGRAM-related env vars: {list(telegram_vars.keys())}")
        logger.info(f"🔍 API-related env vars: {list(api_vars.keys())}")
        
        # Check if token is available
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set - worker will run in monitoring mode")
            logger.warning("🔧 Please check Railway environment variables configuration")
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
