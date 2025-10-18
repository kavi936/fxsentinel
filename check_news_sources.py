#!/usr/bin/env python3
"""
Check news sources and fetch current news
"""

import requests
import json
from datetime import datetime, timedelta
import time

def check_news_sources():
    """Check news sources and fetch current news"""
    print("🔍 Checking News Sources and Current Feed")
    print("=" * 50)
    print(f"📅 Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    # Test different news endpoints
    endpoints_to_test = [
        "/api/news",
        "/api/news?force_refresh=true",
        "/api/news-history?hours=24",
        "/api/dashboard-data"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"🧪 Testing endpoint: {endpoint}")
        try:
            response = requests.get(f"{main_app_url}{endpoint}", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {response.status_code}")
                
                if 'news' in data:
                    news_count = len(data.get('news', []))
                    print(f"   📊 News items: {news_count}")
                    
                    if news_count > 0:
                        print("   🔍 Sample news items:")
                        for i, item in enumerate(data['news'][:3]):
                            title = item.get('title', '')
                            source = item.get('source', '')
                            published = item.get('published_at', '')
                            print(f"      {i+1}. {title[:60]}... ({source})")
                elif 'dashboard' in data and 'news' in data['dashboard']:
                    news_count = len(data['dashboard'].get('news', []))
                    print(f"   📊 Dashboard news items: {news_count}")
                else:
                    print(f"   📊 Response keys: {list(data.keys())}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   📋 Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()
    
    # Try to trigger news refresh manually
    print("🔄 Attempting to trigger news refresh...")
    try:
        # Try the force refresh endpoint
        response = requests.get(f"{main_app_url}/api/news?force_refresh=true", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh successful")
            print(f"📊 News items after refresh: {len(data.get('news', []))}")
            
            if data.get('news'):
                print("🔍 Latest news items:")
                for i, item in enumerate(data['news'][:5]):
                    title = item.get('title', '')
                    source = item.get('source', '')
                    published = item.get('published_at', '')
                    impact = item.get('impact', '')
                    print(f"   {i+1}. {title[:70]}...")
                    print(f"      📰 {source} | 📅 {published} | 🎯 {impact}")
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error during force refresh: {e}")
    
    print()
    print("🔍 **Alternative News Sources Check:**")
    print("=" * 40)
    
    # Check if we can access news sources directly
    news_sources = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://www.forexfactory.com/rss.php"
    ]
    
    for source in news_sources:
        try:
            response = requests.get(source, timeout=10)
            if response.status_code == 200:
                print(f"✅ {source}: Accessible")
            else:
                print(f"❌ {source}: {response.status_code}")
        except Exception as e:
            print(f"❌ {source}: {e}")

def check_worker_news_processing():
    """Check if the worker is processing news correctly"""
    print("🔧 **Worker News Processing Check:**")
    print("=" * 40)
    
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    
    try:
        # Trigger the worker to process news
        response = requests.post(f"{worker_url}/api/trigger-alerts", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Worker trigger successful")
            print(f"📊 News processed: {result.get('news_alerts_processed', False)}")
            print(f"📊 Calendar processed: {result.get('calendar_alerts_processed', False)}")
            print(f"📅 Timestamp: {result.get('timestamp', '')}")
            
            # If news was processed, there should be alerts
            if result.get('news_alerts_processed'):
                print("✅ News processing is working - alerts should be sent")
            else:
                print("⚠️  News processing returned false - no new alerts")
        else:
            print(f"❌ Worker trigger failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking worker: {e}")

if __name__ == "__main__":
    check_news_sources()
    print()
    check_worker_news_processing()
