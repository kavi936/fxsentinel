#!/usr/bin/env python3
"""
Economic Calendar Alert System
Sends pre-event alerts for upcoming economic events
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

class EconomicCalendarAlerts:
    def __init__(self):
        """Initialize the economic calendar alert system"""
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        self.alert_hours_before = [2, 1]  # Send alerts 2 hours and 1 hour before
        self.alert_minutes_before = [10]  # Send alerts 10 minutes before
        self.processed_events = set()  # Track processed events to prevent duplicates
        
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
    
    def is_high_impact_event(self, event: Dict[str, Any]) -> bool:
        """Determine if event is high impact and should trigger alerts"""
        try:
            title = event.get('title', '').lower()
            event_type = event.get('type', '').upper()
            impact = event.get('impact', '').lower()
            
            # Check impact level
            if impact == 'high':
                return True
            
            # Check event type
            if any(event_type in high_type for high_type in self.high_impact_types):
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
            
            # Otherwise, infer from currency
            if currency == 'USD':
                return ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD']
            elif currency == 'EUR':
                return ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF']
            elif currency == 'GBP':
                return ['GBP/USD', 'EUR/GBP', 'GBP/JPY']
            elif currency == 'JPY':
                return ['USD/JPY', 'EUR/JPY', 'GBP/JPY']
            elif currency == 'AUD':
                return ['AUD/USD', 'EUR/AUD', 'GBP/AUD']
            elif currency == 'CAD':
                return ['USD/CAD', 'EUR/CAD', 'GBP/CAD']
            elif currency == 'CHF':
                return ['USD/CHF', 'EUR/CHF', 'GBP/CHF']
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting currency pairs: {e}")
            return []
    
    def should_send_pre_event_alert(self, event: Dict[str, Any]) -> bool:
        """Determine if we should send a pre-event alert for this event"""
        try:
            # Check if it's a high-impact event
            if not self.is_high_impact_event(event):
                return False
            
            # Check if event is upcoming (not past)
            event_time = event.get('time', '')
            event_date = event.get('date', '')
            
            if not event_time or not event_date:
                return False
            
            # Parse event datetime
            try:
                # This is a simplified parser - you might need to adjust based on your date format
                event_datetime = datetime.strptime(f"{event_date} {event_time}", "%a, %b %d %H:%M UTC")
                now = datetime.now()
                
                # Check if event is within next 24 hours
                if event_datetime > now and event_datetime <= now + timedelta(hours=24):
                    return True
                    
            except Exception as e:
                logger.error(f"Error parsing event datetime: {e}")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking pre-event alert need: {e}")
            return False
    
    def get_alert_timing(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all alert timings for an event (2h, 1h, 10min before)"""
        try:
            event_time = event.get('time', '')
            event_date = event.get('date', '')
            
            if not event_time or not event_date:
                return []
            
            # Parse event datetime
            event_datetime = datetime.strptime(f"{event_date} {event_time}", "%a, %b %d %H:%M UTC")
            now = datetime.now()
            
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
        """Get list of users who should receive this pre-event alert"""
        try:
            # Get all users with alert settings
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            
            all_users = firebase_storage.get_all_users_with_alerts()
            users_to_alert = []
            
            affected_pairs = self.get_affected_currency_pairs(event)
            
            for user_data in all_users:
                user_id = user_data.get('user_id')
                settings = user_data.get('settings', {})
                
                # Get the actual chat ID from Firebase
                chat_id = firebase_storage.get_telegram_chat_id(user_id)
                if not chat_id:
                    continue
                
                # Check if user has Telegram enabled
                telegram_enabled = settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                if not telegram_enabled:
                    continue
                
                # Check user preferences
                preferences = settings.get('preferences', {})
                
                # Check if user wants pre-news alerts
                alert_types = preferences.get('alertTypes', {})
                if not alert_types.get('preNews', True):  # Default to True
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
    
    def process_economic_calendar_for_alerts(self) -> Dict[str, Any]:
        """Process economic calendar events and send pre-event alerts"""
        try:
            results = {
                'total_events_checked': 0,
                'high_impact_events': 0,
                'alerts_sent': 0,
                'errors': []
            }
            
            # Get economic calendar events
            try:
                response = requests.get(f"{self.api_base_url}/api/economic-calendar", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])
                else:
                    logger.error(f"Failed to fetch economic calendar: {response.status_code}")
                    return results
            except Exception as e:
                logger.error(f"Error fetching economic calendar: {e}")
                return results
            
            results['total_events_checked'] = len(events)
            
            for event in events:
                event_id = str(event.get('id', ''))
                
                # Skip if already processed
                if event_id in self.processed_events:
                    continue
                
                # Check if we should send pre-event alert
                if not self.should_send_pre_event_alert(event):
                    continue
                
                results['high_impact_events'] += 1
                logger.info(f"Processing high-impact economic event: {event.get('title', '')[:50]}...")
                
                # Get alert timings for this event
                alert_timings = self.get_alert_timing(event)
                
                if not alert_timings:
                    logger.info("No alert timings found for this event")
                    continue
                
                # Get users to alert
                users_to_alert = self.get_users_to_alert(event)
                
                if not users_to_alert:
                    logger.info("No users to alert for this economic event")
                    continue
                
                # Send alerts for each timing
                for timing in alert_timings:
                    # Check if it's time to send this alert
                    now = datetime.now()
                    if abs((timing['time'] - now).total_seconds()) <= 300:  # Within 5 minutes of target time
                        for user_data in users_to_alert:
                            try:
                                success = self._send_pre_event_alert(user_data, event, timing)
                                if success:
                                    results['alerts_sent'] += 1
                            except Exception as e:
                                error_msg = f"Error sending {timing['type']} alert to user {user_data.get('user_id')}: {e}"
                                logger.error(error_msg)
                                results['errors'].append(error_msg)
                
                # Mark as processed
                self.processed_events.add(event_id)
                
                # Keep only last 1000 processed event IDs to prevent memory issues
                if len(self.processed_events) > 1000:
                    self.processed_events = set(list(self.processed_events)[-500:])
            
            logger.info(f"Economic calendar processing complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing economic calendar for alerts: {e}")
            return {'error': str(e)}
    
    def _send_pre_event_alert(self, user_data: Dict[str, Any], event: Dict[str, Any], timing: Dict[str, Any] = None) -> bool:
        """Send pre-event alert to a specific user"""
        try:
            chat_id = user_data.get('chat_id')
            if not chat_id:
                return False
            
            # Create pre-event alert message
            message = self._create_pre_event_alert_message(event, timing)
            
            # Send via Telegram
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("Telegram bot token not configured")
                return False
            
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            telegram_data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(telegram_url, json=telegram_data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Pre-event alert sent successfully to user {user_data.get('user_id')}")
                
                # Save to alert history
                self._save_pre_event_alert_history(user_data.get('user_id'), event, message)
                return True
            else:
                logger.error(f"Failed to send pre-event alert: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending pre-event alert to user: {e}")
            return False
    
    def _create_pre_event_alert_message(self, event: Dict[str, Any], timing: Dict[str, Any] = None) -> str:
        """Create formatted pre-event alert message"""
        try:
            title = event.get('title', '')
            event_type = event.get('type', '')
            currency = event.get('currency', '')
            time = event.get('time', '')
            date = event.get('date', '')
            impact = event.get('impact', '')
            previous = event.get('previous', '')
            expected = event.get('expected', '')
            
            affected_pairs = self.get_affected_currency_pairs(event)
            pairs_text = ', '.join(affected_pairs) if affected_pairs else 'Multiple pairs'
            
            # Determine message type and timing text
            if timing and timing.get('message_type') == 'final_reminder':
                header = "🚨 ECONOMIC EVENT REMINDER"
                timing_text = "Event starts in 10 minutes"
                action_text = "Final position preparation"
            else:
                header = "📅 ECONOMIC EVENT ALERT"
                timing_text = "Event starts in 1-2 hours"
                action_text = "Prepare for market volatility"
            
            message = f"""
{header}
**{title}** - {timing_text}

**Time:** {time} UTC | **Date:** {date}
**Impact:** {impact.upper()} | **Currency:** {currency}

**Event Details:**
• Type: {event_type}
• Affected Pairs: {pairs_text}

**Market Expectations:**
• Previous: {previous}
• Expected: {expected}

**Action Required:** {action_text}
**Dashboard:** Check for detailed analysis
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating pre-event alert message: {e}")
            return f"📅 Upcoming Economic Event: {event.get('title', 'Unknown')}"
    
    def _save_pre_event_alert_history(self, user_id: str, event: Dict[str, Any], message: str) -> bool:
        """Save pre-event alert to user's history"""
        try:
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            
            alert_data = {
                'type': 'preEvent',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'recipients': ['telegram'],
                'status': 'sent',
                'event_id': str(event.get('id', '')),
                'event_title': event.get('title', ''),
                'event_type': event.get('type', ''),
                'event_currency': event.get('currency', ''),
                'event_time': event.get('time', ''),
                'event_date': event.get('date', '')
            }
            
            # Save to Firebase using the existing method
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            path = f"alerts/users/{safe_user_id}/alert_history"
            
            # Get existing history and append new alert
            existing_history = firebase_storage._make_request('GET', path) or []
            if not isinstance(existing_history, list):
                existing_history = []
            
            existing_history.append(alert_data)
            
            # Keep only last 50 alerts to prevent database bloat
            if len(existing_history) > 50:
                existing_history = existing_history[-50:]
            
            firebase_storage._make_request('PUT', path, existing_history)
            return True
            
        except Exception as e:
            logger.error(f"Error saving pre-event alert history: {e}")
            return False

# Global instance
economic_calendar_alerts = EconomicCalendarAlerts()
