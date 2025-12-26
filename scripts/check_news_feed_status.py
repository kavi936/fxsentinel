#!/usr/bin/env python3
"""
Check current news feed status and compare with fresh news
Shows what's in cache vs what should be added
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def check_cache_status():
    """Check current cache status"""
    print("=" * 60)
    print("CURRENT CACHE STATUS")
    print("=" * 60)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        cache = get_persistent_news_cache()
        
        # Get cache status
        status = cache.get_cache_status()
        print(f"Cache Exists: {status.get('exists', False)}")
        print(f"Cache Valid: {status.get('is_valid', False)}")
        print(f"News Count: {status.get('news_count', 0)}")
        print(f"Cache Age: {status.get('age', 'N/A')}")
        print(f"Last Updated: {status.get('last_updated', 'N/A')}")
        
        # Load cached news
        cached_news = cache.load_news()
        if cached_news:
            print(f"\n📰 Cached News Items: {len(cached_news)}")
            print("\nFirst 10 items:")
            for i, item in enumerate(cached_news[:10], 1):
                print(f"  {i}. {item.get('title', 'No title')[:60]}...")
                print(f"     Source: {item.get('source', 'Unknown')}")
                print(f"     Published: {item.get('published_at', 'N/A')[:19]}")
                print(f"     Added to feed: {item.get('added_to_feed_at', 'N/A')[:19]}")
                print()
        else:
            print("\n⚠️  No cached news found")
        
        return cached_news, cache
        
    except Exception as e:
        print(f"❌ Error checking cache: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def check_fresh_news():
    """Check what fresh news is available"""
    print("\n" + "=" * 60)
    print("FRESH NEWS AVAILABLE")
    print("=" * 60)
    
    try:
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        
        # Fetch RSS news
        print("Fetching RSS news...")
        rss_news = news_aggregator.get_recent_news(hours=24)
        print(f"✅ RSS News: {len(rss_news)} items")
        
        # Fetch alternative news
        print("Fetching alternative news...")
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        print(f"✅ Alternative News: {len(alt_news)} items")
        
        # Combine
        fresh_news = rss_news + alt_news
        print(f"\n📰 Total Fresh News: {len(fresh_news)} items")
        
        if fresh_news:
            print("\nFirst 10 fresh items:")
            for i, item in enumerate(fresh_news[:10], 1):
                print(f"  {i}. {item.get('title', 'No title')[:60]}...")
                print(f"     Source: {item.get('source', 'Unknown')}")
                print(f"     Published: {item.get('published_at', 'N/A')[:19]}")
                print()
        
        return fresh_news
        
    except Exception as e:
        print(f"❌ Error fetching fresh news: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_news(cached_news, fresh_news):
    """Compare cached vs fresh news to find what's missing"""
    print("\n" + "=" * 60)
    print("COMPARISON: WHAT'S MISSING")
    print("=" * 60)
    
    if not cached_news:
        print("⚠️  No cached news - all fresh news should be added")
        if fresh_news:
            print(f"📝 {len(fresh_news)} items should be added")
        return
    
    if not fresh_news:
        print("⚠️  No fresh news available")
        return
    
    # Create sets for comparison
    cached_keys = set()
    for item in cached_news:
        key = f"{item.get('title', '')}_{item.get('source', '')}"
        cached_keys.add(key.lower())
    
    fresh_keys = set()
    for item in fresh_news:
        key = f"{item.get('title', '')}_{item.get('source', '')}"
        fresh_keys.add(key.lower())
    
    # Find new items (in fresh but not in cached)
    new_items = []
    for item in fresh_news:
        key = f"{item.get('title', '')}_{item.get('source', '')}"
        if key.lower() not in cached_keys:
            new_items.append(item)
    
    # Find items only in cache (might be old)
    only_in_cache = []
    for item in cached_news:
        key = f"{item.get('title', '')}_{item.get('source', '')}"
        if key.lower() not in fresh_keys:
            only_in_cache.append(item)
    
    print(f"📊 Cached News: {len(cached_news)} items")
    print(f"📊 Fresh News: {len(fresh_news)} items")
    print(f"📊 New Items (should be added): {len(new_items)} items")
    print(f"📊 Items only in cache (might be old): {len(only_in_cache)} items")
    
    if new_items:
        print(f"\n🆕 NEW ITEMS THAT SHOULD BE ADDED ({len(new_items)}):")
        for i, item in enumerate(new_items[:20], 1):  # Show first 20
            print(f"  {i}. {item.get('title', 'No title')[:70]}")
            print(f"     Source: {item.get('source', 'Unknown')}")
            print(f"     Published: {item.get('published_at', 'N/A')[:19]}")
            print()
        
        if len(new_items) > 20:
            print(f"     ... and {len(new_items) - 20} more items")
    else:
        print("\n✅ No new items - cache is up to date!")
    
    if only_in_cache:
        print(f"\n📦 ITEMS ONLY IN CACHE (might be old, {len(only_in_cache)}):")
        for i, item in enumerate(only_in_cache[:10], 1):  # Show first 10
            print(f"  {i}. {item.get('title', 'No title')[:70]}")
            print(f"     Source: {item.get('source', 'Unknown')}")
            print(f"     Added to feed: {item.get('added_to_feed_at', 'N/A')[:19]}")
            print()

def check_fetch_timing(cache):
    """Check if it's time to fetch new news"""
    print("\n" + "=" * 60)
    print("FETCH TIMING CHECK")
    print("=" * 60)
    
    try:
        should_fetch = cache.should_fetch_new_news(fetch_interval_minutes=5)
        print(f"Should fetch new news: {should_fetch}")
        
        if should_fetch:
            print("✅ It's time to fetch new news (> 5 minutes since last fetch)")
        else:
            print("⏳ Not time yet - last fetch was < 5 minutes ago")
        
        return should_fetch
        
    except Exception as e:
        print(f"❌ Error checking fetch timing: {e}")
        return None

def main():
    """Run all checks"""
    print("\n" + "=" * 60)
    print("NEWS FEED STATUS CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    # Check cache
    cached_news, cache = check_cache_status()
    
    # Check fetch timing
    should_fetch = check_fetch_timing(cache)
    
    # Check fresh news
    fresh_news = check_fresh_news()
    
    # Compare
    if cached_news is not None and fresh_news is not None:
        compare_news(cached_news, fresh_news)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if cached_news:
        print(f"✅ Cache has {len(cached_news)} items")
    else:
        print("⚠️  No cache found")
    
    if fresh_news:
        print(f"✅ Fresh news available: {len(fresh_news)} items")
    else:
        print("⚠️  No fresh news available")
    
    if should_fetch:
        print("✅ Should fetch new news now")
    else:
        print("⏳ Not time to fetch yet")

if __name__ == '__main__':
    main()

