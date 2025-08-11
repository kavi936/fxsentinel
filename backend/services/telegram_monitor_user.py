#!/usr/bin/env python3
"""
Telegram Monitor using User Account (not bot token)
This allows reading messages from public channels like WatcherGuru
"""

import os
import re
import fcntl
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from telethon import TelegramClient
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramUserMonitor:
    def __init__(self):
        # Telegram API credentials (user account, not bot)
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')  # Your phone number
        self.session_name = 'fxsentinel_user_session'
        
        # Channel to monitor (only main channel, exclude chat)
        self.target_channels = [
            'WatcherGuru',  # Main channel - https://t.me/WatcherGuru
            '@WatcherGuru',  # With @ symbol
        ]
        
        # Forex keywords for filtering
        self.forex_keywords = [
            'forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'franc',
            'cpi', 'inflation', 'interest rate', 'fed', 'ecb', 'boj', 'boe',
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad',
            'non-farm payrolls', 'gdp', 'retail sales', 'manufacturing',
            'unemployment', 'employment', 'wages', 'trade balance'
        ]
        
        # Impact keywords
        self.high_impact_keywords = ['cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 'non-farm payrolls', 'gdp']
        self.medium_impact_keywords = ['retail sales', 'manufacturing', 'unemployment', 'employment', 'trade balance']
        
        # Client instance
        self.client = None
        self.is_connected = False
        self._connection_lock = asyncio.Lock()
        self._session_lock_file = None
        
    def _acquire_session_lock(self):
        """Acquire a file lock to prevent multiple processes from using the session"""
        try:
            lock_file_path = f"/tmp/telegram_session_{self.session_name}.lock"
            self._session_lock_file = open(lock_file_path, 'w')
            fcntl.flock(self._session_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.info("Acquired session lock")
            return True
        except (IOError, OSError) as e:
            logger.error(f"Could not acquire session lock: {e}")
            return False
    
    def _release_session_lock(self):
        """Release the session lock"""
        if self._session_lock_file:
            try:
                fcntl.flock(self._session_lock_file.fileno(), fcntl.LOCK_UN)
                self._session_lock_file.close()
                logger.info("Released session lock")
            except:
                pass
            self._session_lock_file = None
        
    async def initialize_client(self):
        """Initialize Telegram client with user account"""
        async with self._connection_lock:
            try:
                if not self.api_id or not self.api_hash:
                    logger.error("Telegram API credentials not configured")
                    return False
                
                # Check if already connected
                if self.is_connected and self.client and self.client.is_connected():
                    logger.info("Telegram client already connected")
                    return True
                
                # Acquire session lock
                if not self._acquire_session_lock():
                    logger.error("Could not acquire session lock, another process may be using it")
                    return False
                
                # Create client with user session (not bot)
                self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
                
                # Start client (will prompt for phone/verification on first run)
                await self.client.start(phone=self.phone)
                self.is_connected = True
                logger.info("Telegram user client initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize Telegram user client: {e}")
                self.is_connected = False
                self._release_session_lock()
                return False
    
    async def ensure_connected(self):
        """Ensure client is connected, reconnect if needed"""
        try:
            if not self.client or not self.client.is_connected():
                logger.info("Client not connected, reconnecting...")
                await self.initialize_client()
            
            # Check if we're actually authorized
            if self.client and not await self.client.is_user_authorized():
                logger.error("Client not authorized, need to run setup script first")
                return False
                
            return self.is_connected
        except Exception as e:
            logger.error(f"Error ensuring connection: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect Telegram client"""
        async with self._connection_lock:
            if self.client and self.is_connected:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.is_connected = False
                logger.info("Telegram user client disconnected")
            
            # Release session lock
            self._release_session_lock()
    
    def is_forex_related(self, message_text: str) -> bool:
        """Check if message is forex-related using enhanced filtering"""
        from .enhanced_forex_filter import enhanced_forex_filter
        return enhanced_forex_filter.is_forex_related(message_text, "")
    
    def determine_impact_level(self, message_text: str) -> str:
        """Determine impact level using enhanced filtering"""
        from .enhanced_forex_filter import enhanced_forex_filter
        score = enhanced_forex_filter.get_forex_score(message_text, "")
        return score['impact_level']
    
    def extract_currency_pairs(self, message_text: str) -> List[str]:
        """Extract currency pairs using enhanced filtering"""
        from .enhanced_forex_filter import enhanced_forex_filter
        return enhanced_forex_filter.extract_currency_pairs(message_text, "")
    
    def parse_message(self, message, channel_name: str) -> Optional[Dict[str, Any]]:
        """Parse Telegram message into news format"""
        try:
            # Get message text
            message_text = message.text if hasattr(message, 'text') else ''
            if not message_text:
                return None
            
            # Check if forex-related
            if not self.is_forex_related(message_text):
                return None
            
            # Get message date
            message_date = message.date if hasattr(message, 'date') else datetime.now()
            
            # Clean message text
            clean_text = re.sub(r'http\S+', '', message_text)  # Remove URLs
            clean_text = re.sub(r'@\w+', '', clean_text)  # Remove mentions
            clean_text = clean_text.strip()
            
            # Split into title and summary
            lines = clean_text.split('\n')
            title = lines[0][:100] if lines else "Telegram Update"
            summary = '\n'.join(lines[1:])[:200] if len(lines) > 1 else clean_text[:200]
            
            # Determine impact and currency pairs
            impact = self.determine_impact_level(clean_text)
            currency_pairs = self.extract_currency_pairs(clean_text)
            
            # Generate unique ID
            article_id = hash(f"telegram_user_{channel_name}_{message.id}_{message_date.isoformat()}")
            
            return {
                'id': abs(article_id),
                'title': title,
                'summary': summary + '...' if len(summary) >= 200 else summary,
                'source': f'Telegram - {channel_name}',
                'url': '',  # Telegram messages don't have direct URLs
                'published_at': message_date.isoformat(),
                'impact': impact,
                'currency_pairs': currency_pairs,
                'type': 'TELEGRAM_USER',
                'status': 'PUBLISHED',
                'message_id': message.id,
                'channel': channel_name
            }
            
        except Exception as e:
            logger.error(f"Error parsing Telegram message: {e}")
            return None
    
    async def get_channel_messages(self, channel_username: str, limit: int = 20) -> List[Dict[str, Any]]:  # Reduced from 50 to 20
        """Get recent messages from a Telegram channel using user account"""
        try:
            # Ensure we're connected
            if not await self.ensure_connected():
                logger.error("Failed to connect to Telegram")
                return []
            
            # Try different channel name formats
            channel_variants = [
                channel_username,
                f"@{channel_username}",
                channel_username.replace('@', '')
            ]
            
            channel_entity = None
            for variant in channel_variants:
                try:
                    channel_entity = await self.client.get_entity(variant)
                    break
                except:
                    continue
            
            if not channel_entity:
                logger.error(f"Could not find channel: {channel_username}")
                return []
            
            # Get recent messages (user account can read public channels)
            messages = []
            async for message in self.client.iter_messages(channel_entity, limit=limit):
                if hasattr(message, 'text') and message.text:
                    parsed_message = self.parse_message(message, channel_username)
                    if parsed_message:
                        messages.append(parsed_message)
                        # Stop after finding 10 forex-related messages for performance
                        if len(messages) >= 10:
                            break
            
            logger.info(f"Fetched {len(messages)} forex-related messages from {channel_username}")
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages from {channel_username}: {e}")
            return []
    
    async def get_recent_telegram_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent forex-related news from Telegram channels using user account"""
        try:
            # Ensure we're connected with timeout
            try:
                connected = await asyncio.wait_for(self.ensure_connected(), timeout=10.0)
                if not connected:
                    logger.error("Failed to connect to Telegram within timeout")
                    return []
            except asyncio.TimeoutError:
                logger.error("Telegram connection timeout")
                return []
            
            all_messages = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Fetch from all target channels with timeout
            for channel in self.target_channels:
                try:
                    messages = await asyncio.wait_for(
                        self.get_channel_messages(channel, limit=20),  # Reduced limit
                        timeout=8.0  # Reduced from 15 to 8 seconds
                    )
                    all_messages.extend(messages)
                except asyncio.TimeoutError:
                    logger.error(f"Timeout fetching from {channel}")
                    continue
                except Exception as e:
                    logger.error(f"Error fetching from {channel}: {e}")
                    continue
            
            # Filter by time and remove duplicates
            recent_messages = []
            seen_titles = set()
            
            for message in all_messages:
                try:
                    message_date = datetime.fromisoformat(message['published_at'].replace('Z', '+00:00'))
                    if message_date >= cutoff_time:
                        # Simple deduplication based on title
                        title_key = message['title'][:50].lower()
                        if title_key not in seen_titles:
                            seen_titles.add(title_key)
                            recent_messages.append(message)
                except:
                    # If date parsing fails, include the message
                    recent_messages.append(message)
            
            # Sort by date (newest first)
            recent_messages.sort(key=lambda x: x['published_at'], reverse=True)
            
            logger.info(f"Retrieved {len(recent_messages)} recent Telegram news items")
            return recent_messages[:20]  # Limit to 20 most recent
            
        except Exception as e:
            logger.error(f"Error getting recent Telegram news: {e}")
            return []

# Global instance
telegram_user_monitor = TelegramUserMonitor()
