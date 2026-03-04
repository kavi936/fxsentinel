#!/usr/bin/env python3
"""
Persistent Alert Deduplication Service
Single source of truth for alert deduplication using Firebase Realtime Database
Replaces all in-memory deduplication systems
"""

import logging
import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .firebase_realtime_storage import FirebaseRealtimeStorage

logger = logging.getLogger(__name__)

class PersistentAlertDeduplication:
    """
    Persistent deduplication service that stores state in Firebase Realtime Database
    This ensures deduplication survives restarts and works across multiple instances
    """
    
    def __init__(self):
        self.firebase = FirebaseRealtimeStorage()
        # How long to remember sent alerts. Persists in Firebase so survives restarts.
        # 2h = same story won't be re-sent within 2h even if app restarts or story is re-processed.
        self.alert_ttl_hours = 2.0
        self.cleanup_interval = 20  # Cleanup every N operations (reduced from 50 for more frequent cleanup)
        self.operations_count = 0
        self.duplicates_prevented = 0
        
        # In-memory cache for content hashes (global deduplication)
        # Key: content_hash, Value: expires_at timestamp
        self._content_hash_cache: Dict[str, datetime] = {}
        self._cache_ttl_seconds = 300  # Cache for 5 minutes to reduce Firebase calls
        
        # Thread lock for cache operations
        self._cache_lock = threading.Lock()
        
        # Force send mode (for testing) - bypasses deduplication
        self.force_send_mode = False
        
        # Clear expired hashes on startup to prevent stale cache issues
        self._clear_expired_cache_on_startup()
        
        logger.info("Persistent Alert Deduplication Service initialized with caching and startup cleanup")
    
    def _generate_alert_key(self, alert_type: str, content: str, user_id: str) -> str:
        """Generate unique alert key for deduplication"""
        # Create a hash based on type, content, and user
        content_str = f"{alert_type}:{content}:{user_id}"
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash of alert content for global deduplication"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_alert_path(self, alert_key: str) -> str:
        """Get Firebase path for alert record"""
        return f"alert_deduplication/alerts/{alert_key}"
    
    def _get_content_hash_path(self, content_hash: str) -> str:
        """Get Firebase path for content hash"""
        return f"alert_deduplication/content_hashes/{content_hash}"
    
    def _clear_expired_cache_on_startup(self):
        """Clear expired entries from in-memory cache on startup"""
        try:
            now = datetime.now()
            expired_keys = []
            
            with self._cache_lock:
                for content_hash, expires_at in self._content_hash_cache.items():
                    if now >= expires_at:
                        expired_keys.append(content_hash)
                
                for key in expired_keys:
                    del self._content_hash_cache[key]
            
            if expired_keys:
                logger.info(f"Cleared {len(expired_keys)} expired cache entries on startup")
            
            # Also trigger cleanup of expired Firebase records
            self._cleanup_expired_content_hashes()
            
        except Exception as e:
            logger.warning(f"Error clearing expired cache on startup: {e}")
    
    def _reserve_alert(self, alert_type: str, content: str, user_id: str) -> bool:
        """
        DEPRECATED: Use _check_and_reserve_alert instead for atomic operation
        Kept for backward compatibility
        """
        return self._check_and_reserve_alert(alert_type, content, user_id)
    
    def should_send_alert(self, alert_type: str, content: str, user_id: str) -> bool:
        """
        Check if alert should be sent (not a duplicate)
        Returns: True if alert should be sent, False if it's a duplicate
        """
        try:
            # Force send mode bypasses deduplication (for testing)
            if self.force_send_mode:
                logger.debug(f"Force send mode enabled - bypassing deduplication for {alert_type}")
                return True
            
            self.operations_count += 1
            
            # Automatic cleanup of expired records (increased frequency)
            if self.operations_count % self.cleanup_interval == 0:
                self.cleanup_expired_alerts()
                self._cleanup_expired_content_hashes()
            
            # Generate keys
            alert_key = self._generate_alert_key(alert_type, content, user_id)
            content_hash = self._generate_content_hash(content)
            
            # Check if we've already sent this exact alert to this user
            alert_path = self._get_alert_path(alert_key)
            existing_alert = self.firebase._make_request('GET', alert_path)
            
            # Firebase returns {} on RequestException (error). Fail closed to prevent duplicates.
            if existing_alert == {}:
                logger.error(f"Firebase deduplication check failed (empty response) - blocking alert to prevent duplicates")
                return False
            
            # None = path doesn't exist (no record) - allow
            if existing_alert is None:
                return True
            
            if isinstance(existing_alert, dict):
                status = existing_alert.get('status', 'sent')
                expires_at_str = existing_alert.get('expires_at')
                
                if status in ['sent', 'reserved']:
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if datetime.now() < expires_at:
                                self.duplicates_prevented += 1
                                logger.debug(f"Duplicate alert prevented for user {user_id}: {alert_type} (status: {status})")
                                return False
                        except Exception as e:
                            logger.warning(f"Error parsing expires_at: {e}")
                    else:
                        # Record exists with sent/reserved but no expires_at - treat as duplicate
                        self.duplicates_prevented += 1
                        logger.debug(f"Duplicate alert prevented for user {user_id}: {alert_type} (status: {status}, no expires_at)")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking alert deduplication: {e}")
            return False  # Fail closed to prevent duplicates
    
    def mark_alert_sent(self, alert_type: str, content: str, user_id: str) -> bool:
        """
        Mark an alert as sent to prevent duplicates
        Updates reserved record to sent status, or creates new sent record
        """
        try:
            alert_key = self._generate_alert_key(alert_type, content, user_id)
            content_hash = self._generate_content_hash(content)
            
            # Create alert record
            now = datetime.now()
            expires_at = now + timedelta(hours=self.alert_ttl_hours)
            
            alert_record = {
                'alert_type': alert_type,
                'user_id': user_id,
                'content_hash': content_hash,
                'status': 'sent',  # Mark as sent (not reserved)
                'sent_at': now.isoformat(),
                'expires_at': expires_at.isoformat()
            }
            
            # Store in Firebase (PUT will update if reserved record exists)
            alert_path = self._get_alert_path(alert_key)
            result = self.firebase._make_request('PUT', alert_path, alert_record)
            
            if result is not None:
                logger.debug(f"Marked alert as sent: {alert_type} for user {user_id}")
                return True
            else:
                logger.error(f"CRITICAL: Failed to mark alert as sent in Firebase - duplicate may occur")
                # This is critical - if we can't mark as sent, duplicates will occur
                # Log as error to track this issue
                return False
            
        except Exception as e:
            logger.error(f"CRITICAL: Error marking alert as sent: {e} - duplicate may occur")
            return False
    
    def _get_news_content_string(self, news_item: Dict[str, Any]) -> str:
        """Build content string for per-user deduplication. Always use normalized title+source
        so the same story maps to the same key regardless of path (Unified vs API) or whether
        the payload has an id (which can differ or be missing and cause duplicate sends)."""
        title = str(news_item.get('title', '')).strip().lower()
        source = str(news_item.get('source', '')).strip().lower()
        import re
        title_normalized = re.sub(r'\s+', ' ', title)
        title_normalized = re.sub(r'[^\w\s]', '', title_normalized)
        return f"news:{title_normalized}|{source}"

    def _check_alert_only(self, alert_type: str, content: str, user_id: str) -> bool:
        """
        Check if alert should be sent (no reserve). Returns False if already reserved or sent and not expired.
        State is in Firebase so this works across app restarts and multiple instances.
        Used for quick-check and double-check; reserve is done separately after lock to prevent duplicates.
        """
        try:
            alert_key = self._generate_alert_key(alert_type, content, user_id)
            alert_path = self._get_alert_path(alert_key)
            existing_alert = self.firebase._make_request('GET', alert_path)
            # Firebase returns {} on error - fail closed to prevent duplicates
            if existing_alert == {}:
                logger.error(f"Firebase deduplication check failed (empty response) - blocking alert")
                return False
            # None = no record - allow
            if not existing_alert or not isinstance(existing_alert, dict):
                logger.info(f"📋 DEDUP_ALLOW content={content[:60]}... user={user_id[:16]}... (no record in Firebase)")
                return True
            status = existing_alert.get('status', 'sent')
            expires_at_str = existing_alert.get('expires_at', '')
            # Reserved or sent = duplicate; never allow "reserved recently" to avoid double sends
            if status in ('reserved', 'sent'):
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if datetime.now() < expires_at:
                            self.duplicates_prevented += 1
                            logger.info(f"📋 DEDUP_BLOCK content={content[:60]}... user={user_id[:16]}... status={status} expires_at={expires_at_str[:19]}")
                            return False
                        # else: expired, allow (fall through)
                    except Exception as e:
                        logger.warning(f"Error parsing expires_at: {e}")
                else:
                    logger.info(f"📋 DEDUP_BLOCK content={content[:60]}... user={user_id[:16]}... status={status} no_expires")
                    return False
            logger.info(f"📋 DEDUP_ALLOW content={content[:60]}... user={user_id[:16]}... (no record or expired)")
            return True
        except Exception as e:
            logger.error(f"Error in check-only: {e}")
            return False  # Fail closed to prevent duplicates

    def _get_news_content_hash(self, news_item: Dict[str, Any]) -> str:
        """Generate content hash for news item (for global deduplication).
        Must match _get_news_content_string so per-user and global use the same identity."""
        try:
            content_str = self._get_news_content_string(news_item)
            return hashlib.md5(content_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating news content hash: {e}")
            return ""
    
    def _check_global_content_hash(self, content_hash: str) -> bool:
        """
        Check if content hash has been sent globally (optimization)
        Returns: True if content is new, False if already sent
        """
        try:
            # Force send mode bypasses global deduplication
            if self.force_send_mode:
                return True
            
            now = datetime.now()
            
            # Check in-memory cache first (thread-safe)
            with self._cache_lock:
                if content_hash in self._content_hash_cache:
                    expires_at = self._content_hash_cache[content_hash]
                    if now < expires_at:
                        # Content already sent globally
                        return False
                    else:
                        # Cache expired, remove it
                        del self._content_hash_cache[content_hash]
            
            # Check Firebase for global content hash
            content_hash_path = self._get_content_hash_path(content_hash)
            existing_hash = self.firebase._make_request('GET', content_hash_path)
            
            if existing_hash and isinstance(existing_hash, dict):
                expires_at_str = existing_hash.get('expires_at')
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if now < expires_at:
                            # Content already sent globally - cache it (thread-safe)
                            with self._cache_lock:
                                self._content_hash_cache[content_hash] = expires_at
                            logger.info(f"🚫 Global content hash EXISTS (not expired): {content_hash[:16]}...")
                            return False
                    except Exception as e:
                        logger.warning(f"Error parsing expires_at for content hash: {e}")
            else:
                logger.info(f"✅ Global content hash NEW (not found in Firebase): {content_hash[:16]}...")
            
            # Content is new
            return True
            
        except Exception as e:
            logger.error(f"Error checking global content hash: {e}")
            return True  # Allow alert if check fails
    
    def _mark_global_content_hash(self, content_hash: str):
        """Mark content hash as sent globally (optimization)"""
        try:
            now = datetime.now()
            expires_at = now + timedelta(hours=self.alert_ttl_hours)
            
            # Cache in memory (thread-safe)
            with self._cache_lock:
                self._content_hash_cache[content_hash] = expires_at
            
            # Store in Firebase
            content_hash_path = self._get_content_hash_path(content_hash)
            hash_record = {
                'content_hash': content_hash,
                'sent_at': now.isoformat(),
                'expires_at': expires_at.isoformat()
            }
            self.firebase._make_request('PUT', content_hash_path, hash_record)
            
        except Exception as e:
            logger.error(f"Error marking global content hash: {e}")
    
    def should_send_news_alert(self, news_item: Dict[str, Any], user_id: str) -> bool:
        """
        Check if news alert should be sent (not a duplicate)
        Phase 2 improvement: Hybrid approach - global hash is hint only, per-user is authoritative
        Uses atomic check-and-reserve to prevent race conditions
        CRITICAL: This method atomically checks AND reserves in a single operation
        """
        try:
            news_title = news_item.get('title', 'Unknown')[:50]
            
            # Generate content hash for global deduplication (hint only)
            content_hash = self._get_news_content_hash(news_item)
            
            # Phase 2 improvement: Check global hash as hint only (don't block)
            # Per-user deduplication is authoritative
            if content_hash:
                global_check_result = self._check_global_content_hash(content_hash)
                if not global_check_result:
                    # Content may have been sent globally, but still check per-user
                    # This prevents blocking if global hash was marked but delivery failed
                    logger.info(f"⚠️  Global hash exists (hint) for user {user_id}: {news_title} - checking per-user deduplication anyway")
                else:
                    logger.info(f"✅ Global hash check passed (hint) for user {user_id}: {news_title}")
            
            # Build content string for per-user check (same logic as mark_news_alert_sent)
            content = self._get_news_content_string(news_item)
            # Diagnostic: log content key so duplicate investigations can verify same key across paths
            logger.info(f"📋 DEDUP_KEY news content={content[:80]} user={user_id[:16]}...")
            
            # Check-only (no reserve): prevents duplicates without reserving in quick/double-check.
            # Reserve happens once in unified_alert_processor after lock, so "reserved recently"
            # cannot allow a second sender.
            return self._check_alert_only('news', content, user_id)
            
        except Exception as e:
            logger.error(f"Error checking news alert deduplication: {e}")
            return True  # Allow alert if check fails
    
    def _check_and_reserve_alert(self, alert_type: str, content: str, user_id: str) -> bool:
        """
        Atomically check if alert should be sent AND reserve it.
        Used only when reserving after lock (e.g. reserve_news_alert).
        Reserved or sent (and not expired) = duplicate, returns False.
        """
        import time
        max_retries = 3
        retry_delay = 0.15  # 150ms between retries
        
        for attempt in range(max_retries):
            try:
                alert_key = self._generate_alert_key(alert_type, content, user_id)
                alert_path = self._get_alert_path(alert_key)
                
                # DEBUG: Log attempt
                logger.info(f"🔍 _check_and_reserve_alert attempt {attempt + 1}/{max_retries} for user {user_id}: {alert_type}, key={alert_key[:32]}...")
                
                # Step 1: Check if already exists (including reserved or sent)
                existing_alert = self.firebase._make_request('GET', alert_path)
                logger.info(f"🔍 Existing alert check result: {existing_alert is not None} for user {user_id}")
                
                if existing_alert and isinstance(existing_alert, dict):
                    # Reserved or sent = duplicate (no "reserved recently - allowing" to prevent double sends)
                    status = existing_alert.get('status', 'sent')
                    if status in ('reserved', 'sent'):
                        expires_at_str = existing_alert.get('expires_at')
                        if expires_at_str:
                            try:
                                expires_at = datetime.fromisoformat(expires_at_str)
                                if datetime.now() < expires_at:
                                    self.duplicates_prevented += 1
                                    logger.debug(f"Duplicate alert prevented (status: {status}) for user {user_id}: {alert_type}")
                                    return False
                                # Expired - fall through to Step 2 to reserve again
                            except Exception as e:
                                logger.warning(f"Error parsing expires_at: {e}")
                        else:
                            # No expires_at: treat as duplicate
                            self.duplicates_prevented += 1
                            logger.debug(f"Duplicate alert prevented (status: {status}, no expires_at) for user {user_id}: {alert_type}")
                            return False
                
                # Step 2: Re-check immediately before reserve to avoid overwriting 'sent'
                # (Another thread may have marked_sent between our Step 1 GET and now - e.g. replication lag)
                existing_alert = self.firebase._make_request('GET', alert_path)
                if existing_alert and isinstance(existing_alert, dict):
                    status = existing_alert.get('status', 'sent')
                    if status == 'sent':
                        expires_at_str = existing_alert.get('expires_at')
                        if expires_at_str:
                            try:
                                expires_at = datetime.fromisoformat(expires_at_str)
                                if datetime.now() < expires_at:
                                    self.duplicates_prevented += 1
                                    logger.info(f"📋 DEDUP_BLOCK reserve aborted: record already sent (re-check before PUT) user={user_id[:16]}...")
                                    return False
                            except Exception:
                                pass
                        else:
                            self.duplicates_prevented += 1
                            logger.info(f"📋 DEDUP_BLOCK reserve aborted: record already sent (no expires) user={user_id[:16]}...")
                            return False

                # Step 3: Alert doesn't exist or is expired - try to reserve it
                # Use a unique timestamp to identify our reservation
                # SOLUTION 4: Increased reservation window from 5 to 10 minutes
                now = datetime.now()
                expires_at = now + timedelta(minutes=10)  # Increased from 5 to 10 minutes
                our_reserved_at = now.isoformat()
                
                reserve_record = {
                    'alert_type': alert_type,
                    'user_id': user_id,
                    'status': 'reserved',  # Mark as reserved, not sent yet
                    'reserved_at': our_reserved_at,
                    'expires_at': expires_at.isoformat()
                }
                
                # Step 4: Try to create reservation (PUT is atomic in Firebase)
                result = self.firebase._make_request('PUT', alert_path, reserve_record)
                
                if result is None:
                    # Firebase error - retry
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.warning(f"Failed to reserve alert in Firebase after {max_retries} attempts")
                        return True  # Fail open
                
                # Step 5: Verify we got the reservation (handle eventual consistency)
                # SOLUTION 4: Increased verification delay from 0.2s to 0.5s
                # This gives Firebase more time to propagate changes globally
                time.sleep(0.5)  # Increased from 0.2s to 0.5s for better propagation
                
                verify_alert = self.firebase._make_request('GET', alert_path)
                if verify_alert and isinstance(verify_alert, dict):
                    verify_status = verify_alert.get('status', '')
                    verify_reserved_at = verify_alert.get('reserved_at', '')
                    
                    # If status is reserved and reserved_at matches ours, we got it
                    if verify_status == 'reserved' and verify_reserved_at == our_reserved_at:
                        logger.info(f"📋 RESERVED content={content[:60]}... user={user_id[:16]}... (we won)")
                        logger.info(f"✅ Successfully reserved alert for user {user_id}: {alert_type}")
                        return True
                    elif verify_status == 'reserved' and verify_reserved_at != our_reserved_at:
                        # Someone else reserved it first (different timestamp)
                        logger.warning(f"🚫 Alert already reserved by another instance (their: {verify_reserved_at}, ours: {our_reserved_at})")
                        return False
                    elif verify_status == 'sent':
                        # Already sent
                        logger.warning(f"🚫 Alert already sent for user {user_id}: {alert_type}")
                        return False
                    else:
                        # Status doesn't match - retry
                        if attempt < max_retries - 1:
                            logger.debug(f"Reservation verification failed (status: {verify_status}), retrying...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.warning(f"Reservation verification failed after {max_retries} attempts")
                            return True  # Fail open
                else:
                    # No record found - retry
                    if attempt < max_retries - 1:
                        logger.debug(f"Reservation not found in verification, retrying...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.warning(f"Reservation verification failed - no record found")
                        return True  # Fail open
                
            except Exception as e:
                logger.error(f"Error in check-and-reserve (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.warning(f"Failed to check-and-reserve alert after {max_retries} attempts")
                    return True  # Fail open
        
        # Should not reach here, but fail open if we do
        return True
    
    def mark_news_alert_sent(self, news_item: Dict[str, Any], user_id: str, mark_global_hash: bool = False) -> bool:
        """
        Mark a news alert as sent after successful delivery
        Phase 2 improvement: Only mark global hash if mark_global_hash=True (after successful delivery)
        Updates reserved record to sent status
        """
        try:
            # Single source of truth: same content string as check/reserve (always title+source)
            content = self._get_news_content_string(news_item)
            # Mark per-user alert as sent (updates reserved record)
            per_user_success = self.mark_alert_sent('news', content, user_id)
            
            # Phase 2 improvement: Only mark global hash after successful delivery
            if mark_global_hash and per_user_success:
                content_hash = self._get_news_content_hash(news_item)
                if content_hash:
                    # Mark global content hash only after successful delivery
                    self._mark_global_content_hash(content_hash)
                    logger.info(f"✅ Global hash marked after successful delivery for user {user_id}")
            
            return per_user_success
            
        except Exception as e:
            logger.error(f"Error marking news alert as sent: {e}")
            return False
    
    def reserve_news_alert(self, news_item: Dict[str, Any], user_id: str) -> bool:
        """
        Atomically reserve a news alert for this user (call after lock, before send).
        Returns True if we got the reservation, False if already reserved/sent by another thread or run.
        """
        content = self._get_news_content_string(news_item)
        return self._check_and_reserve_alert('news', content, user_id)
    
    def _economic_content(self, event: Dict[str, Any], alert_timing: str) -> str:
        """Build content string for economic alert dedup (same for check and mark)."""
        title = event.get('title', '')
        event_time = event.get('time', '')
        event_date = event.get('date', '')
        event_id = event.get('id', '')
        if event_id:
            return f"economic:{event_id}:{alert_timing}"
        return f"economic:{title}|{event_time}|{event_date}|{alert_timing}"

    def should_send_economic_alert(self, event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
        """Check if economic alert should be sent (not a duplicate). Caller must call mark_economic_alert_sent after successful send."""
        try:
            content = self._economic_content(event, alert_timing)
            return self.should_send_alert('economic', content, user_id)
        except Exception as e:
            logger.error(f"Error checking economic alert deduplication: {e}")
            return True  # Allow alert if check fails

    def mark_economic_alert_sent(self, event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
        """Mark economic alert as sent (call after successful Telegram send)."""
        try:
            content = self._economic_content(event, alert_timing)
            return self.mark_alert_sent('economic', content, user_id)
        except Exception as e:
            logger.error(f"Error marking economic alert as sent: {e}")
            return False
    
    def cleanup_expired_alerts(self) -> int:
        """Clean up expired alert records from Firebase (including reserved alerts)"""
        try:
            # Get all alerts
            alerts_path = "alert_deduplication/alerts"
            all_alerts = self.firebase._make_request('GET', alerts_path)
            
            if not all_alerts or not isinstance(all_alerts, dict):
                return 0
            
            now = datetime.now()
            expired_count = 0
            reserved_expired_count = 0
            
            # Check each alert and delete expired ones
            for alert_key, alert_data in list(all_alerts.items()):
                if isinstance(alert_data, dict):
                    expires_at_str = alert_data.get('expires_at')
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if now >= expires_at:
                                # Delete expired alert
                                alert_path = self._get_alert_path(alert_key)
                                self.firebase._make_request('DELETE', alert_path)
                                expired_count += 1
                                
                                # Track reserved alerts that expired (these are problematic)
                                status = alert_data.get('status', 'sent')
                                if status == 'reserved':
                                    reserved_expired_count += 1
                                    logger.warning(f"Expired reserved alert found: {alert_key} - alert may have failed to send")
                        except Exception as e:
                            logger.warning(f"Error parsing expires_at for alert {alert_key}: {e}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired alert records ({reserved_expired_count} were reserved)")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired alerts: {e}")
            return 0
    
    def _cleanup_expired_content_hashes(self) -> int:
        """Clean up expired global content hash records from Firebase"""
        try:
            # Get all content hashes
            content_hashes_path = "alert_deduplication/content_hashes"
            all_hashes = self.firebase._make_request('GET', content_hashes_path)
            
            if not all_hashes or not isinstance(all_hashes, dict):
                return 0
            
            now = datetime.now()
            expired_count = 0
            
            # Check each hash and delete expired ones
            for content_hash, hash_data in list(all_hashes.items()):
                if isinstance(hash_data, dict):
                    expires_at_str = hash_data.get('expires_at')
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if now >= expires_at:
                                # Delete expired hash
                                hash_path = self._get_content_hash_path(content_hash)
                                self.firebase._make_request('DELETE', hash_path)
                                # Also remove from in-memory cache
                                with self._cache_lock:
                                    self._content_hash_cache.pop(content_hash, None)
                                expired_count += 1
                        except Exception as e:
                            logger.warning(f"Error parsing expires_at for content hash {content_hash}: {e}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired content hash records")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired content hashes: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        try:
            alerts_path = "alert_deduplication/alerts"
            all_alerts = self.firebase._make_request('GET', alerts_path)
            total_records = len(all_alerts) if isinstance(all_alerts, dict) else 0
            
            return {
                'total_records': total_records,
                'operations_count': self.operations_count,
                'duplicates_prevented': self.duplicates_prevented,
                'alert_ttl_hours': self.alert_ttl_hours
            }
        except Exception as e:
            logger.error(f"Error getting deduplication stats: {e}")
            return {
                'total_records': 0,
                'operations_count': self.operations_count,
                'duplicates_prevented': self.duplicates_prevented,
                'alert_ttl_hours': self.alert_ttl_hours
            }
    
    def clear_user_alerts(self, user_id: str) -> int:
        """Clear all alert records for a specific user"""
        try:
            alerts_path = "alert_deduplication/alerts"
            all_alerts = self.firebase._make_request('GET', alerts_path)
            
            if not all_alerts or not isinstance(all_alerts, dict):
                return 0
            
            cleared_count = 0
            
            # Find and delete all alerts for this user
            for alert_key, alert_data in list(all_alerts.items()):
                if isinstance(alert_data, dict) and alert_data.get('user_id') == user_id:
                    alert_path = self._get_alert_path(alert_key)
                    self.firebase._make_request('DELETE', alert_path)
                    cleared_count += 1
            
            if cleared_count > 0:
                logger.info(f"Cleared {cleared_count} alert records for user {user_id}")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing user alerts: {e}")
            return 0
    
    def set_force_send_mode(self, enabled: bool):
        """Enable/disable force send mode (bypasses deduplication for testing)"""
        self.force_send_mode = enabled
        logger.info(f"Force send mode {'enabled' if enabled else 'disabled'}")
    
    def clear_all_expired_hashes(self) -> int:
        """Manually trigger cleanup of all expired content hashes (for maintenance)"""
        return self._cleanup_expired_content_hashes()
    
    def clear_all_expired_alerts(self) -> int:
        """Manually trigger cleanup of all expired alerts (for maintenance)"""
        return self.cleanup_expired_alerts()

# Global singleton instance
_persistent_deduplication = None

def get_persistent_deduplication() -> PersistentAlertDeduplication:
    """Get the global persistent deduplication instance"""
    global _persistent_deduplication
    if _persistent_deduplication is None:
        _persistent_deduplication = PersistentAlertDeduplication()
    return _persistent_deduplication

# Convenience functions for backward compatibility
def should_send_news_alert(news_item: Dict[str, Any], user_id: str) -> bool:
    """Check if news alert should be sent (not a duplicate)"""
    dedup = get_persistent_deduplication()
    return dedup.should_send_news_alert(news_item, user_id)

def mark_news_alert_sent(news_item: Dict[str, Any], user_id: str, mark_global_hash: bool = False) -> bool:
    """Mark a news alert as sent after successful delivery. Pass mark_global_hash=True to update global content hash."""
    dedup = get_persistent_deduplication()
    return dedup.mark_news_alert_sent(news_item, user_id, mark_global_hash=mark_global_hash)

def reserve_news_alert(news_item: Dict[str, Any], user_id: str) -> bool:
    """Reserve a news alert for this user (call after lock, before send). Returns True if reservation won."""
    dedup = get_persistent_deduplication()
    return dedup.reserve_news_alert(news_item, user_id)

def should_send_economic_alert(event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
    """Check if economic alert should be sent (not a duplicate). Caller must call mark_economic_alert_sent after send."""
    dedup = get_persistent_deduplication()
    return dedup.should_send_economic_alert(event, user_id, alert_timing)

def mark_economic_alert_sent(event: Dict[str, Any], user_id: str, alert_timing: str) -> bool:
    """Mark economic alert as sent (call after successful Telegram send)."""
    dedup = get_persistent_deduplication()
    return dedup.mark_economic_alert_sent(event, user_id, alert_timing)

def get_deduplication_stats() -> Dict[str, Any]:
    """Get deduplication statistics"""
    dedup = get_persistent_deduplication()
    return dedup.get_stats()

def clear_user_deduplication(user_id: str) -> int:
    """Clear deduplication records for a user"""
    dedup = get_persistent_deduplication()
    return dedup.clear_user_alerts(user_id)

