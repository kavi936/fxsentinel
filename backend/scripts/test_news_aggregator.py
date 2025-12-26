#!/usr/bin/env python3
"""
Test the actual news aggregator service to see what it returns
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_news_aggregator():
    """Test the news aggregator directly"""
    print("=" * 80)
    print("TESTING NEWS AGGREGATOR SERVICE")
    print("=" * 80)
    print(f"Test time: {datetime.now().isoformat()}")
    
    try:
        from services.news_aggregator import news_aggregator
        
        print("\n1. Testing get_recent_news(hours=24)...")
        articles = news_aggregator.get_recent_news(hours=24)
        print(f"   ✅ Retrieved {len(articles)} articles")
        
        if articles:
            print(f"\n   Articles by source:")
            sources = {}
            for article in articles:
                source = article.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            for source, count in sorted(sources.items()):
                print(f"      - {source}: {count} articles")
            
            print(f"\n   Sample articles (first 5):")
            for i, article in enumerate(articles[:5], 1):
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                pub_date = article.get('published_at', 'N/A')
                print(f"      {i}. [{source}] {title[:60]}...")
                print(f"         Published: {pub_date}")
        else:
            print(f"\n   ⚠️  No articles returned!")
            print(f"   This means either:")
            print(f"   1. RSS feeds are not returning forex-related articles")
            print(f"   2. All articles are being filtered out")
            print(f"   3. RSS feeds are failing to fetch")
        
        # Test individual feed fetching
        print(f"\n2. Testing individual RSS feeds...")
        for feed_key, feed_config in news_aggregator.rss_feeds.items():
            print(f"\n   Testing {feed_config['name']}...")
            try:
                articles = news_aggregator.fetch_rss_feed(feed_config['url'], feed_config['name'])
                print(f"      ✅ Fetched {len(articles)} forex-related articles")
                if articles:
                    for i, article in enumerate(articles[:2], 1):
                        print(f"         {i}. {article.get('title', 'No title')[:50]}...")
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Error testing news aggregator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_news_aggregator()

