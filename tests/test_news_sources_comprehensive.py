#!/usr/bin/env python3
"""
Comprehensive News Sources Test
Tests all news sources including WatcherGuru, RSS feeds, and alternative sources
"""

import requests
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:5001"  # Adjust if your backend runs on different port

def test_backend_status():
    """Test if backend is running"""
    print("🔍 Testing Backend Status...")
    try:
        response = requests.get(f"{BASE_URL}/api/hello", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend is not running: {e}")
        return False

def test_news_endpoint():
    """Test the main news endpoint"""
    print("\n🔍 Testing News Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/news", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            news_count = len(data.get('news', []))
            sources = data.get('sources', [])
            cache_status = data.get('cache_status', 'unknown')
            
            print(f"✅ News endpoint working - {news_count} articles")
            print(f"   Sources: {sources}")
            print(f"   Cache status: {cache_status}")
            
            # Show breakdown by source
            if news_count > 0:
                print("\n📊 News Breakdown by Source:")
                source_counts = {}
                for item in data.get('news', []):
                    source = item.get('source', 'Unknown')
                    source_counts[source] = source_counts.get(source, 0) + 1
                
                for source, count in source_counts.items():
                    print(f"   {source}: {count} articles")
                
                # Show sample articles
                print("\n📰 Sample Articles:")
                for i, item in enumerate(data.get('news', [])[:3], 1):
                    print(f"   {i}. {item.get('title', 'No title')[:60]}...")
                    print(f"      Source: {item.get('source', 'Unknown')}")
                    print(f"      Impact: {item.get('impact', 'Unknown')}")
                    print(f"      Pairs: {item.get('currency_pairs', [])}")
                    print()
            
            return data.get('news', [])
        else:
            print(f"❌ News endpoint failed - Status: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error testing news endpoint: {e}")
        return []

async def test_telegram_sources():
    """Test Telegram news sources specifically"""
    print("\n🔍 Testing Telegram News Sources...")
    
    try:
        # Import Telegram monitor
        from services.telegram_monitor_user import telegram_user_monitor
        
        # Test initialization
        print("📱 Testing Telegram client initialization...")
        await telegram_user_monitor.initialize_client()
        
        # Test WatcherGuru specifically
        print("\n📰 Testing WatcherGuru Channel...")
        watcherguru_messages = await telegram_user_monitor.get_channel_messages('WatcherGuru', limit=10)
        
        if watcherguru_messages:
            print(f"✅ WatcherGuru working - {len(watcherguru_messages)} messages")
            
            # Show recent messages
            print("\n📋 Recent WatcherGuru Messages:")
            for i, msg in enumerate(watcherguru_messages[:3], 1):
                print(f"   {i}. {msg.get('title', 'No title')[:50]}...")
                print(f"      Impact: {msg.get('impact', 'Unknown')}")
                print(f"      Pairs: {msg.get('currency_pairs', [])}")
                print(f"      Time: {msg.get('published_at', 'Unknown')}")
                print()
        else:
            print("⚠️ No messages found from WatcherGuru")
        
        # Test full Telegram news aggregation
        print("\n🔄 Testing Full Telegram News Aggregation...")
        all_telegram_news = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        
        if all_telegram_news:
            print(f"✅ Telegram aggregation working - {len(all_telegram_news)} total messages")
            
            # Show sources breakdown
            sources = {}
            for news in all_telegram_news:
                source = news.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print("\n📈 Telegram Sources Breakdown:")
            for source, count in sources.items():
                print(f"   {source}: {count} messages")
        else:
            print("⚠️ No Telegram news found")
        
        return all_telegram_news
        
    except Exception as e:
        print(f"❌ Error testing Telegram sources: {e}")
        return []

def test_rss_sources():
    """Test RSS news sources"""
    print("\n🔍 Testing RSS News Sources...")
    
    try:
        from services.news_aggregator import news_aggregator
        
        # Test RSS aggregation
        rss_news = news_aggregator.get_recent_news(hours=24)
        
        if rss_news:
            print(f"✅ RSS aggregation working - {len(rss_news)} articles")
            
            # Show sources breakdown
            sources = {}
            for news in rss_news:
                source = news.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print("\n📈 RSS Sources Breakdown:")
            for source, count in sources.items():
                print(f"   {source}: {count} articles")
            
            # Show sample articles
            print("\n📰 Sample RSS Articles:")
            for i, item in enumerate(rss_news[:3], 1):
                print(f"   {i}. {item.get('title', 'No title')[:60]}...")
                print(f"      Source: {item.get('source', 'Unknown')}")
                print(f"      Impact: {item.get('impact', 'Unknown')}")
                print()
        else:
            print("⚠️ No RSS news found")
        
        return rss_news
        
    except Exception as e:
        print(f"❌ Error testing RSS sources: {e}")
        return []

def test_alternative_sources():
    """Test alternative news sources"""
    print("\n🔍 Testing Alternative News Sources...")
    
    try:
        from services.alternative_news_sources import alternative_news_sources
        
        # Test alternative news aggregation
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        
        if alt_news:
            print(f"✅ Alternative sources working - {len(alt_news)} articles")
            
            # Show sources breakdown
            sources = {}
            for news in alt_news:
                source = news.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print("\n📈 Alternative Sources Breakdown:")
            for source, count in sources.items():
                print(f"   {source}: {count} articles")
            
            # Show sample articles
            print("\n📰 Sample Alternative Articles:")
            for i, item in enumerate(alt_news[:3], 1):
                print(f"   {i}. {item.get('title', 'No title')[:60]}...")
                print(f"      Source: {item.get('source', 'Unknown')}")
                print(f"      Impact: {item.get('impact', 'Unknown')}")
                print()
        else:
            print("⚠️ No alternative news found")
        
        return alt_news
        
    except Exception as e:
        print(f"❌ Error testing alternative sources: {e}")
        return []

def test_individual_rss_feeds():
    """Test individual RSS feeds"""
    print("\n🔍 Testing Individual RSS Feeds...")
    
    try:
        from services.news_aggregator import news_aggregator
        
        feeds = news_aggregator.rss_feeds
        results = {}
        
        for feed_key, feed_config in feeds.items():
            print(f"\n📡 Testing {feed_config['name']}...")
            try:
                articles = news_aggregator.fetch_rss_feed(feed_config['url'], feed_config['name'])
                results[feed_config['name']] = len(articles)
                print(f"   ✅ {feed_config['name']}: {len(articles)} articles")
                
                if articles:
                    print(f"   📰 Sample: {articles[0].get('title', 'No title')[:50]}...")
            except Exception as e:
                results[feed_config['name']] = 0
                print(f"   ❌ {feed_config['name']}: Error - {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing individual RSS feeds: {e}")
        return {}

def generate_report(news_data, telegram_data, rss_data, alt_data, rss_feed_results):
    """Generate comprehensive report"""
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE NEWS SOURCES REPORT")
    print("="*60)
    
    # Overall statistics
    total_news = len(news_data) if news_data else 0
    total_telegram = len(telegram_data) if telegram_data else 0
    total_rss = len(rss_data) if rss_data else 0
    total_alt = len(alt_data) if alt_data else 0
    
    print(f"\n📈 OVERALL STATISTICS:")
    print(f"   Total News Items: {total_news}")
    print(f"   Telegram Sources: {total_telegram}")
    print(f"   RSS Sources: {total_rss}")
    print(f"   Alternative Sources: {total_alt}")
    
    # Source breakdown
    if news_data:
        print(f"\n📊 SOURCE BREAKDOWN:")
        source_counts = {}
        for item in news_data:
            source = item.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {source}: {count} articles")
    
    # RSS Feed Status
    if rss_feed_results:
        print(f"\n📡 RSS FEED STATUS:")
        for feed, count in rss_feed_results.items():
            status = "✅ Working" if count > 0 else "❌ Failed"
            print(f"   {feed}: {status} ({count} articles)")
    
    # WatcherGuru Status
    watcherguru_found = False
    if telegram_data:
        for item in telegram_data:
            if 'WatcherGuru' in item.get('source', ''):
                watcherguru_found = True
                break
    
    print(f"\n🎯 WATCHERGURU STATUS:")
    if watcherguru_found:
        print("   ✅ WatcherGuru is working and providing news")
    else:
        print("   ❌ WatcherGuru not found in news feed")
        print("   💡 Check Telegram API credentials and channel access")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if total_news == 0:
        print("   🚨 CRITICAL: No news is being fetched")
        print("   - Check backend is running")
        print("   - Verify all news sources are accessible")
        print("   - Check network connectivity")
    
    if not watcherguru_found:
        print("   ⚠️ WatcherGuru integration needs attention")
        print("   - Verify TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        print("   - Check TELEGRAM_PHONE is set correctly")
        print("   - Ensure WatcherGuru channel is accessible")
    
    if total_rss == 0:
        print("   ⚠️ RSS feeds are not working")
        print("   - Check RSS feed URLs are accessible")
        print("   - Verify network connectivity")
        print("   - Check for rate limiting")
    
    if total_news > 0 and watcherguru_found:
        print("   ✅ All systems are working properly!")
        print("   - News aggregation is functional")
        print("   - WatcherGuru integration is active")
        print("   - Multiple sources are providing content")

async def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive News Sources Test")
    print("="*60)
    
    # Test backend status first
    if not test_backend_status():
        print("\n❌ Backend is not running. Please start the backend first.")
        return
    
    # Test all sources
    news_data = test_news_endpoint()
    telegram_data = await test_telegram_sources()
    rss_data = test_rss_sources()
    alt_data = test_alternative_sources()
    rss_feed_results = test_individual_rss_feeds()
    
    # Generate comprehensive report
    generate_report(news_data, telegram_data, rss_data, alt_data, rss_feed_results)
    
    print(f"\n🏁 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
