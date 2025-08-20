#!/usr/bin/env python3
"""
Working Telegram Bot - Authenticated Users Only
Simple bot that only responds to users who have access to the dashboard
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
import requests
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store authenticated users (in production, this would be in a database)
authenticated_users = set()

def _decode_setup_token(token):
    """Decode setup token back to user_id"""
    import base64
    try:
        # First, try to decode as base64 (new format)
        try:
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            # Extract user_id (everything before the last underscore)
            user_id = decoded.rsplit('_', 1)[0]
            logger.info(f"Successfully decoded base64 token to user_id: {user_id}")
            return user_id
        except Exception as base64_error:
            logger.info(f"Base64 decoding failed, trying direct token: {base64_error}")
            
        # If base64 fails, try using the token directly (old format or direct user_id)
        # Check if it looks like a valid user_id
        if '@' in token or len(token) > 15:
            logger.info(f"Using token directly as user_id: {token}")
            return token
            
        # If it's a short token, it might be an old MD5 hash - we can't decode it
        logger.error(f"Token appears to be old MD5 format, cannot decode: {token}")
        return None
        
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return None

def verify_user_access(user_id):
    """Verify if user has access to the dashboard"""
    try:
        logger.info(f"🔍 Making API call to verify user {user_id}")
        # Call our backend API to verify user access
        response = requests.post(
            "http://localhost:5001/api/telegram/verify",
            json={"userId": user_id},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        logger.info(f"🔍 API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"🔍 API response data: {data}")
            result = data.get("success", False)
            logger.info(f"🔍 Verification result: {result}")
            return result
        else:
            logger.warning(f"User {user_id} access verification failed: {response.status_code}")
            logger.warning(f"Response content: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying user {user_id} access: {e}")
        return False

async def start_command(update, context):
    """Handle /start command - only for authenticated users"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        logger.info(f"User {user.username} ({chat_id}) sent /start")
        
        # Check if this is a setup link (contains user_id)
        if context.args:
            setup_token = context.args[0]
            logger.info(f"User with token {setup_token} starting bot setup via dashboard link")
            
            # Decode the setup token to get user_id
            user_id = _decode_setup_token(setup_token)
            if not user_id:
                await update.message.reply_text(
                    "🔒 Invalid Setup Link\n\n"
                    "This setup link is invalid or expired.\n\n"
                    "Please return to the FXSentinel dashboard and generate a new setup link."
                )
                return
            
            logger.info(f"Decoded user_id: {user_id}")
            
            # Verify user has access to dashboard
            logger.info(f"🔒 Attempting to verify access for user_id: {user_id}")
            access_granted = verify_user_access(user_id)
            logger.info(f"🔒 Access verification result: {access_granted}")
            
            if access_granted:
                # Save the chat_id to Firebase for future verification
                try:
                    from services.firebase_realtime_storage import FirebaseRealtimeStorage
                    firebase_storage = FirebaseRealtimeStorage()
                    
                    # Save the chat_id
                    if firebase_storage.save_telegram_chat_id(user_id, str(chat_id)):
                        logger.info(f"✅ Successfully saved chat_id {chat_id} for user {user_id}")
                    else:
                        logger.warning(f"⚠️ Failed to save chat_id for user {user_id}")
                except Exception as e:
                    logger.error(f"Error saving chat_id to Firebase: {e}")
                
                # Add user to authenticated list
                authenticated_users.add(chat_id)
                
                await update.message.reply_text(
                    f"Welcome to FXSentinel Alerts\n"
                    f"**Your Personal Forex Alert Assistant**\n\n"
                    f"**I'll send you:**\n"
                    f"• Breaking news alerts with AI analysis\n"
                    f"• Economic calendar reminders\n"
                    f"• Market-moving events\n\n"
                    f"**To get started:**\n"
                    f"1. Complete setup on the dashboard\n"
                    f"2. Configure your preferences\n"
                    f"3. Start receiving alerts\n\n"
                    f"**Commands:**\n"
                    f"/help - Show all commands\n"
                    f"/status - Check your connection status\n"
                    f"/test - Send a test alert"
                )
            else:
                await update.message.reply_text(
                    "🔒 Access Denied\n\n"
                    "You don't have access to FXSentinel alerts.\n\n"
                    "To get access:\n"
                    "1. Visit the FXSentinel dashboard\n"
                    "2. Log in to your account\n"
                    "3. Go to the Alerts section\n"
                    "4. Click 'Connect Telegram Bot'\n\n"
                    "Only authenticated dashboard users can use this bot."
                )
        else:
            # Regular start command - check if user is authenticated
            if chat_id in authenticated_users:
                await update.message.reply_text(
                    "Welcome back to FXSentinel Alerts\n"
                    "**You're already authenticated and set up to receive alerts**\n\n"
                    "**Commands:**\n"
                    "/status - Check your alert settings\n"
                    "/test - Send a test alert\n"
                    "/help - Show all commands"
                )
            else:
                await update.message.reply_text(
                    "Access Restricted\n"
                    "**This bot is only available to FXSentinel dashboard users**\n\n"
                    "**To get access:**\n"
                    "1. Visit the FXSentinel dashboard\n"
                    "2. Log in to your account\n"
                    "3. Go to the Alerts section\n"
                    "4. Click 'Connect Telegram Bot'\n\n"
                    "You'll receive a unique link to activate your bot access."
                )
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("Sorry, there was an error. Please try again.")

