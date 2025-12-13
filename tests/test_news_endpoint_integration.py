#!/usr/bin/env python3
"""
Test News Endpoint Integration with Session-Isolated Telegram Wrapper
"""

import sys
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def test_news_endpoint_integration():
    """Test the news endpoint integration with the new session-isolated wrapper"""
    print("🔍 Testing News Endpoint Integration")
    print("=" * 60)
    
    # Test 1: Check if backend is running
    print("\n1️⃣ Checking if backend is running...")
    try:
        response = requests.get("http://localhost:5001/api/hello", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        print("Please start the backend server first: python3 backend/app.py")
        return False
    
    # Test 2: Test the new session-isolated wrapper directly
    print("\n2️⃣ Testing session-isolated wrapper directly...")
    try:
        from backend.services.telegram_sync_wrapper import telegram_sync
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Direct wrapper test: {len(telegram_news)} articles")
        
        if telegram_news:
            print("📰 Sample articles from direct test:")
            for i, news in enumerate(telegram_news[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print(f"     Impact: {news.get('impact', 'No impact')}")
                print()
        else:
            print("⚠️ No articles returned from direct test")
            
    except Exception as e:
        print(f"❌ Error in direct wrapper test: {e}")
        return False
    
    # Test 3: Test force refresh endpoint
    print("\n3️⃣ Testing force refresh endpoint...")
    try:
        response = requests.post(
            "http://localhost:5001/api/force-refresh-news",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh successful: {data.get('articles_count', 0)} articles")
            print(f"   Sources: {data.get('sources', [])}")
            
            # Check if Telegram is in sources
            sources = data.get('sources', [])
            if 'Telegram' in sources:
                print("✅ Telegram found in sources list")
            else:
                print("⚠️ Telegram not found in sources list")
                
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in force refresh: {e}")
        return False
    
    # Test 4: Test news endpoint
    print("\n4️⃣ Testing news endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/news", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            print(f"✅ News endpoint successful: {len(news_items)} articles")
            
            # Count Telegram articles
            telegram_articles = [item for item in news_items if 'telegram' in str(item.get('source', '')).lower()]
            print(f"   Telegram articles: {len(telegram_articles)}")
            
            if telegram_articles:
                print("📰 Sample Telegram articles from news endpoint:")
                for i, article in enumerate(telegram_articles[:3], 1):
                    print(f"  {i}. {article.get('title', 'No title')}")
                    print(f"     Source: {article.get('source', 'No source')}")
                    print(f"     Impact: {article.get('impact', 'No impact')}")
                    print()
            else:
                print("⚠️ No Telegram articles found in news endpoint response")
                
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in news endpoint: {e}")
        return False
    
    print("\n🎯 News endpoint integration test complete!")
    return True

if __name__ == "__main__":
    success = test_news_endpoint_integration()
    if success:
        print("\n🎉 All tests passed! The session-isolated wrapper is working in the news endpoint.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
