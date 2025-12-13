#!/usr/bin/env python3
"""
Trace Complete News Flow
Trace the entire process from Telegram fetch to live news feed display
"""

import sys
import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def trace_news_flow():
    """Trace the complete news flow process"""
    print("🔍 Tracing Complete News Flow Process")
    print("=" * 60)
    
    # Step 1: Check backend status
    print("\n1️⃣ Backend Status Check")
    print("-" * 30)
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
    
    # Step 2: Test Telegram sync wrapper directly
    print("\n2️⃣ Telegram Sync Wrapper Test")
    print("-" * 30)
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
                print(f"     Type: {news.get('type', 'No type')}")
                print()
        else:
            print("❌ No Telegram news from sync wrapper")
            
    except Exception as e:
        print(f"❌ Error in sync wrapper: {e}")
        return False
    
    # Step 3: Test force refresh endpoint
    print("\n3️⃣ Force Refresh Endpoint Test")
    print("-" * 30)
    try:
        response = requests.post(
            "http://localhost:5001/api/force-refresh-news",
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh: {data.get('articles_count', 0)} articles")
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Sources: {data.get('sources', [])}")
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in force refresh: {e}")
        return False
    
    # Step 4: Test news endpoint with force refresh
    print("\n4️⃣ News Endpoint Test (with force refresh)")
    print("-" * 30)
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
    
    # Step 5: Test news endpoint without force refresh (cached)
    print("\n5️⃣ News Endpoint Test (cached)")
    print("-" * 30)
    try:
        response = requests.get("http://localhost:5001/api/news", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cached news: {data.get('total_articles', 0)} articles")
            print(f"   Cache status: {data.get('cache_status', 'unknown')}")
            print(f"   Sources: {data.get('sources', [])}")
            
            # Check for Telegram news
            news_items = data.get('news', [])
            telegram_news = [item for item in news_items if 'Telegram' in item.get('source', '')]
            
            print(f"   Telegram news count: {len(telegram_news)}")
            
            if telegram_news:
                print("📰 Telegram news found in cached response:")
                for i, news in enumerate(telegram_news[:3], 1):
                    print(f"  {i}. {news.get('title', 'No title')}")
                    print(f"     Source: {news.get('source', 'No source')}")
                    print()
                    
        else:
            print(f"❌ Cached news endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in cached news endpoint: {e}")
        return False
    
    # Step 6: Test frontend news feed component
    print("\n6️⃣ Frontend News Feed Test")
    print("-" * 30)
    try:
        # Check if the frontend is accessible
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
        else:
            print(f"⚠️ Frontend not accessible: {response.status_code}")
            print("   (This is expected if frontend is not running)")
    except Exception as e:
        print(f"⚠️ Frontend not accessible: {e}")
        print("   (This is expected if frontend is not running)")
    
    print("\n🎯 News Flow Analysis Complete!")
    return True

if __name__ == "__main__":
    success = trace_news_flow()
    
    if success:
        print("\n✅ News flow trace completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ News flow trace failed!")
        sys.exit(1)
