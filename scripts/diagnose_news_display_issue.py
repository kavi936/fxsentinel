#!/usr/bin/env python3
"""
Diagnose why new news is not being displayed
Checks API endpoint, cache, and filtering logic
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def check_api_endpoint():
    """Simulate what the API endpoint would return"""
    print("=" * 60)
    print("API ENDPOINT SIMULATION")
    print("=" * 60)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        
        cache = get_persistent_news_cache()
        
        # Simulate the /api/news endpoint logic
        print("\n1. Checking cache...")
        cached_news = cache.load_news()
        print(f"   Cached news: {len(cached_news) if cached_news else 0} items")
        
        print("\n2. Checking if should fetch...")
        should_fetch = cache.should_fetch_new_news(fetch_interval_minutes=5)
        print(f"   Should fetch: {should_fetch}")
        
        if not cached_news or should_fetch:
            print("\n3. Fetching fresh news...")
            # Fetch RSS news
            rss_news = news_aggregator.get_recent_news(hours=24)
            print(f"   RSS news: {len(rss_news)} items")
            
            # Fetch alternative news
            alt_news = alternative_news_sources.get_alternative_news(hours=24)
            print(f"   Alternative news: {len(alt_news)} items")
            
            # Combine
            fresh_news = rss_news + alt_news
            print(f"   Total fresh: {len(fresh_news)} items")
            
            # Merge with cache if exists
            if cached_news and should_fetch:
                print(f"\n4. Merging with cache...")
                all_news = fresh_news + cached_news
                print(f"   Combined: {len(all_news)} items")
            else:
                all_news = fresh_news
            
            # Deduplicate
            print(f"\n5. Deduplicating...")
            seen = set()
            unique_news = []
            for item in all_news:
                key = f"{item.get('title', '')}_{item.get('source', '')}"
                if key.lower() not in seen:
                    seen.add(key.lower())
                    unique_news.append(item)
            print(f"   After dedup: {len(unique_news)} items")
            
            # Save to cache
            print(f"\n6. Saving to cache...")
            if cached_news and should_fetch:
                success = cache.save_news(unique_news, append=True)
            else:
                success = cache.save_news(unique_news, append=False)
            print(f"   Save success: {success}")
            
            return unique_news
        else:
            print("\n3. Using cached news (no fetch needed)")
            return cached_news
            
    except Exception as e:
        print(f"❌ Error simulating API endpoint: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_news_filtering(news_items):
    """Check if news items would pass frontend filtering"""
    print("\n" + "=" * 60)
    print("NEWS FILTERING CHECK")
    print("=" * 60)
    
    if not news_items:
        print("⚠️  No news items to check")
        return
    
    print(f"\nTotal news items: {len(news_items)}")
    
    # Check required fields
    print("\nChecking required fields...")
    missing_fields = {}
    for i, item in enumerate(news_items[:10]):  # Check first 10
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
            missing_fields[i] = missing
            print(f"  Item {i}: Missing {missing}")
    
    if not missing_fields:
        print("  ✅ All items have required fields")
    
    # Check impact levels
    print("\nImpact level distribution:")
    impact_counts = {}
    for item in news_items:
        impact = item.get('impact', 'unknown')
        impact_counts[impact] = impact_counts.get(impact, 0) + 1
    for impact, count in sorted(impact_counts.items()):
        print(f"  {impact}: {count} items")
    
    # Check sources
    print("\nSource distribution:")
    source_counts = {}
    for item in news_items:
        source = item.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {source}: {count} items")

def check_telegram_news():
    """Check if Telegram news is being fetched"""
    print("\n" + "=" * 60)
    print("TELEGRAM NEWS CHECK")
    print("=" * 60)
    
    try:
        from services.telegram_sync_wrapper import telegram_sync
        print("Fetching Telegram news...")
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Telegram news: {len(telegram_news)} items")
        
        if telegram_news:
            print("\nSample Telegram news:")
            for i, item in enumerate(telegram_news[:5], 1):
                print(f"  {i}. {item.get('title', 'No title')[:60]}...")
                print(f"     Source: {item.get('source', 'Unknown')}")
                print(f"     Impact: {item.get('impact', 'Unknown')}")
                print()
        
        return telegram_news
        
    except Exception as e:
        print(f"❌ Error fetching Telegram news: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_cache_after_save():
    """Check what's actually in the cache after save"""
    print("\n" + "=" * 60)
    print("CACHE VERIFICATION")
    print("=" * 60)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        cache = get_persistent_news_cache()
        
        cached_news = cache.load_news()
        if cached_news:
            print(f"✅ Cache has {len(cached_news)} items")
            print("\nFirst 5 items in cache:")
            for i, item in enumerate(cached_news[:5], 1):
                print(f"  {i}. {item.get('title', 'No title')[:60]}...")
                print(f"     Source: {item.get('source', 'Unknown')}")
                print(f"     Published: {item.get('published_at', 'N/A')[:19]}")
                print(f"     Added to feed: {item.get('added_to_feed_at', 'N/A')[:19]}")
                print()
        else:
            print("⚠️  Cache is empty")
        
        return cached_news
        
    except Exception as e:
        print(f"❌ Error checking cache: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all diagnostics"""
    print("\n" + "=" * 60)
    print("NEWS DISPLAY DIAGNOSTIC")
    print("=" * 60)
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    # Check Telegram news specifically (user mentioned WatcherGuru)
    telegram_news = check_telegram_news()
    
    # Simulate API endpoint
    api_news = check_api_endpoint()
    
    # Check filtering
    if api_news:
        check_news_filtering(api_news)
    
    # Verify cache
    cached_news = check_cache_after_save()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if telegram_news:
        print(f"✅ Telegram news available: {len(telegram_news)} items")
        watcher_guru = [item for item in telegram_news if 'watcherguru' in item.get('source', '').lower()]
        if watcher_guru:
            print(f"✅ WatcherGuru news found: {len(watcher_guru)} items")
        else:
            print("⚠️  No WatcherGuru news in Telegram feed")
    else:
        print("⚠️  Telegram news not available")
    
    if api_news:
        print(f"✅ API would return: {len(api_news)} items")
    else:
        print("⚠️  API would return no items")
    
    if cached_news:
        print(f"✅ Cache has: {len(cached_news)} items")
    else:
        print("⚠️  Cache is empty")
    
    print("\n💡 Next steps:")
    print("   1. Check if frontend is calling the API")
    print("   2. Check browser console for errors")
    print("   3. Verify API endpoint is accessible")
    print("   4. Check if news is being filtered out")

if __name__ == '__main__':
    main()

