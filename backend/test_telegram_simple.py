#!/usr/bin/env python3
"""
Simple test script for Telegram connection
Run this to test if Telegram is working without Flask
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.telegram_monitor_user import telegram_user_monitor

async def test_telegram_simple():
    """Simple test of Telegram connection"""
    
    print("🧪 Simple Telegram Test")
    print("=" * 30)
    
    try:
        # Test connection
        print("🔌 Testing connection...")
        connected = await telegram_user_monitor.ensure_connected()
        
        if not connected:
            print("❌ Failed to connect to Telegram")
            return False
        
        print("✅ Connected to Telegram!")
        
        # Test fetching messages with higher limit
        print("\n📰 Fetching recent messages (limit: 20)...")
        messages = await telegram_user_monitor.get_channel_messages('WatcherGuru', limit=20)
        
        if messages:
            print(f"✅ Found {len(messages)} messages")
            print("\n📋 Recent messages:")
            for i, msg in enumerate(messages[:10], 1):  # Show first 10
                print(f"  {i}. {msg['title']}")
                print(f"     Time: {msg['published_at']}")
                print(f"     Impact: {msg['impact']}")
                print()
        else:
            print("⚠️ No messages found")
        
        # Also test the full news aggregation
        print("\n🔄 Testing full news aggregation...")
        all_news = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        
        if all_news:
            print(f"✅ Total Telegram news items: {len(all_news)}")
            print("\n📊 Latest 5 news items:")
            for i, news in enumerate(all_news[:5], 1):
                print(f"   {i}. {news['title']}")
                print(f"      Time: {news['published_at']}")
                print(f"      Source: {news['source']}")
                print()
        else:
            print("⚠️ No Telegram news items found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean disconnect
        await telegram_user_monitor.disconnect()

if __name__ == "__main__":
    success = asyncio.run(test_telegram_simple())
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
