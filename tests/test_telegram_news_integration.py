#!/usr/bin/env python3
"""
Test Telegram News Integration
Debug why WatcherGuru alerts aren't appearing in the live news feed
"""

import sys
import os
import asyncio
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

async def test_telegram_integration():
    """Test the complete Telegram news integration flow"""
    print("🔍 Testing Telegram News Integration")
    print("=" * 50)
    
    # Step 1: Test direct Telegram fetch
    print("\n1️⃣ Testing direct Telegram fetch...")
    try:
        from backend.services.telegram_monitor_user import telegram_user_monitor
        
        # Test getting recent news
        recent_news = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        print(f"✅ Direct Telegram fetch: {len(recent_news)} articles")
        
        if recent_news:
            print("📰 Sample Telegram articles:")
            for i, news in enumerate(recent_news[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print(f"     Impact: {news.get('impact', 'No impact')}")
                print(f"     Type: {news.get('type', 'No type')}")
                print()
        else:
            print("❌ No Telegram news found")
            
    except Exception as e:
        print(f"❌ Error in direct Telegram fetch: {e}")
        return False
    
    # Step 2: Test sync wrapper
    print("\n2️⃣ Testing sync wrapper...")
    try:
        from backend.services.telegram_sync_wrapper import telegram_sync
        
        sync_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Sync wrapper: {len(sync_news)} articles")
        
        if sync_news:
            print("📰 Sample sync wrapper articles:")
            for i, news in enumerate(sync_news[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print()
        else:
            print("❌ No sync wrapper news found")
            
    except Exception as e:
        print(f"❌ Error in sync wrapper: {e}")
        return False
    
    # Step 3: Test force refresh endpoint
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
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in force refresh: {e}")
        return False
    
    # Step 4: Test news endpoint
    print("\n4️⃣ Testing news endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/news?force_refresh=true", timeout=30)
        
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
                print("📰 Telegram news found:")
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
    
    print("\n🎯 Integration test completed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_telegram_integration())
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
