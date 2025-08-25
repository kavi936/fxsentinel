#!/usr/bin/env python3
"""
Smart News Alert Trigger Service
Filters high-impact news and sends alerts to users based on their preferences
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
        self.last_processed_news = set()  # Track processed news IDs
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
        """Determine if news is specifically high-impact for forex markets"""
        try:
            title = news_item.get('title', '').lower()
            content = news_item.get('content', '').lower()
            source = news_item.get('source', '').lower()
            
            # Forex-specific high-impact keywords
            forex_high_impact_keywords = [
                # Central Banks
                'fed', 'federal reserve', 'ecb', 'european central bank', 'boe', 'bank of england',
                'boj', 'bank of japan', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
                'snb', 'swiss national bank', 'rbnz', 'reserve bank of new zealand',
                
                # Major Economic Indicators
                'nfp', 'non-farm payrolls', 'cpi', 'inflation', 'gdp', 'unemployment',
                'interest rate', 'monetary policy', 'quantitative easing', 'tapering',
                'retail sales', 'manufacturing pmi', 'services pmi', 'employment',
                
                # Market-Moving Events
                'breaking', 'urgent', 'flash', 'alert', 'emergency', 'crisis',
                'election', 'referendum', 'trade war', 'sanctions', 'brexit',
                'geopolitical', 'political', 'policy change', 'regulatory',
                
                # Currency-Specific
                'dollar', 'euro', 'pound', 'yen', 'franc', 'australian dollar',
                'canadian dollar', 'new zealand dollar', 'currency', 'forex'
            ]
            
            # Check for forex-specific high-impact keywords
            for keyword in forex_high_impact_keywords:
                if keyword in title or keyword in content:
                    logger.info(f"Forex high-impact news detected: {keyword} in '{title[:50]}...'")
                    return True
            
            # Check source credibility for forex news
            forex_credible_sources = ['reuters', 'bloomberg', 'cnbc', 'marketwatch', 'forexfactory', 'fxstreet', 'investing.com', 'fxempire']
            if any(source_name in source for source_name in forex_credible_sources):
                # Additional check for important forex keywords in credible sources
                important_forex_keywords = ['fed', 'ecb', 'boe', 'boj', 'rba', 'boc', 'nfp', 'cpi', 'gdp', 'interest rate', 'monetary']
                if any(keyword in title for keyword in important_forex_keywords):
                    logger.info(f"Important forex news from credible source: {source} - '{title[:50]}...'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking forex high impact news: {e}")
            return False
    
    def should_analyze_with_ai(self, news_item: Dict[str, Any]) -> bool:
        """Determine if news should be analyzed with AI (cost optimization)"""
        try:
            # Only analyze forex high-impact news
            if not self.is_forex_high_impact(news_item):
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
                'errors': []
            }
            
            for news_item in news_items:
                news_id = str(news_item.get('id', ''))
                
                # Check if forex high impact
                if not self.is_forex_high_impact(news_item):
                    continue
                
                results['high_impact_count'] += 1
                logger.info(f"Processing forex high-impact news: {news_item.get('title', '')[:50]}...")
                
                # Get users to alert
                users_to_alert = self.get_users_to_alert(news_item)
                
                if not users_to_alert:
                    logger.info("No users to alert for this news item")
                    continue
                
                # Determine if AI analysis is needed
                needs_ai_analysis = self.should_analyze_with_ai(news_item)
                
                # Send alerts (AI analysis is triggered within _send_alert_to_user if needed)
                for user_data in users_to_alert:
                    try:
                        success = self._send_alert_to_user(user_data, news_item, needs_ai_analysis)
                        if success:
                            results['alerts_sent'] += 1
                            if needs_ai_analysis:
                                results['ai_analysis_triggered'] += 1
                    except Exception as e:
                        error_msg = f"Error sending alert to user {user_data.get('user_id')}: {e}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            logger.info(f"News processing complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing news for alerts: {e}")
            return {'error': str(e)}
    
    def _send_alert_to_user(self, user_data: Dict[str, Any], news_item: Dict[str, Any], needs_ai_analysis: bool) -> bool:
        """Send alert to a specific user"""
        try:
            user_id = user_data.get('user_id')
            if not user_id:
                logger.error("No user_id provided for alert")
                return False
            
            # Check deduplication first
            from .unified_alert_deduplication import should_send_news_alert
            if not should_send_news_alert(news_item, user_id):
                logger.debug(f"News alert duplicate prevented for user {user_id}")
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
            
            # Use alert service to process the alert (includes subscription validation)
            from .alert_service import get_alert_service
            alert_service = get_alert_service()
            
            # Process alert with subscription validation
            import asyncio
            success = asyncio.run(alert_service.process_alert(alert_data, user_settings, user_id))
            
            if success:
                logger.info(f"Alert sent successfully to user {user_id}")
                # Save to alert history
                self._save_alert_history(user_id, news_item, alert_data['content'])
                return True
            else:
                logger.warning(f"Alert not sent to user {user_id} (subscription check failed or user preferences)")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert to user: {e}")
            return False
    
    def _create_alert_content(self, news_item: Dict[str, Any], ai_analysis: Optional[Dict[str, Any]] = None) -> str:
        """Create alert content without HTML formatting"""
        try:
            title = news_item.get('title', 'Unknown Title')
            source = news_item.get('source', 'Unknown Source')
            summary = news_item.get('summary', '')
            
            # Get currency pairs
            affected_pairs = self.get_affected_currency_pairs(news_item)
            if not affected_pairs:
                affected_pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD']  # Default pairs
            pairs_text = ', '.join(affected_pairs)
            
            # Format timestamp
            try:
                from datetime import datetime
                timestamp = news_item.get('timestamp', '')
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M UTC')
            except:
                formatted_time = datetime.now().strftime('%H:%M UTC')
            
            # Create content
            content = f"Time: {formatted_time}\nSource: {source}\nCurrency Pairs: {pairs_text}"
            
            # Add summary if available
            if summary:
                content += f"\n\nSummary: {summary}"
            
            # Add AI analysis if available
            if ai_analysis and isinstance(ai_analysis, dict):
                analysis_text = ai_analysis.get('analysis', '')
                if analysis_text:
                    # Truncate analysis if too long
                    if len(analysis_text) > 300:
                        analysis_text = analysis_text[:297] + "..."
                    content += f"\n\nAI Analysis: {analysis_text}"
                else:
                    content += f"\n\nAI Analysis: Available on dashboard"
            else:
                content += f"\n\nMarket Impact: Monitor for price action"
            
            return content
            
        except Exception as e:
            logger.error(f"Error creating alert content: {e}")
            return "Breaking forex news - check dashboard for details"
    
    def _trigger_ai_analysis(self, news_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Trigger AI analysis for the news item and return the analysis"""
        try:
            news_id = str(news_item.get('id', ''))
            
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
            else:
                logger.error(f"Failed to trigger AI analysis: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error triggering AI analysis: {e}")
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

# Global instance
news_alert_trigger = NewsAlertTrigger()
