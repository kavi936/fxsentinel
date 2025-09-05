#!/usr/bin/env python3
"""
FXSentinel Background Worker Entry Point
Railway auto-detection entry point for the background worker service
"""

import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the railway worker
if __name__ == "__main__":
    from railway_worker import main
    main()
