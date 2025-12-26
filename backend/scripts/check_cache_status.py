#!/usr/bin/env python3
"""
Check if cached persistent news is up to date
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_cache_status():
    """Check if cache is up to date"""
    print("=" * 100)
    print("CACHED PERSISTENT NEWS STATUS CHECK")
    print("=" * 100)
    print(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        from services.telegram_sync_wrapper import telegram_sync
        
        # Load cache
        news_cache = get_persistent_news_cache()
        cached_news = news_cache.load_news() or []
        
        print(f"💾 CACHED NEWS:")
        print(f"   Total articles: {len(cached_news)}")
        
        if cached_news:
            # Check cache metadata
            cache_info = news_cache._get_cache_info()
            if cache_info:
                last_fetch = cache_info.get('last_fetch')
                timestamp = cache_info.get('timestamp')
                news_count = cache_info.get('news_count', len(cached_news))
                
                print(f"   News count in metadata: {news_count}")
                if timestamp:
                    try:
                        cache_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        age = datetime.now() - cache_time.replace(tzinfo=None) if cache_time.tzinfo else datetime.now() - cache_time
                        print(f"   Cache timestamp: {timestamp}")
                        print(f"   Cache age: {age}")
                    except:
                        print(f"   Cache timestamp: {timestamp}")
                
                if last_fetch:
                    try:
                        fetch_time = datetime.fromisoformat(last_fetch.replace('Z', '+00:00'))
                        age = datetime.now() - fetch_time.replace(tzinfo=None) if fetch_time.tzinfo else datetime.now() - fetch_time
                        print(f"   Last fetch: {last_fetch}")
                        print(f"   Time since last fetch: {age}")
                    except:
                        print(f"   Last fetch: {last_fetch}")
        
        print()
        
        # Fetch fresh news
        print("📡 FETCHING FRESH NEWS...")
        rss_news = news_aggregator.get_recent_news(hours=24)
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24) if telegram_sync.enabled else []
        
        fresh_news = rss_news + alt_news + telegram_news
        
        print(f"   RSS: {len(rss_news)} articles")
        print(f"   Alternative: {len(alt_news)} articles")
        print(f"   Telegram: {len(telegram_news)} articles")
        print(f"   Total fresh: {len(fresh_news)} articles")
        print()
        
        # Compare
        print("=" * 100)
        print("COMPARISON: CACHED vs FRESH")
        print("=" * 100)
        print()
        
        # Create keys for comparison
        cached_keys = {f"{item.get('title', '')}_{item.get('source', '')}" for item in cached_news}
        fresh_keys = {f"{item.get('title', '')}_{item.get('source', '')}" for item in fresh_news}
        
        # Find new articles not in cache
        new_articles = [item for item in fresh_news if f"{item.get('title', '')}_{item.get('source', '')}" not in cached_keys]
        
        # Find articles in cache but not in fresh (old articles)
        old_articles = [item for item in cached_news if f"{item.get('title', '')}_{item.get('source', '')}" not in fresh_keys]
        
        # Find duplicates (in both)
        duplicates = [item for item in fresh_news if f"{item.get('title', '')}_{item.get('source', '')}" in cached_keys]
        
        print(f"📊 CACHED ARTICLES: {len(cached_news)}")
        print(f"📊 FRESH ARTICLES: {len(fresh_news)}")
        print(f"🆕 NEW ARTICLES (not in cache): {len(new_articles)}")
        print(f"📰 OLD ARTICLES (in cache, not in fresh): {len(old_articles)}")
        print(f"🔄 DUPLICATES (in both): {len(duplicates)}")
        print()
        
        # Show new articles
        if new_articles:
            print(f"🆕 NEW ARTICLES TO ADD ({len(new_articles)}):")
            print("-" * 100)
            for i, article in enumerate(new_articles[:10], 1):
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                pub_date = article.get('published_at', 'N/A')
                
                # Calculate age
                try:
                    pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    age = datetime.now() - pub_dt.replace(tzinfo=None) if pub_dt.tzinfo else datetime.now() - pub_dt
                    age_str = str(age).split('.')[0]
                except:
                    age_str = "N/A"
                
                print(f"  {i}. [{source}] {title[:70]}...")
                print(f"     Published: {pub_date[:19]} | Age: {age_str}")
            if len(new_articles) > 10:
                print(f"     ... and {len(new_articles) - 10} more")
            print()
        
        # Check if cache should be updated
        print("=" * 100)
        print("CACHE STATUS")
        print("=" * 100)
        print()
        
        if len(new_articles) > 0:
            print(f"⚠️  CACHE IS OUT OF DATE")
            print(f"   There are {len(new_articles)} new articles that should be added to cache")
            print(f"   Cache should be updated on next fetch (every 5 minutes or on force refresh)")
        else:
            print(f"✅ CACHE IS UP TO DATE")
            print(f"   All fresh articles are already in cache")
            print(f"   No new articles to add")
        
        # Check cache age
        if cached_news:
            # Get most recent article from cache
            cached_news_sorted = sorted(cached_news, key=lambda x: x.get('published_at', ''), reverse=True)
            most_recent = cached_news_sorted[0]
            pub_date = most_recent.get('published_at', '')
            
            try:
                pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                age = datetime.now() - pub_dt.replace(tzinfo=None) if pub_dt.tzinfo else datetime.now() - pub_dt
                print(f"\n   Most recent cached article: {age}")
                print(f"   Title: {most_recent.get('title', 'No title')[:60]}...")
            except:
                pass
        
        # Check if should_fetch_new_news
        print()
        should_fetch = news_cache.should_fetch_new_news(fetch_interval_minutes=5)
        print(f"📅 Should fetch new news? {should_fetch}")
        if should_fetch:
            print(f"   ✅ Yes - last fetch was > 5 minutes ago")
        else:
            print(f"   ⏸️  No - last fetch was < 5 minutes ago")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_cache_status()

