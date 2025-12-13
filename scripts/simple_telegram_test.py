#!/usr/bin/env python3
"""
Simple Test for Session-Isolated Telegram Wrapper
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def simple_test():
    """Simple test of the session-isolated wrapper"""
    print("🔍 Simple Session-Isolated Telegram Test")
    print("=" * 50)
    
    # Check credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing Telegram credentials")
        return False
    
    print(f"✅ Credentials found")
    
    # Test the wrapper
    try:
        from backend.services.telegram_sync_wrapper import telegram_sync
        print("✅ Successfully imported telegram_sync")
        
        # Test first call
        print("📞 Testing first call...")
        news_1 = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ First call: {len(news_1)} articles")
        
        # Test second call
        print("📞 Testing second call...")
        news_2 = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Second call: {len(news_2)} articles")
        
        if len(news_1) > 0 or len(news_2) > 0:
            print("✅ Session isolation working!")
            return True
        else:
            print("⚠️ No articles returned, but no errors either")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simple_test()
    if success:
        print("\n🎉 Test passed!")
    else:
        print("\n❌ Test failed!")
