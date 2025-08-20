#!/usr/bin/env python3
"""
FXSentinel Alert Service
Handles user alert preferences and sends notifications via Telegram
Uses Firebase Realtime Database instead of Firestore
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from telegram import Bot
from telegram.error import TelegramError
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
from .firebase_realtime_storage import FirebaseRealtimeStorage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        """Initialize the alert service"""
        self.telegram_bot = None
        self.firebase_storage = FirebaseRealtimeStorage()
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Telegram bot and Firebase Realtime Database"""
        try:
            # Initialize Telegram bot with proper connection settings
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if bot_token:
                # Use HTTPXRequest with proper connection pool settings
                request = HTTPXRequest(
                    connection_pool_size=8,
                    connect_timeout=30.0,
                    read_timeout=30.0,
                    write_timeout=30.0,
                    pool_timeout=30.0
                )
                self.telegram_bot = Bot(token=bot_token, request=request)
                logger.info("Telegram bot initialized with connection pool settings")
            else:
                logger.warning("TELEGRAM_BOT_TOKEN not found in environment")
            
            # Test Firebase Realtime Database connection
            if self.firebase_storage.test_connection():
                logger.info("Firebase Realtime Database connected")
            else:
                logger.warning("Firebase Realtime Database connection failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            self.telegram_bot = None
    
    async def setup_telegram_bot(self, user_id: str) -> Dict[str, Any]:
        """Generate unique bot link for user setup"""
        try:
            if not self.telegram_bot:
                # Return mock setup for testing when bot is not configured
                logger.warning("Telegram bot not configured, returning mock setup")
                return {
                    "success": True,
                    "botUsername": "@FXSentinelAlertsBot",
                    "botLink": "https://t.me/FXSentinelAlertsBot",
                    "instructions": [
                        "1. Click the link below to start the bot",
                        "2. Send /start to begin setup", 
                        "3. Follow the bot instructions to complete setup",
                        "4. Return here and click 'Verify Connection'"
                    ],
                    "mock": True  # Indicate this is a mock response
                }
            
            # Get bot info with proper error handling
            try:
                bot_info = await self.telegram_bot.get_me()
                
                # Create unique setup link
                setup_link = f"https://t.me/{bot_info.username}?start={user_id}"
                
                return {
                    "success": True,
                    "botUsername": f"@{bot_info.username}",
                    "botLink": setup_link,
                    "instructions": [
                        "1. Click the link below to start the bot",
                        "2. Send /start to begin setup",
                        "3. Follow the bot instructions to complete setup"
                    ]
                }
            except Exception as bot_error:
                logger.error(f"Error getting bot info: {bot_error}")
                # Fallback to known bot info if we can't get it from API
                return {
                    "success": True,
                    "botUsername": "@FXSentinelAlertsBot",
                    "botLink": f"https://t.me/FXSentinelAlertsBot?start={user_id}",
                    "instructions": [
                        "1. Click the link below to start the bot",
                        "2. Send /start to begin setup",
                        "3. Follow the bot instructions to complete setup"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error setting up Telegram bot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_telegram_connection(self, user_id: str) -> Dict[str, Any]:
        """Verify user has completed Telegram bot setup"""
        try:
            if not self.telegram_bot:
                # Return mock verification when bot is not configured
                logger.warning("Telegram bot not configured, returning mock verification")
                return {
                    "connected": True,
                    "chatId": "mock_chat_id_123",
                    "username": "mock_user",
                    "mock": True
                }
            
            # Check if user has a chat ID stored
            user_settings = self.firebase_storage.get_user_alert_settings(user_id)
            if user_settings and user_settings.get('telegram_chat_id'):
                return {
                    "connected": True,
                    "chatId": user_settings['telegram_chat_id'],
                    "username": user_settings.get('telegram_username', 'Unknown')
                }
            else:
                return {
                    "connected": False,
                    "error": "No chat ID found. Please complete bot setup first."
                }
                
        except Exception as e:
            logger.error(f"Error verifying Telegram connection: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def send_telegram_alert(self, chat_id: str, message: str, parse_mode: str = 'HTML') -> bool:
        """Send alert via Telegram"""
        try:
            if not self.telegram_bot:
                logger.warning("Telegram bot not configured, cannot send alert")
                return False
            
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def send_email_alert(self, email: str, subject: str, content: str) -> bool:
        """Send alert via email"""
        try:
            # Email implementation would go here
            # For now, just log that we would send an email
            logger.info(f"Would send email to {email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def process_alert(self, alert_data: Dict[str, Any], user_settings: Dict[str, Any]) -> bool:
        """Process and send alert to user based on their settings"""
        try:
            # Check if user wants this type of alert
            if not self._should_send_alert(alert_data, user_settings):
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(user_settings):
                return False
            
            # Send via configured channels
            success = True
            
            if user_settings.get('channels', {}).get('telegram', {}).get('enabled'):
                telegram_success = await self.send_telegram_alert(
                    user_settings['channels']['telegram']['chatId'],
                    self._format_telegram_message(alert_data)
                )
                success = success and telegram_success
            
            if user_settings.get('channels', {}).get('email', {}).get('enabled'):
                email_success = self.send_email_alert(
                    user_settings['channels']['email']['address'],
                    alert_data['title'],
                    self._format_email_message(alert_data)
                )
                success = success and email_success
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            return False
    
    def _should_send_alert(self, alert_data: Dict[str, Any], user_settings: Dict[str, Any]) -> bool:
        """Check if user should receive this alert based on their preferences"""
        try:
            preferences = user_settings.get('preferences', {})
            
            # Check impact level
            alert_impact = alert_data.get('impact_level', 'medium')
            if not preferences.get('impactLevels', {}).get(alert_impact, True):
                return False
            
            # Check alert type
            alert_type = alert_data.get('type', 'unknown')
            if not preferences.get('alertTypes', {}).get(alert_type, True):
                return False
            
            # Check currency pairs (if specified)
            alert_pairs = alert_data.get('currency_pairs', [])
            user_pairs = preferences.get('currencyPairs', [])
            if alert_pairs and user_pairs:
                # Check if any alert pairs match user's preferred pairs
                if not any(pair in user_pairs for pair in alert_pairs):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking alert preferences: {e}")
            return True  # Default to sending if there's an error
    
    def _is_quiet_hours(self, user_settings: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours"""
        try:
            quiet_hours = user_settings.get('preferences', {}).get('quietHours', {})
            if not quiet_hours.get('enabled', False):
                return False
            
            # Get current time in user's timezone
            current_time = datetime.now()
            start_time = datetime.strptime(quiet_hours.get('start', '22:00'), '%H:%M').time()
            end_time = datetime.strptime(quiet_hours.get('end', '06:00'), '%H:%M').time()
            
            current_time_only = current_time.time()
            
            if start_time <= end_time:
                # Same day quiet hours (e.g., 22:00 to 06:00)
                return start_time <= current_time_only <= end_time
            else:
                # Overnight quiet hours (e.g., 22:00 to 06:00 next day)
                return current_time_only >= start_time or current_time_only <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def _format_telegram_message(self, alert_data: Dict[str, Any]) -> str:
        """Format alert message for Telegram"""
        return f"""
🔥 <b>{alert_data.get('title', 'Alert')}</b>

{alert_data.get('content', 'No content available')}

⏰ {datetime.now().strftime('%H:%M UTC')}
        """.strip()
    
    def _format_email_message(self, alert_data: Dict[str, Any]) -> str:
        """Format alert message for email"""
        return f"""
{alert_data.get('title', 'Alert')}

{alert_data.get('content', 'No content available')}

Sent at: {datetime.now().strftime('%H:%M UTC')}
        """.strip()
    
    async def get_user_alert_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user's alert settings"""
        try:
            settings = self.firebase_storage.get_user_alert_settings(user_id)
            if not settings:
                # Return default settings
                return {
                    'channels': {
                        'telegram': {'enabled': False, 'chatId': '', 'username': ''},
                        'email': {'enabled': False, 'address': ''}
                    },
                    'preferences': {
                        'impactLevels': {'high': True, 'medium': True, 'low': False},
                        'alertTypes': {'preNews': True, 'postNews': True, 'liveNews': True, 'technicalAnalysis': False},
                        'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
                        'quietHours': {'enabled': False, 'start': '22:00', 'end': '06:00', 'timezone': 'UTC'}
                    }
                }
            return settings
            
        except Exception as e:
            logger.error(f"Error getting user alert settings: {e}")
            return {}
    
    async def update_user_alert_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Update user's alert settings"""
        try:
            return self.firebase_storage.update_user_alert_settings(user_id, settings)
            
        except Exception as e:
            logger.error(f"Error updating user alert settings: {e}")
            return False
    
    async def get_users_with_alert_enabled(self, alert_type: str) -> List[Dict[str, Any]]:
        """Get all users who have a specific alert type enabled"""
        try:
            # This would typically query the database for users with this alert type enabled
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting users with alert enabled: {e}")
            return []
    
    async def send_alert_to_subscribers(self, alert_data: Dict[str, Any], alert_type: str) -> int:
        """Send alert to all users who have this type enabled"""
        try:
            # Get users with this alert type enabled
            users = await self.get_users_with_alert_enabled(alert_type)
            
            if not users:
                logger.info(f"No users have {alert_type} alerts enabled")
                return 0
            
            # Format message based on alert type
            message = self._format_alert_message(alert_data, alert_type)
            
            # Send to each user
            success_count = 0
            for user in users:
                if await self.send_telegram_alert(user['chat_id'], message):
                    success_count += 1
                    
                    # Log alert in history
                    await self._log_alert_history(user['user_id'], alert_data, 'telegram')
            
            logger.info(f"Sent {alert_type} alert to {success_count}/{len(users)} users")
            return success_count
            
        except Exception as e:
            logger.error(f"Error sending alert to subscribers: {e}")
            return 0
    
    def _format_alert_message(self, alert_data: Dict[str, Any], alert_type: str) -> str:
        """Format alert message for Telegram"""
        if alert_type == 'liveNews':
            return f"""
🔥 <b>BREAKING: {alert_data.get('title', 'Market News')}</b>

📊 <b>Impact:</b> {alert_data.get('impact_level', 'Medium').upper()}
💱 <b>Pairs:</b> {', '.join(alert_data.get('currency_pairs', []))}

🤖 <b>AI Analysis:</b>
{alert_data.get('analysis', 'Analysis not available')}

⏰ {datetime.now().strftime('%H:%M UTC')}
            """.strip()
        
        elif alert_type == 'preNews':
            return f"""
🚨 <b>UPCOMING: {alert_data.get('event_title', 'Economic Event')}</b>

⏰ <b>Time:</b> {alert_data.get('event_time', 'TBD')}
📈 <b>Expected:</b> {alert_data.get('expected_value', 'N/A')}
🎯 <b>Key Levels:</b> {alert_data.get('key_levels', 'N/A')}

💡 <b>Market Impact:</b>
{alert_data.get('impact_analysis', 'Analysis not available')}
            """.strip()
        
        else:
            return f"""
📊 <b>{alert_data.get('title', 'Alert')}</b>

{alert_data.get('content', 'No content available')}

⏰ {datetime.now().strftime('%H:%M UTC')}
            """.strip()
    
    async def _log_alert_history(self, user_id: str, alert_data: Dict[str, Any], sent_via: str):
        """Log alert in user's history"""
        try:
            history_data = {
                'alert_type': alert_data.get('type', 'unknown'),
                'title': alert_data.get('title', ''),
                'content': alert_data.get('content', ''),
                'priority': alert_data.get('priority', 'medium'),
                'currency_pairs': alert_data.get('currency_pairs', []),
                'sent_via': [sent_via],
                'status': 'sent',
                'sent_at': datetime.now().isoformat()
            }
            
            self.firebase_storage.log_alert_history(user_id, history_data)
            
        except Exception as e:
            logger.error(f"Error logging alert history: {e}")
    
    async def get_user_alert_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's alert history"""
        try:
            alerts = self.firebase_storage.get_user_alert_history(user_id, limit)
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting user alert history: {e}")
            return []

# Create a singleton instance that's properly managed
_alert_service_instance = None

def get_alert_service() -> AlertService:
    """Get the singleton AlertService instance"""
    global _alert_service_instance
    if _alert_service_instance is None:
        _alert_service_instance = AlertService()
    return _alert_service_instance
