#!/usr/bin/env python3
"""
Simple Telegram Bot Runner
A simplified version that avoids event loop conflicts
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start_command(update, context):
    """Handle /start command"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Check if this is a setup link (contains user_id)
        if context.args:
            user_id = context.args[0]
            logger.info(f"User {user_id} starting bot setup via link")
            
            await update.message.reply_text(
                f"🎉 Welcome to FXSentinel Alerts!\n\n"
                f"I'm here to help you set up real-time market alerts.\n\n"
                f"Your user ID: {user_id}\n"
                f"Your Telegram: @{user.username or 'Unknown'}\n\n"
                f"To complete setup, please send: /connect {user_id}\n\n"
                f"Or type /help for more commands."
            )
        else:
            # Regular start command
            await update.message.reply_text(
                "🎉 Welcome to FXSentinel Alerts!\n\n"
                "I'm your personal market alert assistant. I'll send you real-time notifications about:\n"
                "• 🔥 Breaking forex news\n"
                "• 📊 Economic data releases\n"
                "• 🎯 High-impact market events\n\n"
                "To get started, visit the FXSentinel app and click 'Connect Telegram Bot'.\n\n"
                "Commands:\n"
                "/status - Check your alert settings\n"
                "/test - Send a test alert\n"
                "/help - Show all commands"
            )
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("Sorry, there was an error. Please try again.")

async def help_command(update, context):
    """Handle /help command"""
    await update.message.reply_text(
        "🤖 FXSentinel Alerts Bot - Help\n\n"
        "Available commands:\n"
        "/start - Start the bot and get welcome message\n"
        "/help - Show this help message\n"
        "/test - Send a test alert\n"
        "/status - Check your alert settings\n\n"
        "To set up alerts:\n"
        "1. Visit the FXSentinel app\n"
        "2. Go to the Alerts section\n"
        "3. Click 'Connect Telegram Bot'\n"
        "4. Follow the setup instructions"
    )

async def test_command(update, context):
    """Handle /test command"""
    await update.message.reply_text(
        "🧪 Test Alert\n\n"
        "This is a test message from FXSentinel Alerts!\n\n"
        "If you received this, your bot is working correctly.\n"
        "You'll receive real alerts when important market events happen."
    )

async def status_command(update, context):
    """Handle /status command"""
    await update.message.reply_text(
        "📊 Alert Status\n\n"
        "Your alert settings:\n"
        "• Live News: Enabled\n"
        "• Pre-News: Enabled\n"
        "• Post-News: Enabled\n"
        "• Technical Analysis: Disabled\n\n"
        "To modify settings, visit the FXSentinel app."
    )

async def main():
    """Main function to run the bot"""
    # Get bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    logger.info("🚀 Starting FXSentinel Telegram Bot...")
    logger.info(f"📱 Bot token: {bot_token[:10]}...")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("status", status_command))
    
    logger.info("🤖 Bot is starting... Press Ctrl+C to stop")
    
    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
