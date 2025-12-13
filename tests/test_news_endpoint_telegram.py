#!/usr/bin/env python3
"""
Test News Endpoint Telegram Integration
Directly test the Telegram integration in the news endpoint
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

def test_news_endpoint_telegram():
    """Test the Telegram integration in the news endpoint"""
    print("🔍 Testing News Endpoint Telegram Integration")
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
        return False
    
    # Test 2: Test Telegram sync wrapper directly
    print("\n2️⃣ Testing Telegram sync wrapper directly...")
    try:
        from backend.services.telegram_sync_wrapper import telegram_sync
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Direct sync wrapper: {len(telegram_news)} articles")
        
        if telegram_news:
            print("📰 Sample Telegram articles:")
            for i, news in enumerate(telegram_news[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print(f"     Impact: {news.get('impact', 'No impact')}")
                print()
        else:
            print("❌ No Telegram news from sync wrapper")
            
    except Exception as e:
        print(f"❌ Error in sync wrapper: {e}")
        return False
    
    # Test 3: Call news endpoint with force refresh
    print("\n3️⃣ Calling news endpoint with force refresh...")
    try:
        response = requests.get("http://localhost:5001/api/news?force_refresh=true", timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News endpoint: {data.get('total_articles', 0)} articles")
            print(f"   Cache status: {data.get('cache_status', 'unknown')}")
            print(f"   Sources used: {data.get('sources', [])}")
            
            # Check for Telegram news
            news_items = data.get('news', [])
            telegram_news = [item for item in news_items if 'Telegram' in item.get('source', '')]
            
            print(f"   Telegram news count: {len(telegram_news)}")
            
            if telegram_news:
                print("📰 Telegram news found in endpoint:")
                for i, news in enumerate(telegram_news[:3], 1):
                    print(f"  {i}. {news.get('title', 'No title')}")
                    print(f"     Source: {news.get('source', 'No source')}")
                    print(f"     Impact: {news.get('impact', 'No impact')}")
                    print()
            else:
                print("❌ No Telegram news in endpoint response")
                
                # Show all sources
                sources = {}
                for item in news_items:
                    source = item.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                print("📊 All sources in response:")
                for source, count in sorted(sources.items()):
                    print(f"  {source}: {count} articles")
                    
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in news endpoint: {e}")
        return False
    
    print("\n🎯 Test completed!")
    return True

if __name__ == "__main__":
    success = test_news_endpoint_telegram()
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
