#!/usr/bin/env python3
"""
FXSentinel Background Worker - Railway Entry Point
This is the definitive entry point for the background worker service on Railway.
"""

import os
import sys
import time
import logging
import threading
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

# Create Flask app for health checks
from flask import Flask, jsonify
app = Flask(__name__)

# Global worker reference
background_worker = None

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
        "timestamp": time.time(),
        "version": "3.0.0"  # Version bump to force cache refresh
    }
    
    return jsonify(status), 200

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start the background monitoring thread"""
    global background_worker
    
    try:
        if background_worker is None:
            # Import and create the worker
            from services.background_alert_worker import BackgroundAlertWorker
            background_worker = BackgroundAlertWorker()
            logger.info("📦 Background worker created")
        
        if not background_worker.running:
            background_worker.start()
            logger.info("✅ Background monitoring started")
            return jsonify({
                "success": True,
                "message": "Background monitoring started",
                "worker_running": background_worker.running
            }), 200
        else:
            return jsonify({
                "success": True,
                "message": "Background monitoring already running",
                "worker_running": background_worker.running
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Error starting monitoring: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def main():
    """Main function to start the background worker"""
    try:
        logger.info("🚀 Starting FXSentinel Background Worker v3.0.0 on Railway")
        logger.info("🔄 Cache-busting deployment - fresh code loaded")
        
        # Log environment configuration
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        logger.info(f"🌐 API Base URL: {api_base_url}")
        
        # Debug: Log environment variable status (without exposing the actual token)
        token_exists = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        token_value = os.getenv('TELEGRAM_BOT_TOKEN')
        logger.info(f"🔍 TELEGRAM_BOT_TOKEN exists: {token_exists}")
        if token_value:
            logger.info(f"🔍 TELEGRAM_BOT_TOKEN length: {len(token_value)} characters")
            logger.info(f"🔍 TELEGRAM_BOT_TOKEN starts with: {token_value[:10]}...")
        else:
            logger.warning("🔍 TELEGRAM_BOT_TOKEN is None or empty")
        
        # Log all environment variables that start with TELEGRAM or API
        telegram_vars = {k: v for k, v in os.environ.items() if k.startswith('TELEGRAM')}
        api_vars = {k: v for k, v in os.environ.items() if k.startswith('API')}
        logger.info(f"🔍 TELEGRAM-related env vars: {list(telegram_vars.keys())}")
        logger.info(f"🔍 API-related env vars: {list(api_vars.keys())}")
        
        # Check required environment variables
        required_vars = ['TELEGRAM_BOT_TOKEN']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.error("Please set these in your Railway environment variables")
            logger.error("🔧 Current environment variables:")
            for key, value in os.environ.items():
                if any(keyword in key.upper() for keyword in ['TELEGRAM', 'API', 'BOT', 'TOKEN']):
                    logger.error(f"   {key}: {'*' * len(value) if 'TOKEN' in key.upper() else value}")
            
            # Still start Flask app for health checks even without token
            logger.warning("⚠️ Starting Flask app in monitoring mode (no alerts will be sent)")
            port = int(os.environ.get('PORT', 8080))
            app.run(host='0.0.0.0', port=port, debug=False)
            return
        
        logger.info("✅ Environment variables configured")
        
        # Import and start the background worker
        try:
            # Import only the essential worker without heavy dependencies
            from services.background_alert_worker import BackgroundAlertWorker
            
            logger.info("📦 Background worker imported successfully")
            
            # Start the worker in a separate thread
            global background_worker
            background_worker = BackgroundAlertWorker()
            background_worker.start()  # This sets running=True internally
            
            logger.info("✅ Background worker started successfully")
            logger.info("🔄 Worker is now monitoring for alerts...")
            
            # Start Flask app
            port = int(os.environ.get('PORT', 8080))
            logger.info(f"🌐 Starting Flask app on port {port}")
            app.run(host='0.0.0.0', port=port, debug=False)
                
        except ImportError as e:
            logger.error(f"❌ Failed to import background worker: {e}")
            logger.error("Make sure all required services are available")
            # Still start Flask app for health checks
            port = int(os.environ.get('PORT', 8080))
            app.run(host='0.0.0.0', port=port, debug=False)
            return
        except Exception as e:
            logger.error(f"❌ Error starting background worker: {e}")
            # Still start Flask app for health checks
            port = int(os.environ.get('PORT', 8080))
            app.run(host='0.0.0.0', port=port, debug=False)
            return
            
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
    finally:
        logger.info("🔄 Background worker process ending")

if __name__ == "__main__":
    main()
