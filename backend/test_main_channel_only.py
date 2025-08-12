#!/usr/bin/env python3
"""
Test Main Channel Only - Verify Telegram monitor excludes chat channel
"""

import asyncio
from services.telegram_monitor_user import telegram_user_monitor

async def test_main_channel_only():
    """Test that only main WatcherGuru channel is monitored"""
    
    print("📱 TESTING MAIN CHANNEL ONLY")
    print("=" * 60)
    
    print("🎯 Target Channels:")
    for channel in telegram_user_monitor.target_channels:
        print(f"   ✅ {channel}")
    print()
    
    print("❌ Excluded Channels:")
    print("   ❌ WatcherGuruChat (discussions, not news)")
    print()
    
    print("🔍 Testing Channel Access...")
    print("-" * 60)
    
    try:
        # Initialize client
        await telegram_user_monitor.initialize_client()
        
        # Test each target channel
        for channel in telegram_user_monitor.target_channels:
            print(f"📡 Testing: {channel}")
            try:
                messages = await telegram_user_monitor.get_channel_messages(channel, limit=5)
                print(f"   ✅ Success: {len(messages)} messages fetched")
                
                if messages:
                    print(f"   📰 Sample: {messages[0]['title'][:50]}...")
                    print(f"   🏷️  Source: {messages[0]['source']}")
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()
        
        # Test full news aggregation
        print("🔄 Testing Full News Aggregation...")
        print("-" * 60)
        
        all_news = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        
        print(f"📊 Total News Items: {len(all_news)}")
        print()
        
        # Show sources breakdown
        sources = {}
        for news in all_news:
            source = news.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print("📈 Sources Breakdown:")
        for source, count in sources.items():
            print(f"   {source}: {count} items")
        
        print()
        
        # Verify no chat channel content
        chat_sources = [s for s in sources.keys() if 'chat' in s.lower()]
        if chat_sources:
            print("⚠️  WARNING: Chat channel content detected!")
            for source in chat_sources:
                print(f"   ❌ {source}")
        else:
            print("✅ SUCCESS: No chat channel content detected")
        
        print()
        
        # Show sample news items
        print("📰 Sample News Items:")
        print("-" * 60)
        
        for i, news in enumerate(all_news[:5], 1):
            print(f"{i}. {news['title']}")
            print(f"   Source: {news['source']}")
            print(f"   Impact: {news['impact']}")
            print(f"   Time: {news['published_at']}")
            print()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    finally:
        await telegram_user_monitor.disconnect()

if __name__ == "__main__":
    asyncio.run(test_main_channel_only())
