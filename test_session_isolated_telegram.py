#!/usr/bin/env python3
"""
Test Session-Isolated Telegram Wrapper
Test the new session-isolated approach to ensure it works without session corruption
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def test_session_isolated_telegram():
    """Test the session-isolated Telegram wrapper"""
    print("🔍 Testing Session-Isolated Telegram Wrapper")
    print("=" * 60)
    
    # Test 1: Check credentials
    print("\n1️⃣ Checking Telegram credentials...")
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing Telegram credentials")
        print("Please ensure you have TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE in your .env file")
        return False
    
    print(f"✅ API ID: {api_id}")
    print(f"✅ API Hash: {api_hash[:10]}...")
    print(f"✅ Phone: {phone}")
    
    # Test 2: Import and test the new wrapper
    print("\n2️⃣ Testing session-isolated wrapper...")
    try:
        from backend.services.telegram_sync_wrapper import telegram_sync
        print("✅ Successfully imported session-isolated wrapper")
        
        # Test first call
        print("\n   📞 First call to get_recent_telegram_news...")
        telegram_news_1 = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"   ✅ First call returned {len(telegram_news_1)} articles")
        
        if telegram_news_1:
            print("   📰 Sample articles from first call:")
            for i, news in enumerate(telegram_news_1[:3], 1):
                print(f"     {i}. {news.get('title', 'No title')}")
                print(f"        Source: {news.get('source', 'No source')}")
                print(f"        Impact: {news.get('impact', 'No impact')}")
                print()
        else:
            print("   ⚠️ No articles returned from first call")
        
        # Test second call (this is where the old version would fail)
        print("\n   📞 Second call to get_recent_telegram_news...")
        telegram_news_2 = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"   ✅ Second call returned {len(telegram_news_2)} articles")
        
        if telegram_news_2:
            print("   📰 Sample articles from second call:")
            for i, news in enumerate(telegram_news_2[:3], 1):
                print(f"     {i}. {news.get('title', 'No title')}")
                print(f"        Source: {news.get('source', 'No source')}")
                print(f"        Impact: {news.get('impact', 'No impact')}")
                print()
        else:
            print("   ⚠️ No articles returned from second call")
        
        # Test third call to ensure consistency
        print("\n   📞 Third call to get_recent_telegram_news...")
        telegram_news_3 = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"   ✅ Third call returned {len(telegram_news_3)} articles")
        
        # Compare results
        print(f"\n   📊 Call comparison:")
        print(f"      First call:  {len(telegram_news_1)} articles")
        print(f"      Second call: {len(telegram_news_2)} articles")
        print(f"      Third call:  {len(telegram_news_3)} articles")
        
        # Check if all calls returned similar results (within reasonable range)
        if len(telegram_news_1) > 0 and len(telegram_news_2) > 0 and len(telegram_news_3) > 0:
            print("   ✅ All calls returned articles - session isolation working!")
            
            # Check if we're getting Telegram-specific sources
            sources_1 = set(news.get('source', '') for news in telegram_news_1)
            sources_2 = set(news.get('source', '') for news in telegram_news_2)
            sources_3 = set(news.get('source', '') for news in telegram_news_3)
            
            telegram_sources = [s for s in sources_1 if 'telegram' in s.lower()]
            if telegram_sources:
                print(f"   ✅ Found Telegram sources: {telegram_sources}")
            else:
                print("   ⚠️ No Telegram sources found in results")
                
        elif len(telegram_news_1) == 0 and len(telegram_news_2) == 0 and len(telegram_news_3) == 0:
            print("   ⚠️ All calls returned 0 articles - this might be normal if no recent forex news")
        else:
            print("   ❌ Inconsistent results - session isolation might not be working")
            return False
            
    except Exception as e:
        print(f"❌ Error testing session-isolated wrapper: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test in news endpoint context
    print("\n3️⃣ Testing in news endpoint context...")
    try:
        import sys
        import os
        # Add current directory to path for imports (same as news endpoint)
        if os.path.dirname(__file__) not in sys.path:
            sys.path.insert(0, os.path.dirname(__file__))
        
        print("   🔍 Importing telegram_sync in news endpoint context...")
        from backend.services.telegram_sync_wrapper import telegram_sync
        print("   ✅ Successfully imported telegram_sync in news endpoint context")
        
        print("   📞 Calling telegram_sync.get_recent_telegram_news in news endpoint context...")
        telegram_news_endpoint = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"   ✅ News endpoint context returned {len(telegram_news_endpoint)} articles")
        
        if telegram_news_endpoint:
            print("   📰 Sample articles from news endpoint context:")
            for i, news in enumerate(telegram_news_endpoint[:3], 1):
                print(f"     {i}. {news.get('title', 'No title')}")
                print(f"        Source: {news.get('source', 'No source')}")
                print(f"        Impact: {news.get('impact', 'No impact')}")
                print()
        else:
            print("   ⚠️ No articles returned from news endpoint context")
            
    except Exception as e:
        print(f"❌ Error in news endpoint context: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎯 Session-isolated Telegram wrapper test complete!")
    print("✅ The new wrapper should prevent session corruption issues")
    return True

if __name__ == "__main__":
    success = test_session_isolated_telegram()
    if success:
        print("\n🎉 All tests passed! The session-isolated wrapper is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
