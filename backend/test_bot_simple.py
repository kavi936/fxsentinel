#!/usr/bin/env python3
"""
Simple Bot Test
Test if the bot token works by sending a message
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables
load_dotenv()

async def test_bot():
    """Test the bot by getting info"""
    try:
        # Get bot token
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found!")
            return False
        
        print(f"🔑 Bot token: {bot_token[:10]}...")
        
        # Create bot instance
        bot = Bot(token=bot_token)
        
        # Get bot info
        bot_info = await bot.get_me()
        
        print(f"✅ Bot info:")
        print(f"   Name: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
        
        # Test sending a message (you'll need to provide a chat_id)
        print(f"\n📱 Bot is working!")
        print(f"💡 Try messaging @{bot_info.username} with /start")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🧪 Simple Bot Test")
    print("=" * 30)
    
    success = asyncio.run(test_bot())
    
    if success:
        print("\n🎉 Bot test successful!")
        print("📱 Now try messaging the bot in Telegram")
    else:
        print("\n❌ Bot test failed!")

if __name__ == "__main__":
    main()
