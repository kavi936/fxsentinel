#!/usr/bin/env python3
"""
Simple test endpoint for Vercel Python function
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'message': 'Python API is working!',
        'status': 'success',
        'timestamp': '2025-08-27T09:00:00Z'
    })

@app.route('/api/test', methods=['POST'])
def test_post():
    return jsonify({
        'message': 'Python API POST is working!',
        'status': 'success',
        'timestamp': '2025-08-27T09:00:00Z'
    })

# Export for Vercel
handler = app
