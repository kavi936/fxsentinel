#!/usr/bin/env python3
"""
Test script to verify all dependencies are available
Run this before deployment to catch import errors
"""

import sys
import os

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import flask_cors
        print("✅ Flask-CORS imported successfully")
    except ImportError as e:
        print(f"❌ Flask-CORS import failed: {e}")
        return False
    
    try:
        import requests
        print("✅ Requests imported successfully")
    except ImportError as e:
        print(f"❌ Requests import failed: {e}")
        return False
    
    try:
        import bs4
        print("✅ BeautifulSoup4 imported successfully")
    except ImportError as e:
        print(f"❌ BeautifulSoup4 import failed: {e}")
        return False
    
    try:
        import gunicorn
        print("✅ Gunicorn imported successfully")
    except ImportError as e:
        print(f"❌ Gunicorn import failed: {e}")
        return False
    
    try:
        import openai
        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    try:
        import dotenv
        print("✅ Python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ Python-dotenv import failed: {e}")
        return False
    
    try:
        import feedparser
        print("✅ Feedparser imported successfully")
    except ImportError as e:
        print(f"❌ Feedparser import failed: {e}")
        return False
    
    try:
        import telethon
        print("✅ Telethon imported successfully")
    except ImportError as e:
        print(f"❌ Telethon import failed: {e}")
        return False
    
    try:
        import telegram
        print("✅ Python-telegram-bot imported successfully")
    except ImportError as e:
        print(f"❌ Python-telegram-bot import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    # Test service imports
    try:
        from services import news_aggregator
        print("✅ News aggregator service imported successfully")
    except ImportError as e:
        print(f"❌ News aggregator service import failed: {e}")
        return False
    
    try:
        from services import local_ai_analysis
        print("✅ Local AI analysis service imported successfully")
    except ImportError as e:
        print(f"❌ Local AI analysis service import failed: {e}")
        return False
    
    try:
        from services import news_sentiment_analyzer
        print("✅ News sentiment analyzer service imported successfully")
    except ImportError as e:
        print(f"❌ News sentiment analyzer service import failed: {e}")
        return False
    
    try:
        from services import technical_analysis_service
        print("✅ Technical analysis service imported successfully")
    except ImportError as e:
        print(f"❌ Technical analysis service import failed: {e}")
        return False
    
    try:
        from services import finnhub_calendar
        print("✅ Finnhub calendar service imported successfully")
    except ImportError as e:
        print(f"❌ Finnhub calendar service import failed: {e}")
        return False
    
    try:
        from services import finnhub_historical
        print("✅ Finnhub historical service imported successfully")
    except ImportError as e:
        print(f"❌ Finnhub historical service import failed: {e}")
        return False
    
    try:
        from services import telegram_monitor_user
        print("✅ Telegram monitor user service imported successfully")
    except ImportError as e:
        print(f"❌ Telegram monitor user service import failed: {e}")
        return False
    
    try:
        from services import news_cache
        print("✅ News cache service imported successfully")
    except ImportError as e:
        print(f"❌ News cache service import failed: {e}")
        return False
    
    try:
        from services import alternative_news_sources
        print("✅ Alternative news sources service imported successfully")
    except ImportError as e:
        print(f"❌ Alternative news sources service import failed: {e}")
        return False
    
    try:
        from services import enhanced_forex_filter
        print("✅ Enhanced forex filter service imported successfully")
    except ImportError as e:
        print(f"❌ Enhanced forex filter service import failed: {e}")
        return False
    
    print("\n🎉 All imports successful!")
    return True

def test_app_creation():
    """Test if the Flask app can be created"""
    print("\nTesting Flask app creation...")
    
    try:
        # Import the app
        from app import app
        print("✅ Flask app imported successfully")
        
        # Test basic app functionality
        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Testing FXSentinel Backend Dependencies")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test app creation
        app_ok = test_app_creation()
        
        if app_ok:
            print("\n✅ All tests passed! Backend is ready for deployment.")
            sys.exit(0)
        else:
            print("\n❌ App creation failed. Check the Flask app configuration.")
            sys.exit(1)
    else:
        print("\n❌ Import tests failed. Check requirements.txt and dependencies.")
        sys.exit(1)
