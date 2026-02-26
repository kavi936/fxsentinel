#!/usr/bin/env python3
"""
Unified Alert Processor
Processes alerts using direct function calls (no HTTP overhead)
Designed to run as a background thread in the main app
"""

import os
import time
import logging
import threading
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedAlertProcessor:
    """
    Unified alert processor that uses direct function calls instead of HTTP
    Eliminates network latency and improves performance
    """
    
    def __init__(self):
        """Initialize the unified alert processor"""
        self.running = False
        self.thread = None
        self.last_check = None
        
        # Post-news analysis processing
        self.post_news_interval = 300  # 5 minutes
        self.last_post_news_check = None
        
        # Economic calendar check interval
        self.economic_calendar_interval = 300  # 5 minutes
        self.last_economic_calendar_check = None
        
        # Parallel processing settings
        self.max_workers = 10  # Max concurrent user processing
        
        # In-memory cache for user preferences (reduce Firebase reads)
        # Key: user_id, Value: (user_settings_dict, cached_at)
        self._user_settings_cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        self._preferences_cache_ttl_seconds = 300  # Cache for 5 minutes
        self._cache_lock = threading.Lock()
        
        # In-memory cache to prevent checking same news item multiple times
        # Key: news_id, Value: last_checked timestamp
        self._recently_checked: Dict[str, datetime] = {}
        self._check_window_seconds = 300  # Don't check same news within 5 minutes (reduces duplicates from multiple triggers)
        self._recently_checked_lock = threading.Lock()
        
        # Lock dictionary to prevent concurrent processing of same user+news combination
        # Key: (user_id, news_id), Value: threading.Lock
        self._processing_locks: Dict[Tuple[str, str], threading.Lock] = {}
        self._processing_locks_lock = threading.Lock()  # Lock for the locks dictionary
        
        logger.info("UnifiedAlertProcessor initialized with caching")
    
    def start(self):
        """Start the background thread for periodic checks"""
        if self.running:
            logger.warning("UnifiedAlertProcessor is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_periodic_checks, daemon=True)
        self.thread.start()
        logger.info("UnifiedAlertProcessor background thread started")
    
    def stop(self):
        """Stop the background thread"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("UnifiedAlertProcessor stopped")
    
    def get_status(self):
        """Get the current status of the processor"""
        return {
            'running': self.running,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'post_news_interval': self.post_news_interval,
            'last_post_news_check': self.last_post_news_check.isoformat() if self.last_post_news_check else None,
            'economic_calendar_interval': self.economic_calendar_interval,
            'last_economic_calendar_check': self.last_economic_calendar_check.isoformat() if self.last_economic_calendar_check else None
        }
    
    def _run_periodic_checks(self):
        """Main background thread loop for periodic checks (economic calendar, post-news analysis)"""
        logger.info("UnifiedAlertProcessor periodic checks started")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check economic calendar alerts (every 5 minutes)
                if (not self.last_economic_calendar_check or 
                    (current_time - self.last_economic_calendar_check).total_seconds() >= self.economic_calendar_interval):
                    self._check_economic_calendar_alerts()
                    self.last_economic_calendar_check = current_time
                
                # Process post-news analysis (every 5 minutes)
                if (not self.last_post_news_check or 
                    (current_time - self.last_post_news_check).total_seconds() >= self.post_news_interval):
                    self._process_post_news_analysis()
                    self.last_post_news_check = current_time
                
                self.last_check = current_time
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in periodic checks: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def check_news_alerts_async(self, news_items: List[Dict[str, Any]]):
        """
        Check news alerts asynchronously (non-blocking)
        Called immediately when news is fetched
        """
        if not news_items:
            logger.debug("check_news_alerts_async called with empty news_items list")
            return
        
        # Run in background thread to avoid blocking
        # Use non-daemon thread in production to ensure it completes
        thread = threading.Thread(
            target=self._check_news_alerts_with_error_handling,
            args=(news_items,),
            daemon=False  # Changed to False to ensure thread completes in production
        )
        thread.start()
        logger.info(f"Triggered async alert check for {len(news_items)} news items (thread started)")
    
    def _check_news_alerts_with_error_handling(self, news_items: List[Dict[str, Any]]):
        """Wrapper with error handling to ensure logs appear even if thread crashes"""
        try:
            logger.info(f"Background thread started for {len(news_items)} news items")
            self._check_news_alerts(news_items)
            logger.info(f"Background thread completed for {len(news_items)} news items")
        except Exception as e:
            logger.error(f"CRITICAL: Error in alert processing thread: {e}", exc_info=True)
            # Re-raise to ensure error is visible
            raise
    
    def _check_news_alerts(self, news_items: List[Dict[str, Any]]):
        """
        Check news alerts (runs in background thread)
        Uses direct function calls - no HTTP overhead
        """
        try:
            logger.info(f"Checking {len(news_items)} news items for alerts...")
            
            # Import services (direct function calls, no HTTP)
            from services.news_alert_trigger import news_alert_trigger
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            
            # Filter for high-impact forex news
            high_impact = []
            for news_item in news_items:
                if news_alert_trigger.is_forex_high_impact(news_item):
                    high_impact.append(news_item)
            
            if not high_impact:
                logger.info("No high-impact forex news found")
                return
            
            logger.info(f"Found {len(high_impact)} high-impact forex news items")
            
            # SOLUTION 1: Filter out recently checked items to prevent duplicate processing
            # This prevents the same news item from being checked multiple times within 30 seconds
            now = datetime.now()
            high_impact_filtered = []
            
            with self._recently_checked_lock:
                for news_item in high_impact:
                    news_id = str(news_item.get('id', ''))
                    if not news_id:
                        # No ID - process anyway (fallback)
                        high_impact_filtered.append(news_item)
                        continue
                    
                    # Check if we've checked this recently
                    if news_id in self._recently_checked:
                        last_checked = self._recently_checked[news_id]
                        age_seconds = (now - last_checked).total_seconds()
                        if age_seconds < self._check_window_seconds:
                            logger.debug(f"⏭️  Skipping recently checked news: {news_id} (checked {age_seconds:.1f}s ago) - {news_item.get('title', '')[:50]}")
                            continue
                    
                    # Mark as checked and add to processing list
                    high_impact_filtered.append(news_item)
                    self._recently_checked[news_id] = now
                
                # Clean up old entries (keep cache size manageable)
                if len(self._recently_checked) > 1000:
                    # Remove entries older than check window
                    cutoff = now - timedelta(seconds=self._check_window_seconds)
                    self._recently_checked = {
                        k: v for k, v in self._recently_checked.items() 
                        if v > cutoff
                    }
                    logger.debug(f"🧹 Cleaned up recently checked cache, now {len(self._recently_checked)} entries")
            
            if not high_impact_filtered:
                logger.info("No new high-impact news items to process (all were recently checked)")
                return
            
            logger.info(f"Processing {len(high_impact_filtered)} news items (after filtering recently checked)")
            
            # FIX: Don't filter by global hash here - let per-user deduplication handle it
            # Global hash check is done inside should_send_news_alert() as an optimization
            # Removing this check allows per-user processing while still preventing duplicates
            news_items_to_process = high_impact_filtered[:3]  # Max 3 items
            
            if not news_items_to_process:
                logger.info("No high-impact news items to process")
                return
            
            logger.info(f"Processing {len(news_items_to_process)} news items for per-user deduplication")
            
            # Get all users with alerts enabled (direct function call)
            firebase = FirebaseRealtimeStorage()
            users = firebase.get_all_users_with_alerts()
            
            if not users:
                logger.warning("No users with alerts enabled")
                return
            
            logger.info(f"Processing alerts for {len(users)} users")
            
            # Process users in parallel for each news item
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for user_data in users:
                    for news_item in news_items_to_process:
                        future = executor.submit(
                            self._send_alert_to_user,
                            user_data,
                            news_item
                        )
                        futures.append(future)
                
                # Wait for all to complete and collect results
                alerts_sent = 0
                for future in concurrent.futures.as_completed(futures):
                    try:
                        success = future.result(timeout=30)
                        if success:
                            alerts_sent += 1
                    except Exception as e:
                        logger.error(f"Error processing alert future: {e}")
                
                logger.info(f"Alert processing completed: {alerts_sent} alerts sent")
        
        except Exception as e:
            logger.error(f"Error checking news alerts: {e}", exc_info=True)
    
    def _get_user_settings_cached(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get user settings with caching (optimization)
        Reduces Firebase reads by caching settings for 5 minutes
        """
        try:
            now = datetime.now()
            
            # Check cache first
            with self._cache_lock:
                if user_id in self._user_settings_cache:
                    cached_settings, cached_at = self._user_settings_cache[user_id]
                    age_seconds = (now - cached_at).total_seconds()
                    
                    if age_seconds < self._preferences_cache_ttl_seconds:
                        # Cache is valid
                        logger.debug(f"Using cached settings for user {user_id}")
                        return cached_settings
                    else:
                        # Cache expired, remove it
                        del self._user_settings_cache[user_id]
            
            # Get from user_data (already loaded from Firebase)
            user_settings = user_data.get('settings', {})
            
            if user_settings:
                # Cache it
                with self._cache_lock:
                    self._user_settings_cache[user_id] = (user_settings, now)
                    # Limit cache size (keep last 100 users)
                    if len(self._user_settings_cache) > 100:
                        # Remove oldest entry
                        oldest_user = min(
                            self._user_settings_cache.items(),
                            key=lambda x: x[1][1]  # Sort by cached_at
                        )[0]
                        del self._user_settings_cache[oldest_user]
            
            return user_settings
            
        except Exception as e:
            logger.error(f"Error getting cached user settings: {e}")
            return user_data.get('settings', {})
    
    def _send_alert_to_user(self, user_data: Dict[str, Any], news_item: Dict[str, Any]) -> bool:
        """
        Send alert to a single user (thread-safe)
        Uses direct function calls - no HTTP overhead
        OPTIMIZED: Uses cached user settings
        CRITICAL: Uses per-user+news lock to prevent concurrent processing
        """
        user_id = user_data.get('user_id')
        news_id = str(news_item.get('id', ''))
        news_title = news_item.get('title', 'Unknown')[:50]
        
        if not user_id:
            logger.warning(f"🚫 No user_id provided, skipping alert")
            return False
        
        # SOLUTION 1: Quick deduplication check BEFORE lock (fast path)
        # This catches duplicates early without needing to acquire lock
        from services.persistent_alert_deduplication import should_send_news_alert
        logger.info(f"🔍 Quick deduplication check for user {user_id}: {news_title}...")
        
        quick_check = should_send_news_alert(news_item, user_id)
        if not quick_check:
            logger.warning(f"🚫 Duplicate prevented (quick check) for user {user_id}: {news_title}")
            return False
        
        # SOLUTION 2: Use blocking lock to ensure proper serialization
        # This ensures only one thread processes the same user+news combination at a time
        lock_key = (user_id, news_id)
        
        # Get or create lock for this user+news combination
        with self._processing_locks_lock:
            if lock_key not in self._processing_locks:
                self._processing_locks[lock_key] = threading.Lock()
            processing_lock = self._processing_locks[lock_key]
        
        # Acquire lock with blocking=True to ensure serialization
        # This ensures only one thread processes this user+news at a time
        logger.info(f"🔒 Acquiring lock for user {user_id}: {news_title}...")
        processing_lock.acquire(blocking=True)  # Changed from blocking=False
        
        try:
            # DEBUG: Log entry point
            logger.info(f"🔍 _send_alert_to_user called for user {user_id}: {news_title}...")
            
            # SOLUTION 4: Double-check deduplication after acquiring lock
            # This catches any duplicates that might have been processed while waiting for lock
            logger.info(f"🔍 Double-check deduplication for user {user_id}: {news_title}...")
            
            should_send = should_send_news_alert(news_item, user_id)
            logger.info(f"🔍 Deduplication result for user {user_id}: should_send={should_send}")
            
            if not should_send:
                logger.warning(f"🚫 Duplicate prevented (double-check) for user {user_id}: {news_title}")
                return False
            
            # Reserve only after lock so exactly one sender wins; prevents duplicate sends
            from services.persistent_alert_deduplication import reserve_news_alert
            if not reserve_news_alert(news_item, user_id):
                logger.warning(f"🚫 Reservation lost for user {user_id}: {news_title} (another sender won)")
                return False
            
            logger.info(f"✅ Alert approved for user {user_id}: {news_title}")
            
            # OPTIMIZATION: Get user settings from cache
            user_settings = self._get_user_settings_cached(user_id, user_data)
            
            if not user_settings:
                return False
            
            # CONSOLIDATED: Get Telegram chat ID from single source of truth
            # Location: user_data.telegram_chat_id (populated by get_all_users_with_alerts)
            chat_id = user_data.get('telegram_chat_id')
            
            if not chat_id:
                logger.debug(f"User {user_id} has no Telegram chat ID, skipping")
                return False
            
            # Convert to string if needed
            chat_id = str(chat_id)
            
            # Check if user has Telegram enabled (check multiple structures for backward compatibility)
            telegram_enabled = (
                user_settings.get('telegram_enabled', False) or
                user_settings.get('telegram', False) or
                user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)
            )
            
            if not telegram_enabled:
                logger.debug(f"User {user_id} has Telegram disabled")
                return False
            
            # Check if user wants live news alerts
            preferences = user_settings.get('preferences', {})
            alert_types = preferences.get('alertTypes', {})
            live_news_enabled = alert_types.get('liveNews', True)  # Default to True
            
            if not live_news_enabled:
                logger.debug(f"User {user_id} has liveNews alerts disabled")
                return False
            
            # Additional delay to ensure Firebase reservation is fully propagated across all instances
            # This helps prevent race conditions in high-concurrency scenarios
            import time
            time.sleep(0.5)  # Increased to 500ms delay to allow Firebase to propagate reservation globally
            
            # SOLUTION 3: Mark alert as reserved IMMEDIATELY after reservation (before sending)
            # This prevents other threads from sending the same alert
            # Phase 2 improvement: Don't mark global hash yet - only mark per-user reservation
            from services.persistent_alert_deduplication import mark_news_alert_sent
            mark_sent_success = mark_news_alert_sent(news_item, user_id, mark_global_hash=False)
            if not mark_sent_success:
                logger.warning(f"⚠️  Failed to mark alert as reserved in deduplication for user {user_id}")
                # Continue anyway - the reservation should still prevent duplicates
            else:
                logger.info(f"✅ Alert marked as reserved (before delivery) for user {user_id}: {news_title}")
            
            # Additional delay after marking as sent to ensure Firebase propagation
            time.sleep(0.2)  # 200ms delay to allow Firebase to propagate "sent" status
            
            # Import services for alert processing
            from services.news_alert_trigger import news_alert_trigger
            from services.alert_service import get_alert_service
            
            # Determine if AI analysis is needed
            needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
            
            # Create alert data
            alert_data = {
                'title': news_item.get('title', 'Breaking Forex News'),
                'content': news_alert_trigger._create_alert_content(news_item, None),
                'type': 'liveNews',
                'impact_level': news_item.get('impact', 'medium'),
                'currency_pairs': news_alert_trigger.get_affected_currency_pairs(news_item),
                'source': news_item.get('source', 'Unknown'),
                'url': news_item.get('url', ''),
                'timestamp': news_item.get('timestamp', ''),
                'ai_analysis': None
            }
            
            # Trigger AI analysis if needed (async)
            if needs_ai_analysis:
                try:
                    ai_analysis = news_alert_trigger._trigger_ai_analysis(news_item)
                    if ai_analysis:
                        alert_data['ai_analysis'] = ai_analysis
                        alert_data['content'] = news_alert_trigger._create_alert_content(news_item, ai_analysis)
                except Exception as e:
                    logger.warning(f"Error triggering AI analysis for user {user_id}: {e}")
            
            # Send alert using alert service (direct function call)
            alert_service = get_alert_service()
            
            # Process alert (async function, need to handle event loop)
            # Pass user_data so chat_id can be found in user_data.telegram_chat_id
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(
                    alert_service.process_alert(alert_data, user_settings, user_id, user_data)
                )
                loop.close()
            except RuntimeError:
                # Event loop already exists, use it
                success = asyncio.run(
                    alert_service.process_alert(alert_data, user_settings, user_id, user_data)
                )
            
            if success:
                # Phase 2 improvement: Mark global hash only after successful delivery
                from services.persistent_alert_deduplication import mark_news_alert_sent
                mark_news_alert_sent(news_item, user_id, mark_global_hash=True)
                logger.info(f"✅ Alert delivery confirmed - global hash marked for user {user_id}")
                
                # Alert already marked as reserved above (before sending)
                # Just log success here
                
                # SOLUTION 3: Log alert to history with enhanced error handling
                # This ensures alerts appear in the Alerts tab history section
                history_logged = False
                try:
                    from services.firebase_realtime_storage import FirebaseRealtimeStorage
                    firebase_storage = FirebaseRealtimeStorage()
                    
                    # Ensure we have all required fields for frontend display
                    alert_title = alert_data.get('title') or news_item.get('title', 'Breaking Forex News')
                    alert_content = alert_data.get('content', '')
                    alert_timestamp = alert_data.get('timestamp') or news_item.get('timestamp') or datetime.now().isoformat()
                    
                    history_data = {
                        'alert_type': alert_data.get('type', 'liveNews'),
                        'title': alert_title,
                        'content': alert_content,
                        'timestamp': alert_timestamp,
                        'sent_via': ['telegram'],  # Currently only Telegram is supported
                        'status': 'sent',
                        'sent_at': datetime.now().isoformat(),
                        'source': alert_data.get('source', news_item.get('source', 'Unknown')),
                        'url': alert_data.get('url', news_item.get('url', '')),
                        'currency_pairs': alert_data.get('currency_pairs', []),
                        'impact_level': alert_data.get('impact_level', news_item.get('impact', 'medium'))
                    }
                    
                    # Log with explicit success check
                    logger.info(f"🔍 Attempting to log alert to history for user {user_id}: {alert_title[:50]}...")
                    history_logged = firebase_storage.log_alert_history(user_id, history_data)
                    logger.info(f"🔍 History logging result: {history_logged} for user {user_id}")
                    if history_logged:
                        logger.info(f"✅ Logged alert to history for user {user_id}: {alert_title[:50]}...")
                    else:
                        logger.error(f"❌ Failed to log alert to history for user {user_id}: {alert_title[:50]}...")
                        
                except Exception as e:
                    logger.error(f"❌ Error logging alert to history for user {user_id}: {e}", exc_info=True)
                    # Don't fail the alert send if history logging fails
                    history_logged = False
                
                if history_logged:
                    logger.info(f"✅ Alert sent and logged to history for user {user_id}: {alert_title[:50]}...")
                else:
                    logger.warning(f"⚠️  Alert sent but history logging failed for user {user_id}: {alert_title[:50]}...")
                
                logger.info(f"Alert sent successfully to user {user_id}")
                return True
            else:
                logger.warning(f"Failed to send alert to user {user_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending alert to user {user_id}: {e}", exc_info=True)
            return False
        finally:
            # Always release the lock
            processing_lock.release()
            
            # Clean up lock if it's been unused (optional optimization)
            # We'll keep locks for a while to avoid recreating them
    
    def _check_economic_calendar_alerts(self):
        """Check for economic calendar alerts (direct function calls)"""
        try:
            logger.info("Checking for economic calendar alerts...")
            
            # Get economic calendar events from hybrid calendar (direct function call)
            try:
                from services.hybrid_economic_calendar import hybrid_economic_calendar
                # Get events for next 7 days
                start_date = datetime.now().strftime('%Y-%m-%d')
                end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                events = hybrid_economic_calendar.get_economic_events(start_date, end_date)
            except Exception as e:
                logger.error(f"Error getting economic calendar: {e}")
                return
            
            if not events:
                logger.info("No economic events found")
                return
            
            logger.info(f"Found {len(events)} economic calendar events")
            
            # Process upcoming high-impact events
            now = datetime.now()
            alerts_triggered = 0
            
            for event in events:
                # Only process high-impact events that are upcoming
                impact = event.get('impact', '').lower()
                status = event.get('status', '').lower()
                
                if impact == 'high' and status in ['upcoming', 'today']:
                    try:
                        time_str = event.get('time', '')
                        date_str = event.get('date', '')
                        
                        if time_str and date_str:
                            # Parse event datetime - hybrid calendar uses different format
                            # date_str can be "YYYY-MM-DD" or "Mon, Oct 13"
                            # time_str is "HH:MM UTC"
                            
                            # Try parsing date_str as YYYY-MM-DD first (from hybrid calendar)
                            try:
                                if '-' in date_str and len(date_str) == 10:
                                    # Format: "2026-01-02"
                                    event_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                else:
                                    # Format: "Mon, Oct 13" or "Fri, Jan 02"
                                    event_date_obj = datetime.strptime(date_str, '%a, %b %d')
                                    event_date_obj = event_date_obj.replace(year=datetime.now().year)
                                    
                                    # Adjust year if event is in the past (likely next year)
                                    if event_date_obj.date() < datetime.now().date():
                                        # Check if it's more than 30 days in the past
                                        days_diff = (datetime.now().date() - event_date_obj.date()).days
                                        if days_diff > 30:
                                            event_date_obj = event_date_obj.replace(year=datetime.now().year + 1)
                            except ValueError:
                                logger.warning(f"Could not parse date: {date_str}")
                                continue
                            
                            # Parse time_str - format is "HH:MM UTC"
                            try:
                                time_part = time_str.replace(' UTC', '').strip()
                                time_obj = datetime.strptime(time_part, '%H:%M').time()
                            except ValueError:
                                logger.warning(f"Could not parse time: {time_str}")
                                continue
                            
                            # Combine date and time
                            event_datetime = datetime.combine(event_date_obj.date(), time_obj)
                            
                            # Calculate time until event
                            time_until_event = event_datetime - now
                            minutes_until_event = time_until_event.total_seconds() / 60
                            
                            # Only send alerts if within timing windows and event is in the future
                            if minutes_until_event > 0:
                                if (8 <= minutes_until_event <= 10 or      # 10min before
                                    55 <= minutes_until_event <= 60 or    # 1h before
                                    115 <= minutes_until_event <= 120):   # 2h before
                                    
                                    logger.info(f"Sending economic alert for: {event.get('title', 'Unknown')} ({minutes_until_event:.1f} minutes away)")
                                    self._send_economic_alert(event)
                                    alerts_triggered += 1
                            else:
                                logger.debug(f"Event {event.get('title', 'Unknown')} is in the past ({minutes_until_event:.1f} minutes ago)")
                    
                    except Exception as e:
                        logger.error(f"Error checking event timing for {event.get('title', 'Unknown')}: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        continue
            
            if alerts_triggered > 0:
                logger.info(f"Triggered {alerts_triggered} economic calendar alerts")
            else:
                logger.debug("No events within alert timing windows")
        
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def _send_economic_alert(self, event: Dict[str, Any]):
        """Send economic calendar alert (direct function calls)"""
        try:
            from services.economic_calendar_alerts import economic_calendar_alerts
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            
            # Get all users
            firebase = FirebaseRealtimeStorage()
            users = firebase.get_all_users_with_alerts()
            
            if not users:
                return
            
            # Process users in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for user_data in users:
                    future = executor.submit(
                        self._send_economic_alert_to_user,
                        user_data,
                        event
                    )
                    futures.append(future)
                
                # Wait for completion
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result(timeout=30)
                    except Exception as e:
                        logger.error(f"Error processing economic alert: {e}")
        
        except Exception as e:
            logger.error(f"Error sending economic alert: {e}")
    
    def _send_economic_alert_to_user(self, user_data: Dict[str, Any], event: Dict[str, Any]) -> bool:
        """Send economic calendar alert to a single user"""
        try:
            user_id = user_data.get('user_id')
            user_settings = user_data.get('settings', {})
            
            if not user_id or not user_settings:
                return False
            
            # Check if user wants pre-news alerts
            preferences = user_settings.get('preferences', {})
            alert_types = preferences.get('alertTypes', {})
            pre_news_enabled = alert_types.get('preNews', True)
            
            if not pre_news_enabled:
                return False
            
            # Use economic calendar alerts service (direct function call)
            from services.economic_calendar_alerts import economic_calendar_alerts
            
            # Determine alert timing
            now = datetime.now()
            time_str = event.get('time', '')
            date_str = event.get('date', '')
            
            if time_str and date_str:
                # Parse date_str - can be "YYYY-MM-DD" or "Mon, Oct 13"
                try:
                    if '-' in date_str and len(date_str) == 10:
                        # Format: "2026-01-02"
                        event_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        # Format: "Mon, Oct 13" or "Fri, Jan 02"
                        event_date_obj = datetime.strptime(date_str, '%a, %b %d')
                        event_date_obj = event_date_obj.replace(year=datetime.now().year)
                        
                        # Adjust year if event is in the past
                        if event_date_obj.date() < datetime.now().date():
                            days_diff = (datetime.now().date() - event_date_obj.date()).days
                            if days_diff > 30:
                                event_date_obj = event_date_obj.replace(year=datetime.now().year + 1)
                    
                    # Parse time_str - format is "HH:MM UTC"
                    time_part = time_str.replace(' UTC', '').strip()
                    time_obj = datetime.strptime(time_part, '%H:%M').time()
                    
                    # Combine date and time
                    event_datetime = datetime.combine(event_date_obj.date(), time_obj)
                    
                    time_until_event = event_datetime - now
                    minutes_until_event = time_until_event.total_seconds() / 60
                    
                    # Determine alert timing
                    if 8 <= minutes_until_event <= 10:
                        alert_timing = "10min_before"
                    elif 55 <= minutes_until_event <= 60:
                        alert_timing = "1h_before"
                    elif 115 <= minutes_until_event <= 120:
                        alert_timing = "2h_before"
                    else:
                        return False
                except Exception as e:
                    logger.error(f"Error parsing event datetime: {e}")
                    return False
                
                # Send alert (direct function call)
                success = economic_calendar_alerts.send_pre_event_alert(
                    user_data,
                    event,
                    alert_timing
                )
                
                return success
        
        except Exception as e:
            logger.error(f"Error sending economic alert to user {user_data.get('user_id', 'unknown')}: {e}")
            return False
    
    def _process_post_news_analysis(self):
        """Process post-news analysis queue (direct function calls)"""
        try:
            logger.info("Processing post-news analysis queue...")
            
            from services.news_alert_trigger import news_alert_trigger
            
            # Process post-news analysis (async)
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(news_alert_trigger.process_post_news_analysis())
                news_alert_trigger.cleanup_old_history()
                loop.close()
                logger.info("Post-news analysis processing completed")
            except Exception as e:
                logger.error(f"Error in async post-news processing: {e}")
        
        except Exception as e:
            logger.error(f"Error processing post-news analysis: {e}")

# Global instance
_unified_processor = None

def get_unified_processor() -> UnifiedAlertProcessor:
    """Get the global unified alert processor instance"""
    global _unified_processor
    if _unified_processor is None:
        _unified_processor = UnifiedAlertProcessor()
    return _unified_processor

