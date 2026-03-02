#!/usr/bin/env python3
"""
Session-Isolated Synchronous wrapper for Telegram service
Creates a fresh client instance for each call to prevent session corruption
"""

import asyncio
import hashlib
import threading
import os
import tempfile
import uuid
import shutil
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SessionIsolatedTelegramWrapper:
    """Session-isolated synchronous wrapper for Telegram service"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        
        # Use production session file if available, otherwise fall back to local
        if os.path.exists('telegram_session_production.session'):
            self.original_session_name = 'telegram_session_production'
        else:
            self.original_session_name = 'fxsentinel_user_session'
        
        if not all([self.api_id, self.api_hash, self.phone]):
            print("❌ Missing Telegram API credentials")
            self.enabled = False
        else:
            self.enabled = True
    
    def _create_isolated_client(self):
        """Create a completely isolated Telegram client with unique session"""
        # Create a unique session name for this call
        session_id = str(uuid.uuid4())
        session_name = f"temp_session_{session_id}"
        
        # Copy the original session file if it exists
        original_session_file = f"{self.original_session_name}.session"
        new_session_file = f"{session_name}.session"
        
        if os.path.exists(original_session_file):
            try:
                shutil.copy2(original_session_file, new_session_file)
                print(f"✅ Copied authenticated session to {session_name}")
            except Exception as e:
                print(f"⚠️ Could not copy session file: {e}")
                # Continue without copying - will need to authenticate
        
        # Create client with unique session
        client = TelegramClient(session_name, self.api_id, self.api_hash)
        return client, session_name
    
    def _cleanup_session(self, session_name):
        """Clean up temporary session files"""
        try:
            # Remove session file
            session_file = f"{session_name}.session"
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # Remove any other session-related files
            for ext in ['.session-journal', '.session-lock']:
                lock_file = f"{session_name}{ext}"
                if os.path.exists(lock_file):
                    os.remove(lock_file)
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up session {session_name}: {e}")
    
    async def _fetch_telegram_news_isolated(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch Telegram news using an isolated client session"""
        client = None
        session_name = None
        
        try:
            # Create isolated client
            client, session_name = self._create_isolated_client()
            
            # Start client
            await client.start(phone=self.phone)
            
            # Check if authorized
            if not await client.is_user_authorized():
                print("❌ Telegram client not authorized")
                return []
            
            # Target channels - use only unique channels (avoid duplicates from @ and non-@ versions)
            # Try to get the actual channel entity first to avoid duplicates
            target_channel_names = ['WatcherGuru', 'bricsnews']
            channel_entities = {}  # Map of channel ID to channel name to avoid duplicates
            
            all_messages = []
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # First, resolve all channel variants to actual entities
            for channel_name in target_channel_names:
                try:
                    # Try different channel name formats
                    channel_variants = [channel_name, channel_name.replace('@', ''), f"@{channel_name.replace('@', '')}"]
                    
                    channel_entity = None
                    for variant in channel_variants:
                        try:
                            entity = await client.get_entity(variant)
                            # Use channel ID as key to detect duplicates (same channel with different names)
                            channel_id = getattr(entity, 'id', None)
                            if channel_id and channel_id not in channel_entities:
                                channel_entities[channel_id] = (entity, channel_name)
                                channel_entity = entity
                                break
                            elif channel_id in channel_entities:
                                # Already have this channel, skip
                                channel_entity = None
                                break
                        except:
                            continue
                    
                    if not channel_entity:
                        if channel_id in channel_entities:
                            print(f"⚠️ Channel {channel_name} is duplicate of {channel_entities[channel_id][1]}, skipping")
                        else:
                            print(f"⚠️ Could not find channel: {channel_name}")
                        continue
                    
                    # Get messages from this unique channel
                    messages = []
                    async for message in client.iter_messages(channel_entity, limit=20):
                        if hasattr(message, 'text') and message.text:
                            # Parse message - use the original channel name
                            parsed = self._parse_message(message, channel_name)
                            if parsed:
                                messages.append(parsed)
                                if len(messages) >= 10:  # Limit per channel
                                    break
                    
                    all_messages.extend(messages)
                    print(f"✅ Fetched {len(messages)} messages from {channel_name}")
                    
                except Exception as e:
                    print(f"⚠️ Error fetching from {channel_name}: {e}")
                    continue
            
            # Filter by time and deduplicate
            # Use both title AND published_at to catch true duplicates (same message from different channel variants)
            recent_messages = []
            seen_keys = set()
            
            for message in all_messages:
                try:
                    message_date = datetime.fromisoformat(message['published_at'].replace('Z', '+00:00'))
                    if message_date >= cutoff_time:
                        # Create a unique key from title and published_at to catch duplicates
                        title_key = message['title'][:50].lower().strip()
                        date_key = message['published_at'][:16]  # Date + hour:minute (ignore seconds)
                        unique_key = f"{title_key}_{date_key}"
                        
                        if unique_key not in seen_keys:
                            seen_keys.add(unique_key)
                            recent_messages.append(message)
                except Exception as e:
                    # If date parsing fails, still include but use title only for dedup
                    title_key = message.get('title', '')[:50].lower().strip()
                    if title_key and title_key not in seen_keys:
                        seen_keys.add(title_key)
                        recent_messages.append(message)
            
            # Sort by date
            recent_messages.sort(key=lambda x: x['published_at'], reverse=True)
            
            print(f"✅ Retrieved {len(recent_messages)} recent Telegram news items")
            return recent_messages[:30]
            
        except Exception as e:
            print(f"❌ Error in isolated Telegram fetch: {e}")
            return []
        finally:
            # Always disconnect and cleanup
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
            
            if session_name:
                self._cleanup_session(session_name)
    
    def _parse_message(self, message, channel_name: str) -> Optional[Dict[str, Any]]:
        """Parse Telegram message into news format"""
        try:
            import re
            from datetime import datetime
            
            # Get message text
            message_text = message.text if hasattr(message, 'text') else ''
            if not message_text:
                return None
            
            # Check if forex-related - include gold, silver, and commodities as they impact forex
            # Use enhanced filter for better accuracy, but also include commodity keywords
            from .enhanced_forex_filter import enhanced_forex_filter
            
            text_lower = message_text.lower()
            
            # Check using enhanced filter (includes gold, silver, commodities)
            is_forex_related = enhanced_forex_filter.is_forex_related(
                message_text, '', channel_name
            )
            
            # Also check for commodity keywords that are forex-relevant
            # Gold and silver are safe-haven assets that impact currency markets
            commodity_keywords = [
                'gold', 'silver', 'precious metal', 'precious metals',
                'commodity', 'commodities', 'oil', 'crude', 'copper', 'natural gas',
                'safe haven', 'risk-off', 'risk-on'
            ]
            
            has_commodity = any(keyword in text_lower for keyword in commodity_keywords)
            
            # Include if forex-related OR if it's a commodity (gold/silver impact forex markets)
            if not is_forex_related and not has_commodity:
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
            
            # Determine impact level - include gold/silver as high impact (they're safe-haven assets that impact forex)
            high_impact = [
                'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 
                'non-farm payrolls', 'gdp', 'gold', 'silver', 'precious metal', 'precious metals'
            ]
            medium_impact = [
                'retail sales', 'manufacturing', 'unemployment', 'employment', 
                'trade balance', 'commodity', 'commodities', 'oil', 'crude'
            ]
            
            impact = 'low'
            if any(keyword in text_lower for keyword in high_impact):
                impact = 'high'
            elif any(keyword in text_lower for keyword in medium_impact):
                impact = 'medium'
            
            # Extract currency pairs - only match valid trading pairs
            currency_pairs = []
            
            # Valid currency pairs that are actually traded
            valid_pairs = {
                'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD', 'NZD/USD',
                'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/AUD', 'EUR/CAD', 'EUR/NZD',
                'GBP/JPY', 'GBP/CHF', 'GBP/AUD', 'GBP/CAD', 'GBP/NZD',
                'AUD/JPY', 'AUD/CAD', 'AUD/NZD', 'AUD/CHF',
                'CAD/JPY', 'CAD/CHF',
                'NZD/JPY', 'NZD/CHF',
                'CHF/JPY',
                'USD/SEK', 'USD/NOK', 'USD/HKD', 'USD/MXN', 'USD/ZAR', 'USD/TRY', 'USD/PLN', 'USD/CZK',
                'EUR/SEK', 'EUR/NOK', 'EUR/PLN', 'EUR/CZK', 'EUR/TRY',
                'GBP/SEK', 'GBP/NOK', 'GBP/PLN',
                'AUD/SEK', 'AUD/NOK',
                'USD/CNY', 'USD/INR', 'USD/KRW', 'USD/SGD', 'USD/BRL', 'USD/RUB', 'USD/HUF'
            }
            
            # Valid currency pair patterns (with slash)
            pair_pattern = r'\b([A-Z]{3})/([A-Z]{3})\b'
            matches = re.findall(pair_pattern, message_text.upper())
            for base, quote in matches:
                pair = f"{base}/{quote}"
                if pair in valid_pairs:
                    currency_pairs.append(pair)
            
            # Valid currency pair patterns (space-separated)
            pair_pattern_space = r'\b([A-Z]{3})\s+([A-Z]{3})\b'
            matches = re.findall(pair_pattern_space, message_text.upper())
            for base, quote in matches:
                pair = f"{base}/{quote}"
                if pair in valid_pairs:
                    currency_pairs.append(pair)
            
            # If no pairs found, use keyword-based detection
            if not currency_pairs:
                from .enhanced_forex_filter import enhanced_forex_filter
                currency_pairs = enhanced_forex_filter.extract_currency_pairs(message_text, "")
            
            # Generate unique ID (deterministic - hash() is randomized in Python 3)
            raw = f"telegram_isolated_{channel_name}_{message.id}_{message_date.isoformat()}"
            article_id = int(hashlib.md5(raw.encode()).hexdigest()[:12], 16)
            
            # Get current time when item is added to feed
            added_to_feed_at = datetime.now().isoformat()
            
            return {
                'id': article_id,
                'title': title,
                'summary': summary + '...' if len(summary) >= 200 else summary,
                'source': f'Telegram - {channel_name}',
                'url': '',
                'published_at': message_date.isoformat(),  # Original message date from Telegram
                'added_to_feed_at': added_to_feed_at,  # Time when added to live news feed
                'impact': impact,
                'currency_pairs': list(set(currency_pairs)),  # Remove duplicates
                'type': 'TELEGRAM_USER',
                'status': 'PUBLISHED',
                'message_id': message.id,
                'channel': channel_name
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing message: {e}")
            return None
    
    def get_recent_telegram_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent Telegram news synchronously with session isolation"""
        if not self.enabled:
            print("❌ Telegram service not enabled - missing credentials")
            return []
        
        with self._lock:
            try:
                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    print("⚠️ Already in event loop, cannot use sync wrapper")
                    return []
                except RuntimeError:
                    # No event loop running, we can create one
                    pass
                
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Run the isolated async function
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            self._fetch_telegram_news_isolated(hours),
                            timeout=20.0  # Increased timeout for isolated session
                        )
                    )
                    return result
                finally:
                    # Clean up the loop
                    loop.close()
                
            except asyncio.TimeoutError:
                print("⚠️ Telegram news fetch timed out")
                return []
            except Exception as e:
                print(f"❌ Error fetching Telegram news: {e}")
                return []

# Global instance
telegram_sync = SessionIsolatedTelegramWrapper()
