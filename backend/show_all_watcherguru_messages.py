#!/usr/bin/env python3
"""
Show all messages from WatcherGuru (including non-forex ones)
"""

import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def show_all_messages():
    """Show all recent messages from WatcherGuru"""
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    client = TelegramClient('fxsentinel_user_session', api_id, api_hash)
    
    try:
        await client.start()
        print("🔍 Fetching ALL recent messages from WatcherGuru...")
        print("=" * 60)
        
        # Get entity
        entity = await client.get_entity('WatcherGuru')
        print(f"📱 Channel: {entity.title}")
        print(f"👥 Subscribers: {getattr(entity, 'participants_count', 'Unknown')}")
        print(f"📝 Description: {getattr(entity, 'about', 'No description')}")
        print()
        
        # Get recent messages (all, not just forex-related)
        print("📰 Recent Messages (Last 10):")
        print("-" * 60)
        
        message_count = 0
        async for message in client.iter_messages(entity, limit=10):
            if hasattr(message, 'text') and message.text:
                message_count += 1
                print(f"\n{message_count}. {message.text[:200]}...")
                print(f"   Time: {message.date}")
                print(f"   ID: {message.id}")
                print("-" * 40)
                
                if message_count >= 10:
                    break
        
        if message_count == 0:
            print("No text messages found in recent posts")
        else:
            print(f"\n✅ Found {message_count} recent messages")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(show_all_messages())
