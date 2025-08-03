#!/usr/bin/env python3
"""
Vercel serverless function for FXSentinel
"""

import sys
import os

# Add the parent directory to the Python path to access backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the Flask app
from backend.app import app

# Export the Flask app for Vercel
handler = app 