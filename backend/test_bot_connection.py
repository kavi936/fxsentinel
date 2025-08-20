#!/usr/bin/env python3
"""
Test Telegram Bot Connection
Simple script to test if the bot is working
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

async def test_bot_connection():
    """Test if the bot is working"""
    try:
        from telegram import Bot
        
        # Get bot token
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found!")
            return False
        
        # Create bot instance
        bot = Bot(token=bot_token)
        
        # Get bot info
        bot_info = await bot.get_me()
        
        print("🤖 Bot Information:")
        print(f"   Name: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
        print(f"   Can Join Groups: {bot_info.can_join_groups}")
        print(f"   Can Read All Group Messages: {bot_info.can_read_all_group_messages}")
        print(f"   Supports Inline Queries: {bot_info.supports_inline_queries}")
        
        # Test webhook info
        try:
            webhook_info = await bot.get_webhook_info()
            print(f"\n🔗 Webhook Info:")
            print(f"   URL: {webhook_info.url}")
            print(f"   Has Custom Certificate: {webhook_info.has_custom_certificate}")
            print(f"   Pending Update Count: {webhook_info.pending_update_count}")
            print(f"   Last Error Date: {webhook_info.last_error_date}")
            print(f"   Last Error Message: {webhook_info.last_error_message}")
        except Exception as e:
            print(f"⚠️ Could not get webhook info: {e}")
        
        print(f"\n✅ Bot is working!")
        print(f"📱 You can now message @{bot_info.username} and send /start")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        return False

def main():
    """Main function"""
    print("🧪 Testing Telegram Bot Connection")
    print("=" * 50)
    
    success = asyncio.run(test_bot_connection())
    
    if success:
        print("\n🎉 Bot test successful!")
        print("💡 Try messaging the bot now with /start")
    else:
        print("\n❌ Bot test failed!")

if __name__ == "__main__":
    main()
