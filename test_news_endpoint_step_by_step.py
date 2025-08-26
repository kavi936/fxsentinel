#!/usr/bin/env python3
"""
Test News Endpoint Step by Step
Step through the news endpoint logic to see where Telegram news is being lost
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

def test_news_endpoint_step_by_step():
    """Test the news endpoint step by step"""
    print("🔍 Testing News Endpoint Step by Step")
    print("=" * 50)
    
    # Step 1: Test Telegram sync wrapper directly
    print("\n1️⃣ Testing Telegram sync wrapper directly...")
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
    
    # Step 2: Test RSS and alternative news
    print("\n2️⃣ Testing RSS and alternative news...")
    try:
        from backend.services.news_aggregator import news_aggregator
        from backend.services.alternative_news_sources import alternative_news_sources
        
        rss_news = news_aggregator.get_recent_news(hours=24)
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        
        print(f"✅ RSS news: {len(rss_news)} articles")
        print(f"✅ Alternative news: {len(alt_news)} articles")
        
        # Combine all news
        all_news = rss_news + alt_news + telegram_news
        print(f"📊 Combined news before deduplication: {len(all_news)} articles")
        
        # Test deduplication
        from backend.app import remove_duplicate_news
        unique_news = remove_duplicate_news(all_news)
        print(f"📊 Combined news after deduplication: {len(unique_news)} articles")
        
        # Check for Telegram news
        telegram_in_unique = [news for news in unique_news if 'Telegram' in news.get('source', '')]
        print(f"📊 Telegram news in unique list: {len(telegram_in_unique)} articles")
        
        if telegram_in_unique:
            print("📰 Telegram news in unique list:")
            for i, news in enumerate(telegram_in_unique[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print()
        else:
            print("❌ No Telegram news in unique list")
            
    except Exception as e:
        print(f"❌ Error in news aggregation: {e}")
        return False
    
    # Step 3: Test news endpoint response
    print("\n3️⃣ Testing news endpoint response...")
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
    
    print("\n🎯 Step-by-step analysis complete!")
    return True

if __name__ == "__main__":
    success = test_news_endpoint_step_by_step()
    
    if success:
        print("\n✅ Step-by-step test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Step-by-step test failed!")
        sys.exit(1)
