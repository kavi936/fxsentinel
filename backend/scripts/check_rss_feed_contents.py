#!/usr/bin/env python3
"""
Check what RSS feeds are actually returning - all entries, not just filtered ones
"""

import sys
import os
from datetime import datetime, timedelta
import requests
import feedparser

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_feed_contents(url, source_name):
    """Check all entries in a feed"""
    print(f"\n{'='*80}")
    print(f"Checking: {source_name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if feed.bozo:
            print(f"⚠️  Feed parsing error: {feed.bozo_exception}")
            return []
        
        print(f"✅ Feed parsed successfully")
        print(f"   Feed title: {feed.feed.get('title', 'N/A')}")
        print(f"   Total entries in feed: {len(feed.entries)}")
        
        # Check all entries, not just first 10
        now = datetime.now()
        cutoff_1h = now - timedelta(hours=1)
        cutoff_6h = now - timedelta(hours=6)
        cutoff_24h = now - timedelta(hours=24)
        
        recent_1h = []
        recent_6h = []
        recent_24h = []
        older = []
        
        print(f"\n   Analyzing ALL {len(feed.entries)} entries...")
        
        for i, entry in enumerate(feed.entries, 1):
            try:
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                
                title = entry.get('title', 'No title')[:60]
                
                if pub_date:
                    age = now - pub_date
                    if pub_date >= cutoff_1h:
                        recent_1h.append((i, entry, pub_date, age))
                    elif pub_date >= cutoff_6h:
                        recent_6h.append((i, entry, pub_date, age))
                    elif pub_date >= cutoff_24h:
                        recent_24h.append((i, entry, pub_date, age))
                    else:
                        older.append((i, entry, pub_date, age))
                else:
                    older.append((i, entry, None, None))
            except Exception as e:
                print(f"      Entry {i}: Error parsing - {e}")
        
        print(f"\n   📊 BREAKDOWN BY AGE:")
        print(f"      Last hour: {len(recent_1h)} articles")
        print(f"      Last 6 hours: {len(recent_6h)} articles")
        print(f"      Last 24 hours: {len(recent_24h)} articles")
        print(f"      Older than 24h: {len(older)} articles")
        
        # Show recent articles
        if recent_1h:
            print(f"\n   🆕 ARTICLES FROM LAST HOUR ({len(recent_1h)}):")
            for pos, entry, pub_date, age in recent_1h[:5]:
                print(f"      Position {pos}: {entry.get('title', 'No title')[:60]}...")
                print(f"         Published: {pub_date.strftime('%Y-%m-%d %H:%M:%S')} ({age})")
        
        if recent_6h:
            print(f"\n   📰 ARTICLES FROM LAST 6 HOURS ({len(recent_6h)}):")
            for pos, entry, pub_date, age in recent_6h[:5]:
                print(f"      Position {pos}: {entry.get('title', 'No title')[:60]}...")
                print(f"         Published: {pub_date.strftime('%Y-%m-%d %H:%M:%S')} ({age})")
        
        # Check if recent articles are in first 10
        recent_in_first_10 = [item for item in (recent_1h + recent_6h) if item[0] <= 10]
        print(f"\n   ⚠️  Recent articles in first 10 positions: {len(recent_in_first_10)}")
        if len(recent_1h + recent_6h) > len(recent_in_first_10):
            print(f"      ⚠️  WARNING: {len(recent_1h + recent_6h) - len(recent_in_first_10)} recent articles are BEYOND position 10!")
            print(f"      This means we're missing them because we only check first 10 entries!")
        
        return feed.entries
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Check all RSS feeds"""
    print("=" * 80)
    print("RSS FEED CONTENT ANALYSIS")
    print("=" * 80)
    print(f"Check time: {datetime.now().isoformat()}")
    
    # Disable SSL warnings for testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    rss_feeds = {
        'Bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
        'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        'MarketWatch': 'https://feeds.marketwatch.com/marketwatch/marketpulse/',
        'FXStreet': 'https://www.fxstreet.com/rss',
        'ForexLive': 'https://www.forexlive.com/feed/',
    }
    
    all_recent = []
    
    for source_name, url in rss_feeds.items():
        entries = check_feed_contents(url, source_name)
        # Count recent
        now = datetime.now()
        cutoff_6h = now - timedelta(hours=6)
        for entry in entries:
            try:
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                if pub_date and pub_date >= cutoff_6h:
                    all_recent.append((source_name, entry, pub_date))
            except:
                pass
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total recent articles (last 6 hours) across all feeds: {len(all_recent)}")
    
    if all_recent:
        print(f"\n✅ Found {len(all_recent)} recent articles that should be in the feed!")
    else:
        print(f"\n⚠️  No recent articles found in RSS feeds")

if __name__ == "__main__":
    main()

