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
        self.telegram_bot_initialized = False
        self.firebase_storage = FirebaseRealtimeStorage()
        # Don't initialize Telegram bot during __init__ to avoid build-time token access
        logger.info("AlertService initialized (Telegram bot will be initialized on first use)")
    
    def _ensure_telegram_bot(self):
        """Initialize Telegram bot only when needed (lazy initialization)"""
        if self.telegram_bot_initialized:
            return
        
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
            
            self.telegram_bot_initialized = True
                
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.telegram_bot = None
            self.telegram_bot_initialized = True  # Mark as initialized to avoid retries
    
    def _initialize_services(self):
        """Initialize Firebase Realtime Database (Telegram bot is lazy-loaded)"""
        try:
            # Test Firebase Realtime Database connection
            if self.firebase_storage.test_connection():
                logger.info("Firebase Realtime Database connected")
            else:
                logger.warning("Firebase Realtime Database connection failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
    
    async def setup_telegram_bot(self, user_id: str) -> Dict[str, Any]:
        """Generate unique bot link for user setup"""
        try:
            self._ensure_telegram_bot()
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
            self._ensure_telegram_bot()
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
    
    async def send_telegram_alert(self, chat_id: str, message: str, user_id: str = None, parse_mode: str = 'HTML') -> bool:
        """Send alert via robust Telegram service"""
        try:
            from .robust_telegram_service import send_telegram_message_async
            
            success, error = await send_telegram_message_async(
                chat_id=chat_id,
                text=message,
                user_id=user_id,
                message_type="alert"
            )
            
            if success:
                logger.info(f"Telegram alert sent to {chat_id}")
                return True
            else:
                logger.error(f"Failed to send Telegram alert to {chat_id}: {error}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert to {chat_id}: {e}")
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
    
    async def process_alert(self, alert_data: Dict[str, Any], user_settings: Dict[str, Any], user_id: str = None) -> bool:
        """Process and send alert to user based on their settings"""
        try:
            # Check subscription status if user_id is provided
            if user_id:
                subscription_valid = await self._check_user_subscription(user_id)
                if not subscription_valid:
                    logger.warning(f"User {user_id} has invalid subscription, skipping alert")
                    return False
            
            # Check if user wants this type of alert
            if not self._should_send_alert(alert_data, user_settings):
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(user_settings):
                return False
            
            # Send via configured channels
            success = True
            
            # Check for Telegram alerts - handle multiple settings structures
            telegram_enabled = False
            chat_id = None
            
            # Direct telegram setting: telegram: true
            if user_settings.get('telegram', False):
                telegram_enabled = True
                # Get chat_id from mapping since it's not in settings
                if user_id:
                    mapping_path = f"telegram_mappings"
                    all_mappings = self.firebase_storage._make_request('GET', mapping_path)
                    if all_mappings and isinstance(all_mappings, dict):
                        for cid, mapping_data in all_mappings.items():
                            if isinstance(mapping_data, dict) and mapping_data.get('user_id') == user_id:
                                chat_id = cid
                                break
            # New structure: channels.telegram.enabled
            elif user_settings.get('channels', {}).get('telegram', {}).get('enabled'):
                telegram_enabled = True
                chat_id = user_settings['channels']['telegram'].get('chatId')
            # Old structure: telegram_enabled (direct)
            elif user_settings.get('telegram_enabled', False):
                telegram_enabled = True
                # Get chat_id from mapping if not in settings
                if user_id:
                    mapping_path = f"telegram_mappings"
                    all_mappings = self.firebase_storage._make_request('GET', mapping_path)
                    if all_mappings and isinstance(all_mappings, dict):
                        for cid, mapping_data in all_mappings.items():
                            if isinstance(mapping_data, dict) and mapping_data.get('user_id') == user_id:
                                chat_id = cid
                                break
            
            if telegram_enabled and chat_id:
                telegram_success = await self.send_telegram_alert(
                    chat_id,
                    self._format_telegram_message(alert_data),
                    user_id=user_id
                )
                success = success and telegram_success
                logger.info(f"Telegram alert sent to chat_id {chat_id}")
            elif telegram_enabled and not chat_id:
                logger.warning(f"Telegram enabled but no chat_id found for user {user_id}")
            
            # Check for email alerts
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
    
    async def _check_user_subscription(self, user_id: str) -> bool:
        """Check if user has valid subscription status with caching"""
        try:
            from .subscription_cache import get_subscription_status_async
            
            is_valid, error = await get_subscription_status_async(user_id)
            
            if error:
                logger.error(f"Subscription check error for user {user_id}: {error}")
                return False
            
            if not is_valid:
                logger.info(f"User {user_id} subscription invalid - Access denied")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error checking user subscription: {e}")
            return False  # Deny access if we can't verify subscription
    
    def _should_send_alert(self, alert_data: Dict[str, Any], user_settings: Dict[str, Any]) -> bool:
        """Check if user should receive this alert based on their preferences"""
        try:
            # Handle both old and new settings structure
            preferences = user_settings.get('preferences', {})
            
            # If no preferences structure, use direct settings
            if not preferences:
                preferences = user_settings
            
            # Check impact level
            alert_impact = alert_data.get('impact_level', 'medium')
            impact_levels = preferences.get('impactLevels', preferences.get('impact_levels', {}))
            
            # Handle both dict and list formats
            if isinstance(impact_levels, dict):
                if not impact_levels.get(alert_impact, True):
                    return False
            elif isinstance(impact_levels, list):
                if alert_impact not in impact_levels:
                    return False
            
            # Check alert type
            alert_type = alert_data.get('type', 'unknown')
            alert_types = preferences.get('alertTypes', preferences.get('alert_types', {}))
            
            # Handle both dict and list formats
            if isinstance(alert_types, dict):
                if not alert_types.get(alert_type, True):
                    return False
            elif isinstance(alert_types, list):
                if alert_type not in alert_types:
                    return False
            
            # Check currency pairs (if specified)
            alert_pairs = alert_data.get('currency_pairs', [])
            user_pairs = preferences.get('currencyPairs', preferences.get('currency_pairs', []))
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
<b>{alert_data.get('title', 'Alert')}</b>

{alert_data.get('content', 'No content available')}

Time: {datetime.now().strftime('%H:%M UTC')}
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
🚨 BREAKING FOREX NEWS
**{alert_data.get('title', 'Market News')}**

**Time:** {datetime.now().strftime('%H:%M UTC')} | **Impact:** {alert_data.get('impact_level', 'Medium').upper()}
**Pairs:** {', '.join(alert_data.get('currency_pairs', []))}

**AI Analysis:**
{alert_data.get('analysis', 'Analysis not available')}
            """.strip()
        
        elif alert_type == 'preNews':
            return f"""
📅 ECONOMIC EVENT ALERT
**{alert_data.get('event_title', 'Economic Event')}**

**Time:** {alert_data.get('event_time', 'TBD')} | **Expected:** {alert_data.get('expected_value', 'N/A')}
**Key Levels:** {alert_data.get('key_levels', 'N/A')}

**Market Impact:**
{alert_data.get('impact_analysis', 'Analysis not available')}
            """.strip()
        
        else:
            return f"""
**{alert_data.get('title', 'Alert')}**

{alert_data.get('content', 'No content available')}

**Time:** {datetime.now().strftime('%H:%M UTC')}
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
