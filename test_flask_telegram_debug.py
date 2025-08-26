#!/usr/bin/env python3
"""
Debug test to see what's happening when Flask calls Telegram service
"""

import sys
import os
sys.path.append('backend')

def test_flask_context():
    """Test Telegram service in Flask-like context"""
    
    print("🔍 Testing Telegram Service in Flask Context")
    print("=" * 50)
    
    # Test 1: Import the sync wrapper
    print("\n1️⃣ Testing sync wrapper import...")
    try:
        from services.telegram_sync_wrapper import telegram_sync
        print("✅ Successfully imported telegram_sync")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Test 2: Call the sync wrapper
    print("\n2️⃣ Testing sync wrapper call...")
    try:
        result = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Sync wrapper returned: {len(result)} articles")
        
        if result:
            print("📰 Sample articles:")
            for i, news in enumerate(result[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
                print(f"      Source: {news.get('source', 'Unknown')}")
        else:
            print("❌ No articles returned")
            
    except Exception as e:
        print(f"❌ Sync wrapper call error: {e}")
    
    # Test 3: Test the force refresh logic
    print("\n3️⃣ Testing force refresh logic...")
    try:
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        
        fresh_news = []
        
        # Fetch RSS news
        rss_news = news_aggregator.get_recent_news(hours=24)
        fresh_news.extend(rss_news)
        print(f"✅ RSS news: {len(rss_news)} articles")
        
        # Fetch alternative news
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        fresh_news.extend(alt_news)
        print(f"✅ Alternative news: {len(alt_news)} articles")
        
        # Fetch Telegram news
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        fresh_news.extend(telegram_news)
        print(f"✅ Telegram news: {len(telegram_news)} articles")
        
        print(f"📊 Total fresh news: {len(fresh_news)} articles")
        
        # Check for Telegram articles
        telegram_articles = [n for n in fresh_news if 'Telegram' in n.get('source', '')]
        print(f"📱 Telegram articles in fresh news: {len(telegram_articles)}")
        
        if telegram_articles:
            print("📰 Telegram articles found:")
            for i, news in enumerate(telegram_articles[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
        else:
            print("❌ No Telegram articles in fresh news")
            
    except Exception as e:
        print(f"❌ Force refresh logic error: {e}")

if __name__ == "__main__":
    test_flask_context()
