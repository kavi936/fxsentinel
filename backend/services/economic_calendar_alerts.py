#!/usr/bin/env python3
"""
Economic Calendar Alert System
Sends pre-event alerts for upcoming economic events
"""

import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import re # Added for date/time parsing

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EconomicCalendarAlerts:
    def __init__(self):
        """Initialize the economic calendar alert system"""
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        self.alert_hours_before = [2, 1]  # Send alerts 2 hours and 1 hour before
        self.alert_minutes_before = [10]  # Send alerts 10 minutes before
        
        # High-impact event types that should trigger alerts
        self.high_impact_types = [
            'CENTRAL_BANK', 'ECONOMIC_RELEASE', 'POLICY_ANNOUNCEMENT'
        ]
        
        # High-impact event titles/keywords
        self.high_impact_keywords = [
            'fed', 'federal reserve', 'ecb', 'european central bank', 'boe', 'bank of england',
            'boj', 'bank of japan', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
            'nfp', 'non-farm payrolls', 'cpi', 'inflation', 'gdp', 'unemployment',
            'interest rate', 'monetary policy', 'retail sales', 'employment'
        ]
    
    def _validate_event_data(self, event: Dict[str, Any]) -> bool:
        """Validate that event data is legitimate and not historical/mock data"""
        try:
            # Check for required fields (date/time are enough; raw_data is optional for hybrid/API events)
            if not event.get('title') or not event.get('time') or not event.get('date'):
                logger.debug(f"Event missing required fields: {event.get('title', 'Unknown')}")
                return False
            
            # Parse event datetime
            event_datetime = self._parse_event_datetime(event)
            if not event_datetime:
                logger.debug(f"Could not parse event datetime: {event.get('title', 'Unknown')}")
                return False
            
            # Check if event is in the future (not historical)
            now = datetime.now(timezone.utc)
            if event_datetime <= now:
                logger.debug(f"Event is in the past: {event.get('title', 'Unknown')} at {event_datetime}")
                return False
            
            # Check if event is too far in the future (more than 7 days)
            if event_datetime > now + timedelta(days=7):
                logger.debug(f"Event too far in future: {event.get('title', 'Unknown')} at {event_datetime}")
                return False
            
            # Check for suspicious patterns (midnight events, weekend events for non-speeches)
            hour = event_datetime.hour
            weekday = event_datetime.weekday()
            title = event.get('title', '').lower()
            
            # Allow midnight events only for important speeches
            if hour == 0 and 'speech' not in title and 'meeting' not in title:
                logger.debug(f"Suspicious midnight event: {event.get('title', 'Unknown')}")
                return False
            
            # Allow high-impact events on weekends (e.g. some releases); only filter low/medium without justification
            if weekday >= 5 and event.get('impact', 'medium') != 'high':
                if not any(keyword in title for keyword in ['speech', 'meeting', 'conference']):
                    logger.debug(f"Weekend event without justification: {event.get('title', 'Unknown')}")
                    return False
            
            # Check event status (if present); treat missing as upcoming so hybrid/API events are not rejected
            status = (event.get('status') or 'upcoming').strip().upper()
            if status and status not in ['UPCOMING', 'IMMINENT', 'TODAY']:
                logger.debug(f"Event status not upcoming: {event.get('title', 'Unknown')} - {status}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating event data: {e}")
            return False
    
    def _parse_event_datetime(self, event: Dict[str, Any]) -> Optional[datetime]:
        """Parse event datetime from various formats as a UTC-aware datetime."""
        try:
            time_str = event.get('time', '')
            date_str = event.get('date', '')
            
            if not time_str or not date_str:
                return None
            
            # Hybrid calendar format first: date "YYYY-MM-DD", time "HH:MM UTC"
            if '-' in date_str and len(date_str) == 10:
                try:
                    event_date = datetime.strptime(date_str, '%Y-%m-%d')
                    time_part = time_str.replace(' UTC', '').strip()
                    time_obj = datetime.strptime(time_part, '%H:%M').time()
                    return datetime.combine(event_date.date(), time_obj, tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            # Try different datetime formats
            datetime_formats = [
                '%H:%M UTC',  # "14:30 UTC"
                '%Y-%m-%d %H:%M:%S',  # "2024-01-15 14:30:00"
                '%a, %b %d %H:%M UTC',  # "Mon, Jan 15 14:30 UTC"
                '%Y-%m-%d %H:%M',  # "2024-01-15 14:30"
            ]
            
            # Combine date and time
            datetime_str = f"{date_str} {time_str}"
            
            for fmt in datetime_formats:
                try:
                    # Try parsing with current year if not specified
                    if '%Y' not in fmt:
                        current_year = datetime.now().year
                        datetime_str_with_year = f"{current_year} {datetime_str}"
                        parsed = datetime.strptime(datetime_str_with_year, f"%Y {fmt}")
                        return parsed.replace(tzinfo=timezone.utc)
                    else:
                        parsed = datetime.strptime(datetime_str, fmt)
                        return parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            # If all formats fail, try to extract time and date separately
            try:
                # Extract time (HH:MM format)
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    
                    # Extract date components
                    date_match = re.search(r'(\w{3}),?\s+(\w{3})\s+(\d{1,2})', date_str)
                    if date_match:
                        day_name = date_match.group(1)
                        month_name = date_match.group(2)
                        day = int(date_match.group(3))
                        
                        # Map month names to numbers
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        
                        month = month_map.get(month_name.lower(), 1)
                        current_year = datetime.now().year
                        
                        return datetime(current_year, month, day, hour, minute, tzinfo=timezone.utc)
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing event datetime: {e}")
            return None
    
    def is_high_impact_event(self, event: Dict[str, Any]) -> bool:
        """Determine if event is high impact and should trigger alerts"""
        try:
            # First validate the event data
            if not self._validate_event_data(event):
                return False
            
            title = event.get('title', '').lower()
            event_type = event.get('type', '').upper()
            impact = event.get('impact', '').lower()
            
            # Check impact level
            if impact == 'high':
                logger.info(f"High impact event detected: {title[:50]}...")
                return True
            
            # Check event type
            if any(event_type in high_type for high_type in self.high_impact_types):
                logger.info(f"High impact event type detected: {title[:50]}...")
                return True
            
            # Check title keywords
            for keyword in self.high_impact_keywords:
                if keyword in title:
                    logger.info(f"High impact event detected: {keyword} in '{title[:50]}...'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking high impact event: {e}")
            return False
    
    def get_affected_currency_pairs(self, event: Dict[str, Any]) -> List[str]:
        """Extract currency pairs affected by the event"""
        try:
            currency = event.get('currency', '').upper()
            currency_pairs = event.get('currencyPairs', [])
            
            # If currency pairs are explicitly listed, use them
            if currency_pairs and isinstance(currency_pairs, list):
                return currency_pairs
            
            # Otherwise, infer from currency (max 4 pairs)
            if currency == 'USD':
                return ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF']
            elif currency == 'EUR':
                return ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF']
            elif currency == 'GBP':
                return ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF']
            elif currency == 'JPY':
                return ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY']
            elif currency == 'AUD':
                return ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY']
            elif currency == 'CAD':
                return ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD']
            elif currency == 'CHF':
                return ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF']
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting currency pairs: {e}")
            return []
    
    def should_send_pre_event_alert(self, event: Dict[str, Any]) -> bool:
        """Determine if pre-event alert should be sent for this event"""
        try:
            # Check if it's a high-impact event
            if not self.is_high_impact_event(event):
                return False
            
            # Get event datetime
            event_datetime = self._parse_event_datetime(event)
            if not event_datetime:
                return False
            
            # Check if we're within alert timing windows
            now = datetime.now(timezone.utc)
            time_until_event = event_datetime - now
            minutes_until_event = time_until_event.total_seconds() / 60
            
            # Check hour-based alerts (2h and 1h before)
            for hours in self.alert_hours_before:
                alert_minutes = hours * 60
                if 0 <= minutes_until_event <= alert_minutes and minutes_until_event >= alert_minutes - 5:
                    logger.info(f"Pre-event alert triggered: {event.get('title', 'Unknown')} in {hours}h")
                    return True
            
            # Check minute-based alerts (10min before)
            for minutes in self.alert_minutes_before:
                if 0 <= minutes_until_event <= minutes and minutes_until_event >= minutes - 2:
                    logger.info(f"Final reminder triggered: {event.get('title', 'Unknown')} in {minutes}min")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking pre-event alert: {e}")
            return False
    
    def get_alert_timing(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all alert timings for an event (2h, 1h, 10min before)"""
        try:
            event_datetime = self._parse_event_datetime(event)
            if not event_datetime:
                return []
            
            now = datetime.now(timezone.utc)
            alert_timings = []
            
            # Check hour-based alerts (2h and 1h before)
            for hours in self.alert_hours_before:
                alert_time = event_datetime - timedelta(hours=hours)
                if now <= alert_time <= now + timedelta(hours=24):
                    alert_timings.append({
                        'type': f'{hours}h_before',
                        'time': alert_time,
                        'message_type': 'pre_event'
                    })
            
            # Check minute-based alerts (10min before)
            for minutes in self.alert_minutes_before:
                alert_time = event_datetime - timedelta(minutes=minutes)
                if now <= alert_time <= now + timedelta(hours=24):
                    alert_timings.append({
                        'type': f'{minutes}min_before',
                        'time': alert_time,
                        'message_type': 'final_reminder'
                    })
            
            return alert_timings
            
        except Exception as e:
            logger.error(f"Error calculating alert timing: {e}")
            return []
    
    def get_users_to_alert(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of users who should receive alerts for this event.
        Uses same user source and preference shape as rest of app (get_all_users_with_alerts, preferences.alertTypes.preNews).
        """
        try:
            # Get affected currency pairs
            affected_pairs = self.get_affected_currency_pairs(event)
            if not affected_pairs:
                logger.debug(f"No currency pairs found for event: {event.get('title', 'Unknown')}")
                return []
            
            # Use same user source as UnifiedAlertProcessor and news alerts (fix: get_all_users does not exist)
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            all_users = firebase_storage.get_all_users_with_alerts()
            
            users_to_alert = []
            for user_data in all_users:
                try:
                    user_id = user_data.get('user_id')
                    settings = user_data.get('settings', {})
                    # Same preference structure as rest of app (preferences.alertTypes.preNews)
                    preferences = settings.get('preferences', {})
                    alert_types = preferences.get('alertTypes', {})
                    # Economic calendar / pre-news: preNews in alertTypes, or legacy alerts.economicCalendar.enabled
                    pre_news_enabled = alert_types.get('preNews', True)
                    if not pre_news_enabled:
                        alerts_legacy = preferences.get('alerts', settings.get('alerts', {}))
                        pre_news_enabled = alerts_legacy.get('economicCalendar', {}).get('enabled', False)
                    if not pre_news_enabled:
                        continue
                    
                    # Telegram: same check as unified_alert_processor / news_alert_trigger
                    telegram_enabled = (
                        settings.get('telegram_enabled', False) or
                        settings.get('telegram', False) or
                        settings.get('channels', {}).get('telegram', {}).get('enabled', False) or
                        preferences.get('channels', {}).get('telegram', {}).get('enabled', False)
                    )
                    if not telegram_enabled:
                        continue
                    
                    # Currency pairs: support list (canonical) or dict
                    user_pairs = preferences.get('currencyPairs', [])
                    if isinstance(user_pairs, dict):
                        user_pairs = list(user_pairs.keys()) if user_pairs else []
                    if user_pairs and not any(pair in user_pairs for pair in affected_pairs):
                        continue
                    
                    # Impact level
                    impact_levels = preferences.get('impactLevels', {})
                    if not impact_levels.get('high', True):
                        continue
                    
                    # Quiet hours
                    quiet_hours = preferences.get('quietHours', {})
                    if self._is_quiet_hours(quiet_hours):
                        continue
                    
                    chat_id = user_data.get('telegram_chat_id')
                    if not chat_id:
                        chat_id = firebase_storage.get_telegram_chat_id(user_id)
                    if not chat_id:
                        logger.warning(f"No chat ID found for user {user_id}")
                        continue
                    
                    chat_id_str = str(chat_id)
                    users_to_alert.append({
                        'user_id': user_id,
                        'chat_id': chat_id_str,
                        'telegram_chat_id': chat_id_str,
                        'settings': settings
                    })
                except Exception as e:
                    logger.error(f"Error processing user {user_data.get('user_id', 'unknown')}: {e}")
                    continue
            
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
    
    def process_economic_calendar_for_alerts(self) -> Dict[str, Any]:
        """Process economic calendar and send alerts for upcoming events"""
        try:
            results = {
                'total_events': 0,
                'high_impact_events': 0,
                'alerts_sent': 0,
                'errors': []
            }
            
            # Get economic calendar data
            try:
                response = requests.get(f"{self.api_base_url}/api/economic-calendar", timeout=10)
                if response.status_code != 200:
                    logger.warning(f"Failed to get economic calendar: {response.status_code}")
                    return results
                
                calendar_data = response.json()
                
                # Check data source quality
                data_source = calendar_data.get('source', 'unknown')
                if data_source in ['fallback_data', 'mock_data', 'test_data', 'demo_data']:
                    logger.warning(f"⚠️ Skipping economic calendar alerts - using {data_source} (potential false alerts)")
                    return results
                
                events = calendar_data.get('events', [])
                results['total_events'] = len(events)
                
                logger.info(f"📊 Processing {len(events)} events from {data_source}")
                
            except Exception as e:
                logger.error(f"Error fetching economic calendar: {e}")
                return results
            
            # Process each event
            for event in events:
                try:
                    # Check if this event should trigger an alert
                    if not self.should_send_pre_event_alert(event):
                        continue
                    
                    results['high_impact_events'] += 1
                    logger.info(f"Processing high-impact event: {event.get('title', '')[:50]}...")
                    
                    # Get users to alert
                    users_to_alert = self.get_users_to_alert(event)
                    
                    if not users_to_alert:
                        logger.info("No users to alert for this event")
                        continue
                    
                    # Send alerts to users
                    for user_data in users_to_alert:
                        try:
                            success = self._send_pre_event_alert(user_data, event)
                            if success:
                                results['alerts_sent'] += 1
                        except Exception as e:
                            error_msg = f"Error sending alert to user {user_data.get('user_id')}: {e}"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                
                except Exception as e:
                    error_msg = f"Error processing event {event.get('title', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Economic calendar processing complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing economic calendar for alerts: {e}")
            return {'error': str(e)}
    
    def send_pre_event_alert(self, user_data: Dict[str, Any], event: Dict[str, Any], alert_timing: str = None) -> bool:
        """Public entry: send pre-event alert to a user. alert_timing is optional (recomputed inside)."""
        return self._send_pre_event_alert(user_data, event)

    def _send_pre_event_alert(self, user_data: Dict[str, Any], event: Dict[str, Any]) -> bool:
        """Send pre-event alert to a specific user"""
        try:
            user_id = user_data.get('user_id')
            if not user_id:
                logger.error("No user_id provided for economic alert")
                return False
            
            # Get alert timing
            event_datetime = self._parse_event_datetime(event)
            if not event_datetime:
                return False
            
            now = datetime.now(timezone.utc)
            time_until_event = event_datetime - now
            minutes_until_event = time_until_event.total_seconds() / 60
            
            # Must match unified_alert_processor windows (5-minute poll + jitter)
            alert_timing = "unknown"
            if 3 <= minutes_until_event <= 18:
                alert_timing = "10min_before"
            elif 48 <= minutes_until_event <= 68:
                alert_timing = "1h_before"
            elif 105 <= minutes_until_event <= 130:
                alert_timing = "2h_before"
            
            # Check deduplication (Firebase-backed, survives restarts)
            from .persistent_alert_deduplication import should_send_economic_alert
            if not should_send_economic_alert(event, user_id, alert_timing):
                logger.debug(f"Economic alert duplicate prevented for user {user_id}")
                return False
            
            # Create alert data
            alert_data = {
                'title': event.get('title', 'Economic Event'),
                'content': self._create_economic_alert_content(event, alert_timing),
                'type': 'economicCalendar',
                'impact_level': event.get('impact', 'medium'),
                'currency_pairs': self.get_affected_currency_pairs(event),
                'source': 'Economic Calendar',
                'event_time': event.get('time', ''),
                'event_date': event.get('date', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            # Get user settings
            user_settings = user_data.get('settings', {})
            
            # Use alert service to process the alert (pass user_data so chat_id is available)
            from .alert_service import get_alert_service
            alert_service = get_alert_service()
            
            # Process alert with proper async handling (pass user_data for chat_id)
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(
                        alert_service.process_alert(alert_data, user_settings, user_id, user_data=user_data)
                    )
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Error in async alert processing: {e}")
                success = False
            
            if success:
                from .persistent_alert_deduplication import mark_economic_alert_sent
                mark_economic_alert_sent(event, user_id, alert_timing)
                logger.info(f"Economic alert sent successfully to user {user_id}")
                return True
            else:
                logger.warning(f"Economic alert not sent to user {user_id} (subscription check failed or user preferences)")
                return False
                
        except Exception as e:
            logger.error(f"Error sending economic alert to user: {e}")
            return False
    
    def _create_economic_alert_content(self, event: Dict[str, Any], alert_timing: str) -> str:
        """Create economic alert content"""
        try:
            title = event.get('title', 'Unknown Event')
            event_time = event.get('time', '')
            event_date = event.get('date', '')
            currency = event.get('currency', '')
            impact = event.get('impact', 'medium')
            
            # Get currency pairs
            affected_pairs = self.get_affected_currency_pairs(event)
            pairs_text = ', '.join(affected_pairs) if affected_pairs else 'Multiple pairs'
            
            # Format timing message
            if alert_timing == "10min_before":
                timing_msg = "Event starts in 10 minutes"
            elif alert_timing == "1h_before":
                timing_msg = "Event starts in 1 hour"
            elif alert_timing == "2h_before":
                timing_msg = "Event starts in 2 hours"
            else:
                timing_msg = "Event starting soon"
            
            # Create content with HTML formatting for Telegram
            content = f"<b>UPCOMING ECONOMIC EVENT</b>\n\n"
            content += f"<b>{title}</b>\n"
            content += f"<b>{timing_msg}</b>\n\n"
            content += f"<b>Event Details:</b>\n"
            event_time_display = event_time if "UTC" in event_time else f"{event_time} UTC"
            content += f"• Time: {event_time_display}\n"
            content += f"• Date: {event_date}\n"
            content += f"• Currency: {currency}\n"
            content += f"• Impact: {impact.upper()}\n"
            content += f"• Affected Pairs: {pairs_text}\n\n"
            content += f"<b>Prepare for Market Volatility</b>"
            
            return content
            
        except Exception as e:
            logger.error(f"Error creating economic alert content: {e}")
            return "Economic event alert"

# Global instance
economic_calendar_alerts = EconomicCalendarAlerts()
