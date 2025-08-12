import requests
import os
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional

class FinnhubCalendarService:
    """Service for fetching economic calendar data from Finnhub API"""
    
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY', 'd2d51d1r01qjem5j4g9gd2d51d1r01qjem5j4ga0')  # Demo key from email
        self.base_url = 'https://finnhub.io/api/v1'
        self.session = requests.Session()
        self.session.headers.update({
            'X-Finnhub-Token': self.api_key,
            'User-Agent': 'FXSentinel/1.0'
        })
    
    def get_economic_calendar(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Fetch economic calendar events from Finnhub
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: today)
            end_date: End date in YYYY-MM-DD format (default: 7 days from start)
        
        Returns:
            List of economic calendar events
        """
        try:
            # Set default dates if not provided
            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Finnhub economic calendar endpoint
            url = f"{self.base_url}/calendar/economic"
            params = {
                'from': start_date,
                'to': end_date
            }
            
            print(f"📅 Fetching Finnhub economic calendar from {start_date} to {end_date}")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'economicCalendar' not in data:
                print("⚠️ No economic calendar data in response")
                return []
            
            events = data['economicCalendar']
            print(f"✅ Fetched {len(events)} economic events from Finnhub")
            
            # Transform Finnhub data to our format
            transformed_events = []
            for event in events:
                transformed_event = self._transform_event(event)
                if transformed_event:
                    transformed_events.append(transformed_event)
            
            return transformed_events
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching Finnhub calendar: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error in Finnhub calendar: {e}")
            return []
    
    def _transform_event(self, event: Dict) -> Optional[Dict]:
        """
        Transform Finnhub event format to our internal format
        
        Args:
            event: Raw event data from Finnhub
            
        Returns:
            Transformed event data or None if invalid
        """
        try:
            # Extract basic event info
            event_date = event.get('date', '')
            event_time = event.get('time', '')
            
            # Parse date and time
            event_datetime = None
            
            if event_date and event_time:
                try:
                    # Finnhub format: "2024-01-15" and "13:30"
                    datetime_str = f"{event_date} {event_time}"
                    event_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                    
                    # Format for display
                    display_date = event_datetime.strftime('%a, %b %d')
                    display_time = event_datetime.strftime('%H:%M UTC')
                except ValueError:
                    display_date = event_date
                    display_time = event_time
            elif event_time:
                # If we have time but no date, try to extract date from time field
                try:
                    # Check if time field contains date info (e.g., "2025-08-12 00:00:00")
                    if ' ' in event_time and len(event_time) > 10:
                        # Time field contains both date and time
                        event_datetime = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')
                        display_date = event_datetime.strftime('%a, %b %d')
                        display_time = event_datetime.strftime('%H:%M UTC')
                    else:
                        # Just time, use today's date
                        today = datetime.now()
                        display_date = today.strftime('%a, %b %d')
                        display_time = event_time
                except ValueError:
                    # Fallback: use today's date with provided time
                    today = datetime.now()
                    display_date = today.strftime('%a, %b %d')
                    display_time = event_time
            elif event_date:
                # If we have date but no time, use default time
                try:
                    event_datetime = datetime.strptime(event_date, '%Y-%m-%d')
                    display_date = event_datetime.strftime('%a, %b %d')
                    display_time = 'TBD'
                except ValueError:
                    display_date = event_date
                    display_time = 'TBD'
            else:
                # No date or time provided
                display_date = 'TBD'
                display_time = 'TBD'
            
            # Determine impact level
            impact = self._determine_impact(event.get('impact', ''))
            if not impact or impact == 'medium':  # If no impact or default, try to determine from event
                impact = self._determine_impact_from_event(event)
            
            # Get currency pairs affected
            currency = event.get('currency', '')
            
            # If currency is empty, try to extract it from the event name or country
            if not currency:
                currency = self._extract_currency_from_event(event)
            
            currency_pairs = self._get_affected_pairs(currency)
            
            # Determine event type
            event_type = self._determine_event_type(event.get('event', ''))
            
            # Get status
            status = self._determine_status(event_datetime) if 'event_datetime' in locals() else 'UPCOMING'
            
            transformed_event = {
                'id': event.get('id', hash(event.get('event', ''))),
                'time': display_time,
                'date': display_date,
                'title': event.get('event', 'Unknown Event'),
                'type': event_type,
                'currency': currency,
                'status': status,
                'impact': impact,
                'currencyPairs': currency_pairs,
                'previous': event.get('prev', '--'),  # Finnhub uses 'prev' not 'previous'
                'expected': event.get('estimate', '--'),
                'actual': event.get('actual', '--'),
                'source': 'Finnhub',
                'raw_data': event  # Keep original data for debugging
            }
            
            return transformed_event
            
        except Exception as e:
            print(f"❌ Error transforming event {event.get('event', 'Unknown')}: {e}")
            return None
    
    def _determine_impact(self, impact_str: str) -> str:
        """Determine impact level from Finnhub impact string"""
        impact_lower = impact_str.lower()
        
        if 'high' in impact_lower:
            return 'high'
        elif 'medium' in impact_lower:
            return 'medium'
        elif 'low' in impact_lower:
            return 'low'
        else:
            # Default based on event type or currency
            return 'medium'
    
    def _determine_impact_from_event(self, event: Dict) -> str:
        """Determine impact level from event characteristics"""
        event_name = event.get('event', '').lower()
        
        # High impact events
        high_impact_keywords = [
            'non-farm payrolls', 'employment report', 'cpi', 'inflation', 'gdp',
            'interest rate', 'monetary policy', 'federal reserve', 'ecb', 'boe',
            'central bank', 'rate decision'
        ]
        
        # Medium impact events
        medium_impact_keywords = [
            'retail sales', 'manufacturing', 'industrial production', 'housing',
            'consumer confidence', 'business confidence', 'trade balance'
        ]
        
        # Check for high impact keywords
        for keyword in high_impact_keywords:
            if keyword in event_name:
                return 'high'
        
        # Check for medium impact keywords
        for keyword in medium_impact_keywords:
            if keyword in event_name:
                return 'medium'
        
        # Default to low impact
        return 'low'
    
    def _get_affected_pairs(self, currency: str) -> List[str]:
        """Get affected currency pairs based on currency"""
        if not currency:
            return []
        
        # Major currency pairs that are most affected by each currency
        currency_pairs_map = {
            'USD': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD'],
            'EUR': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/CAD', 'EUR/AUD'],
            'GBP': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF', 'GBP/CAD', 'GBP/AUD'],
            'JPY': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY', 'CAD/JPY', 'CHF/JPY'],
            'AUD': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY', 'AUD/CAD', 'AUD/CHF'],
            'CAD': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'CAD/JPY', 'AUD/CAD', 'CAD/CHF'],
            'CHF': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'CHF/JPY', 'AUD/CHF', 'CAD/CHF'],
            'NZD': ['NZD/USD', 'EUR/NZD', 'GBP/NZD', 'NZD/JPY', 'AUD/NZD', 'NZD/CAD']
        }
        
        pairs = currency_pairs_map.get(currency.upper(), [])
        
        # For high impact events, show more pairs; for low impact, show fewer
        if len(pairs) > 3:
            # Return top 3 most liquid pairs for better UI
            return pairs[:3]
        
        return pairs
    
    def _extract_currency_from_event(self, event: Dict) -> str:
        """Extract currency from event name or country information"""
        event_name = event.get('event', '').lower()
        country = event.get('country', '').lower()
        
        # Currency mapping based on country names and common event patterns
        currency_map = {
            # US events
            'united states': 'USD', 'us ': 'USD', 'federal reserve': 'USD', 'fed ': 'USD',
            'non-farm': 'USD', 'cpi': 'USD', 'gdp': 'USD', 'retail sales': 'USD',
            'unemployment': 'USD', 'employment': 'USD', 'manufacturing': 'USD',
            'industrial production': 'USD', 'housing': 'USD', 'consumer confidence': 'USD',
            'business confidence': 'USD', 'trade balance': 'USD', 'current account': 'USD',
            
            # Eurozone events
            'eurozone': 'EUR', 'european': 'EUR', 'ecb': 'EUR', 'euro ': 'EUR',
            'european central bank': 'EUR', 'euro area': 'EUR', 'eurozone ': 'EUR',
            
            # UK events
            'united kingdom': 'GBP', 'uk ': 'GBP', 'britain': 'GBP', 'boe': 'GBP',
            'bank of england': 'GBP', 'british': 'GBP', 'england': 'GBP',
            
            # Japan events
            'japan': 'JPY', 'japanese': 'JPY', 'boj': 'JPY', 'bank of japan': 'JPY',
            'japan ': 'JPY', 'japanese ': 'JPY',
            
            # Australia events
            'australia': 'AUD', 'australian': 'AUD', 'rba': 'AUD', 'reserve bank of australia': 'AUD',
            'australia ': 'AUD', 'australian ': 'AUD',
            
            # Canada events
            'canada': 'CAD', 'canadian': 'CAD', 'boc': 'CAD', 'bank of canada': 'CAD',
            'canada ': 'CAD', 'canadian ': 'CAD',
            
            # Switzerland events
            'switzerland': 'CHF', 'swiss': 'CHF', 'snb': 'CHF', 'swiss national bank': 'CHF',
            'switzerland ': 'CHF', 'swiss ': 'CHF',
            
            # New Zealand events
            'new zealand': 'NZD', 'nz ': 'NZD', 'rbnz': 'NZD', 'reserve bank of new zealand': 'NZD',
            'new zealand ': 'NZD'
        }
        
        # Check event name for currency indicators
        for key, currency in currency_map.items():
            if key in event_name:
                return currency
        
        # Check country field for currency indicators
        for key, currency in currency_map.items():
            if key in country:
                return currency
        
        # Default to USD for major economic events if no specific currency found
        if any(keyword in event_name for keyword in ['cpi', 'gdp', 'employment', 'retail', 'manufacturing']):
            return 'USD'
        
        return ''

    def _determine_event_type(self, event_name: str) -> str:
        """Determine event type based on event name"""
        event_lower = event_name.lower()
        
        if any(keyword in event_lower for keyword in ['rate', 'interest', 'monetary', 'policy']):
            return 'CENTRAL BANK'
        elif any(keyword in event_lower for keyword in ['speech', 'testimony', 'comment']):
            return 'CENTRAL BANK'
        elif any(keyword in event_lower for keyword in ['cpi', 'inflation', 'employment', 'gdp', 'retail', 'manufacturing']):
            return 'ECONOMIC RELEASE'
        else:
            return 'ECONOMIC RELEASE'
    
    def _determine_status(self, event_datetime: datetime) -> str:
        """Determine event status based on datetime"""
        now = datetime.now()
        
        if event_datetime < now:
            return 'COMPLETED'
        elif event_datetime <= now + timedelta(hours=1):
            return 'IMMINENT'
        else:
            return 'UPCOMING'
    
    def test_connection(self) -> Dict:
        """Test Finnhub API connection and return status"""
        try:
            # Test with a simple API call
            url = f"{self.base_url}/calendar/economic"
            params = {
                'from': datetime.now().strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = self.session.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                event_count = len(data.get('economicCalendar', []))
                return {
                    'status': 'success',
                    'message': f'Connected successfully. Found {event_count} events today.',
                    'api_key_valid': True
                }
            elif response.status_code == 401:
                return {
                    'status': 'error',
                    'message': 'Invalid API key',
                    'api_key_valid': False
                }
            else:
                return {
                    'status': 'error',
                    'message': f'API returned status {response.status_code}',
                    'api_key_valid': False
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)}',
                'api_key_valid': False
            }

# Create global instance
finnhub_calendar = FinnhubCalendarService()
