#!/usr/bin/env python3
"""
FXSentinel Alert Service
Handles user alert preferences and sends notifications via Telegram
Uses Firebase Realtime Database instead of Firestore
"""

import os
import asyncio
import logging
import threading
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

# Marketing branding appended to all Telegram messages (for sharing to other channels)
TELEGRAM_BRANDING_TAG = "\n\n@FXSentinelAlertsBot"

class AlertService:
    def __init__(self):
        """Initialize the alert service"""
        self.telegram_bot = None
        self.telegram_bot_initialized = False
        self.firebase_storage = FirebaseRealtimeStorage()
        # Per-chat deduplication to prevent duplicate sends when multiple users
        # share the same Telegram chat_id. Key: (chat_id, content_key)
        self._recent_chat_sends: Dict[str, datetime] = {}
        self._recent_chat_sends_ttl_seconds = 600  # 10 minutes
        self._recent_chat_sends_lock = threading.Lock()
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
        """
        Verify user has completed Telegram bot setup
        CONSOLIDATED: Uses single source of truth for chat_id
        """
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
            
            # CONSOLIDATED: Get chat_id from single location
            chat_id = self.firebase_storage.get_telegram_chat_id(user_id)
            
            if chat_id:
                # Get username from settings if available
                user_settings = self.firebase_storage.get_user_alert_settings(user_id)
                username = 'Unknown'
                if user_settings:
                    # Check multiple locations for username (backward compatibility)
                    username = (
                        user_settings.get('channels', {}).get('telegram', {}).get('username') or
                        user_settings.get('telegram_username') or
                        'Unknown'
                    )
                
                return {
                    "connected": True,
                    "chatId": chat_id,
                    "username": username
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
    
    async def send_telegram_alert(self, chat_id: str, message: str, user_id: str = None, parse_mode: str = 'HTML', alert_type: str = 'news', alert_data: Dict[str, Any] = None) -> bool:
        """
        Send alert via robust Telegram service with circuit breaker and dead letter queue
        
        Args:
            chat_id: Telegram chat ID
            message: Alert message text
            user_id: User ID (optional)
            parse_mode: Message parse mode (default: HTML)
            alert_type: Type of alert (default: news)
            alert_data: Full alert data for dead letter queue (optional)
        """
        try:
            from .robust_telegram_service import send_telegram_message_async
            from .alert_monitoring import get_alert_monitoring
            from .circuit_breaker import get_telegram_circuit_breaker
            from .dead_letter_queue import get_dead_letter_queue
            
            monitoring = get_alert_monitoring()
            circuit_breaker = get_telegram_circuit_breaker()
            dead_letter_queue = get_dead_letter_queue()
            
            # Check circuit breaker state before attempting send (Phase 1 improvement: Enhanced logging)
            cb_stats = circuit_breaker.get_stats()
            if cb_stats['state'] == 'open':
                logger.warning(f"Telegram circuit breaker is OPEN - rejecting request for user {user_id}, chat_id {chat_id}")
                logger.warning(f"Circuit breaker stats: {cb_stats}")
                # Phase 2 improvement: Record metrics
                try:
                    from .alert_metrics import get_alert_metrics
                    get_alert_metrics().record_circuit_breaker_open()
                except Exception as e:
                    logger.debug(f"Error recording metrics: {e}")
                # Add to dead letter queue immediately
                if user_id:
                    dead_letter_queue.add_failed_alert(
                        user_id=user_id,
                        chat_id=chat_id,
                        alert_type=alert_type,
                        title=alert_data.get('title', 'Alert') if alert_data else message.split('\n')[0][:50] if message else 'Alert',
                        content=message,
                        error_message=f"Circuit breaker is open (stats: {cb_stats})",
                        attempts=0,
                        alert_data=alert_data or {}
                    )
                    # Phase 2 improvement: Record dead letter queue addition
                    try:
                        from .alert_metrics import get_alert_metrics
                        get_alert_metrics().record_dead_letter_queue_addition()
                    except Exception as e:
                        logger.debug(f"Error recording metrics: {e}")
                return False
            else:
                logger.debug(f"Circuit breaker state: {cb_stats['state']} - proceeding with alert send")
            
            # Append branding tag for marketing (shared messages carry source)
            if message and not (message.strip().endswith("@FXSentinelAlertsBot")):
                message = message.strip() + TELEGRAM_BRANDING_TAG
            
            # Attempt to send (robust_telegram_service handles retries internally)
            success, error = await send_telegram_message_async(
                chat_id=chat_id,
                text=message,
                user_id=user_id,
                message_type="alert"
            )
            
            if success:
                logger.info(f"Telegram alert sent to {chat_id}")
                # Record success
                if user_id:
                    monitoring.record_success(user_id, alert_type)
                # Record success in circuit breaker
                circuit_breaker._record_success()
                # Phase 2 improvement: Record metrics
                try:
                    from .alert_metrics import get_alert_metrics
                    get_alert_metrics().record_alert_sent(alert_type)
                except Exception as e:
                    logger.debug(f"Error recording metrics: {e}")
                return True
            else:
                logger.error(f"Failed to send Telegram alert to {chat_id}: {error}")
                # Record failure
                if user_id:
                    alert_title = message.split('\n')[0][:50] if message else None
                    monitoring.record_failure(user_id, alert_type, error or "Unknown error", alert_title)
                
                # Record failure in circuit breaker
                circuit_breaker._record_failure()
                # Phase 2 improvement: Record metrics
                try:
                    from .alert_metrics import get_alert_metrics
                    get_alert_metrics().record_alert_failed(alert_type, error or "Unknown error")
                except Exception as e:
                    logger.debug(f"Error recording metrics: {e}")
                
                # Check if this was the final attempt (robust_telegram_service handles retries)
                # For now, we'll add to dead letter queue if error suggests permanent failure
                permanent_errors = ['invalid chat', 'chat not found', 'forbidden', 'unauthorized']
                if error and any(perm_err in error.lower() for perm_err in permanent_errors):
                    # Add to dead letter queue for manual review
                    dead_letter_queue.add_failed_alert(
                        user_id=user_id or 'unknown',
                        chat_id=chat_id,
                        alert_type=alert_type,
                        title=alert_data.get('title', 'Alert') if alert_data else message.split('\n')[0][:50] if message else 'Alert',
                        content=message,
                        error_message=error or "Unknown error",
                        attempts=3,  # robust_telegram_service already retried
                        alert_data=alert_data or {}
                    )
                
                return False
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert to {chat_id}: {e}")
            # Record failure
            if user_id:
                from .alert_monitoring import get_alert_monitoring
                monitoring = get_alert_monitoring()
                monitoring.record_failure(user_id, alert_type, str(e), None)
            
            # Add to dead letter queue
            try:
                from .dead_letter_queue import get_dead_letter_queue
                dead_letter_queue = get_dead_letter_queue()
                dead_letter_queue.add_failed_alert(
                    user_id=user_id or 'unknown',
                    chat_id=chat_id,
                    alert_type=alert_type,
                    title=alert_data.get('title', 'Alert') if alert_data else 'Alert',
                    content=message,
                    error_message=str(e),
                    attempts=0,
                    alert_data=alert_data or {}
                )
            except Exception as dlq_error:
                logger.error(f"Failed to add to dead letter queue: {dlq_error}")
            
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
    
    def _should_send_to_chat(self, chat_id: str, alert_data: Dict[str, Any]) -> bool:
        """
        Per-chat deduplication guard.
        If we've already sent this content_key to this chat_id in the last N minutes, skip.
        This prevents duplicates when multiple backend users share the same Telegram chat.
        """
        try:
            alert_type = alert_data.get('type', 'news')
            title = str(alert_data.get('title', '')).strip().lower()
            if not title or not chat_id:
                return True

            # Normalize title similarly to news dedup (whitespace + punctuation)
            import re
            title_normalized = re.sub(r'\s+', ' ', title)
            title_normalized = re.sub(r'[^\w\s]', '', title_normalized)
            content_key = f"{alert_type}:{title_normalized}"
            key = f"{chat_id}:{content_key}"

            now = datetime.now()
            cutoff = now - timedelta(seconds=self._recent_chat_sends_ttl_seconds)

            with self._recent_chat_sends_lock:
                # Clean up old entries
                if self._recent_chat_sends:
                    self._recent_chat_sends = {
                        k: v for k, v in self._recent_chat_sends.items()
                        if v >= cutoff
                    }

                last_sent_at = self._recent_chat_sends.get(key)
                if last_sent_at and last_sent_at >= cutoff:
                    logger.info(
                        f"📋 CHAT_DEDUP_SKIP chat_id={chat_id} content_key={content_key[:80]} "
                        f"(sent_at={last_sent_at.isoformat()})"
                    )
                    return False

                # Record new send
                self._recent_chat_sends[key] = now
                logger.info(
                    f"📋 CHAT_DEDUP_ALLOW chat_id={chat_id} content_key={content_key[:80]} "
                    f"(first send in window)"
                )
                return True
        except Exception as e:
            logger.error(f"Error in per-chat dedup guard: {e}")
            return True

    async def process_alert(self, alert_data: Dict[str, Any], user_settings: Dict[str, Any], user_id: str = None, user_data: Dict[str, Any] = None) -> bool:
        """Process and send alert to user based on their settings"""
        try:
            # REMOVED: Subscription check - alerts are now available to all users (paid, developer, freemium, etc.)
            # All users can receive alerts regardless of subscription status
            
            # Check if user wants this type of alert
            if not self._should_send_alert(alert_data, user_settings):
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(user_settings):
                return False
            
            # Send via configured channels
            success = True
            
            # Check for Telegram alerts - CONSOLIDATED: Single source of truth for chat_id
            telegram_enabled = False
            chat_id = None
            
            # CONSOLIDATED: Get chat_id from single location (user_data.telegram_chat_id)
            # This is populated by get_all_users_with_alerts() which reads from:
            # alerts/users/{user_id}/telegram_chat_id
            if user_data and user_data.get('telegram_chat_id'):
                chat_id = str(user_data['telegram_chat_id'])
                logger.debug(f"Found chat_id in user_data.telegram_chat_id: {chat_id}")
            else:
                # Record chat ID lookup failure for monitoring
                from .alert_monitoring import get_alert_monitoring
                monitoring = get_alert_monitoring()
                monitoring.record_chat_id_lookup_failure(user_id)
                # Phase 2 improvement: Record metrics
                try:
                    from .alert_metrics import get_alert_metrics
                    get_alert_metrics().record_chat_id_lookup_failure()
                except Exception as e:
                    logger.debug(f"Error recording metrics: {e}")
            
            # Check if Telegram is enabled (check multiple structures for backward compatibility)
            if user_settings.get('telegram', False) or \
               user_settings.get('channels', {}).get('telegram', {}).get('enabled', False) or \
               user_settings.get('telegram_enabled', False):
                telegram_enabled = True
            
            if telegram_enabled and chat_id:
                # Per-chat deduplication: if this chat_id already received this content_key
                # recently, skip to avoid duplicates when multiple users share a chat.
                if not self._should_send_to_chat(chat_id, alert_data):
                    logger.info(
                        f"Skipping Telegram send for user {user_id} to chat_id {chat_id} "
                        f"due to per-chat dedup guard"
                    )
                    telegram_success = False
                else:
                    telegram_success = await self.send_telegram_alert(
                        chat_id,
                        self._format_telegram_message(alert_data),
                        user_id=user_id,
                        alert_type=alert_data.get('type', 'news'),
                        alert_data=alert_data  # Pass full alert data for dead letter queue
                    )
                success = success and telegram_success
                
                # Log to history if Telegram alert was sent successfully
                if telegram_success:
                    try:
                        await self._log_alert_history(user_id, alert_data, 'telegram')
                    except Exception as e:
                        logger.error(f"Error logging alert history: {e}")
                        # Don't fail the alert send if history logging fails
                
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
    
    def _format_live_news_message(self, alert_data: Dict[str, Any]) -> str:
        """Format live news alert message for Telegram with clean HTML layout."""
        title = alert_data.get('title', 'Alert')
        summary = alert_data.get('content', 'No content available')
        source = alert_data.get('source', 'Unknown')
        pairs = alert_data.get('currency_pairs') or []
        pairs_text = ', '.join(pairs) if pairs else 'Multiple pairs'

        # Prefer event timestamp from alert_data if available
        event_time = None
        try:
            timestamp = alert_data.get('timestamp') or ''
            if timestamp:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                event_time = dt.strftime('%H:%M UTC')
        except Exception:
            event_time = None

        if not event_time:
            event_time = datetime.now().strftime('%H:%M UTC')

        return f"""
<b>{title}</b>

<b>Time:</b> {event_time}
<b>Source:</b> {source}
<b>Currency Pairs:</b> {pairs_text}

<b>Summary:</b>
{summary}

Check dashboard for detailed analysis
        """.strip()

    def _format_telegram_message(self, alert_data: Dict[str, Any]) -> str:
        """Format alert message for Telegram."""
        # Use a specialised layout for live news to keep alerts clean and scannable
        if alert_data.get('type') == 'liveNews':
            return self._format_live_news_message(alert_data)

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
            from datetime import datetime
            history_data = {
                'alert_type': alert_data.get('type', alert_data.get('alert_type', 'unknown')),
                'title': alert_data.get('title', ''),
                'content': alert_data.get('content', ''),
                'priority': alert_data.get('priority', 'medium'),
                'currency_pairs': alert_data.get('currency_pairs', []),
                'sent_via': [sent_via],
                'status': 'sent',
                'sent_at': datetime.now().isoformat(),
                'timestamp': alert_data.get('timestamp', datetime.now().isoformat()),  # Add timestamp for frontend
                'source': alert_data.get('source', ''),
                'url': alert_data.get('url', ''),
                'impact_level': alert_data.get('impact_level', alert_data.get('priority', 'medium'))
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
