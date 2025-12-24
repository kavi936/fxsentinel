#!/usr/bin/env python3
"""
Script to update calendar events JSON file with actual release data.
Fetches actual values from Finnhub API or cached database for events that have already occurred.
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Add parent directory to path to import backend services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load environment variables
load_dotenv()

class CalendarUpdater:
    """Updates calendar events with actual release data"""
    
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'economic_calendar.db')
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'X-Finnhub-Token': self.api_key,
                'User-Agent': 'FXSentinel-CalendarUpdater/1.0'
            })
            print("✅ Finnhub API key configured")
        else:
            print("⚠️ FINNHUB_API_KEY not set - will try to use cached database")
    
    def parse_event_date(self, date_str: str) -> Optional[datetime]:
        """Parse event date from various formats"""
        try:
            # Try ISO format with timezone: "2025-12-21T06:00:00-05:00"
            if 'T' in date_str:
                # Remove timezone offset for parsing
                if '+' in date_str or (date_str.count('-') > 2 and date_str[-6] == '-'):
                    # Has timezone offset
                    if date_str.endswith('Z'):
                        date_str = date_str[:-1]
                    else:
                        # Remove timezone offset (e.g., -05:00)
                        tz_index = date_str.rfind('-')
                        if tz_index > 10:  # Not part of date
                            date_str = date_str[:tz_index]
                return datetime.fromisoformat(date_str.replace('Z', ''))
            
            # Try YYYY-MM-DD format
            return datetime.strptime(date_str, '%Y-%m-%d')
        except Exception as e:
            print(f"⚠️ Error parsing date '{date_str}': {e}")
            return None
    
    def is_event_past(self, event: Dict) -> bool:
        """Check if an event has already occurred"""
        date_str = event.get('date', '')
        if not date_str:
            return False
        
        event_dt = self.parse_event_date(date_str)
        if not event_dt:
            return False
        
        # Compare with current time (UTC)
        now = datetime.now(timezone.utc)
        # Make event_dt timezone-aware if it's not
        if event_dt.tzinfo is None:
            event_dt = event_dt.replace(tzinfo=timezone.utc)
        
        return event_dt < now
    
    def get_actual_from_database(self, event: Dict) -> Optional[str]:
        """Try to get actual value from cached database"""
        # Try multiple database paths
        db_paths = [
            self.db_path,
            os.path.join(os.path.dirname(__file__), '..', 'data', 'economic_calendar.db'),
            os.path.join(os.path.dirname(__file__), '..', 'backend', 'economic_calendar.db'),
        ]
        
        db_path_to_use = None
        for db_path in db_paths:
            if os.path.exists(db_path):
                db_path_to_use = db_path
                break
        
        if not db_path_to_use:
            return None
        
        try:
            conn = sqlite3.connect(db_path_to_use)
            cursor = conn.cursor()
            
            # Parse event date
            event_dt = self.parse_event_date(event.get('date', ''))
            if not event_dt:
                conn.close()
                return None
            
            event_date_str = event_dt.strftime('%Y-%m-%d')
            event_title = event.get('title', '').lower()
            event_country = event.get('country', '')
            
            # Try multiple matching strategies
            # Strategy 1: Exact match by title, date, and country
            query1 = '''
                SELECT actual_value 
                FROM economic_events 
                WHERE date = ? 
                AND LOWER(title) LIKE ? 
                AND country = ?
                AND actual_value IS NOT NULL 
                AND actual_value != '' 
                AND actual_value != '--'
                ORDER BY datetime_utc DESC
                LIMIT 1
            '''
            
            cursor.execute(query1, (event_date_str, f'%{event_title}%', event_country))
            result = cursor.fetchone()
            
            if result and result[0]:
                conn.close()
                return str(result[0])
            
            # Strategy 2: Match by title keywords and date (more flexible)
            # Extract key words from title
            title_words = [word for word in event_title.split() if len(word) > 3]
            if title_words:
                # Try matching with key words
                for word in title_words[:3]:  # Use first 3 significant words
                    query2 = '''
                        SELECT actual_value 
                        FROM economic_events 
                        WHERE date = ? 
                        AND LOWER(title) LIKE ?
                        AND actual_value IS NOT NULL 
                        AND actual_value != '' 
                        AND actual_value != '--'
                        ORDER BY datetime_utc DESC
                        LIMIT 1
                    '''
                    cursor.execute(query2, (event_date_str, f'%{word}%'))
                    result = cursor.fetchone()
                    if result and result[0]:
                        conn.close()
                        return str(result[0])
            
            # Strategy 3: Match by date range (±1 day) and title keywords
            date_before = (event_dt - timedelta(days=1)).strftime('%Y-%m-%d')
            date_after = (event_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            
            if title_words:
                for word in title_words[:2]:  # Use first 2 significant words
                    query3 = '''
                        SELECT actual_value 
                        FROM economic_events 
                        WHERE date BETWEEN ? AND ?
                        AND LOWER(title) LIKE ?
                        AND actual_value IS NOT NULL 
                        AND actual_value != '' 
                        AND actual_value != '--'
                        ORDER BY datetime_utc DESC
                        LIMIT 1
                    '''
                    cursor.execute(query3, (date_before, date_after, f'%{word}%'))
                    result = cursor.fetchone()
                    if result and result[0]:
                        conn.close()
                        return str(result[0])
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"⚠️ Error querying database {db_path_to_use}: {e}")
            return None
    
    def get_actual_from_api(self, event: Dict) -> Optional[str]:
        """Try to get actual value from Finnhub API"""
        if not self.api_key:
            return None
        
        try:
            # Parse event date
            event_dt = self.parse_event_date(event.get('date', ''))
            if not event_dt:
                return None
            
            # Get date range (event date ± 1 day to account for timezone differences)
            start_date = (event_dt - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (event_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Make API request
            url = f"{self.base_url}/calendar/economic"
            params = {
                'from': start_date,
                'to': end_date
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'economicCalendar' not in data:
                return None
            
            events = data['economicCalendar']
            event_title = event.get('title', '').lower()
            event_country = event.get('country', '')
            
            # Find matching event
            for api_event in events:
                api_title = api_event.get('event', '').lower()
                api_country = api_event.get('country', '')
                api_actual = api_event.get('actual')
                
                # Check if titles match (fuzzy match)
                if event_title in api_title or api_title in event_title:
                    if api_country == event_country or not event_country:
                        if api_actual and str(api_actual).strip() and str(api_actual) != 'None':
                            return self.format_value(str(api_actual))
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error fetching from API: {e}")
            return None
    
    def format_value(self, value: str) -> str:
        """Format economic value consistently"""
        value = str(value).strip()
        if not value or value == 'None':
            return '--'
        
        # If value already has unit indicators, return as is
        if any(unit_char in value for unit_char in ['%', 'K', 'M', 'B', 'T']):
            return value
        
        # Try to format as number
        try:
            num_value = float(value)
            # For small numbers, add percentage if it seems like a percentage
            if abs(num_value) < 10:
                return f"{num_value:.1f}%"
            else:
                return f"{num_value:.1f}"
        except (ValueError, TypeError):
            return value
    
    def update_event_with_actual(self, event: Dict) -> Dict:
        """Update a single event with actual value if available"""
        # Ensure 'actual' field exists (initialize with empty string if missing)
        if 'actual' not in event:
            event['actual'] = ''
        
        # Check if event already has actual value
        if event.get('actual') and event.get('actual') not in ['', '--', None]:
            return event
        
        # Only update past events
        if not self.is_event_past(event):
            return event
        
        print(f"🔍 Looking for actual value for: {event.get('title')} ({event.get('date')})")
        
        # Try database first (faster and free)
        actual_value = self.get_actual_from_database(event)
        
        # If not found in database, try API
        if not actual_value:
            actual_value = self.get_actual_from_api(event)
        
        if actual_value:
            event['actual'] = actual_value
            print(f"✅ Updated {event.get('title')} with actual: {actual_value}")
        else:
            # Set to empty string if not found (to indicate we tried)
            event['actual'] = ''
            print(f"⚠️ No actual value found for {event.get('title')}")
        
        return event
    
    def update_calendar_file(self, file_path: str) -> bool:
        """Update calendar events in JSON file with actual values"""
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    print("❌ File is empty")
                    return False
                
                events = json.loads(content)
            
            if not isinstance(events, list):
                print("❌ JSON file should contain an array of events")
                return False
            
            print(f"📅 Found {len(events)} events in file")
            print(f"📅 Current date/time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            
            # Count past vs future events
            past_events = 0
            future_events = 0
            
            # Update events with actual values
            updated_count = 0
            for event in events:
                if self.is_event_past(event):
                    past_events += 1
                    original_actual = event.get('actual', '')
                    updated_event = self.update_event_with_actual(event)
                    if updated_event.get('actual') != original_actual and updated_event.get('actual'):
                        updated_count += 1
                else:
                    future_events += 1
            
            # Write updated JSON back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 Summary:")
            print(f"   Past events: {past_events}")
            print(f"   Future events: {future_events}")
            print(f"   Updated with actual values: {updated_count}")
            print(f"💾 Saved to {file_path}")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Error updating calendar: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update calendar events with actual release data')
    parser.add_argument('file', help='Path to JSON file with calendar events')
    args = parser.parse_args()
    
    updater = CalendarUpdater()
    success = updater.update_calendar_file(args.file)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

