#!/usr/bin/env python3
"""
Synchronous wrapper for Telegram service to avoid async issues in Flask
"""

import asyncio
import threading
from typing import List, Dict, Any
from .telegram_monitor_user import telegram_user_monitor

class TelegramSyncWrapper:
    """Synchronous wrapper for Telegram service"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._loop = None
    
    def _get_or_create_loop(self):
        """Get or create event loop for current thread"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop
    
    def get_recent_telegram_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent Telegram news synchronously"""
        with self._lock:
            try:
                loop = self._get_or_create_loop()
                asyncio.set_event_loop(loop)
                
                # Run the async function
                result = loop.run_until_complete(
                    asyncio.wait_for(
                        telegram_user_monitor.get_recent_telegram_news(hours),
                        timeout=15.0
                    )
                )
                
                return result
                
            except asyncio.TimeoutError:
                print("⚠️ Telegram news fetch timed out")
                return []
            except Exception as e:
                print(f"❌ Error fetching Telegram news: {e}")
                return []

# Global instance
telegram_sync = TelegramSyncWrapper()
