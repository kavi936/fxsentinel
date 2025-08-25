import requests
import os
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
import re

class FinnhubHistoricalService:
    """Service for fetching historical economic data from Finnhub"""
    
    def __init__(self):
        # Use environment variable only, no hardcoded keys
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY environment variable not set")
        self.base_url = "https://finnhub.io/api/v1"
        self.session = requests.Session()
        self.session.headers.update({'X-Finnhub-Token': self.api_key})
    
    def _parse_economic_value(self, value) -> Optional[float]:
        """
        Parse economic data value from various formats
        
        Args:
            value: Raw value from API (could be string, number, or None)
            
        Returns:
            Parsed float value or None if invalid
        """
        if value is None:
            return None
            
        # If it's already a number, return it
        if isinstance(value, (int, float)):
            return float(value)
            
        # If it's a string, try to parse it
        if isinstance(value, str):
            # Remove any whitespace
            value = value.strip()
            
            # Handle percentage values (e.g., "2.3 %", "2.3%")
            if '%' in value:
                # Extract the numeric part
                numeric_part = re.sub(r'[^\d.-]', '', value)
                try:
                    return float(numeric_part)
                except ValueError:
                    return None
            
            # Handle plain numeric strings
            try:
                return float(value)
            except ValueError:
                return None
                
        return None

    def _deduplicate_data(self, historical_data: List[Dict]) -> List[Dict]:
        """
        Remove duplicate data points for the same date, keeping the most recent/relevant one
        
        Args:
            historical_data: List of historical data points
            
        Returns:
            Deduplicated list of historical data points
        """
        if not historical_data:
            return []
        
        print(f"📊 Starting deduplication with {len(historical_data)} points")
        
        # Group by date
        date_groups = {}
        for point in historical_data:
            date = point.get('date')
            if date:
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(point)
        
        # For each date, select the best data point
        deduplicated = []
        duplicates_removed = 0
        
        for date, points in date_groups.items():
            if len(points) == 1:
                deduplicated.append(points[0])
            else:
                # Multiple points for same date - select the best one
                # Score each point based on data quality
                best_point = max(points, key=lambda p: 
                    (p.get('expected') is not None,  # Prefer points with expected values
                     p.get('previous') is not None,  # Prefer points with previous values
                     p.get('event_name', '').lower().count('official'),  # Prefer official releases
                     len(p.get('country', '')),  # Prefer more specific country data
                     p.get('event_name', '').lower().count('final'),  # Prefer final releases
                     p.get('event_name', '').lower().count('preliminary') == 0))  # Avoid preliminary data
                deduplicated.append(best_point)
                duplicates_removed += len(points) - 1
        
        # Sort by date (oldest first)
        deduplicated.sort(key=lambda x: x.get('date', ''))
        
        print(f"📊 Deduplication complete: {len(historical_data)} -> {len(deduplicated)} points (removed {duplicates_removed} duplicates)")
        return deduplicated

    def _validate_data_point(self, value: float, indicator: str) -> bool:
        """
        Validate if a data point is reasonable for the given indicator
        
        Args:
            value: The numeric value to validate
            indicator: The economic indicator name
            
        Returns:
            True if the value is reasonable, False otherwise
        """
        if value is None or not isinstance(value, (int, float)):
            return False
            
        # Define reasonable ranges for different indicators (much stricter)
        indicator_ranges = {
            'cpi': (-10, 30),  # CPI can be negative (deflation) but not extreme
            'inflation': (-10, 30),
            'gdp': (-20, 20),  # GDP growth rates (more realistic range)
            'unemployment': (0, 30),  # Unemployment rates (more realistic)
            'employment': (-50, 100),  # Employment changes
            'retail sales': (-20, 50),  # Retail sales changes
            'interest rate': (-5, 25),  # Interest rates
            'manufacturing': (0, 70)  # PMI and manufacturing indices
        }
        
        indicator_lower = indicator.lower()
        for key, (min_val, max_val) in indicator_ranges.items():
            if key in indicator_lower:
                return min_val <= value <= max_val
        
        # Default validation for unknown indicators (much stricter)
        return -50 <= value <= 100

    def get_historical_data_for_indicator(self, indicator_name: str, months: int = 24) -> List[Dict]:
        """
        Get historical data for a specific economic indicator
        
        Args:
            indicator_name: Name of the economic indicator
            months: Number of months of historical data
            
        Returns:
            List of historical data points
        """
        if not self.api_key:
            print("❌ Finnhub API key not configured")
            return []

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
            
            print(f"📊 Total events from Finnhub: {len(events)}")
            
            # Filter events for the specific indicator with more flexible matching
            indicator_events = []
            indicator_lower = indicator_name.lower()
            
            # Create a list of possible matches for different indicators
            indicator_matches = {
                'cpi': ['cpi', 'inflation', 'consumer price index'],
                'gdp': ['gdp', 'gross domestic product'],
                'unemployment': ['unemployment', 'jobless', 'employment'],
                'employment': ['employment', 'non farm payrolls', 'payrolls'],
                'retail sales': ['retail sales', 'retail'],
                'inflation': ['inflation', 'cpi', 'consumer price'],
                'interest rate': ['interest rate', 'rate decision'],
                'manufacturing': ['manufacturing', 'pmi', 'industrial production']
            }
            
            # Get the list of keywords to match for this indicator
            keywords = indicator_matches.get(indicator_lower, [indicator_lower])
            
            for event in events:
                event_name = event.get('event', '').lower()
                country = event.get('country', '').lower()
                
                # Check if this event matches our indicator keywords
                matches = False
                for keyword in keywords:
                    if keyword in event_name:
                        matches = True
                        break
                
                # Also check if the indicator name is in the event name (backward compatibility)
                if not matches and indicator_lower in event_name:
                    matches = True
                
                if matches:
                    # Only include events with actual data
                    if event.get('actual') is not None:
                        indicator_events.append(event)
                        print(f"✅ Matched event: {event.get('event')} ({event.get('country')}) - {event.get('actual')}")
            
            print(f"📊 Found {len(indicator_events)} matching events for {indicator_name}")
            
            # Sort by date (most recent first)
            indicator_events.sort(key=lambda x: x.get('time', ''), reverse=True)
            
            # Transform to chart-friendly format
            historical_data = []
            filtered_count = 0
            
            for event in indicator_events:
                try:
                    # Parse the date from time field
                    time_str = event.get('time', '')
                    if time_str and ' ' in time_str:
                        date_str = time_str.split(' ')[0]
                        event_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # Parse and normalize the actual value
                        raw_actual = event.get('actual')
                        parsed_actual = self._parse_economic_value(raw_actual)
                        
                        # Validate the data point
                        if parsed_actual is not None and self._validate_data_point(parsed_actual, indicator_name):
                            historical_data.append({
                                'date': event_date.strftime('%Y-%m-%d'),
                                'value': parsed_actual,
                                'previous': self._parse_economic_value(event.get('prev')),
                                'expected': self._parse_economic_value(event.get('estimate')),
                                'unit': event.get('unit', ''),
                                'event_name': event.get('event'),
                                'country': event.get('country', ''),
                                'raw_value': raw_actual  # Keep original for debugging
                            })
                        else:
                            filtered_count += 1
                            print(f"⚠️ Skipping invalid data point: {raw_actual} for {indicator_name}")
                except Exception as e:
                    print(f"⚠️ Error parsing event date: {e}")
                    continue
            
            # Deduplicate the data
            historical_data = self._deduplicate_data(historical_data)
            
            print(f"✅ Found {len(historical_data)} valid historical data points for {indicator_name} (filtered out {filtered_count} invalid points)")
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
