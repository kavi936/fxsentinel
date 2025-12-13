#!/usr/bin/env python3
"""
Simple FXSentinel Background Worker - Railway Entry Point
This is a simplified version to test Railway deployment.
"""

import os
import sys
import time
import logging
from datetime import datetime

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
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def root():
    """Root endpoint"""
    return "FXSentinel Background Worker v2.0.0 is running", 200

@app.route('/api/health')
def health():
    """Health check endpoint for Railway"""
    status = {
        "status": "healthy",
        "service": "background-worker-v2",
        "worker_running": True,
        "timestamp": time.time(),
        "version": "2.0.0",
        "environment": {
            "telegram_token_set": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            "api_base_url": os.getenv('API_BASE_URL', 'Not set'),
            "port": os.getenv('PORT', 'Not set')
        }
    }
    
    return jsonify(status), 200

def main():
    """Main function to start the simple worker"""
    try:
        logger.info("🚀 Starting FXSentinel Simple Background Worker v2.0.0 on Railway")
        logger.info("🔄 This is a test deployment to verify Railway configuration")
        
        # Log environment configuration
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        logger.info(f"🌐 API Base URL: {api_base_url}")
        
        # Debug: Log environment variable status
        token_exists = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        logger.info(f"🔍 TELEGRAM_BOT_TOKEN exists: {token_exists}")
        
        if token_exists:
            token_value = os.getenv('TELEGRAM_BOT_TOKEN')
            logger.info(f"🔍 TELEGRAM_BOT_TOKEN length: {len(token_value)} characters")
            logger.info(f"🔍 TELEGRAM_BOT_TOKEN starts with: {token_value[:10]}...")
        else:
            logger.warning("🔍 TELEGRAM_BOT_TOKEN is None or empty")
        
        logger.info("✅ Simple worker configuration complete")
        logger.info("🌐 Starting Flask app...")
        
        # Start Flask app
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"🌐 Starting Flask app on port {port}")
        logger.info(f"🌐 Host: 0.0.0.0, Port: {port}")
        logger.info(f"🌐 Environment PORT: {os.environ.get('PORT', 'Not set')}")
        app.run(host='0.0.0.0', port=port, debug=False)
            
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
    finally:
        logger.info("🔄 Simple background worker process ending")

if __name__ == "__main__":
    main()
