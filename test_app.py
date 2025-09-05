#!/usr/bin/env python3
"""
Ultra-simple test app for Railway deployment
"""

import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from Railway! Test app is working."

@app.route('/api/health')
def health():
    return {"status": "ok", "message": "Test app is running"}, 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting test app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
