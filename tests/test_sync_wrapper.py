#!/usr/bin/env python3
"""
Test the synchronous Telegram wrapper
"""

import sys
sys.path.append('backend')

def test_sync_wrapper():
    """Test the synchronous wrapper"""
    
    print("🔍 Testing Synchronous Telegram Wrapper")
    print("=" * 50)
    
    try:
        from services.telegram_sync_wrapper import telegram_sync
        
        print("✅ Successfully imported telegram_sync")
        
        # Test the wrapper
        print("\n📰 Testing Telegram news fetch...")
        result = telegram_sync.get_recent_telegram_news(hours=24)
        
        print(f"✅ Sync wrapper result: {len(result)} articles")
        
        if result:
            print("📰 Sample articles:")
            for i, news in enumerate(result[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
        else:
            print("❌ No articles from sync wrapper")
            
    except Exception as e:
        print(f"❌ Sync wrapper error: {e}")

if __name__ == "__main__":
    test_sync_wrapper()
