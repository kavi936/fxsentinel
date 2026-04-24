#!/usr/bin/env python3
"""
Smart News Alert Trigger Service
Filters high-impact news and sends alerts to users based on their preferences
FIXED: Repeated alerts, improved AI analysis, added post-news analysis
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAlertTrigger:
    def __init__(self):
        """Initialize the news alert trigger service"""
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        # Removed in-memory deduplication - now using persistent_alert_deduplication
        # This ensures deduplication survives restarts and works across instances
        self.high_impact_keywords = [
            'fed', 'federal reserve', 'ecb', 'european central bank', 'boe', 'bank of england',
            'boj', 'bank of japan', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
            'nfp', 'non-farm payrolls', 'cpi', 'inflation', 'gdp', 'unemployment',
            'interest rate', 'monetary policy', 'quantitative easing', 'tapering',
            'breaking', 'urgent', 'flash', 'alert', 'emergency', 'crisis',
            'election', 'referendum', 'trade war', 'sanctions', 'brexit'
        ]
        
        self.currency_keywords = {
            'EUR/USD': ['euro', 'eur', 'european', 'ecb', 'eurozone'],
            'USD/JPY': ['yen', 'jpy', 'japanese', 'boj', 'japan'],
            'GBP/USD': ['pound', 'gbp', 'british', 'boe', 'uk', 'brexit'],
            'USD/CHF': ['franc', 'chf', 'swiss', 'snb'],
            'AUD/USD': ['australian', 'aud', 'rba', 'australia'],
            'USD/CAD': ['canadian', 'cad', 'boc', 'canada'],
            'NZD/USD': ['new zealand', 'nzd', 'rbnz', 'kiwi']
        }
        
        # Post-news analysis tracking
        self.post_news_analysis_queue = {}  # Track news that needs post-analysis
        self.analysis_cooldown = 300  # 5 minutes cooldown before post-analysis
    
    def is_high_impact_news(self, news_item: Dict[str, Any]) -> bool:
        """Determine if news item is high impact and should trigger alerts"""
        try:
            # Use enhanced forex filter for better accuracy
            from services.enhanced_forex_filter import EnhancedForexFilter
            forex_filter = EnhancedForexFilter()
            
            title = news_item.get('title', '')
            summary = news_item.get('summary', '')
            content = news_item.get('content', '')
            source = news_item.get('source', '')
            
            # Use the enhanced filter's strict alert criteria
            is_high_impact = forex_filter.is_high_impact_for_alerts(title, summary, source)
            
            if is_high_impact:
                logger.info(f"High impact news detected by enhanced filter: '{title[:50]}...'")
            
            return is_high_impact
            
        except Exception as e:
            logger.error(f"Error checking high impact news: {e}")
            return False
    
    def get_affected_currency_pairs(self, news_item: Dict[str, Any]) -> List[str]:
        """Extract currency pairs mentioned in the news"""
        try:
            title = news_item.get('title', '').lower()
            content = news_item.get('content', '').lower()
            
            affected_pairs = []
            
            for pair, keywords in self.currency_keywords.items():
                if any(keyword in title or keyword in content for keyword in keywords):
                    affected_pairs.append(pair)
            
            return affected_pairs
            
        except Exception as e:
            logger.error(f"Error extracting currency pairs: {e}")
            return []
    
    def is_forex_high_impact(self, news_item: Dict[str, Any]) -> bool:
        """Backward-compatible alias for high-impact market checks."""
        try:
            return self.is_high_impact_news(news_item)
            
        except Exception as e:
            logger.error(f"Error checking forex high impact news: {e}")
            return False
    
    def should_analyze_with_ai(self, news_item: Dict[str, Any]) -> bool:
        """Determine if news should be analyzed with AI (cost optimization).
        Set DISABLE_AI_FOR_ALERTS=true in env to never use API credits for alert analysis."""
        try:
            # Opt-out: do not use AI/OpenAI for alerts (saves API credits)
            if os.getenv('DISABLE_AI_FOR_ALERTS', '').strip().lower() in ('true', '1', 'yes'):
                logger.debug("AI analysis for alerts disabled via DISABLE_AI_FOR_ALERTS")
                return False
            
            # Only analyze high-impact market news
            if not self.is_high_impact_news(news_item):
                return False
            
            # Check if it's from a credible source
            source = news_item.get('source', '').lower()
            credible_sources = ['reuters', 'bloomberg', 'cnbc', 'marketwatch', 'forexfactory', 'fxstreet', 'investing.com']
            
            if any(source_name in source for source_name in credible_sources):
                return True
            
            # For other sources, only analyze if it has very high-impact keywords
            title = news_item.get('title', '').lower()
            critical_keywords = ['fed', 'ecb', 'boe', 'boj', 'nfp', 'cpi', 'gdp', 'breaking', 'urgent', 'interest rate']
            
            if any(keyword in title for keyword in critical_keywords):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining AI analysis need: {e}")
            return False
    
    def should_send_post_news_analysis(self, news_item: Dict[str, Any]) -> bool:
        """Determine if news should get post-news analysis after initial alert"""
        try:
            # Only high-impact market news gets post-analysis
            if not self.is_high_impact_news(news_item):
                return False
            
            # Check if it's a major economic release
            title = news_item.get('title', '').lower()
            post_analysis_keywords = [
                'cpi', 'inflation', 'nfp', 'non-farm payrolls', 'gdp', 'unemployment',
                'fed', 'ecb', 'boe', 'boj', 'interest rate', 'monetary policy',
                'retail sales', 'manufacturing', 'employment'
            ]
            
            if any(keyword in title for keyword in post_analysis_keywords):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining post-news analysis need: {e}")
            return False
    
    def get_users_to_alert(self, news_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of users who should receive this alert based on their preferences"""
        try:
            # Get all users with alert settings
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            
            all_users = firebase_storage.get_all_users_with_alerts()
            users_to_alert = []
            
            affected_pairs = self.get_affected_currency_pairs(news_item)
            
            for user_data in all_users:
                user_id = user_data.get('user_id')
                settings = user_data.get('settings', {})
                
                # Check if user has Telegram enabled
                telegram_enabled = settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                if not telegram_enabled:
                    continue
                
                # Check user preferences
                preferences = settings.get('preferences', {})
                
                # Check if user wants this type of alert
                alert_types = preferences.get('alertTypes', {})
                if not alert_types.get('liveNews', True):  # Default to True
                    continue
                
                # Check if user is interested in affected currency pairs
                user_pairs = preferences.get('currencyPairs', [])
                if affected_pairs and user_pairs:
                    # Check if any affected pairs match user's preferences
                    if not any(pair in user_pairs for pair in affected_pairs):
                        continue
                
                # Check impact level
                impact_levels = preferences.get('impactLevels', {})
                if not impact_levels.get('high', True):  # Default to True
                    continue
                
                # Check quiet hours
                quiet_hours = preferences.get('quietHours', {})
                if self._is_quiet_hours(quiet_hours):
                    continue
                
                # Get the actual chat ID from Firebase
                from services.firebase_realtime_storage import FirebaseRealtimeStorage
                firebase_storage = FirebaseRealtimeStorage()
                chat_id = firebase_storage.get_telegram_chat_id(user_id)
                
                if not chat_id:
                    logger.warning(f"No chat ID found for user {user_id}")
                    continue
                
                # User should receive this alert
                users_to_alert.append({
                    'user_id': user_id,
                    'chat_id': chat_id,  # Use the actual chat ID from Firebase
                    'settings': settings
                })
            
            return users_to_alert
            
        except Exception as e:
            logger.error(f"Error getting users to alert: {e}")
            return []
    
    def _is_quiet_hours(self, quiet_hours: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours"""
        try:
            if not quiet_hours.get('enabled', False):
                return False
            
            current_time = datetime.now()
            start_time = quiet_hours.get('start', '22:00')
            end_time = quiet_hours.get('end', '06:00')
            
            # Simple time comparison (can be enhanced with timezone support)
            current_hour = current_time.hour
            start_hour = int(start_time.split(':')[0])
            end_hour = int(end_time.split(':')[0])
            
            if start_hour <= end_hour:
                # Same day (e.g., 06:00 to 22:00)
                return start_hour <= current_hour <= end_hour
            else:
                # Overnight (e.g., 22:00 to 06:00)
                return current_hour >= start_hour or current_hour <= end_hour
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def process_news_for_alerts(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process news items and trigger alerts for high-impact news"""
        try:
            results = {
                'total_processed': len(news_items),
                'high_impact_count': 0,
                'alerts_sent': 0,
                'ai_analysis_triggered': 0,
                'post_news_queued': 0,
                'duplicates_prevented': 0,
                'errors': []
            }
            
            for news_item in news_items:
                news_id = str(news_item.get('id', ''))
                
                # Check if high-impact market news
                if not self.is_high_impact_news(news_item):
                    continue
                
                results['high_impact_count'] += 1
                logger.info(f"Processing high-impact market news: {news_item.get('title', '')[:50]}...")
                
                # Get users to alert
                users_to_alert = self.get_users_to_alert(news_item)
                
                if not users_to_alert:
                    logger.info("No users to alert for this news item")
                    continue
                
                # Determine if AI analysis is needed
                needs_ai_analysis = self.should_analyze_with_ai(news_item)
                
                # Check if post-news analysis should be queued
                if self.should_send_post_news_analysis(news_item):
                    self._queue_post_news_analysis(news_item)
                    results['post_news_queued'] += 1
                
                # Send alerts (AI analysis is triggered within _send_alert_to_user if needed)
                for user_data in users_to_alert:
                    try:
                        success = self._send_alert_to_user(user_data, news_item, needs_ai_analysis)
                        if success:
                            results['alerts_sent'] += 1
                            if needs_ai_analysis:
                                results['ai_analysis_triggered'] += 1
                        else:
                            results['duplicates_prevented'] += 1
                    except Exception as e:
                        error_msg = f"Error sending alert to user {user_data.get('user_id')}: {e}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            logger.info(f"News processing complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing news for alerts: {e}")
            return {'error': str(e)}
    
    async def _send_alert_to_user(self, user_data: Dict[str, Any], news_item: Dict[str, Any], needs_ai_analysis: bool) -> bool:
        """Send alert to a specific user"""
        try:
            user_id = user_data.get('user_id')
            if not user_id:
                logger.error("No user_id provided for alert")
                return False
            
            # PERSISTENT DEDUPLICATION: Same reserve flow as Path 1 (UnifiedAlertProcessor)
            from .persistent_alert_deduplication import should_send_news_alert, reserve_news_alert
            
            if not should_send_news_alert(news_item, user_id):
                logger.debug(f"Duplicate news alert prevented for user {user_id}: {news_item.get('title', '')[:30]}...")
                return False
            
            if not reserve_news_alert(news_item, user_id):
                logger.debug(f"Reservation lost for user {user_id}: {news_item.get('title', '')[:30]}... (another sender won)")
                return False
            
            # Trigger AI analysis first if needed
            ai_analysis = None
            if needs_ai_analysis:
                ai_analysis = self._trigger_ai_analysis(news_item)
            
            # Create alert data
            alert_data = {
                'title': news_item.get('title', 'Breaking Forex News'),
                'content': self._create_alert_content(news_item, ai_analysis),
                'type': 'liveNews',
                'impact_level': news_item.get('impact', 'medium'),
                'currency_pairs': self.get_affected_currency_pairs(news_item),
                'source': news_item.get('source', 'Unknown'),
                'url': news_item.get('url', ''),
                'timestamp': news_item.get('timestamp', ''),
                'ai_analysis': ai_analysis
            }
            
            # Get user settings
            user_settings = user_data.get('settings', {})
            
            # Use alert service to process the alert
            from .alert_service import get_alert_service
            alert_service = get_alert_service()
            
            # Process alert (pass user_data so chat_id is available, same as Path 1)
            success = await alert_service.process_alert(alert_data, user_settings, user_id, user_data=user_data)
            
            if success:
                logger.info(f"Alert sent successfully to user {user_id}")
                # Mark alert as sent after successful delivery (not before)
                from .persistent_alert_deduplication import mark_news_alert_sent
                mark_news_alert_sent(news_item, user_id)
                # Save to alert history
                self._save_alert_history(user_id, news_item, alert_data['content'])
                return True
            else:
                logger.warning(f"Alert not sent to user {user_id} (subscription check failed or user preferences)")
                # Don't mark as sent if delivery failed - allows retry
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert to user: {e}")
            return False
    
    def _queue_post_news_analysis(self, news_item: Dict[str, Any]):
        """Queue news item for post-news analysis"""
        try:
            news_id = str(news_item.get('id', ''))
            title = news_item.get('title', '')
            
            # Add to post-news analysis queue
            self.post_news_analysis_queue[news_id] = {
                'news_item': news_item,
                'queued_at': datetime.now(),
                'title': title
            }
            
            logger.info(f"Queued news for post-analysis: {title[:50]}...")
            
            # Clean up old entries (older than 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            expired_keys = []
            for key, data in self.post_news_analysis_queue.items():
                if data['queued_at'] < cutoff_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.post_news_analysis_queue[key]
                
        except Exception as e:
            logger.error(f"Error queuing post-news analysis: {e}")
    
    async def process_post_news_analysis(self):
        """Process queued news items for post-news analysis"""
        try:
            if not self.post_news_analysis_queue:
                return
            
            logger.info(f"Processing {len(self.post_news_analysis_queue)} queued news items for post-analysis")
            
            current_time = datetime.now()
            processed_count = 0
            
            for news_id, queue_data in list(self.post_news_analysis_queue.items()):
                try:
                    news_item = queue_data['news_item']
                    queued_at = queue_data['queued_at']
                    
                    # Check if enough time has passed since initial alert
                    time_since_queued = (current_time - queued_at).total_seconds()
                    if time_since_queued < self.analysis_cooldown:
                        continue
                    
                    # Trigger post-news analysis
                    post_analysis = await self._trigger_post_news_analysis(news_item)
                    
                    if post_analysis:
                        # Send post-news analysis to users
                        await self._send_post_news_analysis(news_item, post_analysis)
                        processed_count += 1
                    
                    # Remove from queue
                    del self.post_news_analysis_queue[news_id]
                    
                except Exception as e:
                    logger.error(f"Error processing post-news analysis for {news_id}: {e}")
                    # Remove from queue on error
                    del self.post_news_analysis_queue[news_id]
            
            if processed_count > 0:
                logger.info(f"Completed post-news analysis for {processed_count} news items")
                
        except Exception as e:
            logger.error(f"Error processing post-news analysis: {e}")
    
    async def _trigger_post_news_analysis(self, news_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Trigger post-news analysis for a news item"""
        try:
            news_id = str(news_item.get('id', ''))
            title = news_item.get('title', '')
            
            # Create post-news analysis request
            analysis_data = {
                'news_id': news_id,
                'title': title,
                'content': news_item.get('summary', ''),
                'source': news_item.get('source', ''),
                'analysis_type': 'post_news_analysis',
                'timestamp': news_item.get('timestamp', '')
            }
            
            # Call post-news analysis endpoint
            analysis_url = f"{self.api_base_url}/api/post-news-analysis"
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(analysis_url, json=analysis_data, timeout=30)
            
            if response.status_code == 200:
                analysis_result = response.json()
                logger.info(f"Post-news analysis completed for: {title[:50]}...")
                return analysis_result
            else:
                logger.error(f"Failed to trigger post-news analysis: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error triggering post-news analysis: {e}")
            return None
    
    async def _send_post_news_analysis(self, news_item: Dict[str, Any], analysis: Dict[str, Any]):
        """Send post-news analysis to users"""
        try:
            # Get users who should receive post-news analysis
            users_to_alert = self.get_users_to_alert(news_item)
            
            if not users_to_alert:
                return
            
            # Create post-news alert data
            alert_data = {
                'title': f"Post-News Analysis: {news_item.get('title', 'Market Update')}",
                'content': self._create_post_news_content(news_item, analysis),
                'type': 'postNews',
                'impact_level': 'high',
                'currency_pairs': self.get_affected_currency_pairs(news_item),
                'source': news_item.get('source', 'Unknown'),
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis
            }
            
            # Send to each user
            from .alert_service import get_alert_service
            alert_service = get_alert_service()
            
            for user_data in users_to_alert:
                try:
                    user_id = user_data.get('user_id')
                    user_settings = user_data.get('settings', {})
                    
                    # Check if user wants post-news alerts
                    alert_types = user_settings.get('preferences', {}).get('alertTypes', {})
                    if not alert_types.get('postNews', True):
                        continue
                    
                    # Send the post-news analysis
                    success = await alert_service.process_alert(alert_data, user_settings, user_id)
                    
                    if success:
                        logger.info(f"Post-news analysis sent to user {user_id}")
                    
                except Exception as e:
                    logger.error(f"Error sending post-news analysis to user {user_data.get('user_id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending post-news analysis: {e}")
    
    def _create_post_news_content(self, news_item: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Create content for post-news analysis alert"""
        try:
            title = news_item.get('title', 'Unknown Title')
            source = news_item.get('source', 'Unknown Source')
            
            # Get currency pairs
            affected_pairs = self.get_affected_currency_pairs(news_item)
            if not affected_pairs:
                affected_pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD']  # Default pairs
            pairs_text = ', '.join(affected_pairs)
            
            # Format timestamp
            formatted_time = datetime.now().strftime('%H:%M UTC')
            
            # Create content
            content = f"POST-NEWS ANALYSIS\n\n"
            content += f"Original News: {title}\n"
            content += f"Source: {source}\n"
            content += f"Currency Pairs: {pairs_text}\n"
            content += f"Analysis Time: {formatted_time}\n\n"
            
            # Add analysis content
            if analysis and isinstance(analysis, dict):
                analysis_text = analysis.get('analysis', '')
                market_impact = analysis.get('market_impact', '')
                trading_implications = analysis.get('trading_implications', '')
                
                if analysis_text:
                    content += f"Analysis:\n{analysis_text}\n\n"
                
                if market_impact:
                    content += f"Market Impact:\n{market_impact}\n\n"
                
                if trading_implications:
                    content += f"Trading Implications:\n{trading_implications}\n\n"
            else:
                content += "Analysis available on dashboard\n\n"
            
            content += "Check dashboard for detailed charts and analysis"
            
            return content
            
        except Exception as e:
            logger.error(f"Error creating post-news content: {e}")
            return "Post-news analysis available on dashboard"
    
    def _create_alert_content(self, news_item: Dict[str, Any], ai_analysis: Optional[Dict[str, Any]] = None) -> str:
        """Create the core content for a live news alert (summary only).

        The full Telegram layout (title, time, source, pairs, summary block) is handled
        in AlertService._format_live_news_message so this function focuses on the
        textual summary that appears under <b>Summary:</b>.
        """
        try:
            summary = news_item.get('summary', '') or news_item.get('title', 'Breaking forex news')

            # Truncate overly long summaries to keep alerts readable on mobile
            max_length = 400
            if len(summary) > max_length:
                summary = summary[: max_length - 3] + "..."

            return summary

        except Exception as e:
            logger.error(f"Error creating alert content: {e}")
            return "Breaking forex news - check dashboard for details"
    
    def _trigger_ai_analysis(self, news_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Trigger AI analysis for the news item and return the analysis (non-blocking).
        No-op if DISABLE_AI_FOR_ALERTS is set (avoids calling /api/analysis and using OpenAI)."""
        try:
            if os.getenv('DISABLE_AI_FOR_ALERTS', '').strip().lower() in ('true', '1', 'yes'):
                logger.debug("AI analysis for alerts disabled (DISABLE_AI_FOR_ALERTS), skipping API call")
                return None
            
            news_id = str(news_item.get('id', ''))
            
            # Skip AI analysis if news_id is missing or empty (non-blocking)
            if not news_id or news_id == '':
                logger.debug(f"Skipping AI analysis - news item has no ID: {news_item.get('title', 'Unknown')[:50]}...")
                return None
            
            # Convert news item to event format for AI analysis
            event_data = {
                'event': {
                    'title': news_item.get('title', 'Unknown News'),
                    'currency': 'USD',  # Default currency for news
                    'impact': news_item.get('impact', 'medium'),
                    'description': news_item.get('summary', news_item.get('title', '')),
                    'time': news_item.get('timestamp', ''),
                    'source': news_item.get('source', 'News Source')
                },
                'analysisType': 'news_analysis'
            }
            
            # Call the simpler AI analysis endpoint (faster)
            analysis_url = f"{self.api_base_url}/api/analysis/{news_id}"
            headers = {'Content-Type': 'application/json'}
            response = requests.get(analysis_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                analysis_data = response.json()
                logger.info(f"AI analysis triggered successfully for news {news_id}")
                return analysis_data
            elif response.status_code == 404:
                # News item not found in cache - this is OK, skip AI analysis
                logger.debug(f"AI analysis skipped - news item {news_id} not found in cache (404)")
                return None
            else:
                logger.warning(f"AI analysis failed with status {response.status_code} for news {news_id}")
                return None
                
        except Exception as e:
            # Non-blocking: log warning but don't fail the alert
            logger.warning(f"Error triggering AI analysis (non-blocking): {e}")
            return None
    
    def _save_alert_history(self, user_id: str, news_item: Dict[str, Any], message: str) -> bool:
        """Save alert to user's history"""
        try:
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            
            alert_data = {
                'type': 'liveNews',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'recipients': ['telegram'],
                'status': 'sent',
                'news_id': str(news_item.get('id', '')),
                'news_title': news_item.get('title', ''),
                'news_source': news_item.get('source', '')
            }
            
            firebase_storage.log_alert_history(user_id, alert_data)
            return True
            
        except Exception as e:
            logger.error(f"Error saving alert history: {e}")
            return False
    
    def _mark_user_disconnected(self, user_id: str) -> bool:
        """Mark user as disconnected when chat ID is invalid"""
        try:
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            
            # Update user's Telegram settings to disabled
            user_settings = firebase_storage.get_user_alert_settings(user_id)
            if user_settings:
                if 'channels' not in user_settings:
                    user_settings['channels'] = {}
                if 'telegram' not in user_settings['channels']:
                    user_settings['channels']['telegram'] = {}
                
                user_settings['channels']['telegram']['enabled'] = False
                user_settings['channels']['telegram']['chatId'] = ''
                
                firebase_storage.update_user_alert_settings(user_id, user_settings)
                logger.info(f"Marked user {user_id} as disconnected due to invalid chat ID")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking user as disconnected: {e}")
            return False
    
    def cleanup_old_history(self):
        """Clean up old alert history to prevent memory bloat"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=24)
            
            # Clean up news alert history
            expired_keys = []
            for key, sent_time in self.news_alert_history.items():
                if sent_time < cutoff_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.news_alert_history[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} old alert history entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up alert history: {e}")

# Global instance
news_alert_trigger = NewsAlertTrigger()
