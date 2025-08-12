import requests
import os
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional

class FinnhubHistoricalService:
    """Service for fetching historical economic data from Finnhub"""
    
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY', 'd2d51d1r01qjem5j4g9gd2d51d1r01qjem5j4ga0')
        self.base_url = 'https://finnhub.io/api/v1'
        self.session = requests.Session()
        self.session.headers.update({
            'X-Finnhub-Token': self.api_key,
            'User-Agent': 'FXSentinel/1.0'
        })
    
    def get_historical_data_for_indicator(self, indicator_name: str, months: int = 24) -> List[Dict]:
        """
        Get historical data for a specific economic indicator
        
        Args:
            indicator_name: Name of the indicator (e.g., 'CPI', 'GDP', 'Unemployment')
            months: Number of months of historical data to fetch
            
        Returns:
            List of historical data points
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # Fetch historical calendar data
            url = f"{self.base_url}/calendar/economic"
            params = {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            print(f"📊 Fetching historical data for {indicator_name} ({months} months)")
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('economicCalendar', [])
            
            # Filter events for the specific indicator
            indicator_events = []
            indicator_lower = indicator_name.lower()
            
            for event in events:
                event_name = event.get('event', '').lower()
                
                # Check if this event matches our indicator
                if indicator_lower in event_name:
                    # Only include events with actual data
                    if event.get('actual') is not None:
                        indicator_events.append(event)
            
            # Sort by date (most recent first)
            indicator_events.sort(key=lambda x: x.get('time', ''), reverse=True)
            
            # Transform to chart-friendly format
            historical_data = []
            for event in indicator_events:
                try:
                    # Parse the date from time field
                    time_str = event.get('time', '')
                    if time_str and ' ' in time_str:
                        date_str = time_str.split(' ')[0]
                        event_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        historical_data.append({
                            'date': event_date.strftime('%Y-%m-%d'),
                            'value': event.get('actual'),
                            'previous': event.get('prev'),
                            'expected': event.get('estimate'),
                            'unit': event.get('unit', ''),
                            'event_name': event.get('event'),
                            'country': event.get('country', '')
                        })
                except Exception as e:
                    print(f"⚠️ Error parsing event date: {e}")
                    continue
            
            print(f"✅ Found {len(historical_data)} historical data points for {indicator_name}")
            return historical_data
            
        except Exception as e:
            print(f"❌ Error fetching historical data for {indicator_name}: {e}")
            return []
    
    def get_cpi_historical_data(self, months: int = 24) -> List[Dict]:
        """Get historical CPI data"""
        return self.get_historical_data_for_indicator('CPI', months)
    
    def get_gdp_historical_data(self, months: int = 24) -> List[Dict]:
        """Get historical GDP data"""
        return self.get_historical_data_for_indicator('GDP', months)
    
    def get_unemployment_historical_data(self, months: int = 24) -> List[Dict]:
        """Get historical unemployment data"""
        return self.get_historical_data_for_indicator('Unemployment', months)
    
    def get_employment_historical_data(self, months: int = 24) -> List[Dict]:
        """Get historical employment data"""
        return self.get_historical_data_for_indicator('Employment', months)
    
    def get_retail_sales_historical_data(self, months: int = 24) -> List[Dict]:
        """Get historical retail sales data"""
        return self.get_historical_data_for_indicator('Retail Sales', months)
    
    def get_chart_data_for_event(self, event_name: str, months: int = 12) -> Dict:
        """
        Get chart data for a specific economic event
        
        Args:
            event_name: Name of the economic event
            months: Number of months of historical data
            
        Returns:
            Chart data with historical values and metadata
        """
        try:
            # Extract indicator type from event name
            event_lower = event_name.lower()
            
            if 'cpi' in event_lower or 'inflation' in event_lower:
                indicator = 'CPI'
                historical_data = self.get_historical_data_for_indicator(indicator, months)
            elif 'gdp' in event_lower:
                indicator = 'GDP'
                historical_data = self.get_historical_data_for_indicator(indicator, months)
            elif 'unemployment' in event_lower:
                indicator = 'Unemployment'
                historical_data = self.get_historical_data_for_indicator(indicator, months)
            elif 'employment' in event_lower:
                indicator = 'Employment'
                historical_data = self.get_historical_data_for_indicator(indicator, months)
            elif 'retail' in event_lower:
                indicator = 'Retail Sales'
                historical_data = self.get_historical_data_for_indicator(indicator, months)
            else:
                # Try to match the event name directly
                historical_data = self.get_historical_data_for_indicator(event_name, months)
            
            if historical_data:
                # Calculate some basic statistics for AI analysis
                values = [point['value'] for point in historical_data if point['value'] is not None]
                
                if values:
                    avg_value = sum(values) / len(values)
                    min_value = min(values)
                    max_value = max(values)
                    trend = 'up' if values[0] > values[-1] else 'down' if values[0] < values[-1] else 'stable'
                else:
                    avg_value = min_value = max_value = 0
                    trend = 'unknown'
                
                return {
                    'indicator': indicator,
                    'historical_data': historical_data,
                    'data_points': len(historical_data),
                    'statistics': {
                        'average': avg_value,
                        'minimum': min_value,
                        'maximum': max_value,
                        'trend': trend,
                        'latest_value': historical_data[0]['value'] if historical_data else None,
                        'previous_value': historical_data[1]['value'] if len(historical_data) > 1 else None
                    },
                    'timeframe': f"{months} months",
                    'last_updated': datetime.now().isoformat()
                }
            else:
                return {
                    'indicator': indicator,
                    'historical_data': [],
                    'data_points': 0,
                    'statistics': {},
                    'timeframe': f"{months} months",
                    'last_updated': datetime.now().isoformat(),
                    'error': 'No historical data available'
                }
                
        except Exception as e:
            print(f"❌ Error getting chart data for {event_name}: {e}")
            return {
                'indicator': 'Unknown',
                'historical_data': [],
                'data_points': 0,
                'statistics': {},
                'timeframe': f"{months} months",
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def test_historical_access(self) -> Dict:
        """Test access to historical data"""
        try:
            # Test with a short time range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            url = f"{self.base_url}/calendar/economic"
            params = {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('economicCalendar', [])
                events_with_data = [e for e in events if e.get('actual') is not None]
                
                return {
                    'status': 'success',
                    'total_events': len(events),
                    'events_with_data': len(events_with_data),
                    'message': f'Access to historical data confirmed. Found {len(events_with_data)} events with actual data.'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'API returned status {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing historical access: {str(e)}'
            }

# Create global instance
finnhub_historical = FinnhubHistoricalService()
