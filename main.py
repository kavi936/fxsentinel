#!/usr/bin/env python3
"""
FXSentinel Background Worker Flask App
Railway auto-detection entry point that runs the background worker
"""

import os
import sys
import threading
import time
from flask import Flask

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Create Flask app for Railway detection
app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint for Railway"""
    return "FXSentinel Background Worker is running", 200

@app.route('/api/health')
def api_health():
    """API health check endpoint"""
    return {"status": "healthy", "service": "background-worker"}, 200

def start_background_worker():
    """Start the background worker in a separate thread"""
    try:
        from railway_worker import main
        # Run the background worker in a separate thread
        worker_thread = threading.Thread(target=main, daemon=True)
        worker_thread.start()
        print("✅ Background worker started in separate thread")
    except Exception as e:
        print(f"❌ Error starting background worker: {e}")

# Start the background worker when the Flask app starts
if __name__ == "__main__":
    start_background_worker()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
else:
    # When running with gunicorn, start the worker
    start_background_worker()
