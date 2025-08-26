#!/usr/bin/env python3
"""
Setup Telegram session for Railway production server
This script handles the initial authentication and session setup
"""

import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_telegram_session():
    """Setup Telegram session for production"""
    
    # Get credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        logger.error("❌ Missing Telegram credentials in environment")
        logger.error("Please set: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return False
    
    try:
        logger.info("🚀 Setting up Telegram session...")
        logger.info(f"📱 Phone: {phone}")
        logger.info(f"🔑 API ID: {api_id}")
        
        # Create client
        client = TelegramClient('fxsentinel_user_session', api_id, api_hash)
        
        # Start the client
        await client.start(phone=phone)
        
        # Check if we're authorized
        if await client.is_user_authorized():
            logger.info("✅ Telegram session authorized successfully!")
            
            # Test connection by getting our own info
            me = await client.get_me()
            logger.info(f"👤 Logged in as: {me.first_name} (@{me.username})")
            
            # Test accessing WatcherGuru channel
            try:
                # Try to get messages from WatcherGuru
                watcher_guru = await client.get_entity('WatcherGuru')
                messages = await client.get_messages(watcher_guru, limit=5)
                logger.info(f"✅ Successfully accessed WatcherGuru channel")
                logger.info(f"📰 Found {len(messages)} recent messages")
                
                # Show sample messages
                for i, msg in enumerate(messages[:3]):
                    if msg.text:
                        logger.info(f"   {i+1}. {msg.text[:100]}...")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not access WatcherGuru: {e}")
                logger.info("This might be normal if the channel is private or requires subscription")
            
            await client.disconnect()
            return True
            
        else:
            logger.error("❌ Failed to authorize Telegram session")
            return False
            
    except SessionPasswordNeededError:
        logger.error("❌ Two-factor authentication is enabled")
        logger.error("Please disable 2FA or use a different account")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error setting up Telegram session: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Railway Telegram Session Setup")
    print("=" * 50)
    
    # Check if we're on Railway
    if os.getenv('RAILWAY_ENVIRONMENT'):
        print("✅ Running on Railway production server")
    else:
        print("⚠️ Not running on Railway - this script is designed for production")
    
    # Run the setup
    success = asyncio.run(setup_telegram_session())
    
    if success:
        print("✅ Telegram session setup completed successfully!")
        print("🎉 WatcherGuru alerts should now work in the live news feed")
    else:
        print("❌ Telegram session setup failed")
        print("Please check your credentials and try again")

if __name__ == "__main__":
    main()
