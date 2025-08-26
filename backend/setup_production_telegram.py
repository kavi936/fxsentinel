#!/usr/bin/env python3
"""
Setup Telegram user session for production server
Run this once on production to authenticate and save the session
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

async def setup_production_telegram():
    """Setup Telegram session for production user account"""
    
    # Get credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    session_name = 'fxsentinel_user_session'
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing Telegram credentials in environment")
        print("Please set: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return False
    
    print("🔐 Setting up Telegram user session for production...")
    print(f"📱 Phone: {phone}")
    print(f"🆔 API ID: {api_id}")
    print(f"🔑 API Hash: {api_hash[:10]}...")
    print("=" * 50)
    
    try:
        # Create client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start client (this will prompt for verification code)
        print("📞 Starting Telegram client...")
        await client.start(phone=phone)
        
        # Test connection
        if await client.is_user_authorized():
            print("✅ Successfully authenticated!")
            
            # Get user info
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} (@{me.username})")
            
            # Test WatcherGuru access
            print("\n🔍 Testing WatcherGuru channel access...")
            try:
                channel = await client.get_entity('WatcherGuru')
                print(f"✅ Can access WatcherGuru channel: {channel.title}")
                
                # Test message fetching
                print("📰 Testing message fetching...")
                message_count = 0
                async for message in client.iter_messages(channel, limit=5):
                    if hasattr(message, 'text') and message.text:
                        print(f"   Message {message_count + 1}: {message.text[:100]}...")
                        message_count += 1
                        if message_count >= 3:
                            break
                
                print(f"✅ Successfully fetched {message_count} messages from WatcherGuru")
                
            except Exception as e:
                print(f"⚠️ Warning: Could not access WatcherGuru: {e}")
            
            print("\n🎉 Production setup complete! Session saved.")
            print("💡 You can now run the main application without re-authentication.")
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False
    finally:
        if 'client' in locals():
            await client.disconnect()

if __name__ == "__main__":
    print("🚀 Production Telegram User Session Setup")
    print("=" * 50)
    
    success = asyncio.run(setup_production_telegram())
    
    if success:
        print("\n✅ Production setup successful! You can now run your application.")
    else:
        print("\n❌ Production setup failed. Please check your credentials and try again.")
