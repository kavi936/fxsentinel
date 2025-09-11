#!/usr/bin/env python3
"""
Economic Calendar Data Extractor for FXSentinel
Extracts all available economic calendar data from Finnhub API before expiration
and stores it in a local SQLite database for continued use during development.
"""

import os
import sqlite3
import json
import time
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EconomicDataExtractor:
    """Extracts and stores economic calendar data from Finnhub API"""
    
    def __init__(self, db_path: str = "economic_calendar.db"):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        self.db_path = db_path
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'X-Finnhub-Token': self.api_key,
                'User-Agent': 'FXSentinel-DataExtractor/1.0'
            })
            logger.info("✅ Finnhub API key configured for data extraction")
        else:
            logger.error("❌ FINNHUB_API_KEY not set - cannot extract data")
            raise ValueError("FINNHUB_API_KEY environment variable is required")
        
        # Initialize database
        self._init_database()
        
        # Rate limiting to respect API limits
        self.request_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
    
    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create economic_events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS economic_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT,
                    datetime_utc TEXT,
                    currency TEXT,
                    country TEXT,
                    impact TEXT,
                    event_type TEXT,
                    previous_value TEXT,
                    expected_value TEXT,
                    actual_value TEXT,
                    unit TEXT,
                    source TEXT DEFAULT 'finnhub',
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON economic_events(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_currency ON economic_events(currency)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_impact ON economic_events(impact)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_datetime ON economic_events(datetime_utc)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON economic_events(event_type)')
            
            # Create extraction_log table to track what data we've extracted
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extraction_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    events_found INTEGER DEFAULT 0,
                    events_stored INTEGER DEFAULT 0,
                    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed'
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise
    
    def _rate_limit(self):
        """Implement rate limiting to respect API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_api_request(self, start_date: str, end_date: str) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/calendar/economic"
            params = {
                'from': start_date,
                'to': end_date
            }
            
            logger.info(f"📅 Fetching data from {start_date} to {end_date}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'economicCalendar' not in data:
                logger.warning(f"⚠️ No economic calendar data in response for {start_date} to {end_date}")
                return None
            
            events = data['economicCalendar']
            logger.info(f"✅ Fetched {len(events)} events from {start_date} to {end_date}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed for {start_date} to {end_date}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error for {start_date} to {end_date}: {e}")
            return None
    
    def _store_events(self, events: List[Dict], start_date: str, end_date: str) -> Tuple[int, int]:
        """Store events in database with deduplication"""
        if not events:
            return 0, 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        events_found = len(events)
        events_stored = 0
        
        try:
            for event in events:
                # Create unique event ID
                event_id = self._generate_event_id(event)
                
                # Check if event already exists
                cursor.execute('SELECT id FROM economic_events WHERE event_id = ?', (event_id,))
                if cursor.fetchone():
                    continue  # Skip duplicate
                
                # Parse and format event data
                event_data = self._parse_event_data(event)
                if not event_data:
                    continue
                
                # Insert event
                cursor.execute('''
                    INSERT INTO economic_events (
                        event_id, title, date, time, datetime_utc, currency, country,
                        impact, event_type, previous_value, expected_value, actual_value,
                        unit, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id,
                    event_data['title'],
                    event_data['date'],
                    event_data['time'],
                    event_data['datetime_utc'],
                    event_data['currency'],
                    event_data['country'],
                    event_data['impact'],
                    event_data['event_type'],
                    event_data['previous_value'],
                    event_data['expected_value'],
                    event_data['actual_value'],
                    event_data['unit'],
                    json.dumps(event_data['raw_data'])
                ))
                
                events_stored += 1
            
            # Log extraction
            cursor.execute('''
                INSERT INTO extraction_log (start_date, end_date, events_found, events_stored)
                VALUES (?, ?, ?, ?)
            ''', (start_date, end_date, events_found, events_stored))
            
            conn.commit()
            logger.info(f"✅ Stored {events_stored} new events from {start_date} to {end_date}")
            
        except Exception as e:
            logger.error(f"❌ Error storing events: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return events_found, events_stored
    
    def _generate_event_id(self, event: Dict) -> str:
        """Generate unique event ID from event data"""
        # Use a combination of event name, date, time, and country for uniqueness
        event_name = event.get('event', '').strip()
        event_date = event.get('date', '')
        event_time = event.get('time', '')
        country = event.get('country', '')
        
        # Create a hash-like ID
        id_string = f"{event_name}|{event_date}|{event_time}|{country}"
        return str(hash(id_string))
    
    def _parse_event_data(self, event: Dict) -> Optional[Dict]:
        """Parse and clean event data for storage"""
        try:
            # Extract basic information
            title = event.get('event', '').strip()
            if not title:
                return None
            
            event_date = event.get('date', '')
            event_time = event.get('time', '')
            currency = event.get('currency', '')
            country = event.get('country', '')
            impact = event.get('impact', 'medium').lower()
            unit = event.get('unit', '')
            
            # Parse datetime - handle cases where date is in time field
            datetime_utc = None
            if event_time and ' ' in event_time and len(event_time) > 10:
                # Full datetime format in time field (e.g., "2025-09-10 00:00:00")
                datetime_utc = event_time
                # Extract date from datetime
                if not event_date:
                    event_date = event_time.split(' ')[0]
            elif event_date and event_time:
                # Date and time separate
                datetime_utc = f"{event_date} {event_time}"
            elif event_date:
                # Only date available
                datetime_utc = event_date
            elif event_time:
                # Only time available, use today's date
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')
                datetime_utc = f"{today} {event_time}"
                event_date = today
            
            # Determine event type
            event_type = self._determine_event_type(title)
            
            # Format economic values
            previous_value = self._format_economic_value(event.get('prev'), unit)
            expected_value = self._format_economic_value(event.get('estimate'), unit)
            actual_value = self._format_economic_value(event.get('actual'), unit)
            
            return {
                'title': title,
                'date': event_date,
                'time': event_time,
                'datetime_utc': datetime_utc,
                'currency': currency,
                'country': country,
                'impact': impact,
                'event_type': event_type,
                'previous_value': previous_value,
                'expected_value': expected_value,
                'actual_value': actual_value,
                'unit': unit,
                'raw_data': event
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing event data: {e}")
            return None
    
    def _determine_event_type(self, title: str) -> str:
        """Determine event type from title"""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['rate', 'interest', 'monetary', 'policy', 'fomc', 'ecb', 'boe', 'boj', 'rba', 'boc', 'snb', 'rbnz']):
            return 'CENTRAL_BANK'
        elif any(keyword in title_lower for keyword in ['speech', 'testimony', 'comment', 'interview', 'presentation']):
            return 'CENTRAL_BANK'
        elif any(keyword in title_lower for keyword in ['cpi', 'inflation', 'employment', 'gdp', 'retail', 'manufacturing', 'pmi']):
            return 'ECONOMIC_RELEASE'
        else:
            return 'ECONOMIC_RELEASE'
    
    def _format_economic_value(self, value, unit: str = '') -> str:
        """Format economic values consistently"""
        if value is None or value == 'None':
            return '--'
        
        value_str = str(value).strip()
        if not value_str or value_str == 'None':
            return '--'
        
        # If value already has unit indicators, return as is
        if any(unit_char in value_str for unit_char in ['%', 'K', 'M', 'B', 'T']):
            return value_str
        
        # Try to format as number
        try:
            num_value = float(value_str)
            if unit == '%' or '%' in value_str:
                return f"{num_value:.1f}%"
            elif 'K' in unit or num_value >= 1000:
                return f"{num_value:.0f}K"
            else:
                return f"{num_value:.1f}"
        except (ValueError, TypeError):
            return value_str
    
    def extract_historical_data(self, start_date: date, end_date: date) -> Dict:
        """Extract historical economic data for a date range"""
        logger.info(f"🔄 Starting historical data extraction from {start_date} to {end_date}")
        
        total_events_found = 0
        total_events_stored = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Extract data in weekly chunks to avoid overwhelming the API
            week_end = min(current_date + timedelta(days=6), end_date)
            
            start_str = current_date.strftime('%Y-%m-%d')
            end_str = week_end.strftime('%Y-%m-%d')
            
            # Make API request
            data = self._make_api_request(start_str, end_str)
            if data and 'economicCalendar' in data:
                events_found, events_stored = self._store_events(data['economicCalendar'], start_str, end_str)
                total_events_found += events_found
                total_events_stored += events_stored
            
            # Move to next week
            current_date = week_end + timedelta(days=1)
        
        logger.info(f"✅ Historical extraction complete: {total_events_stored} events stored from {total_events_found} found")
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'events_found': total_events_found,
            'events_stored': total_events_stored,
            'status': 'completed'
        }
    
    def extract_future_data(self, months_ahead: int = 12) -> Dict:
        """Extract future economic data for the next N months"""
        start_date = date.today()
        end_date = start_date + timedelta(days=months_ahead * 30)
        
        logger.info(f"🔄 Starting future data extraction for next {months_ahead} months")
        
        return self.extract_historical_data(start_date, end_date)
    
    def extract_comprehensive_data(self, historical_months: int = 24, future_months: int = 12) -> Dict:
        """Extract comprehensive economic data (historical + future)"""
        logger.info(f"🚀 Starting comprehensive data extraction: {historical_months} months historical, {future_months} months future")
        
        # Calculate date ranges
        today = date.today()
        historical_start = today - timedelta(days=historical_months * 30)
        future_end = today + timedelta(days=future_months * 30)
        
        results = {
            'historical': None,
            'future': None,
            'summary': {}
        }
        
        try:
            # Extract historical data
            logger.info("📚 Extracting historical data...")
            results['historical'] = self.extract_historical_data(historical_start, today)
            
            # Extract future data
            logger.info("🔮 Extracting future data...")
            results['future'] = self.extract_historical_data(today, future_end)
            
            # Summary
            results['summary'] = {
                'total_events_found': results['historical']['events_found'] + results['future']['events_found'],
                'total_events_stored': results['historical']['events_stored'] + results['future']['events_stored'],
                'extraction_date': datetime.now().isoformat(),
                'database_path': self.db_path
            }
            
            logger.info(f"🎉 Comprehensive extraction complete!")
            logger.info(f"   📊 Total events found: {results['summary']['total_events_found']}")
            logger.info(f"   💾 Total events stored: {results['summary']['total_events_stored']}")
            logger.info(f"   🗄️ Database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Error during comprehensive extraction: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the extracted data"""
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
            
            # Recent extractions
            cursor.execute('''
                SELECT start_date, end_date, events_stored, extraction_date 
                FROM extraction_log 
                ORDER BY extraction_date DESC 
                LIMIT 10
            ''')
            recent_extractions = cursor.fetchall()
            
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
                'recent_extractions': [
                    {
                        'start_date': row[0],
                        'end_date': row[1],
                        'events_stored': row[2],
                        'extraction_date': row[3]
                    } for row in recent_extractions
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {'error': str(e)}

def main():
    """Main function to run the data extraction"""
    try:
        # Initialize extractor
        extractor = EconomicDataExtractor()
        
        # Get current database stats
        logger.info("📊 Current database statistics:")
        stats = extractor.get_database_stats()
        if 'error' not in stats:
            logger.info(f"   Total events: {stats['total_events']}")
            logger.info(f"   Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        
        # Extract comprehensive data
        # Historical: 24 months back, Future: 12 months ahead
        results = extractor.extract_comprehensive_data(historical_months=24, future_months=12)
        
        # Print final statistics
        logger.info("\n📈 Final extraction results:")
        if 'summary' in results:
            logger.info(f"   Total events found: {results['summary']['total_events_found']}")
            logger.info(f"   Total events stored: {results['summary']['total_events_stored']}")
            logger.info(f"   Database location: {results['summary']['database_path']}")
        
        # Get updated database stats
        logger.info("\n📊 Updated database statistics:")
        final_stats = extractor.get_database_stats()
        if 'error' not in final_stats:
            logger.info(f"   Total events: {final_stats['total_events']}")
            logger.info(f"   Date range: {final_stats['date_range']['earliest']} to {final_stats['date_range']['latest']}")
            logger.info(f"   Top currencies: {list(final_stats['currency_distribution'].keys())[:5]}")
        
        logger.info("\n✅ Data extraction completed successfully!")
        logger.info("💡 You can now use the cached data even after your API key expires.")
        
    except Exception as e:
        logger.error(f"❌ Data extraction failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
