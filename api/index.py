#!/usr/bin/env python3
"""
Vercel serverless function for FXSentinel
"""

import sys
import os

# Add the parent directory to the Python path to access backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    # Import the Flask app
    from backend.app import app
    
    # Export the Flask app for Vercel
    handler = app
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback handler if import fails
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            "message": "FXSentinel API - Import Error",
            "error": str(e),
            "status": "error"
        })
    
    handler = app 