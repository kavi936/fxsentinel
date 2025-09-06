#!/usr/bin/env python3
"""
Minimal Test Worker
Absolute minimal version to test Railway deployment
"""

import os
from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.route('/')
def root():
    return "FXSentinel Minimal Test Worker - OK", 200

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "minimal-test-worker",
        "timestamp": time.time(),
        "version": "1.0.0"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting minimal test worker on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
