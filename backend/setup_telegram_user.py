#!/usr/bin/env python3
"""
Setup script for Telegram user authentication
Run this once to authenticate and save the session
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables
load_dotenv()

async def setup_telegram_session():
    """Setup Telegram session for user account"""
    
    # Get credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    session_name = 'fxsentinel_user_session'
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing Telegram credentials in .env file")
        print("Please set: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return False
    
    print("🔐 Setting up Telegram user session...")
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
            
            # Test channel access
            print("\n🔍 Testing WatcherGuru channel access...")
            try:
                channel = await client.get_entity('WatcherGuru')
                print(f"✅ Can access WatcherGuru channel: {channel.title}")
            except Exception as e:
                print(f"⚠️ Warning: Could not access WatcherGuru: {e}")
            
            print("\n🎉 Setup complete! Session saved.")
            print("💡 You can now run the main application without re-authentication.")
            
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False
    finally:
        # Disconnect
        if 'client' in locals():
            await client.disconnect()

if __name__ == "__main__":
    print("🚀 Telegram User Session Setup")
    print("=" * 50)
    
    success = asyncio.run(setup_telegram_session())
    
    if success:
        print("\n✅ Setup successful! You can now run your application.")
    else:
        print("\n❌ Setup failed. Please check your credentials and try again.")
