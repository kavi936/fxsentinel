#!/usr/bin/env python3
"""
Generate Telegram session file locally for Railway deployment
Run this locally to create the session file, then upload to Railway
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

async def generate_telegram_session():
    """Generate Telegram session file"""
    
    # Get credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        logger.error("❌ Missing Telegram credentials in environment")
        logger.error("Please set: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return False
    
    try:
        logger.info("🚀 Generating Telegram session file...")
        logger.info(f"📱 Phone: {phone}")
        logger.info(f"🔑 API ID: {api_id}")
        
        # Create client
        client = TelegramClient('fxsentinel_user_session', api_id, api_hash)
        
        # Start the client (this will prompt for code if needed)
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
            
            # Check if session file was created
            session_file = 'fxsentinel_user_session.session'
            if os.path.exists(session_file):
                logger.info(f"✅ Session file created: {session_file}")
                logger.info("📁 You can now upload this file to Railway")
                return True
            else:
                logger.error("❌ Session file was not created")
                return False
            
        else:
            logger.error("❌ Failed to authorize Telegram session")
            return False
            
    except SessionPasswordNeededError:
        logger.error("❌ Two-factor authentication is enabled")
        logger.error("Please disable 2FA or use a different account")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error generating Telegram session: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Local Telegram Session Generator")
    print("=" * 50)
    print("This script will generate a session file that can be uploaded to Railway")
    print("Make sure you have your Telegram credentials in your .env file")
    print()
    
    # Run the setup
    success = asyncio.run(generate_telegram_session())
    
    if success:
        print()
        print("✅ Session file generated successfully!")
        print("📋 Next steps:")
        print("1. Upload fxsentinel_user_session.session to Railway")
        print("2. Deploy the updated code")
        print("3. Test the Telegram integration")
    else:
        print()
        print("❌ Session file generation failed")
        print("Please check your credentials and try again")

if __name__ == "__main__":
    main()
