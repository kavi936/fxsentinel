#!/usr/bin/env python3
"""
Test if cache is updating consistently
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_cache_update():
    """Test cache update mechanism"""
    print("=" * 100)
    print("TESTING CACHE UPDATE MECHANISM")
    print("=" * 100)
    print()
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        from services.telegram_sync_wrapper import telegram_sync
        
        news_cache = get_persistent_news_cache()
        
        # Step 1: Check current cache state
        print("1. CHECKING CURRENT CACHE STATE")
        print("-" * 100)
        cached_news = news_cache.load_news()
        print(f"   Cached articles: {len(cached_news) if cached_news else 0}")
        
        should_fetch = news_cache.should_fetch_new_news(fetch_interval_minutes=5)
        print(f"   Should fetch new: {should_fetch}")
        print()
        
        # Step 2: Fetch fresh news
        print("2. FETCHING FRESH NEWS")
        print("-" * 100)
        rss_news = news_aggregator.get_recent_news(hours=24)
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24) if telegram_sync.enabled else []
        
        fresh_news = rss_news + alt_news + telegram_news
        print(f"   Fresh news: {len(fresh_news)} articles")
        print()
        
        # Step 3: Simulate the merge logic from app.py
        print("3. SIMULATING CACHE UPDATE")
        print("-" * 100)
        
        if cached_news and should_fetch:
            print(f"   Merging {len(fresh_news)} fresh with {len(cached_news)} cached...")
            all_news = fresh_news + cached_news
            
            # Deduplicate
            seen = {}
            unique_news = []
            for item in all_news:
                key = f"{item.get('title', '')}_{item.get('source', '')}"
                if key not in seen:
                    seen[key] = item
                    unique_news.append(item)
            
            all_news = unique_news
            print(f"   After deduplication: {len(all_news)} articles")
            
            # Set added_to_feed_at
            current_time = datetime.now().isoformat()
            cached_keys = {f"{item.get('title', '')}_{item.get('source', '')}" for item in cached_news}
            
            for item in all_news:
                key = f"{item.get('title', '')}_{item.get('source', '')}"
                if key not in cached_keys and 'added_to_feed_at' not in item:
                    item['added_to_feed_at'] = current_time
            
            # Sort
            all_news.sort(key=lambda x: x.get('added_to_feed_at') or x.get('published_at') or '', reverse=True)
            
            print(f"   Ready to save: {len(all_news)} articles")
        else:
            all_news = fresh_news
            print(f"   No cache or shouldn't fetch - using fresh only: {len(all_news)} articles")
        
        print()
        
        # Step 4: Save to cache
        print("4. SAVING TO CACHE")
        print("-" * 100)
        save_success = news_cache.save_news(all_news, append=False)
        
        if save_success:
            print(f"   ✅ Successfully saved {len(all_news)} articles to cache")
        else:
            print(f"   ❌ Failed to save to cache (Firebase error)")
            return
        
        print()
        
        # Step 5: Verify cache was updated
        print("5. VERIFYING CACHE UPDATE")
        print("-" * 100)
        updated_cache = news_cache.load_news()
        print(f"   Cached articles after save: {len(updated_cache) if updated_cache else 0}")
        
        if updated_cache:
            # Check most recent
            updated_cache.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            print(f"   Most recent article: {updated_cache[0].get('title', 'No title')[:60]}...")
            print(f"   Published: {updated_cache[0].get('published_at', 'N/A')}")
        
        print()
        
        # Step 6: Check cache metadata
        print("6. CACHE METADATA")
        print("-" * 100)
        cache_path = news_cache._get_cache_path()
        cache_data = news_cache.firebase._make_request('GET', cache_path)
        
        if cache_data:
            print(f"   Timestamp: {cache_data.get('timestamp', 'N/A')}")
            print(f"   Last fetch: {cache_data.get('last_fetch', 'N/A')}")
            print(f"   News count: {cache_data.get('news_count', 0)}")
            print(f"   Max age hours: {cache_data.get('max_age_hours', 'N/A')}")
        else:
            print("   ❌ No cache data found in Firebase")
        
        print()
        print("=" * 100)
        print("SUMMARY")
        print("=" * 100)
        
        if save_success and updated_cache:
            print("✅ Cache update mechanism is working correctly")
            print(f"   Cache now contains {len(updated_cache)} articles")
            print("   Cache will update every 5 minutes when /api/news is called")
        else:
            print("❌ Cache update mechanism has issues")
            if not save_success:
                print("   - Failed to save to Firebase")
            if not updated_cache:
                print("   - Cache is empty after save")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cache_update()

