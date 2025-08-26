#!/usr/bin/env python3
"""
Test News Endpoint Telegram Only
Test only the Telegram fetching in the news endpoint context
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def test_news_endpoint_telegram_only():
    """Test only the Telegram fetching in the news endpoint context"""
    print("🔍 Testing News Endpoint Telegram Only")
    print("=" * 50)
    
    # Test 1: Direct sync wrapper test
    print("\n1️⃣ Direct sync wrapper test...")
    try:
        from backend.services.telegram_sync_wrapper import telegram_sync
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Direct sync wrapper: {len(telegram_news)} articles")
        
        if telegram_news:
            print("📰 Sample Telegram articles:")
            for i, news in enumerate(telegram_news[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print(f"     Impact: {news.get('impact', 'No impact')}")
                print()
        else:
            print("❌ No Telegram news from sync wrapper")
            
    except Exception as e:
        print(f"❌ Error in sync wrapper: {e}")
        return False
    
    # Test 2: Simulate news endpoint context
    print("\n2️⃣ Simulate news endpoint context...")
    try:
        import sys
        import os
        # Add current directory to path for imports (same as news endpoint)
        if os.path.dirname(__file__) not in sys.path:
            sys.path.insert(0, os.path.dirname(__file__))
        
        print("🔍 Attempting to import telegram_sync in news endpoint context...")
        from backend.services.telegram_sync_wrapper import telegram_sync
        print("✅ Successfully imported telegram_sync in news endpoint context")
        
        print("🔍 Calling telegram_sync.get_recent_telegram_news in news endpoint context...")
        telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"🔍 Telegram sync returned {len(telegram_news)} articles in news endpoint context")
        
        if telegram_news:
            print("📰 Sample Telegram articles in news endpoint context:")
            for i, news in enumerate(telegram_news[:3], 1):
                print(f"  {i}. {news.get('title', 'No title')}")
                print(f"     Source: {news.get('source', 'No source')}")
                print(f"     Impact: {news.get('impact', 'No impact')}")
                print()
        else:
            print("❌ No Telegram news in news endpoint context")
            
    except Exception as e:
        print(f"❌ Error in news endpoint context: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎯 Telegram-only test complete!")
    return True

if __name__ == "__main__":
    success = test_news_endpoint_telegram_only()
    
    if success:
        print("\n✅ Telegram-only test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Telegram-only test failed!")
        sys.exit(1)
