#!/usr/bin/env python3
"""
FXSentinel Telegram Bot Starter
Starts the Telegram bot as a separate process to handle user commands
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start_telegram_bot():
    """Start the Telegram bot"""
    try:
        from services.telegram_bot_setup import telegram_bot_setup
        
        # Check if bot token is configured
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
            logger.error("💡 Please add your bot token to the .env file")
            return False
        
        logger.info("🚀 Starting FXSentinel Telegram Bot...")
        logger.info(f"📱 Bot token: {bot_token[:10]}...")
        
        # Start the bot and keep it running
        logger.info("🤖 Bot is starting... Press Ctrl+C to stop")
        await telegram_bot_setup.start_bot()
        
        return True
            
    except ImportError as e:
        logger.error(f"❌ Error importing telegram bot setup: {e}")
        logger.error("💡 Make sure all dependencies are installed")
        return False
    except Exception as e:
        logger.error(f"❌ Error starting Telegram bot: {e}")
        return False

def main():
    """Main function"""
    print("🤖 FXSentinel Telegram Bot Starter")
    print("=" * 50)
    
    # Check environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        print("💡 Please add your bot token to the .env file")
        print("🔗 Get a bot token from @BotFather on Telegram")
        return
    
    print(f"✅ Bot token found: {bot_token[:10]}...")
    print("🚀 Starting bot...")
    
    try:
        # Run the bot
        asyncio.run(start_telegram_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
