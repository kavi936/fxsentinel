#!/usr/bin/env python3
"""
Show the most recent news from all sources
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def show_recent_news():
    """Fetch and display the most recent news"""
    print("=" * 100)
    print("MOST RECENT NEWS FROM ALL SOURCES")
    print("=" * 100)
    print(f"Fetch time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Import services
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        from services.telegram_sync_wrapper import telegram_sync
        from services.persistent_news_cache import get_persistent_news_cache
        
        print("📡 Fetching news from all sources...")
        print()
        
        # Fetch from all sources
        rss_news = news_aggregator.get_recent_news(hours=24)
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24) if telegram_sync.enabled else []
        
        # Combine all news
        all_news = rss_news + alt_news + telegram_news
        
        print(f"✅ RSS Feeds: {len(rss_news)} articles")
        print(f"✅ Alternative Sources: {len(alt_news)} articles")
        print(f"✅ Telegram: {len(telegram_news)} articles")
        print(f"📊 Total: {len(all_news)} articles")
        print()
        
        # Load cached news for comparison
        news_cache = get_persistent_news_cache()
        cached_news = news_cache.load_news() or []
        print(f"💾 Cached: {len(cached_news)} articles")
        print()
        
        # Sort by published_at (newest first)
        all_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        # Show most recent articles
        print("=" * 100)
        print("MOST RECENT ARTICLES (Last 24 Hours)")
        print("=" * 100)
        print()
        
        now = datetime.now()
        
        # Categorize by recency
        last_hour = []
        last_6h = []
        last_24h = []
        
        for article in all_news:
            try:
                pub_str = article.get('published_at', '')
                if pub_str:
                    pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                    age = now - pub_date.replace(tzinfo=None) if pub_date.tzinfo else now - pub_date
                    
                    if age <= timedelta(hours=1):
                        last_hour.append((article, age))
                    elif age <= timedelta(hours=6):
                        last_6h.append((article, age))
                    elif age <= timedelta(hours=24):
                        last_24h.append((article, age))
            except:
                pass
        
        # Show by recency
        if last_hour:
            print(f"🆕 LAST HOUR ({len(last_hour)} articles):")
            print("-" * 100)
            for i, (article, age) in enumerate(last_hour[:10], 1):
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                impact = article.get('impact', 'N/A')
                pub_date = article.get('published_at', 'N/A')
                pairs = article.get('currency_pairs', [])
                
                print(f"\n{i}. [{source}] {title}")
                print(f"   Impact: {impact} | Published: {pub_date} | Age: {age}")
                if pairs:
                    print(f"   Currency Pairs: {', '.join(pairs[:3])}")
            print()
        
        if last_6h:
            print(f"📰 LAST 6 HOURS ({len(last_6h)} articles):")
            print("-" * 100)
            for i, (article, age) in enumerate(last_6h[:10], 1):
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                impact = article.get('impact', 'N/A')
                pub_date = article.get('published_at', 'N/A')
                pairs = article.get('currency_pairs', [])
                
                print(f"\n{i}. [{source}] {title}")
                print(f"   Impact: {impact} | Published: {pub_date} | Age: {age}")
                if pairs:
                    print(f"   Currency Pairs: {', '.join(pairs[:3])}")
            print()
        
        if last_24h:
            print(f"📅 LAST 24 HOURS ({len(last_24h)} articles):")
            print("-" * 100)
            for i, (article, age) in enumerate(last_24h[:10], 1):
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                impact = article.get('impact', 'N/A')
                pub_date = article.get('published_at', 'N/A')
                pairs = article.get('currency_pairs', [])
                
                print(f"\n{i}. [{source}] {title}")
                print(f"   Impact: {impact} | Published: {pub_date} | Age: {age}")
                if pairs:
                    print(f"   Currency Pairs: {', '.join(pairs[:3])}")
            print()
        
        # Summary by source
        print("=" * 100)
        print("SUMMARY BY SOURCE")
        print("=" * 100)
        sources = {}
        for article in all_news:
            source = article.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} articles")
        
        print()
        print("=" * 100)
        print("TOP 20 MOST RECENT ARTICLES (All Sources)")
        print("=" * 100)
        print()
        
        for i, article in enumerate(all_news[:20], 1):
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown')
            impact = article.get('impact', 'N/A')
            pub_date = article.get('published_at', 'N/A')
            pairs = article.get('currency_pairs', [])
            
            # Calculate age
            try:
                pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                age = now - pub_dt.replace(tzinfo=None) if pub_dt.tzinfo else now - pub_dt
                age_str = str(age).split('.')[0]  # Remove microseconds
            except:
                age_str = "N/A"
            
            print(f"{i:2d}. [{source:20s}] {title[:60]}...")
            print(f"     Impact: {impact:6s} | Published: {pub_date[:19]} | Age: {age_str}")
            if pairs:
                print(f"     Pairs: {', '.join(pairs[:4])}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_recent_news()

