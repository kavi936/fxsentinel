#!/usr/bin/env python3
"""
Check publication dates of articles to see if we're getting fresh news
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_article_dates():
    """Check publication dates of fresh vs cached articles"""
    print("=" * 80)
    print("CHECKING ARTICLE PUBLICATION DATES")
    print("=" * 80)
    print(f"Check time: {datetime.now().isoformat()}")
    
    # Get fresh news
    print("\n1. Fetching fresh news...")
    from services.news_aggregator import news_aggregator
    from services.alternative_news_sources import alternative_news_sources
    
    fresh_rss = news_aggregator.get_recent_news(hours=24)
    fresh_alt = alternative_news_sources.get_alternative_news(hours=24)
    fresh_news = fresh_rss + fresh_alt
    
    print(f"   ✅ Fresh RSS: {len(fresh_rss)} articles")
    print(f"   ✅ Fresh Alternative: {len(fresh_alt)} articles")
    print(f"   ✅ Total fresh: {len(fresh_news)} articles")
    
    # Get cached news
    print("\n2. Loading cached news...")
    from services.persistent_news_cache import get_persistent_news_cache
    news_cache = get_persistent_news_cache()
    cached_news = news_cache.load_news() or []
    print(f"   ✅ Cached: {len(cached_news)} articles")
    
    # Analyze publication dates
    print("\n3. Analyzing publication dates...")
    now = datetime.now()
    time_ranges = {
        'Last hour': now - timedelta(hours=1),
        'Last 6 hours': now - timedelta(hours=6),
        'Last 12 hours': now - timedelta(hours=12),
        'Last 24 hours': now - timedelta(hours=24),
        'Older than 24h': None
    }
    
    def categorize_by_date(articles, label):
        print(f"\n   {label}:")
        counts = {key: 0 for key in time_ranges.keys()}
        recent_articles = []
        
        for article in articles:
            try:
                pub_str = article.get('published_at', '')
                if not pub_str:
                    counts['Older than 24h'] += 1
                    continue
                
                pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                age = now - pub_date
                
                if age <= timedelta(hours=1):
                    counts['Last hour'] += 1
                    recent_articles.append((article, age))
                elif age <= timedelta(hours=6):
                    counts['Last 6 hours'] += 1
                elif age <= timedelta(hours=12):
                    counts['Last 12 hours'] += 1
                elif age <= timedelta(hours=24):
                    counts['Last 24 hours'] += 1
                else:
                    counts['Older than 24h'] += 1
            except Exception as e:
                counts['Older than 24h'] += 1
        
        for time_range, count in counts.items():
            print(f"      {time_range}: {count} articles")
        
        if recent_articles:
            print(f"\n   Most recent articles (last hour):")
            for i, (article, age) in enumerate(recent_articles[:5], 1):
                print(f"      {i}. {article.get('title', 'No title')[:60]}...")
                print(f"         Age: {age}")
                print(f"         Source: {article.get('source', 'Unknown')}")
        
        return counts
    
    fresh_counts = categorize_by_date(fresh_news, "Fresh News")
    cached_counts = categorize_by_date(cached_news, "Cached News")
    
    # Compare
    print("\n4. Comparison:")
    print(f"   Fresh news in last hour: {fresh_counts['Last hour']}")
    print(f"   Cached news in last hour: {cached_counts['Last hour']}")
    
    if fresh_counts['Last hour'] == 0 and cached_counts['Last hour'] == 0:
        print(f"\n   ⚠️  NO ARTICLES PUBLISHED IN THE LAST HOUR")
        print(f"   This explains why there's no 'new' news - nothing new has been published!")
    
    # Check what the most recent articles are
    print("\n5. Most recent articles (all sources):")
    all_articles = fresh_news + cached_news
    articles_with_dates = []
    
    for article in all_articles:
        try:
            pub_str = article.get('published_at', '')
            if pub_str:
                pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                articles_with_dates.append((article, pub_date))
        except:
            pass
    
    # Normalize datetimes for comparison
    def normalize_dt(dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        return dt
    
    articles_with_dates.sort(key=lambda x: normalize_dt(x[1]), reverse=True)
    
    print(f"   Top 10 most recent articles:")
    for i, (article, pub_date) in enumerate(articles_with_dates[:10], 1):
        age = now - pub_date
        print(f"      {i}. [{article.get('source', 'Unknown')}] {article.get('title', 'No title')[:50]}...")
        print(f"         Published: {pub_date.strftime('%Y-%m-%d %H:%M:%S')} ({age})")

if __name__ == "__main__":
    check_article_dates()

