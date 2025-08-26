#!/usr/bin/env python3
"""
Test script to check Telegram integration on production server
"""

import requests
import json

def test_production_telegram():
    """Test Telegram integration on production server"""
    
    print("🔍 Testing Production Telegram Integration")
    print("=" * 50)
    
    # Test 1: Check if force refresh includes Telegram
    print("\n1️⃣ Testing Force Refresh Endpoint...")
    try:
        response = requests.post("https://fxsentinel-production.up.railway.app/api/force-refresh-news", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh successful: {data.get('articles_count', 0)} articles")
            print(f"📊 Alert results: {data.get('alert_results', {})}")
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Force refresh error: {e}")
    
    # Test 2: Check regular news endpoint
    print("\n2️⃣ Testing Regular News Endpoint...")
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news", timeout=30)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            telegram_news = [n for n in news_items if 'Telegram' in n.get('source', '')]
            print(f"✅ News endpoint: {len(news_items)} total articles")
            print(f"📱 Telegram articles: {len(telegram_news)}")
            if telegram_news:
                print("📰 Sample Telegram articles:")
                for i, news in enumerate(telegram_news[:3]):
                    print(f"   {i+1}. {news.get('title', 'No title')}")
            else:
                print("❌ No Telegram articles found")
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ News endpoint error: {e}")
    
    # Test 3: Check health endpoint for Telegram status
    print("\n3️⃣ Testing Health Endpoint...")
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            telegram_status = data.get('telegram_monitor', {})
            print(f"✅ Health check: {telegram_status}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    test_production_telegram()
