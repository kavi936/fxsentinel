#!/usr/bin/env python3
"""
Test script to check Telegram channel access
"""

import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_channel_access():
    """Test access to WatcherGuru channel"""
    
    # Get credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not all([api_id, api_hash, bot_token]):
        print("❌ Missing Telegram credentials in .env file")
        return
    
    print("🔍 Testing Telegram channel access...")
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    print(f"Bot Token: {bot_token[:20]}...")
    print()
    
    # Initialize client
    client = TelegramClient('test_session', api_id, api_hash)
    
    try:
        # Start client with bot token
        await client.start(bot_token=bot_token)
        print("✅ Telegram client started successfully")
        
        # Test different channel name formats
        channel_variants = [
            'WatcherGuru',
            '@WatcherGuru',
            'WatcherGuru_Official',
            'WatcherGuruNews',
            'WatcherGuruChat'
        ]
        
        for channel_name in channel_variants:
            print(f"\n🔍 Testing: {channel_name}")
            try:
                # Try to get channel entity
                entity = await client.get_entity(channel_name)
                
                if hasattr(entity, 'username'):
                    print(f"✅ PUBLIC CHANNEL: @{entity.username}")
                    print(f"   Title: {entity.title}")
                    print(f"   Participants: {getattr(entity, 'participants_count', 'Unknown')}")
                    print(f"   Description: {getattr(entity, 'about', 'No description')[:100]}...")
                else:
                    print(f"🔒 PRIVATE CHANNEL: {entity.title}")
                    print(f"   ID: {entity.id}")
                    print(f"   Access: Limited")
                    
            except Exception as e:
                print(f"❌ Error accessing {channel_name}: {str(e)}")
        
        # Test if we can get recent messages from public channels
        print(f"\n📱 Testing message access...")
        for channel_name in channel_variants:
            try:
                entity = await client.get_entity(channel_name)
                if hasattr(entity, 'username'):
                    print(f"\n📰 Testing messages from @{entity.username}:")
                    message_count = 0
                    async for message in client.iter_messages(entity, limit=5):
                        if hasattr(message, 'text') and message.text:
                            print(f"   Message {message_count + 1}: {message.text[:100]}...")
                            message_count += 1
                        if message_count >= 3:
                            break
                    if message_count == 0:
                        print("   No text messages found")
                        
            except Exception as e:
                print(f"❌ Error getting messages from {channel_name}: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error initializing client: {e}")
    
    finally:
        await client.disconnect()
        print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_channel_access())
