#!/usr/bin/env python3
"""
Test Deduplication Logic
See what happens to Telegram news during deduplication
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def test_deduplication():
    """Test the deduplication logic with Telegram news"""
    print("🔍 Testing Deduplication Logic")
    print("=" * 50)
    
    # Import the deduplication function
    from backend.app import remove_duplicate_news, clean_news_title
    
    # Create sample Telegram news
    telegram_news = [
        {
            "id": 3303827184124807074,
            "title": "**JUST IN:** 🇺🇸 Federal Reserve Governor Lisa Cook says President Trump has \"no authority\" to fire h",
            "summary": "\n\"I will continue to carry out my duties.\"",
            "source": "Telegram - WatcherGuru",
            "url": "",
            "published_at": "2025-08-26T03:54:58+00:00",
            "impact": "high",
            "currency_pairs": [],
            "type": "TELEGRAM_USER",
            "status": "PUBLISHED",
            "message_id": 10286,
            "channel": "WatcherGuru"
        },
        {
            "id": 3303827184124807075,
            "title": "**BREAKING:** 🇺🇸 President Trump fires Federal Reserve Governor Lisa Cook.",
            "summary": "Breaking news about Fed Governor",
            "source": "Telegram - WatcherGuru",
            "url": "",
            "published_at": "2025-08-26T03:55:00+00:00",
            "impact": "high",
            "currency_pairs": [],
            "type": "TELEGRAM_USER",
            "status": "PUBLISHED",
            "message_id": 10287,
            "channel": "WatcherGuru"
        }
    ]
    
    # Create sample RSS news
    rss_news = [
        {
            "id": 123456789,
            "title": "Federal Reserve Governor Lisa Cook says President Trump has no authority to fire her",
            "summary": "Fed Governor responds to Trump comments",
            "source": "Bloomberg",
            "url": "https://www.bloomberg.com/news/article1",
            "published_at": "2025-08-26T03:56:00+00:00",
            "impact": "high",
            "currency_pairs": ["USD"],
            "type": "RSS_FEED",
            "status": "PUBLISHED"
        }
    ]
    
    # Combine all news
    all_news = telegram_news + rss_news
    
    print(f"📊 Original news count: {len(all_news)}")
    print("📰 Original news:")
    for i, news in enumerate(all_news, 1):
        print(f"  {i}. {news.get('title', 'No title')}")
        print(f"     Source: {news.get('source', 'No source')}")
        print(f"     URL: '{news.get('url', 'No URL')}'")
        print()
    
    # Test title cleaning
    print("🧹 Testing title cleaning:")
    for news in all_news:
        original_title = news.get('title', '')
        cleaned_title = clean_news_title(original_title)
        print(f"  Original: '{original_title}'")
        print(f"  Cleaned:  '{cleaned_title}'")
        print()
    
    # Test deduplication
    print("🔄 Testing deduplication:")
    unique_news = remove_duplicate_news(all_news)
    
    print(f"📊 After deduplication: {len(unique_news)} articles")
    print("📰 Unique news:")
    for i, news in enumerate(unique_news, 1):
        print(f"  {i}. {news.get('title', 'No title')}")
        print(f"     Source: {news.get('source', 'No source')}")
        print(f"     URL: '{news.get('url', 'No URL')}'")
        print()
    
    # Check if Telegram news survived
    telegram_survived = [news for news in unique_news if 'Telegram' in news.get('source', '')]
    print(f"📊 Telegram news survived: {len(telegram_survived)} out of {len(telegram_news)}")
    
    if telegram_survived:
        print("✅ Telegram news survived deduplication!")
    else:
        print("❌ All Telegram news was removed during deduplication!")
    
    return len(telegram_survived) > 0

if __name__ == "__main__":
    success = test_deduplication()
    
    if success:
        print("\n✅ Deduplication test passed!")
        sys.exit(0)
    else:
        print("\n❌ Deduplication test failed!")
        sys.exit(1)
