#!/usr/bin/env python3
"""
Cached Economic Calendar Service for FXSentinel
Serves economic calendar data from local SQLite database when API is unavailable.
This allows continued operation after API key expiration.
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CachedEconomicCalendarService:
    """Service for serving cached economic calendar data from local database"""
    
    def __init__(self, db_path: str = "economic_calendar.db"):
        self.db_path = db_path
        self.cache_available = self._check_cache_availability()
        
        if self.cache_available:
            logger.info(f"✅ Cached economic calendar service initialized with {db_path}")
        else:
            logger.warning(f"⚠️ Cache database not found at {db_path}")
    
    def _check_cache_availability(self) -> bool:
        """Check if cache database exists and has data"""
        try:
            if not os.path.exists(self.db_path):
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if table exists and has data
            cursor.execute('SELECT COUNT(*) FROM economic_events')
            count = cursor.fetchone()[0]
            
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ Error checking cache availability: {e}")
            return False
    
    def get_economic_calendar(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get economic calendar events from cached database
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: today)
            end_date: End date in YYYY-MM-DD format (default: 7 days from start)
        
        Returns:
            List of economic calendar events in the same format as Finnhub API
        """
        if not self.cache_available:
            logger.warning("⚠️ Cache not available - returning empty calendar")
            return []
        
        try:
            # Set default dates if not provided
            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            logger.info(f"📅 Fetching cached economic calendar from {start_date} to {end_date}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query events within date range, prioritizing real economic indicators
            cursor.execute('''
                SELECT * FROM economic_events 
                WHERE date >= ? AND date <= ?
                ORDER BY 
                    CASE impact 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                        ELSE 4 
                    END,
                    datetime_utc ASC, time ASC
            ''', (start_date, end_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Transform database rows to API format
            events = []
            for row in rows:
                event = self._transform_db_row_to_event(row)
                if event:
                    events.append(event)
            
            logger.info(f"✅ Retrieved {len(events)} cached events from {start_date} to {end_date}")
            
            # Add metadata to indicate this is cached data
            if events:
                events[0]['_metadata'] = {
                    'data_quality': 'cached',
                    'source': 'cached_database',
                    'cache_date': self._get_cache_info(),
                    'recommendation': 'data_from_cache'
                }
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error fetching cached calendar: {e}")
            return []
    
    def _transform_db_row_to_event(self, row: tuple) -> Optional[Dict]:
        """Transform database row to event format matching Finnhub API"""
        try:
            # Database columns: id, event_id, title, date, time, datetime_utc, currency, country,
            # impact, event_type, previous_value, expected_value, actual_value, unit, source, raw_data, created_at, updated_at
            
            # Parse raw_data if available
            raw_data = {}
            if row[15]:  # raw_data column
                try:
                    raw_data = json.loads(row[15])
                except:
                    pass
            
            # Parse date and time from the time field (which contains full datetime)
            time_field = row[4]  # time field contains "2025-09-11 12:15:00"
            date_field = row[3]  # date field (usually empty)
            
            # Extract date and time from time field
            formatted_date = ""
            formatted_time = ""
            
            if time_field and ' ' in time_field:
                try:
                    from datetime import datetime
                    # Parse the datetime string
                    dt = datetime.strptime(time_field, '%Y-%m-%d %H:%M:%S')
                    
                    # Format date as "Thur, Aug 12" (day of week, month, day)
                    formatted_date = dt.strftime('%a, %b %d')
                    
                    # Format time as "8:00 GST" (hour:minute, timezone)
                    # Convert to GST (UTC+4) for display
                    gst_time = dt.replace(hour=(dt.hour + 4) % 24)
                    formatted_time = gst_time.strftime('%H:%M GST')
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing datetime {time_field}: {e}")
                    # Fallback to original values
                    formatted_date = date_field if date_field else ""
                    formatted_time = time_field if time_field else ""
            else:
                # Fallback to original values
                formatted_date = date_field if date_field else ""
                formatted_time = time_field if time_field else ""
            
            # Create event in Finnhub format
            event = {
                'id': row[1],  # event_id
                'event': row[2],  # title
                'date': formatted_date,  # formatted date
                'time': formatted_time,  # formatted time
                'currency': row[6],  # currency
                'country': row[7],  # country
                'impact': row[8],  # impact
                'prev': row[10],  # previous_value
                'estimate': row[11],  # expected_value
                'actual': row[12],  # actual_value
                'unit': row[13],  # unit
                'source': 'cached_database'
            }
            
            # Merge with original raw data if available
            if raw_data:
                event.update(raw_data)
            
            return event
            
        except Exception as e:
            logger.error(f"❌ Error transforming database row: {e}")
            return None
    
    def _get_cache_info(self) -> Dict:
        """Get information about the cached data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total events count
            cursor.execute('SELECT COUNT(*) FROM economic_events')
            total_events = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute('SELECT MIN(date), MAX(date) FROM economic_events')
            date_range = cursor.fetchone()
            
            # Get last extraction date
            cursor.execute('''
                SELECT extraction_date FROM extraction_log 
                ORDER BY extraction_date DESC LIMIT 1
            ''')
            last_extraction = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_events': total_events,
                'date_range': {
                    'earliest': date_range[0],
                    'latest': date_range[1]
                },
                'last_extraction': last_extraction[0] if last_extraction else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache info: {e}")
            return {}
    
    def get_cache_statistics(self) -> Dict:
        """Get detailed statistics about the cached data"""
        if not self.cache_available:
            return {'error': 'Cache not available'}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total events
            cursor.execute('SELECT COUNT(*) FROM economic_events')
            total_events = cursor.fetchone()[0]
            
            # Events by currency
            cursor.execute('''
                SELECT currency, COUNT(*) as count 
                FROM economic_events 
                WHERE currency IS NOT NULL AND currency != ''
                GROUP BY currency 
                ORDER BY count DESC
                LIMIT 10
            ''')
            currency_stats = dict(cursor.fetchall())
            
            # Events by impact
            cursor.execute('''
                SELECT impact, COUNT(*) as count 
                FROM economic_events 
                GROUP BY impact 
                ORDER BY count DESC
            ''')
            impact_stats = dict(cursor.fetchall())
            
            # Events by type
            cursor.execute('''
                SELECT event_type, COUNT(*) as count 
                FROM economic_events 
                GROUP BY event_type 
                ORDER BY count DESC
            ''')
            type_stats = dict(cursor.fetchall())
            
            # Date range
            cursor.execute('SELECT MIN(date), MAX(date) FROM economic_events')
            date_range = cursor.fetchone()
            
            # Recent events (next 7 days)
            today = datetime.now().strftime('%Y-%m-%d')
            week_later = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT COUNT(*) FROM economic_events 
                WHERE date >= ? AND date <= ?
            ''', (today, week_later))
            upcoming_events = cursor.fetchone()[0]
            
            # High impact events in next 7 days
            cursor.execute('''
                SELECT COUNT(*) FROM economic_events 
                WHERE date >= ? AND date <= ? AND impact = 'high'
            ''', (today, week_later))
            upcoming_high_impact = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_events': total_events,
                'currency_distribution': currency_stats,
                'impact_distribution': impact_stats,
                'type_distribution': type_stats,
                'date_range': {
                    'earliest': date_range[0],
                    'latest': date_range[1]
                },
                'upcoming_events': {
                    'next_7_days': upcoming_events,
                    'high_impact_next_7_days': upcoming_high_impact
                },
                'cache_info': self._get_cache_info()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache statistics: {e}")
            return {'error': str(e)}
    
    def search_events(self, query: str, limit: int = 50) -> List[Dict]:
        """Search for events by title or description"""
        if not self.cache_available:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search in title
            cursor.execute('''
                SELECT * FROM economic_events 
                WHERE title LIKE ? 
                ORDER BY date DESC, time DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event = self._transform_db_row_to_event(row)
                if event:
                    events.append(event)
            
            logger.info(f"🔍 Found {len(events)} events matching '{query}'")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error searching events: {e}")
            return []
    
    def get_events_by_currency(self, currency: str, days_ahead: int = 30) -> List[Dict]:
        """Get events for a specific currency"""
        if not self.cache_available:
            return []
        
        try:
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM economic_events 
                WHERE currency = ? AND date >= ? AND date <= ?
                ORDER BY date ASC, time ASC
            ''', (currency.upper(), start_date, end_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event = self._transform_db_row_to_event(row)
                if event:
                    events.append(event)
            
            logger.info(f"💰 Found {len(events)} events for {currency} in next {days_ahead} days")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error getting events by currency: {e}")
            return []
    
    def get_high_impact_events(self, days_ahead: int = 7) -> List[Dict]:
        """Get high impact events in the next N days"""
        if not self.cache_available:
            return []
        
        try:
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM economic_events 
                WHERE impact = 'high' AND date >= ? AND date <= ?
                ORDER BY date ASC, time ASC
            ''', (start_date, end_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event = self._transform_db_row_to_event(row)
                if event:
                    events.append(event)
            
            logger.info(f"🔥 Found {len(events)} high impact events in next {days_ahead} days")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error getting high impact events: {e}")
            return []
    
    def is_cache_available(self) -> bool:
        """Check if cache is available and has data"""
        return self.cache_available

# Create global instance
cached_economic_calendar = CachedEconomicCalendarService()
