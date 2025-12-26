#!/usr/bin/env python3
"""
Check if recent articles from RSS feeds are forex-related
"""

import sys
import os
from datetime import datetime, timedelta
import requests
import feedparser

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_recent_articles():
    """Check if recent articles are forex-related"""
    print("=" * 80)
    print("CHECKING IF RECENT ARTICLES ARE FOREX-RELATED")
    print("=" * 80)
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Import forex filter
    from services.enhanced_forex_filter import enhanced_forex_filter
    
    rss_feeds = {
        'Bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
        'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    }
    
    now = datetime.now()
    cutoff_6h = now - timedelta(hours=6)
    
    all_recent = []
    forex_recent = []
    non_forex_recent = []
    
    for source_name, url in rss_feeds.items():
        print(f"\n{'='*80}")
        print(f"Checking: {source_name}")
        print(f"{'='*80}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            print(f"Total entries: {len(feed.entries)}")
            
            # Check ALL entries, not just first 10
            for i, entry in enumerate(feed.entries, 1):
                try:
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        import time
                        pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    
                    if pub_date and pub_date >= cutoff_6h:
                        title = entry.get('title', '')
                        summary = entry.get('summary', '')
                        
                        # Check if forex-related
                        is_forex = enhanced_forex_filter.is_forex_related(title, summary, source_name)
                        
                        age = now - pub_date
                        status = "✅ FOREX" if is_forex else "❌ NOT FOREX"
                        
                        print(f"\n   Position {i}: [{status}]")
                        print(f"      Title: {title[:70]}...")
                        print(f"      Published: {pub_date.strftime('%Y-%m-%d %H:%M:%S')} ({age})")
                        
                        all_recent.append((source_name, entry, pub_date, is_forex))
                        
                        if is_forex:
                            forex_recent.append((source_name, entry, pub_date))
                        else:
                            non_forex_recent.append((source_name, entry, pub_date))
                            
                except Exception as e:
                    print(f"   Entry {i}: Error - {e}")
                    
        except Exception as e:
            print(f"❌ Error fetching {source_name}: {e}")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total recent articles (last 6 hours): {len(all_recent)}")
    print(f"   ✅ Forex-related: {len(forex_recent)}")
    print(f"   ❌ Not forex-related: {len(non_forex_recent)}")
    
    if len(forex_recent) > 0:
        print(f"\n✅ Found {len(forex_recent)} recent forex articles that should be in the feed!")
        print(f"   These articles are being published but may not be appearing because:")
        print(f"   1. They're beyond position 10 in the feed")
        print(f"   2. We stop after 5 forex articles per source")
        print(f"   3. They're being filtered as duplicates")
    else:
        print(f"\n⚠️  No recent forex articles found")
        print(f"   Recent articles exist but they're not forex-related")

if __name__ == "__main__":
    check_recent_articles()

