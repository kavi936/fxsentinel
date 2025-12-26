#!/usr/bin/env python3
"""
Diagnostic script to compare fresh news with cached news
Helps identify why new news isn't appearing in the feed
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fetch_all_news_sources():
    """Fetch news from all sources"""
    print("=" * 80)
    print("FETCHING NEWS FROM ALL SOURCES")
    print("=" * 80)
    
    all_news = []
    sources_breakdown = {}
    
    # 1. RSS News
    print("\n📰 Fetching RSS News...")
    try:
        from services.news_aggregator import news_aggregator
        rss_news = news_aggregator.get_recent_news(hours=24)
        print(f"   ✅ Fetched {len(rss_news)} articles from RSS feeds")
        all_news.extend(rss_news)
        sources_breakdown['RSS Feeds'] = len(rss_news)
        
        # Show breakdown by source
        rss_sources = {}
        for item in rss_news:
            source = item.get('source', 'Unknown')
            rss_sources[source] = rss_sources.get(source, 0) + 1
        for source, count in sorted(rss_sources.items()):
            print(f"      - {source}: {count} articles")
    except Exception as e:
        print(f"   ❌ Error fetching RSS news: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Alternative News Sources
    print("\n📰 Fetching Alternative News Sources...")
    try:
        from services.alternative_news_sources import alternative_news_sources
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        print(f"   ✅ Fetched {len(alt_news)} articles from alternative sources")
        all_news.extend(alt_news)
        sources_breakdown['Alternative Sources'] = len(alt_news)
        
        # Show breakdown by source
        alt_sources = {}
        for item in alt_news:
            source = item.get('source', 'Unknown')
            alt_sources[source] = alt_sources.get(source, 0) + 1
        for source, count in sorted(alt_sources.items()):
            print(f"      - {source}: {count} articles")
    except Exception as e:
        print(f"   ❌ Error fetching alternative news: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Telegram News
    print("\n📰 Fetching Telegram News...")
    try:
        from services.telegram_sync_wrapper import telegram_sync
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"   ✅ Fetched {len(telegram_news)} articles from Telegram")
        all_news.extend(telegram_news)
        sources_breakdown['Telegram'] = len(telegram_news)
        
        # Show breakdown by source
        telegram_sources = {}
        for item in telegram_news:
            source = item.get('source', 'Unknown')
            telegram_sources[source] = telegram_sources.get(source, 0) + 1
        for source, count in sorted(telegram_sources.items()):
            print(f"      - {source}: {count} articles")
    except Exception as e:
        print(f"   ❌ Error fetching Telegram news: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n📊 TOTAL FRESH NEWS: {len(all_news)} articles")
    print(f"   Sources breakdown: {sources_breakdown}")
    
    return all_news, sources_breakdown

def load_cached_news():
    """Load news from cache"""
    print("\n" + "=" * 80)
    print("LOADING CACHED NEWS")
    print("=" * 80)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        news_cache = get_persistent_news_cache()
        cached_news = news_cache.load_news()
        
        if cached_news:
            print(f"✅ Loaded {len(cached_news)} articles from cache")
            
            # Show breakdown by source
            cached_sources = {}
            for item in cached_news:
                source = item.get('source', 'Unknown')
                cached_sources[source] = cached_sources.get(source, 0) + 1
            
            print(f"   Sources breakdown:")
            for source, count in sorted(cached_sources.items()):
                print(f"      - {source}: {count} articles")
            
            # Show oldest and newest
            if cached_news:
                sorted_by_time = sorted(cached_news, key=lambda x: x.get('added_to_feed_at') or x.get('published_at') or '')
                oldest = sorted_by_time[0]
                newest = sorted_by_time[-1]
                print(f"\n   Oldest article: {oldest.get('title', 'No title')[:60]}...")
                print(f"      Added: {oldest.get('added_to_feed_at', 'N/A')}")
                print(f"   Newest article: {newest.get('title', 'No title')[:60]}...")
                print(f"      Added: {newest.get('added_to_feed_at', 'N/A')}")
        else:
            print("⚠️  No cached news found")
            cached_news = []
        
        return cached_news
    except Exception as e:
        print(f"❌ Error loading cached news: {e}")
        import traceback
        traceback.print_exc()
        return []

def normalize_title(title: str) -> str:
    """Normalize title for comparison (same logic as deduplication)"""
    if not title:
        return ""
    # Remove common prefixes and normalize
    import re
    cleaned = title.strip()
    # Remove prefixes like **JUST IN:** etc.
    prefixes = ['**JUST IN:**', '**BREAKING:**', '**UPDATE:**', 'JUST IN:', 'BREAKING:', 'UPDATE:']
    for prefix in prefixes:
        if cleaned.upper().startswith(prefix.upper()):
            cleaned = cleaned[len(prefix):].strip()
    # Normalize: lowercase, remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned.lower().strip())
    return cleaned

def create_dedup_key(item: Dict[str, Any]) -> str:
    """Create deduplication key (same logic as backend)"""
    title = item.get('title', '').strip()
    source = item.get('source', '').strip()
    return f"{title}_{source}"

def compare_news(fresh_news: List[Dict[str, Any]], cached_news: List[Dict[str, Any]]):
    """Compare fresh news with cached news"""
    print("\n" + "=" * 80)
    print("COMPARING FRESH NEWS vs CACHED NEWS")
    print("=" * 80)
    
    # Create sets for comparison using the same logic as backend deduplication
    fresh_ids = {str(item.get('id', '')) for item in fresh_news if item.get('id')}
    fresh_dedup_keys = {create_dedup_key(item) for item in fresh_news}
    fresh_normalized_titles = {normalize_title(item.get('title', '')) for item in fresh_news}
    
    cached_ids = {str(item.get('id', '')) for item in cached_news if item.get('id')}
    cached_dedup_keys = {create_dedup_key(item) for item in cached_news}
    cached_normalized_titles = {normalize_title(item.get('title', '')) for item in cached_news}
    
    # Find new articles (in fresh but not in cache)
    new_by_id = fresh_ids - cached_ids
    new_by_dedup_key = fresh_dedup_keys - cached_dedup_keys
    new_by_normalized_title = fresh_normalized_titles - cached_normalized_titles
    
    # Find articles that should be new (using dedup key logic)
    truly_new_articles = []
    for item in fresh_news:
        dedup_key = create_dedup_key(item)
        if dedup_key not in cached_dedup_keys:
            truly_new_articles.append(item)
    
    print(f"\n📊 STATISTICS:")
    print(f"   Fresh news total: {len(fresh_news)}")
    print(f"   Cached news total: {len(cached_news)}")
    print(f"   New articles (by ID): {len(new_by_id)}")
    print(f"   New articles (by dedup key): {len(new_by_dedup_key)}")
    print(f"   New articles (by normalized title): {len(new_by_normalized_title)}")
    print(f"   Truly new articles (not in cache by dedup key): {len(truly_new_articles)}")
    
    # Show new articles
    if truly_new_articles:
        print(f"\n🆕 NEW ARTICLES NOT IN CACHE ({len(truly_new_articles)}):")
        for i, item in enumerate(truly_new_articles[:10], 1):  # Show first 10
            title = item.get('title', 'No title')
            source = item.get('source', 'Unknown')
            pub_date = item.get('published_at', 'N/A')
            print(f"   {i}. [{source}] {title[:70]}...")
            print(f"      Published: {pub_date}")
        if len(truly_new_articles) > 10:
            print(f"   ... and {len(truly_new_articles) - 10} more")
    else:
        print("\n⚠️  NO NEW ARTICLES FOUND - All fresh news is already in cache")
    
    # Find articles in cache but not in fresh (old articles)
    old_by_dedup_key = cached_dedup_keys - fresh_dedup_keys
    
    old_articles = []
    for item in cached_news:
        dedup_key = create_dedup_key(item)
        if dedup_key not in fresh_dedup_keys:
            old_articles.append(item)
    
    print(f"\n📊 OLD ARTICLES IN CACHE BUT NOT IN FRESH ({len(old_articles)}):")
    print(f"   These are articles that were cached but are no longer in fresh news")
    print(f"   (This is normal - they're older articles that should stay in cache)")
    
    # Show duplicates (in both fresh and cache)
    duplicates = fresh_dedup_keys & cached_dedup_keys
    print(f"\n📊 DUPLICATE ARTICLES (in both fresh and cache): {len(duplicates)}")
    if duplicates:
        print(f"   These should be deduplicated during merge (keeping cached version)")
        for i, key in enumerate(list(duplicates)[:5], 1):
            # Find example from cache
            cached_example = next((item for item in cached_news if create_dedup_key(item) == key), None)
            if cached_example:
                print(f"   {i}. {cached_example.get('title', 'No title')[:60]}... [{cached_example.get('source', 'Unknown')}]")
        if len(duplicates) > 5:
            print(f"   ... and {len(duplicates) - 5} more duplicates")
    
    # Show what the merged list should look like
    print(f"\n📊 EXPECTED MERGED LIST:")
    print(f"   New articles (top): {len(truly_new_articles)}")
    print(f"   Duplicates (will be deduplicated): {len(duplicates)}")
    print(f"   Old articles (bottom): {len(old_articles)}")
    print(f"   Total expected after merge: {len(truly_new_articles) + len(old_articles)}")
    print(f"   (Duplicates will be removed, keeping cached versions)")
    
    # Check publication dates to see if there are recent articles
    print(f"\n📅 PUBLICATION DATE ANALYSIS:")
    from datetime import datetime, timedelta
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    six_hours_ago = now - timedelta(hours=6)
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    fresh_recent = []
    cached_recent = []
    
    for item in fresh_news:
        try:
            pub_str = item.get('published_at', '')
            if pub_str:
                pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                if pub_date >= one_hour_ago:
                    fresh_recent.append(item)
        except:
            pass
    
    for item in cached_news:
        try:
            pub_str = item.get('published_at', '')
            if pub_str:
                pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                if pub_date >= one_hour_ago:
                    cached_recent.append(item)
        except:
            pass
    
    print(f"   Fresh articles published in last hour: {len(fresh_recent)}")
    print(f"   Cached articles published in last hour: {len(cached_recent)}")
    
    if fresh_recent:
        print(f"\n   Recent fresh articles (last hour):")
        for i, item in enumerate(fresh_recent[:5], 1):
            print(f"      {i}. {item.get('title', 'No title')[:60]}... [{item.get('source', 'Unknown')}]")
            print(f"         Published: {item.get('published_at', 'N/A')}")
    
    return truly_new_articles, old_articles

def check_cache_status():
    """Check cache status and timing"""
    print("\n" + "=" * 80)
    print("CACHE STATUS")
    print("=" * 80)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        news_cache = get_persistent_news_cache()
        
        cache_status = news_cache.get_cache_status()
        print(f"   Cache exists: {cache_status.get('exists', False)}")
        print(f"   Cache is valid: {cache_status.get('is_valid', False)}")
        print(f"   Cache age: {cache_status.get('age', 'N/A')}")
        print(f"   News count: {cache_status.get('news_count', 0)}")
        print(f"   Last updated: {cache_status.get('last_updated', 'N/A')}")
        
        # Check if should fetch new
        should_fetch = news_cache.should_fetch_new_news(fetch_interval_minutes=5)
        print(f"\n   Should fetch new news (5 min interval): {should_fetch}")
        
    except Exception as e:
        print(f"❌ Error checking cache status: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main diagnostic function"""
    print("\n" + "=" * 80)
    print("NEWS FEED DIAGNOSTIC TOOL")
    print("=" * 80)
    print(f"Run time: {datetime.now().isoformat()}")
    
    # 1. Fetch all fresh news
    fresh_news, sources_breakdown = fetch_all_news_sources()
    
    # 2. Load cached news
    cached_news = load_cached_news()
    
    # 3. Check cache status
    check_cache_status()
    
    # 4. Compare
    truly_new, old_articles = compare_news(fresh_news, cached_news)
    
    # 5. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Fresh news available: {len(fresh_news)} articles")
    print(f"✅ Cached news: {len(cached_news)} articles")
    print(f"🆕 New articles to add: {len(truly_new)} articles")
    print(f"📊 Expected total after merge: ~{len(truly_new) + len(cached_news)} articles")
    
    if len(truly_new) > 0:
        print(f"\n⚠️  ISSUE DETECTED: {len(truly_new)} new articles should be in the feed but aren't!")
        print("   These articles should appear at the top of the feed.")
    else:
        print(f"\n✅ No new articles - cache is up to date")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

