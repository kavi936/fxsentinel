#!/usr/bin/env python3
"""
Test local Telegram integration in the Flask server
"""

import requests
import json
import time

def test_local_telegram():
    """Test Telegram integration on local server"""
    
    print("🔍 Testing Local Telegram Integration")
    print("=" * 50)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    # Test 1: Check if server is running
    print("\n1️⃣ Testing server connection...")
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Force refresh to clear cache
    print("\n2️⃣ Testing force refresh...")
    try:
        response = requests.post("http://localhost:5001/api/force-refresh-news", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh: {data.get('articles_count', 0)} articles")
            print(f"📊 Message: {data.get('message', '')}")
            
            # Check if there are any errors
            alert_results = data.get('alert_results', {})
            errors = alert_results.get('errors', [])
            if errors:
                print(f"⚠️ Errors: {errors}")
            else:
                print("✅ No errors reported")
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Force refresh error: {e}")
    
    # Test 3: Check news endpoint
    print("\n3️⃣ Testing news endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/news", timeout=30)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            telegram_news = [n for n in news_items if 'Telegram' in n.get('source', '')]
            
            print(f"✅ News endpoint: {len(news_items)} total articles")
            print(f"📱 Telegram articles: {len(telegram_news)}")
            print(f"📊 Cache status: {data.get('cache_status', 'unknown')}")
            print(f"📋 Sources: {data.get('sources', [])}")
            
            if telegram_news:
                print("📰 Telegram articles found:")
                for i, news in enumerate(telegram_news[:3]):
                    print(f"   {i+1}. {news.get('title', 'No title')}")
            else:
                print("❌ No Telegram articles found")
                
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ News endpoint error: {e}")
    
    # Test 4: Check if we can access the Telegram service directly
    print("\n4️⃣ Testing direct Telegram service...")
    try:
        import sys
        sys.path.append('backend')
        from services.telegram_monitor_user import telegram_user_monitor
        import asyncio
        
        # Test direct access
        result = asyncio.run(telegram_user_monitor.get_recent_telegram_news(hours=24))
        print(f"✅ Direct Telegram service: {len(result)} articles")
        
        if result:
            print("📰 Sample articles:")
            for i, news in enumerate(result[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
        else:
            print("❌ No articles from direct service")
            
    except Exception as e:
        print(f"❌ Direct service error: {e}")

if __name__ == "__main__":
    test_local_telegram()
