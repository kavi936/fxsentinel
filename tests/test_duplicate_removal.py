#!/usr/bin/env python3
"""
Test to check if duplicate removal is removing Telegram articles
"""

import sys
sys.path.append('backend')

def test_duplicate_removal():
    """Test duplicate removal logic"""
    
    print("🔍 Testing Duplicate Removal Logic")
    print("=" * 50)
    
    try:
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        from services.telegram_sync_wrapper import telegram_sync
        
        fresh_news = []
        
        # Fetch all news sources
        rss_news = news_aggregator.get_recent_news(hours=24)
        fresh_news.extend(rss_news)
        print(f"✅ RSS news: {len(rss_news)} articles")
        
        alt_news = alternative_news_sources.get_alternative_news(hours=24)
        fresh_news.extend(alt_news)
        print(f"✅ Alternative news: {len(alt_news)} articles")
        
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        fresh_news.extend(telegram_news)
        print(f"✅ Telegram news: {len(telegram_news)} articles")
        
        print(f"📊 Before duplicate removal: {len(fresh_news)} articles")
        
        # Check Telegram articles before duplicate removal
        telegram_before = [n for n in fresh_news if 'Telegram' in n.get('source', '')]
        print(f"📱 Telegram articles before: {len(telegram_before)}")
        
        # Apply duplicate removal (same logic as Flask)
        def remove_duplicate_news(news_list):
            """Remove duplicate news items based on title and source"""
            seen = set()
            unique_news = []
            for item in news_list:
                # Create a unique key based on title and source
                key = f"{item.get('title', '')}_{item.get('source', '')}"
                if key not in seen:
                    seen.add(key)
                    unique_news.append(item)
            return unique_news
        
        # Remove duplicates
        unique_news = remove_duplicate_news(fresh_news)
        print(f"📊 After duplicate removal: {len(unique_news)} articles")
        
        # Check Telegram articles after duplicate removal
        telegram_after = [n for n in unique_news if 'Telegram' in n.get('source', '')]
        print(f"📱 Telegram articles after: {len(telegram_after)}")
        
        if len(telegram_after) < len(telegram_before):
            print("❌ Duplicate removal removed Telegram articles!")
            print("📋 Removed Telegram articles:")
            for news in telegram_before:
                if news not in telegram_after:
                    print(f"   - {news.get('title', 'No title')} ({news.get('source', 'Unknown')})")
        else:
            print("✅ Duplicate removal preserved Telegram articles")
            
        # Check for any duplicates in Telegram articles
        telegram_titles = [n.get('title', '') for n in telegram_news]
        duplicates = [title for title in set(telegram_titles) if telegram_titles.count(title) > 1]
        if duplicates:
            print(f"⚠️ Found duplicate titles in Telegram: {duplicates}")
        else:
            print("✅ No duplicate titles in Telegram articles")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_duplicate_removal()
