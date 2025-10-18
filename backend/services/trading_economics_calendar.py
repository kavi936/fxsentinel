"""
Trading Economics Economic Calendar Service
Free tier using guest credentials: guest:guest
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

class TradingEconomicsCalendar:
    def __init__(self):
        # Trading Economics allows guest access with guest:guest credentials
        # This provides limited but free access to economic calendar data
        self.base_url = "https://api.tradingeconomics.com"
        self.credentials = "guest:guest"  # Free guest access
        self.cache = {}
        self.cache_file = os.path.join(os.path.dirname(__file__), '..', 'cache', 'trading_economics_cache.json')
        self.cache_ttl = 3600  # 1 hour cache
        self._load_cache()
        print("🚀 Trading Economics Calendar initialized (Guest Access)")
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"📁 Loaded cache with {len(self.cache)} entries")
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def get_economic_events(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get economic events from Trading Economics
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of economic calendar events
        """
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        cache_key = f"events_{start_date}_{end_date}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            cache_age = datetime.now().timestamp() - cache_data['timestamp']
            
            if cache_age < self.cache_ttl:
                print(f"📋 Using cached events for {start_date} to {end_date} (age: {cache_age/60:.1f}min)")
                return cache_data['data']
            else:
                print(f"⚠️ Cache expired (age: {cache_age/3600:.1f}h), fetching fresh data...")
        
        print(f"🔄 Fetching events from Trading Economics for {start_date} to {end_date}")
        
        try:
            # Trading Economics API endpoint for calendar
            # Guest access is limited but sufficient for basic calendar data
            url = f"{self.base_url}/calendar"
            
            params = {
                'c': self.credentials,
                'd1': start_date,
                'd2': end_date
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data or len(data) == 0:
                    print("⚠️ No events returned from Trading Economics")
                    return []
                
                # Parse and transform events
                events = self._parse_events(data, start_date, end_date)
                
                # Cache the results
                self.cache[cache_key] = {
                    'data': events,
                    'timestamp': datetime.now().timestamp()
                }
                self._save_cache()
                
                print(f"✅ Found {len(events)} events from Trading Economics")
                return events
                
            elif response.status_code == 429:
                print("⚠️ Rate limited by Trading Economics")
                return []
            else:
                print(f"⚠️ Trading Economics API error: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return []
        except Exception as e:
            print(f"❌ Error fetching Trading Economics data: {e}")
            return []
    
    def _parse_events(self, data: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        """Parse Trading Economics events into our standard format"""
        events = []
        
        try:
            for item in data:
                try:
                    # Extract basic info
                    title = item.get('Event', '')
                    country = item.get('Country', '')
                    date_str = item.get('Date', '')
                    category = item.get('Category', '')
                    
                    if not title or not date_str:
                        continue
                    
                    # Parse date
                    event_date = self._parse_date(date_str)
                    if not event_date:
                        continue
                    
                    event_date_str = event_date.strftime('%Y-%m-%d')
                    
                    # Check if event is within date range
                    if not (start_date <= event_date_str <= end_date):
                        continue
                    
                    # Get currency from country
                    currency = self._get_currency_from_country(country)
                    
                    # Determine impact level
                    impact = self._determine_impact(title, category)
                    
                    # Get time
                    event_time = event_date.strftime('%H:%M')
                    
                    # Format display date
                    display_date = event_date.strftime('%a, %b %d')
                    
                    # Get actual, forecast, and previous values
                    actual = self._format_value(item.get('Actual'))
                    forecast = self._format_value(item.get('Forecast'))
                    previous = self._format_value(item.get('Previous'))
                    
                    event = {
                        'id': f"te_{item.get('CalendarId', hash(title))}",
                        'title': title,
                        'date': display_date,
                        'time': f"{event_time} UTC",
                        'country': self._map_country_code(country),
                        'currency': currency,
                        'impact': impact,
                        'actual': actual,
                        'expected': forecast,
                        'previous': previous,
                        'source': 'Trading Economics',
                        'status': self._get_status(event_date),
                        'type': self._get_event_type(title, category),
                        'currencyPairs': self._get_currency_pairs(currency),
                        'raw_data': item
                    }
                    
                    events.append(event)
                    
                except Exception as e:
                    print(f"⚠️ Error parsing event: {e}")
                    continue
            
            # Sort by date/time
            events.sort(key=lambda x: x.get('raw_data', {}).get('Date', ''))
            
        except Exception as e:
            print(f"❌ Error parsing events: {e}")
        
        return events
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from Trading Economics format"""
        try:
            # Format: "2025-04-11T00:00:00" or similar ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None
    
    def _get_currency_from_country(self, country: str) -> str:
        """Map country to currency"""
        currency_map = {
            'United States': 'USD',
            'Euro Area': 'EUR',
            'United Kingdom': 'GBP',
            'Japan': 'JPY',
            'Australia': 'AUD',
            'Canada': 'CAD',
            'Switzerland': 'CHF',
            'New Zealand': 'NZD',
            'China': 'CNY',
            'Germany': 'EUR',
            'France': 'EUR',
            'Italy': 'EUR',
            'Spain': 'EUR',
            'Netherlands': 'EUR'
        }
        return currency_map.get(country, 'USD')
    
    def _map_country_code(self, country: str) -> str:
        """Map country name to 2-letter code"""
        country_code_map = {
            'United States': 'US',
            'Euro Area': 'EU',
            'United Kingdom': 'GB',
            'Japan': 'JP',
            'Australia': 'AU',
            'Canada': 'CA',
            'Switzerland': 'CH',
            'New Zealand': 'NZ',
            'China': 'CN',
            'Germany': 'DE',
            'France': 'FR',
            'Italy': 'IT',
            'Spain': 'ES'
        }
        return country_code_map.get(country, country[:2].upper())
    
    def _determine_impact(self, title: str, category: str) -> str:
        """Determine impact level from title and category"""
        title_lower = title.lower()
        
        high_impact_keywords = [
            'gdp', 'interest rate', 'unemployment', 'non-farm', 'nfp',
            'cpi', 'inflation', 'retail sales', 'fed', 'ecb', 'boe'
        ]
        
        medium_impact_keywords = [
            'manufacturing', 'pmi', 'industrial production',
            'trade balance', 'consumer confidence', 'housing'
        ]
        
        for keyword in high_impact_keywords:
            if keyword in title_lower:
                return 'high'
        
        for keyword in medium_impact_keywords:
            if keyword in title_lower:
                return 'medium'
        
        return 'low'
    
    def _format_value(self, value) -> str:
        """Format economic value for display"""
        if value is None or value == '':
            return 'TBD'
        return str(value)
    
    def _get_status(self, event_date: datetime) -> str:
        """Determine event status"""
        now = datetime.now()
        
        if event_date < now:
            return 'completed'
        elif event_date.date() == now.date():
            return 'today'
        else:
            return 'upcoming'
    
    def _get_event_type(self, title: str, category: str) -> str:
        """Determine event type"""
        title_lower = title.lower()
        
        if 'interest rate' in title_lower or 'monetary policy' in title_lower:
            return 'Interest Rate'
        elif 'cpi' in title_lower or 'inflation' in title_lower:
            return 'Economic Indicator'
        elif 'gdp' in title_lower:
            return 'Economic Indicator'
        elif 'employment' in title_lower or 'unemployment' in title_lower or 'payroll' in title_lower:
            return 'Employment'
        elif 'retail sales' in title_lower:
            return 'Retail Sales'
        elif 'manufacturing' in title_lower or 'industrial' in title_lower:
            return 'Manufacturing'
        else:
            return 'Economic Indicator'
    
    def _get_currency_pairs(self, currency: str) -> List[str]:
        """Get relevant currency pairs (max 4)"""
        currency_pairs = {
            'USD': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
            'EUR': ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF'],
            'GBP': ['GBPUSD', 'EURGBP', 'GBPJPY', 'GBPCHF'],
            'JPY': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY'],
            'AUD': ['AUDUSD', 'EURAUD', 'GBPAUD', 'AUDJPY'],
            'CAD': ['USDCAD', 'EURCAD', 'GBPCAD', 'AUDCAD'],
            'CHF': ['USDCHF', 'EURCHF', 'GBPCHF', 'AUDCHF'],
            'NZD': ['NZDUSD', 'EURNZD', 'GBPNZD', 'NZDJPY'],
            'CNY': ['USDCNY', 'EURCNY', 'GBPCNY', 'JPYCNY']
        }
        
        return currency_pairs.get(currency, ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'])
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("🗑️ Trading Economics cache cleared")

# Create global instance
trading_economics_calendar = TradingEconomicsCalendar()

