#!/usr/bin/env python3
"""
FXSentinel Alert Triggers
Detects when alerts should be sent and triggers them automatically
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .alert_service import get_alert_service
from .telegram_monitor_user import telegram_user_monitor
from .gpt_ai_analysis import GPTAIAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertTriggers:
    def __init__(self):
        """Initialize alert triggers"""
        self.last_check_time = datetime.now()
        self.processed_news_ids = set()  # Track processed news to avoid duplicates
        self.alert_service = get_alert_service()
    
    async def check_live_news_alerts(self):
        """Check for new high-impact news and trigger alerts"""
        try:
            logger.info("Checking for live news alerts...")
            
            # Get recent news from WatcherGuru (last 5 minutes to reduce duplicates)
            recent_news = await telegram_user_monitor.get_recent_telegram_news(hours=0.08)
            
            if not recent_news:
                logger.info("No recent news found")
                return
            
            for news_item in recent_news:
                # Create more unique news ID with timestamp
                news_id = f"{news_item.get('id', '')}_{news_item.get('title', '')}_{news_item.get('published_at', '')}_{int(time.time())}"
                
                # Skip if already processed
                if news_id in self.processed_news_ids:
                    logger.info(f"Skipping duplicate news: {news_item.get('title', '')[:50]}...")
                    continue
                
                # Only alert for high-impact news
                if news_item.get('impact') == 'high':
                    logger.info(f"Processing high-impact news: {news_item.get('title', 'Unknown')}")
                    
                    # Get AI analysis if not already present
                    if not news_item.get('analysis'):
                        try:
                            analyzer = GPTAIAnalyzer()
                            # Create a simple market context for analysis
                            from .enhanced_ai_analysis import MarketContext
                            market_context = MarketContext(
                                current_prices={},
                                recent_volatility={},
                                market_sentiment={},
                                key_levels={},
                                economic_calendar=[],
                                bond_yields={},
                                equity_indices={},
                                commodity_prices={},
                                central_bank_expectations={},
                                historical_reactions={}
                            )
                            analysis_result = analyzer.analyze_macro_event(news_item, market_context, "post_event")
                            news_item['analysis'] = analysis_result.analysis if hasattr(analysis_result, 'analysis') else 'Analysis not available'
                        except Exception as e:
                            logger.error(f"Error getting AI analysis: {e}")
                            news_item['analysis'] = 'AI analysis temporarily unavailable'
                    
                    # Create alert data
                    alert_data = {
                        'type': 'liveNews',
                        'title': news_item.get('title', 'Breaking News'),
                        'content': news_item.get('summary', ''),
                        'analysis': news_item.get('analysis', ''),
                        'impact_level': news_item.get('impact', 'medium'),
                        'currency_pairs': news_item.get('currency_pairs', []),
                        'priority': 'high',
                        'source': news_item.get('source', 'WatcherGuru'),
                        'published_at': news_item.get('published_at', ''),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Send to all users with live news alerts enabled
                    sent_count = await self.alert_service.send_alert_to_subscribers(alert_data, 'liveNews')
                    logger.info(f"Sent live news alert to {sent_count} users")
                    
                    # Mark as processed
                    self.processed_news_ids.add(news_id)
                    
                    # Keep processed IDs list manageable (last 1000)
                    if len(self.processed_news_ids) > 1000:
                        self.processed_news_ids = set(list(self.processed_news_ids)[-500:])
            
            self.last_check_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking live news alerts: {e}")
    
    async def check_economic_calendar_alerts(self):
        """Check upcoming economic events and send pre-news alerts"""
        try:
            logger.info("Checking for upcoming economic events...")
            
            # This would integrate with your economic calendar service
            # For now, we'll create a placeholder
            upcoming_events = await self._get_upcoming_events(hours=2)
            
            for event in upcoming_events:
                if event.get('impact') == 'high':
                    alert_data = {
                        'type': 'preNews',
                        'event_title': event.get('title', 'Economic Event'),
                        'event_time': event.get('time', 'TBD'),
                        'expected_value': event.get('expected', 'N/A'),
                        'key_levels': event.get('key_levels', 'N/A'),
                        'impact_analysis': event.get('impact_analysis', 'High impact event expected'),
                        'currency_pairs': event.get('currency_pairs', []),
                        'priority': 'high',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    sent_count = await self.alert_service.send_alert_to_subscribers(alert_data, 'preNews')
                    logger.info(f"Sent pre-news alert to {sent_count} users")
                    
        except Exception as e:
            logger.error(f"Error checking economic calendar alerts: {e}")
    
    async def _get_upcoming_events(self, hours: int = 2) -> List[Dict[str, Any]]:
        """Get upcoming economic events (placeholder for now)"""
        # This would integrate with your economic calendar service
        # For MVP, return empty list
        return []
    
    async def trigger_test_alert(self, user_id: str) -> bool:
        """Send a test alert to a specific user"""
        try:
            # Get user's Telegram settings
            user_ref = self.alert_service.db.collection('users').document(user_id)
            telegram_ref = user_ref.collection('alert_settings').document('telegram')
            telegram_doc = await telegram_ref.get()
            
            if not telegram_doc.exists or not telegram_doc.to_dict().get('enabled', False):
                logger.error(f"User {user_id} does not have Telegram alerts enabled")
                return False
            
            chat_id = telegram_doc.to_dict().get('chat_id')
            
            # Create test alert
            test_alert = {
                'type': 'test',
                'title': 'Test Alert - FXSentinel',
                'content': 'This is a test alert to verify your Telegram bot setup is working correctly.',
                'priority': 'low',
                'timestamp': datetime.now().isoformat()
            }
            
            # Send test alert
            message = self.alert_service._format_alert_message(test_alert, 'test')
            success = await self.alert_service.send_telegram_alert(chat_id, message)
            
            if success:
                # Log in history
                await self.alert_service._log_alert_history(user_id, test_alert, 'telegram')
                logger.info(f"Test alert sent successfully to user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending test alert: {e}")
            return False
    
    async def start_background_monitoring(self):
        """Start background monitoring for alerts"""
        logger.info("Starting background alert monitoring...")
        
        while True:
            try:
                # Check for live news alerts every 2 minutes
                await self.check_live_news_alerts()
                
                # Check for economic calendar alerts every 5 minutes
                if datetime.now().minute % 5 == 0:
                    await self.check_economic_calendar_alerts()
                
                # Wait 2 minutes before next check
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def process_news_for_alerts(self, news_item: Dict[str, Any]) -> bool:
        """Process a single news item and send alerts if needed"""
        try:
            # Only process high-impact news
            if news_item.get('impact') != 'high':
                return False
            
            # Get AI analysis
            if not news_item.get('analysis'):
                try:
                    analyzer = GPTAIAnalyzer()
                    # Create a simple market context for analysis
                    from .enhanced_ai_analysis import MarketContext
                    market_context = MarketContext(
                        current_prices={},
                        recent_volatility={},
                        market_sentiment={},
                        key_levels={},
                        economic_calendar=[],
                        bond_yields={},
                        equity_indices={},
                        commodity_prices={},
                        central_bank_expectations={},
                        historical_reactions={}
                    )
                    analysis_result = analyzer.analyze_macro_event(news_item, market_context, "post_event")
                    news_item['analysis'] = analysis_result.analysis if hasattr(analysis_result, 'analysis') else 'Analysis not available'
                except Exception as e:
                    logger.error(f"Error getting AI analysis: {e}")
                    news_item['analysis'] = 'AI analysis temporarily unavailable'
            
            # Create alert data
            alert_data = {
                'type': 'liveNews',
                'title': news_item.get('title', 'Breaking News'),
                'content': news_item.get('summary', ''),
                'analysis': news_item.get('analysis', ''),
                'impact_level': news_item.get('impact', 'medium'),
                'currency_pairs': news_item.get('currency_pairs', []),
                'priority': 'high',
                'source': news_item.get('source', 'WatcherGuru'),
                'published_at': news_item.get('published_at', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to subscribers
            sent_count = await self.alert_service.send_alert_to_subscribers(alert_data, 'liveNews')
            logger.info(f"Processed news item for alerts, sent to {sent_count} users")
            
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Error processing news for alerts: {e}")
            return False

# Global instance
alert_triggers = AlertTriggers()
