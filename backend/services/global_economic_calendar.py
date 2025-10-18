import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class GlobalEconomicCalendar:
    def __init__(self):
        self.forexfactory_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        self.cache = {}
        self.cache_file = os.path.join(os.path.dirname(__file__), '..', 'cache', 'global_economic_calendar_cache.json')
        self.cache_ttl = 6 * 60 * 60  # 6 hours cache - longer to prevent rate limiting
        self._load_cache()
        print("🚀 Global Economic Calendar initialized (ForexFactory)")
        
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
    
    def get_economic_events(self, start_date: str, end_date: str) -> List[Dict]:
        """Get economic events from ForexFactory (global coverage)"""
        cache_key = f"events_{start_date}_{end_date}"
        
        # Check cache first
        has_valid_cache = False
        has_stale_cache = False
        stale_cache_data = None
        
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            cache_age = datetime.now().timestamp() - cache_data['timestamp']
            
            if cache_age < self.cache_ttl:
                print(f"📋 Using cached global events for {start_date} to {end_date} (age: {cache_age/3600:.1f}h)")
                return cache_data['data']
            else:
                # Cache exists but expired - keep it as fallback
                has_stale_cache = True
                stale_cache_data = cache_data['data']
                print(f"⚠️ Cache expired (age: {cache_age/3600:.1f}h), fetching fresh data...")
        
        print(f"🔄 Fetching fresh global events for {start_date} to {end_date}")
        
        try:
            # Get ForexFactory data (covers 190+ countries) with retry logic
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'cross-site',
                        'Referer': 'https://www.forexfactory.com/'
                    }
                    
                    response = requests.get(self.forexfactory_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        events = self._parse_global_events(data, start_date, end_date)
                        
                        # Cache the results
                        self.cache[cache_key] = {
                            'data': events,
                            'timestamp': datetime.now().timestamp()
                        }
                        self._save_cache()
                        
                        print(f"✅ Found {len(events)} global economic events")
                        return events
                    elif response.status_code == 429:
                        print(f"⚠️ Rate limited (429) - attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            print("❌ Max retries reached for rate limiting")
                            # Return stale cache if available
                            if has_stale_cache:
                                print(f"⚠️ Rate limited, returning stale cache ({len(stale_cache_data)} events)")
                                return stale_cache_data
                            return []
                    else:
                        print(f"⚠️ ForexFactory API error: {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        else:
                            # Return stale cache if available
                            if has_stale_cache:
                                print(f"⚠️ API failed, returning stale cache ({len(stale_cache_data)} events)")
                                return stale_cache_data
                            return []
                            
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Request error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        # Return stale cache if available
                        if has_stale_cache:
                            print(f"⚠️ Requests failed, returning stale cache ({len(stale_cache_data)} events)")
                            return stale_cache_data
                        return []
                
        except Exception as e:
            print(f"❌ Error fetching global economic data: {e}")
            # Return stale cache if available
            if has_stale_cache:
                print(f"⚠️ Exception occurred, returning stale cache ({len(stale_cache_data)} events)")
                return stale_cache_data
            return []
    
    def _parse_global_events(self, data: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        """Parse global events into our standard format"""
        events = []
        
        try:
            for item in data:
                try:
                    # ForexFactory JSON format: {"title": "...", "country": "...", "date": "...", "impact": "...", "forecast": "...", "previous": "..."}
                    title = item.get('title', '')
                    country = item.get('country', 'USD')
                    date_str = item.get('date', '')
                    impact = item.get('impact', 'Low')
                    forecast = item.get('forecast', '')
                    previous = item.get('previous', '')
                    
                    if not title or not date_str:
                        continue
                    
                    # Parse the ISO date format: "2025-10-05T16:00:00-04:00"
                    event_date = self._parse_iso_date(date_str)
                    event_time = self._extract_time_from_iso(date_str)
                    
                    # Check if event is within date range
                    if start_date <= event_date <= end_date:
                        event = {
                            'id': f"global_{hash(f'{title}_{date_str}')}",
                            'title': title,
                            'date': event_date,
                            'time': event_time,
                            'country': self._get_country_from_currency(country),
                            'currency': country,
                            'impact': self._map_impact_level(impact),
                            'actual': 'TBD',  # ForexFactory doesn't provide actual in this feed
                            'expected': forecast if forecast != '' else 'N/A',
                            'previous': previous if previous != '' else 'N/A',
                            'source': 'ForexFactory',
                            'status': self._get_status_from_date(event_date),
                            'type': self._get_event_type_from_title(title),
                            'currencyPairs': self._get_currency_pairs(country)
                        }
                        
                        events.append(event)
                        
                except Exception as e:
                    print(f"⚠️ Error parsing global event: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error parsing global data: {e}")
            
        return events
    
    def _parse_iso_date(self, date_str: str) -> str:
        """Parse ISO date format"""
        try:
            # ForexFactory uses ISO format: "2025-10-05T16:00:00-04:00"
            if 'T' in date_str:
                # Extract just the date part
                date_part = date_str.split('T')[0]
                return date_part
            elif '-' in date_str and len(date_str) == 10:
                return date_str  # Already in YYYY-MM-DD format
            else:
                return datetime.now().strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_time_from_iso(self, date_str: str) -> str:
        """Extract time from ISO date string"""
        try:
            if 'T' in date_str:
                # Extract time part from "2025-10-05T16:00:00-04:00"
                time_part = date_str.split('T')[1].split('-')[0]  # Remove timezone
                return time_part[:5]  # Return HH:MM format
            else:
                return '12:00'
        except:
            return '12:00'
    
    def _get_country_from_currency(self, currency: str) -> str:
        """Get country from currency code"""
        currency_country_map = {
            'USD': 'US',
            'EUR': 'EU',
            'GBP': 'GB',
            'JPY': 'JP',
            'CAD': 'CA',
            'AUD': 'AU',
            'CHF': 'CH',
            'NZD': 'NZ',
            'CNY': 'CN',
            'BRL': 'BR',
            'SEK': 'SE',
            'NOK': 'NO',
            'HKD': 'HK',
            'SGD': 'SG',
            'KRW': 'KR',
            'INR': 'IN',
            'MXN': 'MX',
            'ZAR': 'ZA',
            'RUB': 'RU',
            'TRY': 'TR'
        }
        return currency_country_map.get(currency, currency)
    
    def _map_impact_level(self, impact: str) -> str:
        """Map ForexFactory impact to our levels (lowercase for CSS consistency)"""
        impact_lower = str(impact).lower()
        if impact_lower in ['high', 'red', '3', 'critical']:
            return 'high'
        elif impact_lower in ['medium', 'orange', '2', 'yellow']:
            return 'medium'
        elif impact_lower in ['holiday']:
            return 'holiday'
        else:
            return 'low'
    
    def _get_status_from_date(self, date_str: str) -> str:
        """Determine status from date"""
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if event_date < today:
                return 'completed'
            elif event_date == today:
                return 'today'
            else:
                return 'upcoming'
        except:
            return 'upcoming'
    
    def _get_event_type_from_title(self, title: str) -> str:
        """Determine event type from title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['interest rate', 'fed', 'ecb', 'boe', 'rate decision', 'cash rate']):
            return 'Interest Rate'
        elif any(word in title_lower for word in ['cpi', 'inflation', 'price index', 'ppi']):
            return 'Economic Indicator'
        elif any(word in title_lower for word in ['gdp', 'gross domestic']):
            return 'Economic Indicator'
        elif any(word in title_lower for word in ['unemployment', 'employment', 'payroll', 'jobs', 'claims']):
            return 'Employment'
        elif any(word in title_lower for word in ['retail sales', 'consumer spending']):
            return 'Retail Sales'
        elif any(word in title_lower for word in ['industrial', 'manufacturing', 'factory']):
            return 'Manufacturing'
        elif any(word in title_lower for word in ['speaks', 'speech', 'testimony']):
            return 'Central Bank Speech'
        elif any(word in title_lower for word in ['pmi', 'confidence', 'sentiment']):
            return 'Business Sentiment'
        elif any(word in title_lower for word in ['trade balance', 'exports', 'imports']):
            return 'Trade Balance'
        elif any(word in title_lower for word in ['bond auction', 'treasury']):
            return 'Government Debt'
        elif any(word in title_lower for word in ['holiday']):
            return 'Holiday'
        else:
            return 'Economic Indicator'
    
    def _get_currency_pairs(self, currency: str) -> List[str]:
        """Get relevant currency pairs for the currency (max 4 pairs)"""
        currency_pairs = {
            'USD': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
            'EUR': ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF'],
            'GBP': ['GBPUSD', 'EURGBP', 'GBPJPY', 'GBPCHF'],
            'JPY': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY'],
            'CHF': ['USDCHF', 'EURCHF', 'GBPCHF', 'AUDCHF'],
            'CAD': ['USDCAD', 'EURCAD', 'GBPCAD', 'AUDCAD'],
            'AUD': ['AUDUSD', 'EURAUD', 'GBPAUD', 'AUDJPY'],
            'NZD': ['NZDUSD', 'EURNZD', 'GBPNZD', 'NZDJPY'],
            'CNY': ['USDCNY', 'EURCNY', 'GBPCNY', 'JPYCNY'],
            'BRL': ['USDBRL', 'EURBRL', 'GBPBRL', 'JPYBRL'],
            'SEK': ['USDSEK', 'EURSEK', 'GBPSEK', 'JPYSEK'],
            'NOK': ['USDNOK', 'EURNOK', 'GBPNOK', 'JPYNOK'],
            'HKD': ['USDHKD', 'EURHKD', 'GBPHKD', 'JPYHKD'],
            'SGD': ['USDSGD', 'EURSGD', 'GBPSGD', 'JPYSGD'],
            'KRW': ['USDKRW', 'EURKRW', 'GBPKRW', 'JPYKRW'],
            'INR': ['USDINR', 'EURINR', 'GBPINR', 'JPYINR'],
            'MXN': ['USDMXN', 'EURMXN', 'GBPMXN', 'JPYMXN'],
            'ZAR': ['USDZAR', 'EURZAR', 'GBPZAR', 'JPYZAR'],
            'RUB': ['USDRUB', 'EURRUB', 'GBPRUB', 'JPYRUB'],
            'TRY': ['USDTRY', 'EURTRY', 'GBPTRY', 'JPYTRY']
        }
        
        return currency_pairs.get(currency, ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'])
    
    def get_event_summary(self, start_date: str, end_date: str) -> Dict:
        """Get summary statistics for events in date range"""
        events = self.get_economic_events(start_date, end_date)
        
        if not events:
            return {
                'total_events': 0,
                'countries': {},
                'impact_levels': {},
                'event_types': {},
                'high_impact_events': []
            }
        
        # Calculate statistics
        countries = {}
        impact_levels = {}
        event_types = {}
        high_impact_events = []
        
        for event in events:
            # Count by country
            country = event['country']
            countries[country] = countries.get(country, 0) + 1
            
            # Count by impact
            impact = event['impact']
            impact_levels[impact] = impact_levels.get(impact, 0) + 1
            
            # Count by type
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Collect high impact events
            if impact == 'High':
                high_impact_events.append({
                    'title': event['title'],
                    'date': event['date'],
                    'time': event['time'],
                    'country': event['country'],
                    'currency': event['currency']
                })
        
        return {
            'total_events': len(events),
            'countries': dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)),
            'impact_levels': dict(sorted(impact_levels.items(), key=lambda x: x[1], reverse=True)),
            'event_types': dict(sorted(event_types.items(), key=lambda x: x[1], reverse=True)),
            'high_impact_events': high_impact_events
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("🗑️ Global economic calendar cache cleared")

# Create global instance
global_economic_calendar = GlobalEconomicCalendar()
