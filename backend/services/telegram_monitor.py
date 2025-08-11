import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from telethon import TelegramClient, events
from telethon.tl.types import Channel, User
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramMonitor:
    def __init__(self):
        # Telegram API credentials (will be set via environment variables)
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.session_name = 'fxsentinel_session'
        
        # Channel to monitor
        self.target_channels = [
            'WatcherGuru',  # Main channel - https://t.me/WatcherGuru
            '@WatcherGuru',  # With @ symbol
            'WatcherGuruChat',  # Chat channel mentioned in description
            'forex_signals',  # Test public forex channel
            'forex_news',  # Test public forex channel
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
        
    async def initialize_client(self):
        """Initialize Telegram client"""
        try:
            if not self.api_id or not self.api_hash:
                logger.error("Telegram API credentials not configured")
                return False
                
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start(bot_token=self.bot_token)
            self.is_connected = True
            logger.info("Telegram client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect Telegram client"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            logger.info("Telegram client disconnected")
    
    def is_forex_related(self, message_text: str) -> bool:
        """Check if message is forex-related"""
        text = message_text.lower()
        
        for keyword in self.forex_keywords:
            if keyword.lower() in text:
                return True
        return False
    
    def determine_impact_level(self, message_text: str) -> str:
        """Determine impact level of the message"""
        text = message_text.lower()
        
        for keyword in self.high_impact_keywords:
            if keyword.lower() in text:
                return 'high'
        
        for keyword in self.medium_impact_keywords:
            if keyword.lower() in text:
                return 'medium'
        
        return 'low'
    
    def extract_currency_pairs(self, message_text: str) -> List[str]:
        """Extract currency pairs from message"""
        text = message_text.lower()
        currency_pairs = []
        
        # Common currency pair patterns
        pairs = ['eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd', 'eur/gbp', 'eur/jpy', 'gbp/jpy']
        
        for pair in pairs:
            if pair in text:
                currency_pairs.append(pair.upper())
        
        return currency_pairs
    
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
            article_id = hash(f"telegram_{channel_name}_{message.id}_{message_date.isoformat()}")
            
            return {
                'id': abs(article_id),
                'title': title,
                'summary': summary + '...' if len(summary) >= 200 else summary,
                'source': f'Telegram - {channel_name}',
                'url': '',  # Telegram messages don't have direct URLs
                'published_at': message_date.isoformat(),
                'impact': impact,
                'currency_pairs': currency_pairs,
                'type': 'TELEGRAM',
                'status': 'PUBLISHED',
                'message_id': message.id,
                'channel': channel_name
            }
            
        except Exception as e:
            logger.error(f"Error parsing Telegram message: {e}")
            return None
    
    async def get_channel_messages(self, channel_username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from a Telegram channel"""
        try:
            if not self.is_connected:
                await self.initialize_client()
            
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
            
            # Get recent messages
            messages = []
            async for message in self.client.iter_messages(channel_entity, limit=limit):
                if hasattr(message, 'text') and message.text:
                    parsed_message = self.parse_message(message, channel_username)
                    if parsed_message:
                        messages.append(parsed_message)
            
            logger.info(f"Fetched {len(messages)} forex-related messages from {channel_username}")
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages from {channel_username}: {e}")
            return []
    
    async def get_recent_telegram_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent forex-related news from Telegram channels"""
        try:
            if not self.is_connected:
                await self.initialize_client()
            
            all_messages = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Fetch from all target channels
            for channel in self.target_channels:
                try:
                    messages = await self.get_channel_messages(channel, limit=100)
                    all_messages.extend(messages)
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
telegram_monitor = TelegramMonitor()
