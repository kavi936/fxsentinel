"""
Hybrid Economic Calendar
Combines curated event schedule with AlphaVantage historical data
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class HybridEconomicCalendar:
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY_1', 'J9NZPOVTZCE1U80M')
        self.cache_file = os.path.join(os.path.dirname(__file__), '..', 'cache', 'hybrid_calendar_cache.json')
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour for AlphaVantage data
        self._load_cache()
        print("🚀 Hybrid Economic Calendar initialized")
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
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
        Get economic events from curated calendar with AlphaVantage historical data
        
        Returns:
            List of economic calendar events with real dates and historical values
        """
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"📅 Fetching hybrid calendar for {start_date} to {end_date}")
        
        # Get curated events
        all_events = self._get_curated_events()
        
        # Enrich with AlphaVantage data
        enriched_events = []
        for event in all_events:
            # Check if event is in date range
            try:
                event_date_obj = datetime.strptime(event['date'], '%a, %b %d')
                event_date_obj = event_date_obj.replace(year=datetime.now().year)
                event_date_str = event_date_obj.strftime('%Y-%m-%d')
                
                if start_date <= event_date_str <= end_date:
                    # Enrich with AlphaVantage data
                    enriched_event = self._enrich_with_alpha_vantage(event)
                    enriched_events.append(enriched_event)
            except Exception as e:
                print(f"⚠️ Error processing event {event.get('title')}: {e}")
                continue
        
        print(f"✅ Returning {len(enriched_events)} enriched events")
        return enriched_events
    
    def _get_curated_events(self) -> List[Dict]:
        """
        Curated economic calendar with REAL upcoming events from ForexFactory
        Last Updated: October 11, 2025
        Source: ForexFactory Calendar
        Coverage: October 5-16, 2025 (36 events)
        """
        events = [
            # SUNDAY, OCTOBER 5
            {
                'title': 'MI Inflation Gauge m/m',
                'date': 'Sun, Oct 5',
                'time': '00:00 UTC',  # 20:00 EST + 4 hours
                'currency': 'AUD',
                'impact': 'medium',
                'actual': '0.4%',
                'forecast': 'N/A',
                'previous': '-0.3%'
            },
            {
                'title': 'ANZ Commodity Prices m/m',
                'date': 'Sun, Oct 5',
                'time': '00:00 UTC',
                'currency': 'NZD',
                'impact': 'medium',
                'actual': '-1.1%',
                'forecast': 'N/A',
                'previous': '0.7%'
            },
            
            # MONDAY, OCTOBER 6
            {
                'title': 'Unemployment Rate',
                'date': 'Mon, Oct 6',
                'time': '07:00 UTC',  # 03:00 EST + 4
                'currency': 'CHF',
                'impact': 'medium',
                'actual': '3.0%',
                'forecast': '2.9%',
                'previous': '2.9%'
            },
            {
                'title': 'Sentix Investor Confidence',
                'date': 'Mon, Oct 6',
                'time': '08:30 UTC',  # 04:30 EST + 4
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '-5.4',
                'forecast': '-7.5',
                'previous': '-9.2'
            },
            {
                'title': 'Construction PMI',
                'date': 'Mon, Oct 6',
                'time': '08:30 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': '46.2',
                'forecast': '46.1',
                'previous': '45.5'
            },
            {
                'title': 'Housing Equity Withdrawal q/q',
                'date': 'Mon, Oct 6',
                'time': '08:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-16.1B',
                'forecast': '-4.5B',
                'previous': '-4.9B'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Mon, Oct 6',
                'time': '09:00 UTC',  # 05:00 EST + 4
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '0.1%',
                'forecast': '0.1%',
                'previous': '-0.4%'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Mon, Oct 6',
                'time': '15:00 UTC',  # 11:00 EST + 4
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Mon, Oct 6',
                'time': '17:00 UTC',  # 13:00 EST + 4
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'NZIER Business Confidence',
                'date': 'Mon, Oct 6',
                'time': '21:00 UTC',  # 17:00 EST + 4
                'currency': 'NZD',
                'impact': 'medium',
                'actual': '18',
                'forecast': 'N/A',
                'previous': '22'
            },
            {
                'title': 'FOMC Member Schmid Speaks',
                'date': 'Mon, Oct 6',
                'time': '21:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Westpac Consumer Sentiment',
                'date': 'Mon, Oct 6',
                'time': '22:57 UTC',  # 18:57 EST + 4
                'currency': 'AUD',
                'impact': 'medium',
                'actual': '-3.5%',
                'forecast': 'N/A',
                'previous': '-3.1%'
            },
            {
                'title': 'Household Spending y/y',
                'date': 'Mon, Oct 6',
                'time': '23:30 UTC',  # 19:30 EST + 4
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '2.3%',
                'forecast': '1.4%',
                'previous': '1.4%'
            },
            {
                'title': 'ANZ Job Advertisements m/m',
                'date': 'Tue, Oct 7',
                'time': '00:30 UTC',  # 20:30 EST + 4 (next day UTC)
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-3.3%',
                'forecast': 'N/A',
                'previous': '-0.3%'
            },
            {
                'title': '30-y Bond Auction',
                'date': 'Tue, Oct 7',
                'time': '03:35 UTC',  # 23:35 EST + 4 (next day UTC)
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.25|3.4',
                'forecast': 'N/A',
                'previous': '3.26|3.3'
            },
            
            # TUESDAY, OCTOBER 7
            {
                'title': 'Official Cash Rate',
                'date': 'Wed, Oct 8',
                'time': '01:00 UTC',  # 21:00 EST + 4 (next day UTC)
                'currency': 'NZD',
                'impact': 'high',
                'actual': '2.50%',
                'forecast': '2.75%',
                'previous': '3.00%'
            },
            {
                'title': 'RBNZ Rate Statement',
                'date': 'Wed, Oct 8',
                'time': '01:00 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            
            # THURSDAY, OCTOBER 9
            {
                'title': 'RBA Gov Bullock Speaks',
                'date': 'Thu, Oct 9',
                'time': '22:00 UTC',  # 18:00 EST + 4
                'currency': 'AUD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Bank Lending y/y',
                'date': 'Thu, Oct 9',
                'time': '23:50 UTC',  # 19:50 EST + 4
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '3.8%',
                'forecast': '3.7%',
                'previous': '3.5%'
            },
            {
                'title': 'PPI y/y',
                'date': 'Thu, Oct 9',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '2.7%',
                'forecast': '2.5%',
                'previous': '2.7%'
            },
            
            # FRIDAY, OCTOBER 10
            {
                'title': 'Employment Change',
                'date': 'Fri, Oct 10',
                'time': '12:30 UTC',  # 08:30 EST + 4
                'currency': 'CAD',
                'impact': 'high',
                'actual': '60.4K',
                'forecast': '2.8K',
                'previous': '-65.5K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Oct 10',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '7.1%',
                'forecast': '7.2%',
                'previous': '7.1%'
            },
            {
                'title': 'FOMC Member Goolsbee Speaks',
                'date': 'Fri, Oct 10',
                'time': '13:45 UTC',  # 09:45 EST + 4
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Prelim UoM Consumer Sentiment',
                'date': 'Fri, Oct 10',
                'time': '14:00 UTC',  # 10:00 EST + 4
                'currency': 'USD',
                'impact': 'high',
                'actual': '55.0',
                'forecast': '54.1',
                'previous': '55.1'
            },
            {
                'title': 'Prelim UoM Inflation Expectations',
                'date': 'Fri, Oct 10',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '4.6%',
                'forecast': 'N/A',
                'previous': '4.7%'
            },
            
            # TUESDAY, OCTOBER 14
            {
                'title': 'Fed Chair Powell Speaks',
                'date': 'Tue, Oct 14',
                'time': '16:20 UTC',  # 12:20 EST + 4
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Tue, Oct 14',
                'time': '17:00 UTC',  # 13:00 EST + 4
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            
            # WEDNESDAY, OCTOBER 15
            {
                'title': 'RBA Gov Bullock Speaks',
                'date': 'Wed, Oct 15',
                'time': '19:45 UTC',  # 15:45 EST + 4
                'currency': 'AUD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Employment Change',
                'date': 'Thu, Oct 16',
                'time': '00:30 UTC',  # 20:30 EST + 4 (next day UTC)
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',  # Future event
                'forecast': '20.0K',  # Was in "actual"
                'previous': '-5.4K'  # Was in "forecast"
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Thu, Oct 16',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',  # Future event
                'forecast': '4.3%',  # Was in "actual"
                'previous': '4.2%'  # Was in "forecast"
            },
            
            # THURSDAY, OCTOBER 16
            {
                'title': 'GDP m/m',
                'date': 'Thu, Oct 16',
                'time': '06:00 UTC',  # 02:00 EST + 4
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',  # Future event
                'forecast': '0.1%',  # Was in "actual"
                'previous': '0.0%'  # Was in "forecast"
            },
            {
                'title': 'Core PPI m/m',
                'date': 'Thu, Oct 16',
                'time': '12:30 UTC',  # Tentative - using standard 08:30 EST + 4
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',  # Future event
                'forecast': '0.3%',  # Was in "actual"
                'previous': '-0.1%'  # Was in "forecast"
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Thu, Oct 16',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',  # Future event
                'forecast': '0.3%',  # Was in "actual"
                'previous': '0.7%'  # Was in "forecast"
            },
            {
                'title': 'PPI m/m',
                'date': 'Thu, Oct 16',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',  # Future event
                'forecast': '0.3%',  # Was in "actual"
                'previous': '-0.1%'  # Was in "forecast"
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Thu, Oct 16',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',  # Future event
                'forecast': '0.4%',  # Was in "actual"
                'previous': '0.6%'  # Was in "forecast"
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Oct 16',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            }
        ]
        
        return events
    
    def _enrich_with_alpha_vantage(self, event: Dict) -> Dict:
        """Enrich event with historical data from AlphaVantage or use provided values"""
        
        # Check if event already has actual/forecast/previous values from ForexFactory
        if 'actual' in event and 'forecast' in event and 'previous' in event:
            return self._format_event(event,
                                    previous=event.get('previous', 'N/A'),
                                    forecast=event.get('forecast', 'TBD'),
                                    actual=event.get('actual', 'TBD'))
        
        av_function = event.get('alpha_vantage_function')
        
        if not av_function:
            # No AlphaVantage data available, use placeholder
            return self._format_event(event, previous='N/A', forecast='TBD', actual='TBD')
        
        # Check cache
        cache_key = f"av_{av_function}"
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_data['timestamp'] < self.cache_ttl:
                data = cache_data['data']
                return self._format_event(event, 
                                         previous=data.get('previous', 'N/A'),
                                         forecast=data.get('forecast', 'TBD'),
                                         actual='TBD')
        
        # Fetch from AlphaVantage
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': av_function,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                second_latest = data['data'][1] if len(data['data']) > 1 else None
                
                previous_value = latest.get('value', 'N/A')
                second_value = second_latest.get('value', 'N/A') if second_latest else 'N/A'
                
                # Format values based on indicator type
                previous_formatted = self._format_value(av_function, previous_value)
                
                # Generate simple forecast (average of last 2 values or slight change)
                try:
                    if isinstance(previous_value, (int, float)) and second_value != 'N/A':
                        avg = (float(previous_value) + float(second_value)) / 2
                        forecast = self._format_value(av_function, avg)
                    else:
                        forecast = previous_formatted
                except:
                    forecast = 'TBD'
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': {'previous': previous_formatted, 'forecast': forecast},
                    'timestamp': datetime.now().timestamp()
                }
                self._save_cache()
                
                return self._format_event(event, previous=previous_formatted, 
                                         forecast=forecast, actual='TBD')
            else:
                return self._format_event(event, previous='N/A', forecast='TBD', actual='TBD')
                
        except Exception as e:
            print(f"⚠️ AlphaVantage error for {av_function}: {e}")
            return self._format_event(event, previous='N/A', forecast='TBD', actual='TBD')
    
    def _format_value(self, function: str, value) -> str:
        """Format value based on indicator type"""
        if value == 'N/A' or value is None:
            return 'N/A'
        
        try:
            num_value = float(value)
            
            # CPI, inflation - show as index value
            if function in ['CPI', 'INFLATION']:
                return f"{num_value:.1f}"
            
            # Rates - show as percentage
            elif function in ['UNEMPLOYMENT', 'FEDERAL_FUNDS_RATE']:
                return f"{num_value:.1f}%"
            
            # Payroll - show in thousands
            elif function == 'NONFARM_PAYROLL':
                return f"{int(num_value)}K"
            
            # Retail sales, durables - show in millions
            elif function in ['RETAIL_SALES', 'DURABLES']:
                return f"${num_value/1000:.1f}B"
            
            # GDP - show as percentage
            elif function == 'REAL_GDP':
                return f"{num_value:.1f}%"
            
            else:
                return str(num_value)
        except:
            return str(value)
    
    def _format_event(self, base_event: Dict, previous: str, forecast: str, actual: str) -> Dict:
        """Format event into standard calendar format"""
        # Parse the date to get YYYY-MM-DD format for frontend
        date_str = base_event['date']
        try:
            # Parse "Mon, Oct 13" format
            event_date = datetime.strptime(date_str, '%a, %b %d')
            event_date = event_date.replace(year=datetime.now().year)
            date_yyyy_mm_dd = event_date.strftime('%Y-%m-%d')
        except:
            date_yyyy_mm_dd = datetime.now().strftime('%Y-%m-%d')
        
        # Determine country from currency
        country_map = {
            'USD': 'US', 'EUR': 'EU', 'GBP': 'GB', 'JPY': 'JP',
            'AUD': 'AU', 'CAD': 'CA', 'CHF': 'CH', 'NZD': 'NZ', 'CNY': 'CN'
        }
        
        return {
            'id': f"hybrid_{hash(base_event['title'])}",
            'title': base_event['title'],
            'date': date_yyyy_mm_dd,  # YYYY-MM-DD format for frontend filtering
            'time': base_event['time'],
            'country': country_map.get(base_event.get('currency', 'USD'), 'US'),
            'currency': base_event.get('currency', 'USD'),
            'impact': base_event.get('impact', 'medium'),
            'previous': previous,
            'expected': forecast,
            'actual': actual,
            'source': 'Hybrid Calendar',
            'status': self._get_status(base_event['date']),
            'type': base_event.get('category', 'Economic Indicator'),
            'currencyPairs': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
            'description': base_event.get('description', ''),
            'raw_data': {
                'date': date_yyyy_mm_dd,
                'time': base_event['time']
            }
        }
    
    def _get_status(self, date_str: str) -> str:
        """Determine event status from date"""
        try:
            event_date = datetime.strptime(date_str, '%a, %b %d')
            event_date = event_date.replace(year=datetime.now().year)
            today = datetime.now()
            
            if event_date.date() < today.date():
                return 'completed'
            elif event_date.date() == today.date():
                return 'today'
            else:
                return 'upcoming'
        except:
            return 'upcoming'
    
    def clear_cache(self):
        """Clear AlphaVantage cache"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("🗑️ Hybrid calendar cache cleared")

# Global instance
hybrid_economic_calendar = HybridEconomicCalendar()

