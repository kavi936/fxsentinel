#!/usr/bin/env python3
"""
FXSentinel Telegram Bot Setup
Handles user registration and bot commands for alerts
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError
from .alert_service import get_alert_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBotSetup:
    def __init__(self):
        """Initialize the Telegram bot setup"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.application = None
        self.bot = None
        self.alert_service = get_alert_service()
        
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command handlers"""
        try:
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("connect", self.connect_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("test", self.test_command))
            
            # Add message handler for user setup
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            logger.info("Telegram bot handlers setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up bot handlers: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Check if this is a setup link (contains user_id)
            if context.args:
                user_id = context.args[0]
                logger.info(f"User {user_id} starting bot setup via link")
                
                # Store temporary setup data
                context.user_data['setup_user_id'] = user_id
                context.user_data['setup_step'] = 'waiting_confirmation'
                
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
    
    async def connect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /connect command"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Check if user provided user_id
            if not context.args:
                await update.message.reply_text(
                    "❌ Please provide your user ID.\n\n"
                    "Usage: /connect YOUR_USER_ID\n\n"
                    "You can find your user ID in the FXSentinel app."
                )
                return
            
            user_id = context.args[0]
            logger.info(f"User {user_id} attempting to connect Telegram account")
            
            # Verify the connection
            result = await self.alert_service.verify_telegram_connection(
                user_id=user_id,
                chat_id=str(chat_id),
                username=user.username or user.first_name
            )
            
            if result.get('success'):
                await update.message.reply_text(
                    "✅ Connection successful!\n\n"
                    "Your Telegram account is now connected to FXSentinel Alerts.\n\n"
                    "You'll receive notifications about:\n"
                    "• 🔥 Breaking forex news\n"
                    "• 📊 Economic data releases\n"
                    "• 🎯 High-impact market events\n\n"
                    "To test your setup, send: /test\n\n"
                    "To check your settings, send: /status"
                )
                
                # Send test alert
                await asyncio.sleep(2)
                await self.send_welcome_alert(user_id, chat_id)
                
            else:
                await update.message.reply_text(
                    f"❌ Connection failed: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or contact support."
                )
                
        except Exception as e:
            logger.error(f"Error in connect command: {e}")
            await update.message.reply_text("Sorry, there was an error. Please try again.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Find user by chat_id
            user_id = await self._find_user_by_chat_id(str(chat_id))
            
            if not user_id:
                await update.message.reply_text(
                    "❌ Your Telegram account is not connected to FXSentinel.\n\n"
                    "Please visit the FXSentinel app and click 'Connect Telegram Bot' to get started."
                )
                return
            
            # Get user's alert settings
            settings = await self.alert_service.get_user_alert_settings(user_id)
            
            if not settings:
                await update.message.reply_text(
                    "❌ Could not retrieve your alert settings.\n\n"
                    "Please visit the FXSentinel app to configure your preferences."
                )
                return
            
            # Format status message
            status_msg = "📊 Your Alert Settings:\n\n"
            
            # Alert types
            alert_types = settings.get('alert_types', {})
            status_msg += "🔔 Alert Types:\n"
            status_msg += f"• Live News: {'✅' if alert_types.get('liveNews') else '❌'}\n"
            status_msg += f"• Pre-News: {'✅' if alert_types.get('preNews') else '❌'}\n"
            status_msg += f"• Post-News: {'✅' if alert_types.get('postNews') else '❌'}\n\n"
            
            # Impact levels
            impact_levels = settings.get('impact_levels', {})
            status_msg += "📈 Impact Levels:\n"
            status_msg += f"• High: {'✅' if impact_levels.get('high') else '❌'}\n"
            status_msg += f"• Medium: {'✅' if impact_levels.get('medium') else '❌'}\n"
            status_msg += f"• Low: {'❌' if impact_levels.get('low') else '✅'}\n\n"
            
            # Currency pairs
            currency_pairs = settings.get('currency_pairs', [])
            status_msg += f"💱 Currency Pairs: {', '.join(currency_pairs[:5])}"
            if len(currency_pairs) > 5:
                status_msg += f" (+{len(currency_pairs) - 5} more)"
            
            status_msg += "\n\nTo change settings, visit the FXSentinel app."
            
            await update.message.reply_text(status_msg)
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text("Sorry, there was an error. Please try again.")
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Find user by chat_id
            user_id = await self._find_user_by_chat_id(str(chat_id))
            
            if not user_id:
                await update.message.reply_text(
                    "❌ Your Telegram account is not connected to FXSentinel.\n\n"
                    "Please visit the FXSentinel app and click 'Connect Telegram Bot' to get started."
                )
                return
            
            # Send test alert
            success = await self.alert_service.send_telegram_alert(
                str(chat_id),
                "🧪 <b>Test Alert - FXSentinel</b>\n\n"
                "This is a test alert to verify your setup is working correctly.\n\n"
                "If you received this message, your alerts are properly configured!\n\n"
                "⏰ " + datetime.now().strftime('%H:%M UTC'),
                parse_mode='HTML'
            )
            
            if success:
                await update.message.reply_text(
                    "✅ Test alert sent successfully!\n\n"
                    "You should have received a test message. If you didn't, please check your Telegram settings."
                )
            else:
                await update.message.reply_text(
                    "❌ Failed to send test alert.\n\n"
                    "Please try again or contact support."
                )
                
        except Exception as e:
            logger.error(f"Error in test command: {e}")
            await update.message.reply_text("Sorry, there was an error. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 <b>FXSentinel Alerts Bot Commands</b>

/start - Welcome message and setup instructions
/connect USER_ID - Connect your Telegram to FXSentinel
/status - Check your current alert settings
/test - Send a test alert to verify setup
/help - Show this help message

📱 <b>Setup Instructions:</b>
1. Visit the FXSentinel app
2. Go to the Alerts tab
3. Click "Connect Telegram Bot"
4. Follow the setup instructions
5. Send /connect YOUR_USER_ID to complete setup

🔔 <b>Alert Types:</b>
• Live News - Breaking forex news
• Pre-News - Upcoming economic events
• Post-News - Analysis after news release

💡 <b>Need Help?</b>
Visit the FXSentinel app or contact support.
        """.strip()
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        try:
            user = update.effective_user
            message_text = update.message.text
            
            # Check if user is in setup mode
            if context.user_data.get('setup_step') == 'waiting_confirmation':
                user_id = context.user_data.get('setup_user_id')
                
                if user_id and message_text.lower() in ['yes', 'confirm', 'ok', 'y']:
                    # Complete setup
                    result = await self.alert_service.verify_telegram_connection(
                        user_id=user_id,
                        chat_id=str(update.effective_chat.id),
                        username=user.username or user.first_name
                    )
                    
                    if result.get('success'):
                        await update.message.reply_text(
                            "✅ Setup completed successfully!\n\n"
                            "Your Telegram account is now connected to FXSentinel Alerts.\n\n"
                            "Send /test to verify everything is working."
                        )
                        
                        # Clear setup data
                        context.user_data.clear()
                    else:
                        await update.message.reply_text(
                            f"❌ Setup failed: {result.get('error', 'Unknown error')}\n\n"
                            "Please try again or contact support."
                        )
                else:
                    await update.message.reply_text(
                        "Please type 'yes' to confirm the setup, or send /help for more information."
                    )
            else:
                # Regular message - provide help
                await update.message.reply_text(
                    "Hi! I'm the FXSentinel Alerts bot.\n\n"
                    "Send /help to see available commands, or visit the FXSentinel app to get started."
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _find_user_by_chat_id(self, chat_id: str) -> Optional[str]:
        """Find user ID by Telegram chat ID"""
        try:
            # Search through all users to find matching chat_id
            users_ref = self.alert_service.db.collection('users')
            async for user_doc in users_ref.stream():
                user_id = user_doc.id
                
                # Check Telegram settings
                telegram_ref = user_doc.reference.collection('alert_settings').document('telegram')
                telegram_doc = await telegram_ref.get()
                
                if telegram_doc.exists:
                    telegram_data = telegram_doc.to_dict()
                    if telegram_data.get('chat_id') == chat_id:
                        return user_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by chat_id: {e}")
            return None
    
    async def send_welcome_alert(self, user_id: str, chat_id: str):
        """Send welcome alert to new user"""
        try:
            welcome_message = """
🎉 <b>Welcome to FXSentinel Alerts!</b>

Your Telegram account is now connected and ready to receive real-time market alerts.

<b>What you'll receive:</b>
• 🔥 Breaking forex news from WatcherGuru
• 📊 AI-powered market analysis
• 🎯 High-impact economic events

<b>Next steps:</b>
1. Visit the FXSentinel app
2. Configure your alert preferences
3. Choose which currency pairs to monitor
4. Set your preferred impact levels

<b>Commands:</b>
/status - Check your settings
/test - Send a test alert
/help - Show all commands

Happy trading! 📈
            """.strip()
            
            await self.alert_service.send_telegram_alert(str(chat_id), welcome_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error sending welcome alert: {e}")
    
    async def start_bot(self):
        """Start the Telegram bot"""
        try:
            if not self.application:
                logger.error("Bot application not initialized")
                return False
            
            logger.info("Starting Telegram bot...")
            await self.application.initialize()
            await self.application.start()
            
            # Run polling in a way that doesn't conflict with existing event loops
            logger.info("Bot is now running and listening for messages...")
            await self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return False
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot stopped")
                
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

# Global instance
telegram_bot_setup = TelegramBotSetup()
