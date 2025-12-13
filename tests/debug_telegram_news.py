#!/usr/bin/env python3
"""
Debug Telegram News Processing
Trace what happens to Telegram news during force refresh
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

def debug_telegram_news_processing():
    """Debug the complete Telegram news processing flow"""
    print("🔍 Debugging Telegram News Processing")
    print("=" * 50)
    
    # Step 1: Get Telegram news directly
    print("\n1️⃣ Getting Telegram news directly...")
    try:
        from backend.services.telegram_sync_wrapper import telegram_sync
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Direct Telegram fetch: {len(telegram_news)} articles")
        
        if telegram_news:
            print("📰 Sample Telegram articles:")
            for i, news in enumerate(telegram_news[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print(f"     Impact: {news.get('impact', 'No impact')}")
                print(f"     Type: {news.get('type', 'No type')}")
                print()
    except Exception as e:
        print(f"❌ Error in direct Telegram fetch: {e}")
        return False
    
    # Step 2: Test deduplication logic
    print("\n2️⃣ Testing deduplication logic...")
    try:
        # Simulate the deduplication logic from force refresh
        def remove_duplicate_news(news_list):
            """Remove duplicate news items based on title and source"""
            seen = set()
            unique_news = []
            for item in news_list:
                # Create a unique key based on title and source
                key = f"{item.get('title', '')}_{item.get('source', '')}"
                if key not in seen:
                    seen.add(key)
                    unique_news.append(item)
                else:
                    print(f"   🔄 Duplicate removed: {item.get('title', 'No title')} ({item.get('source', 'No source')})")
            return unique_news
        
        # Test with just Telegram news
        unique_telegram = remove_duplicate_news(telegram_news)
        print(f"✅ After deduplication: {len(unique_telegram)} articles (from {len(telegram_news)})")
        
        if len(unique_telegram) < len(telegram_news):
            print("📊 Duplicates found and removed:")
            for i, news in enumerate(telegram_news):
                key = f"{news.get('title', '')}_{news.get('source', '')}"
                print(f"  {i+1}. {news.get('title', 'No title')} ({news.get('source', 'No source')})")
        
    except Exception as e:
        print(f"❌ Error in deduplication test: {e}")
        return False
    
    # Step 3: Test force refresh and check results
    print("\n3️⃣ Testing force refresh...")
    try:
        response = requests.post(
            "http://localhost:5001/api/force-refresh-news",
            headers={"Content-Type": "application/json"},
            timeout=60
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
    
    # Step 4: Check final news feed
    print("\n4️⃣ Checking final news feed...")
    try:
        response = requests.get("http://localhost:5001/api/news?force_refresh=true", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News endpoint: {data.get('total_articles', 0)} articles")
            print(f"   Cache status: {data.get('cache_status', 'unknown')}")
            print(f"   Sources used: {data.get('sources', [])}")
            
            # Check for Telegram news
            news_items = data.get('news', [])
            telegram_news_in_feed = [item for item in news_items if 'Telegram' in item.get('source', '')]
            
            print(f"   Telegram news in feed: {len(telegram_news_in_feed)}")
            
            if telegram_news_in_feed:
                print("📰 Telegram news found in feed:")
                for i, news in enumerate(telegram_news_in_feed[:3], 1):
                    print(f"  {i}. {news.get('title', 'No title')}")
                    print(f"     Source: {news.get('source', 'No source')}")
                    print(f"     Impact: {news.get('impact', 'No impact')}")
                    print()
            else:
                print("❌ No Telegram news in final feed")
                
                # Show all sources
                sources = {}
                for item in news_items:
                    source = item.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                print("📊 All sources in final feed:")
                for source, count in sorted(sources.items()):
                    print(f"  {source}: {count} articles")
                    
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in news endpoint: {e}")
        return False
    
    print("\n🎯 Debug completed!")
    return True

if __name__ == "__main__":
    success = debug_telegram_news_processing()
    
    if success:
        print("\n✅ Debug completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Debug failed!")
        sys.exit(1)
