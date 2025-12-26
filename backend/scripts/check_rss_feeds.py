#!/usr/bin/env python3
"""
Direct check of RSS feeds to see what they're actually returning
"""

import sys
import os
from datetime import datetime, timedelta
import feedparser

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_rss_feed(url, source_name):
    """Check a single RSS feed"""
    print(f"\n{'='*80}")
    print(f"Checking: {source_name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    try:
        feed = feedparser.parse(url)
        
        if feed.bozo:
            print(f"⚠️  Feed parsing error: {feed.bozo_exception}")
            return []
        
        print(f"✅ Feed parsed successfully")
        print(f"   Feed title: {feed.feed.get('title', 'N/A')}")
        print(f"   Total entries: {len(feed.entries)}")
        
        # Show recent entries
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_count = 0
        
        print(f"\n   Recent entries (last 24 hours):")
        for i, entry in enumerate(feed.entries[:10], 1):
            try:
                # Try to get published date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                
                title = entry.get('title', 'No title')[:70]
                
                if pub_date:
                    age = datetime.now() - pub_date
                    is_recent = pub_date >= cutoff_time
                    if is_recent:
                        recent_count += 1
                    
                    status = "✅ RECENT" if is_recent else "⏰ OLD"
                    print(f"      {i}. [{status}] {title}...")
                    print(f"         Published: {pub_date.strftime('%Y-%m-%d %H:%M:%S')} ({age})")
                else:
                    print(f"      {i}. [⚠️  NO DATE] {title}...")
                    print(f"         Link: {entry.get('link', 'N/A')[:60]}...")
                
            except Exception as e:
                print(f"      {i}. [❌ ERROR] {entry.get('title', 'No title')[:70]}...")
                print(f"         Error: {e}")
        
        print(f"\n   Summary: {recent_count}/{len(feed.entries)} entries are from last 24 hours")
        return feed.entries
        
    except Exception as e:
        print(f"❌ Error fetching feed: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Check all RSS feeds"""
    print("=" * 80)
    print("RSS FEED DIRECT CHECK")
    print("=" * 80)
    print(f"Check time: {datetime.now().isoformat()}")
    
    # RSS feeds from news_aggregator
    rss_feeds = {
        'Reuters': 'https://feeds.reuters.com/reuters/businessNews',
        'Bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
        'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        'MarketWatch': 'https://feeds.marketwatch.com/marketwatch/marketpulse/',
        'FXStreet': 'https://www.fxstreet.com/rss',
        'Investing.com Forex': 'https://www.investing.com/rss/news_forex.rss',
        'ForexLive': 'https://www.forexlive.com/feed/',
        'DailyFX': 'https://www.dailyfx.com/feeds/forex_news.xml',
    }
    
    all_entries = []
    
    for source_name, url in rss_feeds.items():
        entries = check_rss_feed(url, source_name)
        all_entries.extend(entries)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total entries across all feeds: {len(all_entries)}")
    
    # Check how many are recent
    cutoff_time = datetime.now() - timedelta(hours=24)
    recent_entries = []
    
    for entry in all_entries:
        try:
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                import time
                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                import time
                pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            
            if pub_date and pub_date >= cutoff_time:
                recent_entries.append((entry, pub_date))
        except:
            pass
    
    print(f"Recent entries (last 24 hours): {len(recent_entries)}")
    
    if recent_entries:
        print(f"\n✅ Found {len(recent_entries)} recent articles!")
        print(f"   These should be appearing in the news feed")
    else:
        print(f"\n⚠️  No recent articles found in RSS feeds")
        print(f"   This could mean:")
        print(f"   1. RSS feeds are not updating")
        print(f"   2. No news has been published in the last 24 hours")
        print(f"   3. Feed parsing is failing")

if __name__ == "__main__":
    main()

