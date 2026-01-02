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
    
    async def _check_subscription_status(self, user_id: str, email: str = None) -> Dict[str, Any]:
        """Check if user has valid subscription status with caching"""
        try:
            from .subscription_cache import get_subscription_status_async
            
            is_valid, error = await get_subscription_status_async(user_id)
            
            return {
                'has_access': is_valid,
                'status': 'valid' if is_valid else 'invalid',
                'error': error
            }
            
        except Exception as e:
            logger.error(f"Error checking subscription status: {e}")
            return {
                'has_access': False,
                'status': 'error',
                'error': str(e)
            }
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Check if this is a setup link (contains user_id)
            if context.args:
                user_id = context.args[0]
                logger.info(f"User {user_id} starting bot setup via link")
                
                # REMOVED: Subscription check - alerts are now available to all users (paid, developer, freemium, etc.)
                # All users can set up and use Telegram alerts regardless of subscription status
                subscription_check = await self._check_subscription_status(
                    user_id, 
                    user.username or user.first_name
                )
                # Note: subscription_check is still retrieved for display purposes, but access is not blocked
                
                # Store temporary setup data
                context.user_data['setup_user_id'] = user_id
                context.user_data['setup_step'] = 'waiting_confirmation'
                
                await update.message.reply_text(
                    f"Welcome to FXSentinel Alerts\n\n"
                    f"I'm here to help you set up real-time market alerts.\n\n"
                    f"Your user ID: {user_id}\n"
                    f"Your Telegram: @{user.username or 'Unknown'}\n"
                    f"Subscription Status: {subscription_check['status'].title()}\n\n"
                    f"To complete setup, please send: /connect {user_id}\n\n"
                    f"Or type /help for more commands."
                )
            else:
                # Regular start command
                await update.message.reply_text(
                    "Welcome to FXSentinel Alerts\n\n"
                    "I'm your personal market alert assistant. I'll send you real-time notifications about:\n"
                    "• Breaking forex news\n"
                    "• Economic data releases\n"
                    "• High-impact market events\n\n"
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
                    "Please provide your user ID.\n\n"
                    "Usage: /connect YOUR_USER_ID\n\n"
                    "You can find your user ID in the FXSentinel app."
                )
                return
            
            user_id = context.args[0]
            logger.info(f"User {user_id} attempting to connect Telegram account")
            
            # Check subscription status before allowing connection
            # REMOVED: Subscription check - alerts are now available to all users
            subscription_check = await self._check_subscription_status(
                user_id, 
                user.username or user.first_name
            )
            # Note: subscription_check is still retrieved for display purposes, but access is not blocked
            
            # Verify the connection
            result = await self.alert_service.verify_telegram_connection(
                user_id=user_id,
                chat_id=str(chat_id),
                username=user.username or user.first_name
            )
            
            if result.get('success'):
                # Store the chat_id to user_id mapping for future lookups
                await self._store_chat_id_mapping(str(chat_id), user_id)
                
                await update.message.reply_text(
                    "Connection successful\n\n"
                    "Your Telegram account is now connected to FXSentinel Alerts.\n\n"
                    f"Subscription Status: {subscription_check['status'].title()}\n\n"
                    "You'll receive notifications about:\n"
                    "• Breaking forex news\n"
                    "• Economic data releases\n"
                    "• High-impact market events\n\n"
                    "To test your setup, send: /test\n\n"
                    "To check your settings, send: /status"
                )
                
                # Send test alert
                await asyncio.sleep(2)
                await self.send_welcome_alert(user_id, chat_id)
                
            else:
                await update.message.reply_text(
                    f"Connection failed: {result.get('error', 'Unknown error')}\n\n"
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
                    "Your Telegram account is not connected to FXSentinel.\n\n"
                    "Please visit the FXSentinel app and click 'Connect Telegram Bot' to get started."
                )
                return
            
            # Check subscription status
            subscription_check = await self._check_subscription_status(user_id)
            
            # REMOVED: Subscription check - alerts are now available to all users
            # Note: subscription_check is still retrieved for display purposes, but access is not blocked
            
            # Get user's alert settings
            # Note: user_id might be hashed, so we need to handle both cases
            settings = None
            
            # Try getting settings with the user_id as-is (might be hashed)
            try:
                # If user_id looks like a hash (32 hex chars), get settings directly
                import re
                if re.match(r'^[a-f0-9]{32}$', user_id):
                    # Already hashed, get settings directly
                    settings_path = f"alerts/users/{user_id}/settings"
                    settings_result = self.alert_service.firebase_storage._make_request('GET', settings_path)
                    if settings_result and isinstance(settings_result, dict):
                        # Merge with defaults
                        from services.firebase_realtime_storage import FirebaseRealtimeStorage
                        default_settings = FirebaseRealtimeStorage().default_settings.copy()
                        default_settings.update(settings_result)
                        settings = default_settings
                else:
                    # Not hashed, use normal method
                    settings = await self.alert_service.get_user_alert_settings(user_id)
            except Exception as e:
                logger.error(f"Error getting settings: {e}")
                # Fallback: try normal method
                try:
                    settings = await self.alert_service.get_user_alert_settings(user_id)
                except:
                    pass
            
            if not settings:
                await update.message.reply_text(
                    "Could not retrieve your alert settings.\n\n"
                    "Please visit the FXSentinel app to configure your preferences."
                )
                return
            
            # Format status message
            status_msg = "<b>Your Alert Settings</b>\n\n"
            
            # Subscription status
            status_msg += f"<b>Subscription:</b> {subscription_check['status'].title()}\n\n"
            
            # Alert types - check both old and new structure
            preferences = settings.get('preferences', {})
            alert_types = preferences.get('alertTypes', settings.get('alert_types', {}))
            
            status_msg += "<b>Alert Types:</b>\n"
            if isinstance(alert_types, dict):
                status_msg += f"• Live News: {'Enabled' if alert_types.get('liveNews', True) else 'Disabled'}\n"
                status_msg += f"• Pre-News: {'Enabled' if alert_types.get('preNews', True) else 'Disabled'}\n"
                status_msg += f"• Post-News: {'Enabled' if alert_types.get('postNews', True) else 'Disabled'}\n"
                status_msg += f"• Technical Analysis: {'Enabled' if alert_types.get('technicalAnalysis', False) else 'Disabled'}\n\n"
            else:
                status_msg += "• All types enabled\n\n"
            
            # Impact levels - check both old and new structure
            impact_levels = preferences.get('impactLevels', settings.get('impact_levels', {}))
            status_msg += "<b>Impact Levels:</b>\n"
            if isinstance(impact_levels, dict):
                status_msg += f"• High: {'Enabled' if impact_levels.get('high', True) else 'Disabled'}\n"
                status_msg += f"• Medium: {'Enabled' if impact_levels.get('medium', True) else 'Disabled'}\n"
                status_msg += f"• Low: {'Disabled' if impact_levels.get('low', False) else 'Enabled'}\n\n"
            else:
                status_msg += "• All levels enabled\n\n"
            
            # Currency pairs - check both old and new structure
            currency_pairs = preferences.get('currencyPairs', settings.get('currency_pairs', []))
            if currency_pairs:
                status_msg += f"<b>Currency Pairs:</b> {', '.join(currency_pairs[:5])}"
                if len(currency_pairs) > 5:
                    status_msg += f" (+{len(currency_pairs) - 5} more)"
                status_msg += "\n"
            else:
                status_msg += "<b>Currency Pairs:</b> All pairs\n"
            
            status_msg += "\nTo change settings, visit the FXSentinel app."
            
            await update.message.reply_text(status_msg, parse_mode='HTML')
            
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
                    "Your Telegram account is not connected to FXSentinel.\n\n"
                    "Please visit the FXSentinel app and click 'Connect Telegram Bot' to get started."
                )
                return
            
            # Check subscription status
            subscription_check = await self._check_subscription_status(user_id)
            
            # REMOVED: Subscription check - alerts are now available to all users
            # Note: subscription_check is still retrieved for display purposes, but access is not blocked
            
            # Send test alert
            success = await self.alert_service.send_telegram_alert(
                str(chat_id),
                "<b>Test Alert - FXSentinel</b>\n\n"
                "This is a test alert to verify your setup is working correctly.\n\n"
                "If you received this message, your alerts are properly configured.\n\n"
                "Time: " + datetime.now().strftime('%H:%M UTC'),
                parse_mode='HTML'
            )
            
            if success:
                await update.message.reply_text(
                    "Test alert sent successfully\n\n"
                    "You should have received a test message. If you didn't, please check your Telegram settings."
                )
            else:
                await update.message.reply_text(
                    "Failed to send test alert\n\n"
                    "Please try again or contact support."
                )
                
        except Exception as e:
            logger.error(f"Error in test command: {e}")
            await update.message.reply_text("Sorry, there was an error. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
<b>FXSentinel Alerts Bot Commands</b>

/start - Welcome message and setup instructions
/connect USER_ID - Connect your Telegram to FXSentinel
/status - Check your current alert settings
/test - Send a test alert to verify setup
/help - Show this help message

<b>Setup Instructions:</b>
1. Visit the FXSentinel app
2. Go to the Alerts tab
3. Click "Connect Telegram Bot"
4. Follow the setup instructions
5. Send /connect YOUR_USER_ID to complete setup

<b>Alert Types:</b>
• Live News - Breaking forex news
• Pre-News - Upcoming economic events
• Post-News - Analysis after news release

<b>Need Help?</b>
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
                            "Setup completed successfully\n\n"
                            "Your Telegram account is now connected to FXSentinel Alerts.\n\n"
                            "Send /test to verify everything is working."
                        )
                        
                        # Clear setup data
                        context.user_data.clear()
                    else:
                        await update.message.reply_text(
                            f"Setup failed: {result.get('error', 'Unknown error')}\n\n"
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
        """Find user ID by Telegram chat ID using Firebase Realtime Database"""
        try:
            # Use Firebase Realtime Database to find user by chat_id
            # We'll store a mapping of chat_id to user_id in the database
            import hashlib
            
            # First, try to find the mapping directly
            mapping_path = f"telegram_mappings/{chat_id}"
            mapping_result = self.alert_service.firebase_storage._make_request('GET', mapping_path)
            
            if mapping_result and isinstance(mapping_result, dict) and 'user_id' in mapping_result:
                logger.info(f"Found user mapping for chat_id {chat_id}: {mapping_result['user_id']}")
                return mapping_result['user_id']
            
            # If no direct mapping, we need to search through all users
            # This is less efficient but handles legacy data
            logger.info(f"No direct mapping found for chat_id {chat_id}, searching through users...")
            
            # Get all users from the alerts directory
            users_path = "alerts/users"
            users_result = self.alert_service.firebase_storage._make_request('GET', users_path)
            
            if not users_result or not isinstance(users_result, dict):
                logger.warning("No users found in Firebase Realtime Database")
                return None
            
            # Search through each user's settings to find matching chat_id
            for safe_user_id, user_data in users_result.items():
                if isinstance(user_data, dict) and 'settings' in user_data:
                    settings = user_data['settings']
                    if isinstance(settings, dict) and 'channels' in settings:
                        channels = settings['channels']
                        if isinstance(channels, dict) and 'telegram' in channels:
                            telegram_settings = channels['telegram']
                            if isinstance(telegram_settings, dict) and telegram_settings.get('chatId') == chat_id:
                                # Found the user, now we need to get the original user_id
                                # Since we're using hashed user_ids, we need to store this mapping
                                logger.info(f"Found user with chat_id {chat_id} in settings")
                                
                                # Try to get the original user_id from a reverse mapping
                                # For now, we'll return the hashed ID and let the calling code handle it
                                return safe_user_id
            
            logger.warning(f"No user found with chat_id {chat_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by chat_id: {e}")
            return None
    
    async def _store_chat_id_mapping(self, chat_id: str, user_id: str) -> bool:
        """Store mapping of chat_id to user_id in Firebase Realtime Database"""
        try:
            mapping_data = {
                'user_id': user_id,
                'chat_id': chat_id,
                'created_at': datetime.now().isoformat()
            }
            
            mapping_path = f"telegram_mappings/{chat_id}"
            result = self.alert_service.firebase_storage._make_request('PUT', mapping_path, mapping_data)
            
            if result is not None:
                logger.info(f"Stored chat_id mapping: {chat_id} -> {user_id}")
                return True
            else:
                logger.error(f"Failed to store chat_id mapping for {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing chat_id mapping: {e}")
            return False
    
    async def send_welcome_alert(self, user_id: str, chat_id: str):
        """Send welcome alert to new user"""
        try:
            welcome_message = """
<b>Welcome to FXSentinel Alerts</b>

Your Telegram account is now connected and ready to receive real-time market alerts.

<b>What you'll receive:</b>
• Breaking forex news from WatcherGuru
• AI-powered market analysis
• High-impact economic events

<b>Next steps:</b>
1. Visit the FXSentinel app
2. Configure your alert preferences
3. Choose which currency pairs to monitor
4. Set your preferred impact levels

<b>Commands:</b>
/status - Check your settings
/test - Send a test alert
/help - Show all commands

Happy trading!
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
