#!/usr/bin/env python3
"""
Test script to fetch messages from WatcherGuru using user account
"""

import asyncio
from services.telegram_monitor_user import telegram_user_monitor

async def test_watcherguru_messages():
    """Test fetching messages from WatcherGuru"""
    
    print("🔍 Testing WatcherGuru message fetching...")
    print("=" * 50)
    
    try:
        # Initialize the user monitor
        print("📱 Initializing Telegram user client...")
        await telegram_user_monitor.initialize_client()
        
        # Test individual channel
        print("\n📰 Testing WatcherGuru channel...")
        messages = await telegram_user_monitor.get_channel_messages('WatcherGuru', limit=10)
        
        if messages:
            print(f"✅ Successfully fetched {len(messages)} messages from WatcherGuru!")
            print("\n📋 Recent Messages:")
            print("-" * 50)
            
            for i, msg in enumerate(messages[:5], 1):
                print(f"\n{i}. {msg['title']}")
                print(f"   Source: {msg['source']}")
                print(f"   Impact: {msg['impact'].upper()}")
                print(f"   Time: {msg['published_at']}")
                print(f"   Currency Pairs: {msg['currency_pairs']}")
                print(f"   Summary: {msg['summary'][:100]}...")
                print("-" * 30)
        else:
            print("⚠️ No forex-related messages found in recent posts")
            print("   (This could mean no recent forex content or different keywords needed)")
        
        # Test the full news aggregation
        print("\n🔄 Testing full news aggregation...")
        all_news = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        
        if all_news:
            print(f"✅ Total Telegram news items: {len(all_news)}")
            print("\n📊 News Summary:")
            for i, news in enumerate(all_news[:3], 1):
                print(f"   {i}. {news['title']} ({news['source']})")
        else:
            print("⚠️ No Telegram news items found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you've run the setup script successfully")
        print("2. Check your .env file has correct credentials")
        print("3. Ensure you have internet connection")
    
    finally:
        # Disconnect
        await telegram_user_monitor.disconnect()
        print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_watcherguru_messages())
