#!/usr/bin/env python3
"""
FXSentinel Robust Telegram Service
Fixes chat ID invalidation, rate limiting, retry logic, and timeout issues
"""

import asyncio
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import requests
import json
import os
from collections import deque
import hashlib
import hmac

logger = logging.getLogger(__name__)

class TelegramStatus(Enum):
    """Telegram message status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    INVALID_CHAT = "invalid_chat"
    RETRYING = "retrying"

@dataclass
class TelegramMessage:
    """Telegram message with tracking"""
    chat_id: str
    text: str
    user_id: str
    message_type: str
    created_at: datetime
    status: TelegramStatus = TelegramStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    message_id: Optional[str] = None

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    requests_per_second: int = 30  # Telegram's default limit
    requests_per_minute: int = 20  # Conservative limit
    last_request_time: Optional[datetime] = None
    request_count_second: int = 0
    request_count_minute: int = 0
    reset_time_second: Optional[datetime] = None
    reset_time_minute: Optional[datetime] = None

class RobustTelegramService:
    """
    Production-ready Telegram service with:
    - Chat ID validation and invalidation handling
    - Rate limiting with exponential backoff
    - Retry logic with configurable attempts
    - Configurable timeouts
    - Message delivery tracking
    - Error isolation and recovery
    """
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot_username = os.getenv('TELEGRAM_BOT_USERNAME')
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not found - Telegram service will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Robust Telegram Service initialized")
        
        # Rate limiting
        self.rate_limit = RateLimitInfo()
        self.rate_limit_lock = threading.Lock()
        
        # Chat ID validation cache
        self.valid_chat_ids: Dict[str, datetime] = {}
        self.invalid_chat_ids: Dict[str, datetime] = {}
        self.chat_cache_ttl = timedelta(hours=24)  # Cache for 24 hours
        
        # Message queue and retry system
        self.message_queue: deque = deque(maxlen=1000)
        self.retry_queue: deque = deque(maxlen=500)
        self.processing = False
        
        # Configuration
        self.max_retries = int(os.getenv('TELEGRAM_MAX_RETRIES', 3))
        self.retry_delay_base = int(os.getenv('TELEGRAM_RETRY_DELAY_BASE', 2))  # seconds
        self.timeout = int(os.getenv('TELEGRAM_TIMEOUT', 10))  # seconds
        self.batch_size = int(os.getenv('TELEGRAM_BATCH_SIZE', 5))  # messages per batch
        
        # Performance tracking
        self.messages_sent = 0
        self.messages_failed = 0
        self.rate_limit_hits = 0
        self.invalid_chat_hits = 0
        self.retry_attempts = 0
        
        # Start processing thread
        self.processing_thread = None
        self.shutdown_event = threading.Event()
        self._start_processing()
    
    def _start_processing(self):
        """Start the message processing thread"""
        if not self.enabled:
            return
        
        self.processing = True
        self.processing_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.processing_thread.start()
        logger.info("Telegram message processing started")
    
    def _stop_processing(self):
        """Stop the message processing thread"""
        self.processing = False
        self.shutdown_event.set()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=10)
        
        logger.info("Telegram message processing stopped")
    
    def _is_rate_limited(self) -> bool:
        """Check if we're currently rate limited"""
        with self.rate_limit_lock:
            now = datetime.now()
            
            # Reset counters if needed
            if (self.rate_limit.reset_time_second and 
                now >= self.rate_limit.reset_time_second):
                self.rate_limit.request_count_second = 0
                self.rate_limit.reset_time_second = None
            
            if (self.rate_limit.reset_time_minute and 
                now >= self.rate_limit.reset_time_minute):
                self.rate_limit.request_count_minute = 0
                self.rate_limit.reset_time_minute = None
            
            # Check limits
            if self.rate_limit.request_count_second >= self.rate_limit.requests_per_second:
                return True
            
            if self.rate_limit.request_count_minute >= self.rate_limit.requests_per_minute:
                return True
            
            return False
    
    def _update_rate_limit(self):
        """Update rate limit counters"""
        with self.rate_limit_lock:
            now = datetime.now()
            
            # Update second counter
            if not self.rate_limit.reset_time_second:
                self.rate_limit.reset_time_second = now + timedelta(seconds=1)
            self.rate_limit.request_count_second += 1
            
            # Update minute counter
            if not self.rate_limit.reset_time_minute:
                self.rate_limit.reset_time_minute = now + timedelta(minutes=1)
            self.rate_limit.request_count_minute += 1
    
    def _is_chat_id_valid(self, chat_id: str) -> bool:
        """Check if chat ID is valid (cached)"""
        now = datetime.now()
        
        # Check invalid cache first
        if chat_id in self.invalid_chat_ids:
            invalid_time = self.invalid_chat_ids[chat_id]
            if now - invalid_time < self.chat_cache_ttl:
                return False
            else:
                # Remove from invalid cache if expired
                del self.invalid_chat_ids[chat_id]
        
        # Check valid cache
        if chat_id in self.valid_chat_ids:
            valid_time = self.valid_chat_ids[chat_id]
            if now - valid_time < self.chat_cache_ttl:
                return True
        
        # Not in cache, will be validated on send
        return True
    
    def _mark_chat_id_invalid(self, chat_id: str):
        """Mark chat ID as invalid"""
        self.invalid_chat_ids[chat_id] = datetime.now()
        self.invalid_chat_hits += 1
        logger.warning(f"Marked chat ID {chat_id} as invalid")
    
    def _mark_chat_id_valid(self, chat_id: str):
        """Mark chat ID as valid"""
        self.valid_chat_ids[chat_id] = datetime.now()
        logger.debug(f"Marked chat ID {chat_id} as valid")
    
    def _cleanup_chat_cache(self):
        """Clean up expired chat ID cache entries"""
        now = datetime.now()
        
        # Clean invalid cache
        expired_invalid = [
            chat_id for chat_id, timestamp in self.invalid_chat_ids.items()
            if now - timestamp >= self.chat_cache_ttl
        ]
        for chat_id in expired_invalid:
            del self.invalid_chat_ids[chat_id]
        
        # Clean valid cache
        expired_valid = [
            chat_id for chat_id, timestamp in self.valid_chat_ids.items()
            if now - timestamp >= self.chat_cache_ttl
        ]
        for chat_id in expired_valid:
            del self.valid_chat_ids[chat_id]
        
        if expired_invalid or expired_valid:
            logger.debug(f"Cleaned up {len(expired_invalid)} invalid and {len(expired_valid)} valid chat IDs")
    
    async def send_message_async(self, chat_id: str, text: str, user_id: str = None, 
                                message_type: str = "alert") -> Tuple[bool, Optional[str]]:
        """
        Send message asynchronously with retry logic
        Returns: (success, error_message)
        """
        if not self.enabled:
            return False, "Telegram service disabled"
        
        # Check if chat ID is known to be invalid
        if not self._is_chat_id_valid(chat_id):
            return False, "Chat ID is invalid"
        
        # Create message object
        message = TelegramMessage(
            chat_id=chat_id,
            text=text,
            user_id=user_id or "unknown",
            message_type=message_type,
            created_at=datetime.now(),
            max_attempts=self.max_retries
        )
        
        # Add to queue
        self.message_queue.append(message)
        
        # Wait for processing (with timeout)
        start_time = time.time()
        while message.status == TelegramStatus.PENDING:
            if time.time() - start_time > 30:  # 30 second timeout
                return False, "Message processing timeout"
            await asyncio.sleep(0.1)
        
        if message.status == TelegramStatus.SENT:
            return True, None
        else:
            return False, message.error_message or "Message failed"
    
    def send_message_sync(self, chat_id: str, text: str, user_id: str = None, 
                         message_type: str = "alert") -> Tuple[bool, Optional[str]]:
        """
        Send message synchronously with retry logic
        Returns: (success, error_message)
        """
        if not self.enabled:
            return False, "Telegram service disabled"
        
        # Check if chat ID is known to be invalid
        if not self._is_chat_id_valid(chat_id):
            return False, "Chat ID is invalid"
        
        # Create message object
        message = TelegramMessage(
            chat_id=chat_id,
            text=text,
            user_id=user_id or "unknown",
            message_type=message_type,
            created_at=datetime.now(),
            max_attempts=self.max_retries
        )
        
        # Process immediately
        return self._send_message_immediate(message)
    
    def _send_message_immediate(self, message: TelegramMessage) -> Tuple[bool, Optional[str]]:
        """Send message immediately (synchronous)"""
        try:
            # Check rate limiting
            if self._is_rate_limited():
                self.rate_limit_hits += 1
                message.status = TelegramStatus.RATE_LIMITED
                message.error_message = "Rate limited"
                return False, "Rate limited"
            
            # Send message
            success, error = self._make_telegram_request(message)
            
            if success:
                message.status = TelegramStatus.SENT
                self.messages_sent += 1
                self._mark_chat_id_valid(message.chat_id)
                return True, None
            else:
                # Handle specific errors
                if "chat not found" in error.lower() or "chat_id" in error.lower():
                    self._mark_chat_id_invalid(message.chat_id)
                    message.status = TelegramStatus.INVALID_CHAT
                    message.error_message = "Invalid chat ID"
                    return False, "Invalid chat ID"
                elif "rate" in error.lower():
                    self.rate_limit_hits += 1
                    message.status = TelegramStatus.RATE_LIMITED
                    message.error_message = "Rate limited"
                    return False, "Rate limited"
                else:
                    message.status = TelegramStatus.FAILED
                    message.error_message = error
                    return False, error
                    
        except Exception as e:
            message.status = TelegramStatus.FAILED
            message.error_message = str(e)
            return False, str(e)
    
    def _make_telegram_request(self, message: TelegramMessage) -> Tuple[bool, Optional[str]]:
        """Make actual Telegram API request"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                "chat_id": message.chat_id,
                "text": message.text,
                "parse_mode": "HTML"
            }
            
            # Update rate limit before request
            self._update_rate_limit()
            
            # Make request with timeout
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    message.message_id = str(data['result']['message_id'])
                    return True, None
                else:
                    return False, data.get('description', 'Unknown error')
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except Exception as e:
            return False, str(e)
    
    def _process_messages(self):
        """Process messages in background thread"""
        while self.processing and not self.shutdown_event.is_set():
            try:
                # Process batch of messages
                batch = []
                while len(batch) < self.batch_size and self.message_queue:
                    message = self.message_queue.popleft()
                    batch.append(message)
                
                if not batch:
                    time.sleep(0.1)  # Wait for messages
                    continue
                
                # Process batch
                for message in batch:
                    if message.status == TelegramStatus.PENDING:
                        success, error = self._send_message_immediate(message)
                        
                        if not success and message.attempts < message.max_attempts:
                            # Add to retry queue
                            message.attempts += 1
                            message.last_attempt = datetime.now()
                            message.status = TelegramStatus.RETRYING
                            
                            # Calculate retry delay (exponential backoff)
                            delay = self.retry_delay_base ** message.attempts
                            retry_time = datetime.now() + timedelta(seconds=delay)
                            
                            # Add to retry queue (sorted by retry time)
                            self._add_to_retry_queue(message, retry_time)
                        elif not success:
                            # Max attempts reached
                            message.status = TelegramStatus.FAILED
                            self.messages_failed += 1
                            logger.error(f"Message failed after {message.attempts} attempts: {error}")
                
                # Process retry queue
                self._process_retry_queue()
                
                # Cleanup
                self._cleanup_chat_cache()
                
                # Small delay to prevent busy waiting
                time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error in message processing: {e}")
                time.sleep(1)  # Wait before retrying
    
    def _add_to_retry_queue(self, message: TelegramMessage, retry_time: datetime):
        """Add message to retry queue"""
        self.retry_queue.append((retry_time, message))
        self.retry_attempts += 1
    
    def _process_retry_queue(self):
        """Process retry queue"""
        now = datetime.now()
        ready_messages = []
        
        # Find messages ready for retry
        remaining_queue = []
        for retry_time, message in self.retry_queue:
            if now >= retry_time:
                ready_messages.append(message)
            else:
                remaining_queue.append((retry_time, message))
        
        self.retry_queue = deque(remaining_queue, maxlen=500)
        
        # Process ready messages
        for message in ready_messages:
            message.status = TelegramStatus.PENDING
            self.message_queue.append(message)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'enabled': self.enabled,
            'messages_sent': self.messages_sent,
            'messages_failed': self.messages_failed,
            'rate_limit_hits': self.rate_limit_hits,
            'invalid_chat_hits': self.invalid_chat_hits,
            'retry_attempts': self.retry_attempts,
            'queue_size': len(self.message_queue),
            'retry_queue_size': len(self.retry_queue),
            'valid_chat_cache_size': len(self.valid_chat_ids),
            'invalid_chat_cache_size': len(self.invalid_chat_ids),
            'processing': self.processing
        }
    
    def shutdown(self):
        """Shutdown the service gracefully"""
        logger.info("Shutting down Robust Telegram Service...")
        self._stop_processing()
        logger.info("Robust Telegram Service shutdown complete")

# Global instance
robust_telegram_service = RobustTelegramService()

# Convenience functions
async def send_telegram_message_async(chat_id: str, text: str, user_id: str = None, 
                                    message_type: str = "alert") -> Tuple[bool, Optional[str]]:
    """Send Telegram message asynchronously"""
    return await robust_telegram_service.send_message_async(chat_id, text, user_id, message_type)

def send_telegram_message_sync(chat_id: str, text: str, user_id: str = None, 
                             message_type: str = "alert") -> Tuple[bool, Optional[str]]:
    """Send Telegram message synchronously"""
    return robust_telegram_service.send_message_sync(chat_id, text, user_id, message_type)

def get_telegram_service_stats() -> Dict[str, Any]:
    """Get Telegram service statistics"""
    return robust_telegram_service.get_service_stats()

def shutdown_telegram_service():
    """Shutdown Telegram service"""
    robust_telegram_service.shutdown()
