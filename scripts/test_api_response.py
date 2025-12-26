#!/usr/bin/env python3
"""
Test what the /api/news endpoint actually returns
Simulates the endpoint to see the exact response format
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def simulate_api_response():
    """Simulate what /api/news returns"""
    print("=" * 60)
    print("SIMULATING /api/news RESPONSE")
    print("=" * 60)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        from services.telegram_sync_wrapper import telegram_sync
        
        cache = get_persistent_news_cache()
        
        # Simulate the endpoint logic
        print("\n1. Checking cache...")
        cached_news = cache.load_news()
        print(f"   Cached: {len(cached_news) if cached_news else 0} items")
        
        print("\n2. Fetching fresh news...")
        # Fetch RSS
        rss_news = news_aggregator.get_recent_news(hours=24)
        print(f"   RSS: {len(rss_news)} items")
        
        # Fetch alternative
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        print(f"   Alternative: {len(alt_news)} items")
        
        # Fetch Telegram (might fail locally)
        telegram_news = []
        try:
            telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
            print(f"   Telegram: {len(telegram_news)} items")
        except Exception as e:
            print(f"   Telegram: Failed ({e})")
        
        # Combine
        fresh_news = rss_news + alt_news + telegram_news
        print(f"   Total fresh: {len(fresh_news)} items")
        
        # Merge with cache if exists
        if cached_news:
            all_news = fresh_news + cached_news
        else:
            all_news = fresh_news
        
        # Deduplicate
        seen = {}
        unique_news = []
        for item in all_news:
            key = f"{item.get('title', '')}_{item.get('source', '')}"
            if key.lower() not in seen:
                seen[key.lower()] = item
                unique_news.append(item)
        
        print(f"\n3. After deduplication: {len(unique_news)} items")
        
        # Check for Telegram news
        telegram_items = [item for item in unique_news if 'telegram' in item.get('source', '').lower()]
        print(f"   Telegram items in response: {len(telegram_items)}")
        
        if telegram_items:
            print("\n   Telegram news items:")
            for i, item in enumerate(telegram_items[:3], 1):
                print(f"     {i}. {item.get('title', 'No title')[:60]}...")
                print(f"        Source: {item.get('source', 'Unknown')}")
                print(f"        Impact: {item.get('impact', 'Unknown')}")
                print(f"        ID: {item.get('id', 'No ID')}")
                print()
        
        # Simulate response format
        response_data = {
            "news": unique_news,
            "last_updated": datetime.now().isoformat(),
            "sources": ["RSS Feeds", "Alternative Sources", "Telegram"] if telegram_news else ["RSS Feeds", "Alternative Sources"],
            "total_articles": len(unique_news),
            "cache_status": "fresh"
        }
        
        print("\n4. Response structure:")
        print(f"   news: {len(response_data['news'])} items")
        print(f"   total_articles: {response_data['total_articles']}")
        print(f"   sources: {response_data['sources']}")
        print(f"   cache_status: {response_data['cache_status']}")
        
        # Check if all items have required fields
        print("\n5. Checking required fields...")
        missing_fields_count = 0
        for item in unique_news[:5]:  # Check first 5
            missing = []
            if not item.get('id'):
                missing.append('id')
            if not item.get('title'):
                missing.append('title')
            if not item.get('source'):
                missing.append('source')
            if not item.get('published_at'):
                missing.append('published_at')
            if not item.get('added_to_feed_at'):
                missing.append('added_to_feed_at')
            
            if missing:
                missing_fields_count += 1
                print(f"   Item missing: {missing}")
        
        if missing_fields_count == 0:
            print("   ✅ All items have required fields")
        
        # Check if Telegram items would pass frontend filter
        print("\n6. Frontend filter check...")
        def isForexRelevant(item):
            title = (item.get('title', '') or '').lower()
            summary = (item.get('summary', '') or '').lower()
            text = f"{title} {summary}"
            
            coreForexKeywords = ['fed', 'ecb', 'boj', 'boe', 'forex', 'currency']
            return any(keyword in text for keyword in coreForexKeywords)
        
        filtered_count = 0
        for item in telegram_items:
            if isForexRelevant(item):
                filtered_count += 1
        
        print(f"   Telegram items that pass filter: {filtered_count}/{len(telegram_items)}")
        
        return response_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run test"""
    print("\n" + "=" * 60)
    print("API RESPONSE TEST")
    print("=" * 60)
    print()
    
    response = simulate_api_response()
    
    if response:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Response would contain {response['total_articles']} articles")
        print(f"✅ Sources: {', '.join(response['sources'])}")
        print(f"✅ Cache status: {response['cache_status']}")
        print("\n💡 If news is not displaying:")
        print("   1. Check browser Network tab - is response 200 OK?")
        print("   2. Check response JSON - does it contain 'news' array?")
        print("   3. Check browser Console - any JavaScript errors?")
        print("   4. Check if frontend filter is removing items")

if __name__ == '__main__':
    main()

