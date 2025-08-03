#!/usr/bin/env python3
"""
Main entry point for the FXSentinel application.
This file helps Railway detect this as a Python application.
The actual application logic is in backend/app.py
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the main application
from backend.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 