#!/usr/bin/env python3
"""
Vercel serverless function for FXSentinel
"""

import sys
import os
from flask import Flask, jsonify, request

# Create a simple Flask app for testing
app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'FXSentinel API is running',
        'timestamp': '2025-08-27T09:00:00Z'
    })

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        # For now, just return success to test the endpoint
        return jsonify({'success': True, 'message': 'Webhook received'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'Main API is working!',
        'status': 'success'
    })

# Try to import the full backend if available
try:
    # Add the parent directory to the Python path to access backend
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    
    # Import the Flask app
    from backend.app import app as backend_app
    
    # Use the backend app if import succeeds
    app = backend_app
    print("✅ Successfully imported backend app")
    
except ImportError as e:
    print(f"⚠️ Backend import failed: {e}")
    print("✅ Using simplified API endpoints")
    # Keep using the simplified app above

# Export the Flask app for Vercel
handler = app 