#!/usr/bin/env python3
"""
Test if new news is being saved to cache correctly
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_cache_save():
    """Test cache save functionality"""
    print("=" * 100)
    print("TESTING CACHE SAVE FUNCTIONALITY")
    print("=" * 100)
    print()
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        from services.telegram_sync_wrapper import telegram_sync
        
        news_cache = get_persistent_news_cache()
        
        # Step 1: Check current cache
        print("1. CHECKING CURRENT CACHE")
        print("-" * 100)
        cached_news = news_cache.load_news(allow_stale=True)
        print(f"   Cached articles: {len(cached_news) if cached_news else 0}")
        
        if cached_news:
            cached_keys = {f"{item.get('title', '')}_{item.get('source', '')}" for item in cached_news}
            print(f"   Cached keys: {len(cached_keys)} unique items")
        else:
            cached_keys = set()
        print()
        
        # Step 2: Fetch fresh news
        print("2. FETCHING FRESH NEWS")
        print("-" * 100)
        rss_news = news_aggregator.get_recent_news(hours=24)
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24) if telegram_sync.enabled else []
        
        fresh_news = rss_news + alt_news + telegram_news
        print(f"   Fresh news: {len(fresh_news)} articles")
        
        fresh_keys = {f"{item.get('title', '')}_{item.get('source', '')}" for item in fresh_news}
        print(f"   Fresh keys: {len(fresh_keys)} unique items")
        
        # Find truly new items
        new_keys = fresh_keys - cached_keys
        print(f"   Truly new items (not in cache): {len(new_keys)}")
        
        if new_keys:
            print(f"   Sample new items:")
            for i, key in enumerate(list(new_keys)[:5], 1):
                # Find the item
                for item in fresh_news:
                    item_key = f"{item.get('title', '')}_{item.get('source', '')}"
                    if item_key == key:
                        print(f"      {i}. {item.get('title', 'No title')[:60]}...")
                        print(f"         Source: {item.get('source', 'Unknown')}")
                        break
        print()
        
        # Step 3: Test save with append=True
        print("3. TESTING SAVE WITH append=True")
        print("-" * 100)
        print(f"   Saving {len(fresh_news)} fresh items with append=True")
        print(f"   (This should add {len(new_keys)} new items and preserve existing)")
        
        save_success = news_cache.save_news(fresh_news, append=True)
        
        if save_success:
            print(f"   ✅ Save succeeded")
        else:
            print(f"   ❌ Save failed")
            return
        
        print()
        
        # Step 4: Verify cache was updated
        print("4. VERIFYING CACHE UPDATE")
        print("-" * 100)
        updated_cache = news_cache.load_news(allow_stale=True)
        print(f"   Cached articles after save: {len(updated_cache) if updated_cache else 0}")
        
        if updated_cache:
            updated_keys = {f"{item.get('title', '')}_{item.get('source', '')}" for item in updated_cache}
            print(f"   Updated keys: {len(updated_keys)} unique items")
            
            # Check if new items were added
            added_keys = updated_keys - cached_keys
            print(f"   New items added to cache: {len(added_keys)}")
            
            if len(added_keys) > 0:
                print(f"   ✅ SUCCESS: {len(added_keys)} new items were added to cache")
                print(f"   Sample added items:")
                for i, key in enumerate(list(added_keys)[:5], 1):
                    for item in updated_cache:
                        item_key = f"{item.get('title', '')}_{item.get('source', '')}"
                        if item_key == key:
                            print(f"      {i}. {item.get('title', 'No title')[:60]}...")
                            print(f"         Source: {item.get('source', 'Unknown')}")
                            print(f"         Added: {item.get('added_to_feed_at', 'N/A')}")
                            break
            else:
                print(f"   ⚠️  WARNING: No new items were added to cache")
                print(f"   This might indicate a problem with the append logic")
        else:
            print(f"   ❌ Cache is empty after save")
        
        print()
        print("=" * 100)
        print("SUMMARY")
        print("=" * 100)
        if updated_cache and len(added_keys) > 0:
            print(f"✅ Cache save is working correctly")
            print(f"   Added {len(added_keys)} new items to cache")
        else:
            print(f"❌ Cache save may have issues")
            print(f"   Expected to add {len(new_keys)} new items, but {len(added_keys)} were added")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cache_save()

