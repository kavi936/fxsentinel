#!/usr/bin/env python3
"""
Debug script to test Telegram access on production server
"""

import requests
import json

def test_telegram_debug():
    """Test Telegram debugging on production server"""
    
    print("🔍 Debugging Production Telegram Integration")
    print("=" * 50)
    
    # Test 1: Check if there's a specific Telegram debug endpoint
    print("\n1️⃣ Testing Telegram Debug Endpoint...")
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/health/telegram", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Telegram health: {data}")
        else:
            print(f"❌ Telegram health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram health error: {e}")
    
    # Test 2: Check if we can force a Telegram-only refresh
    print("\n2️⃣ Testing Telegram-Only Refresh...")
    try:
        # Try to trigger a force refresh and see if we get more detailed logs
        response = requests.post("https://fxsentinel-production.up.railway.app/api/force-refresh-news", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh response: {data}")
            
            # Check if the response includes any error information
            if 'alert_results' in data and 'errors' in data['alert_results']:
                errors = data['alert_results']['errors']
                if errors:
                    print(f"⚠️ Errors found: {errors}")
                else:
                    print("✅ No errors reported")
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Force refresh error: {e}")
    
    # Test 3: Check if we can access the news endpoint with force refresh parameter
    print("\n3️⃣ Testing News Endpoint with Force Refresh...")
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news?force_refresh=true", timeout=60)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            telegram_news = [n for n in news_items if 'Telegram' in n.get('source', '')]
            print(f"✅ News with force refresh: {len(news_items)} total articles")
            print(f"📱 Telegram articles: {len(telegram_news)}")
            print(f"📊 Cache status: {data.get('cache_status', 'unknown')}")
            print(f"📋 Sources used: {data.get('sources', [])}")
        else:
            print(f"❌ News with force refresh failed: {response.status_code}")
    except Exception as e:
        print(f"❌ News with force refresh error: {e}")

if __name__ == "__main__":
    test_telegram_debug()