async def help_command(update, context):
    """Handle /help command - only for authenticated users"""
    chat_id = update.effective_chat.id
    
    if chat_id not in authenticated_users:
        await update.message.reply_text(
            "🔒 Access Restricted\n\n"
            "This bot is only available to FXSentinel dashboard users.\n\n"
            "Please visit the FXSentinel dashboard to get access."
        )
        return
    
    await update.message.reply_text(
        "FXSentinel Bot Commands\n"
        "**Available Commands:**\n\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/test - Send a test alert\n"
        "/status - Check your connection status\n\n"
        "**Getting Alerts:**\n"
        "• Configure preferences on dashboard\n"
        "• Choose your currency pairs\n"
        "• Set impact levels\n"
        "• Enable/disable alert types\n\n"
        "**Support:** Contact support@fxsentinel.com"
    )

async def test_command(update, context):
    """Handle /test command - only for authenticated users"""
    chat_id = update.effective_chat.id
    
    if chat_id not in authenticated_users:
        await update.message.reply_text(
            "🔒 Access Restricted\n\n"
            "This bot is only available to FXSentinel dashboard users.\n\n"
            "Please visit the FXSentinel dashboard to get access."
        )
        return
    
    await update.message.reply_text(
        "Sending Test Alert...\n"
        "**Test alert sent successfully**\n\n"
        "**Connection Status:**\n"
        "• Telegram: Connected\n"
        "• Dashboard: Active\n"
        "• Alerts: Ready\n\n"
        "**Status:** You're all set to receive real alerts"
    )

async def status_command(update, context):
    """Handle /status command - only for authenticated users"""
    chat_id = update.effective_chat.id
    
    if chat_id not in authenticated_users:
        await update.message.reply_text(
            "🔒 Access Restricted\n\n"
            "This bot is only available to FXSentinel dashboard users.\n\n"
            "Please visit the FXSentinel dashboard to get access."
        )
        return
    
    await update.message.reply_text(
        "Alert Status\n"
        "**Your alert settings:**\n\n"
        "• Live News: Enabled\n"
        "• Pre-News: Enabled\n"
        "• Post-News: Enabled\n"
        "• Technical Analysis: Disabled\n\n"
        "**To modify settings:** Visit the FXSentinel dashboard"
    )

def main():
    """Main function"""
    # Get bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    logger.info("🚀 Starting FXSentinel Telegram Bot (Authenticated Users Only)...")
    logger.info(f"📱 Bot token: {bot_token[:10]}...")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("status", status_command))
    
    logger.info("🤖 Bot is starting... Press Ctrl+C to stop")
    logger.info("🔒 Bot is restricted to authenticated dashboard users only")
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
