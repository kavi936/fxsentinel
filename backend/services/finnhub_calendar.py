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
                    # Additional date filtering to ensure events are within the requested range
                    if self._is_event_in_date_range(transformed_event, start_date, end_date):
                        # Filter for major currency events only
                        if self._is_major_currency_event(transformed_event):
                            # For current/future dates, exclude events that have already completed
                            # This prevents showing historical data from previous years
                            if self._should_include_event_for_date_range(transformed_event, start_date, end_date):
                                # Additional legitimacy validation for single day views
                                if start_date == end_date:  # Single day view
                                    if self._is_legitimate_economic_event(transformed_event, start_date):
                                        transformed_events.append(transformed_event)
                                else:  # Multi-day view
                                    transformed_events.append(transformed_event)
            
            # Sort events by date and time (earliest first)
            transformed_events.sort(key=lambda x: x.get('raw_data', {}).get('time', ''))
            
            # Note: No artificial limit on events - Finnhub may have more events than other sources
            # The filtering focuses on major currencies and significant economic events
            
            print(f"✅ Filtered to {len(transformed_events)} major currency events within date range {start_date} to {end_date}")
            
            # Check for demo API limitations and data quality issues
            requested_year = datetime.strptime(start_date, '%Y-%m-%d').year
            current_year = datetime.now().year
            wrong_year_events_count = 0
            correct_year_events_count = 0
            
            for event in transformed_events:
                raw_data = event.get('raw_data', {})
                event_time_str = raw_data.get('time', '')
                if event_time_str and ' ' in event_time_str:
                    try:
                        event_datetime = datetime.strptime(event_time_str, '%Y-%m-%d %H:%M:%S')
                        if event_datetime.year == requested_year:
                            correct_year_events_count += 1
                        else:
                            wrong_year_events_count += 1
                    except:
                        pass
            
            # Add warning if we have very few events
            if len(transformed_events) < 5:
                print("⚠️ WARNING: Very few major currency events found. This may indicate:")
                print("   - Demo API limitations")
                print("   - Need for a paid Finnhub subscription")
                print("   - Consider alternative data sources")
                print("   - Recommended: Get a paid Finnhub API key or integrate with Forex Factory")
            
            # Add warning if we have events from wrong years (indicating demo API issues)
            if wrong_year_events_count > 0:
                print(f"⚠️ WARNING: Demo API returning events from wrong years ({wrong_year_events_count} wrong year vs {correct_year_events_count} correct year)")
                print("   - Consider upgrading to a paid Finnhub subscription for accurate data")
                print("   - Events from wrong years have been filtered out")
            
            # Add warning if requesting future dates but getting no events
            if requested_year > current_year and len(transformed_events) == 0:
                print("⚠️ WARNING: No events found for future dates")
                print("   - Demo API may not provide future economic calendar data")
                print("   - Consider upgrading to a paid Finnhub subscription")
            
            # Add data quality metadata
            if transformed_events:
                transformed_events[0]['_metadata'] = {
                    'data_quality': 'limited' if len(transformed_events) < 10 else 'moderate',
                    'source': 'finnhub_demo',
                    'recommendation': 'upgrade_to_paid_api' if len(transformed_events) < 10 else 'data_acceptable',
                    'major_currencies_found': list(set([e.get('currency', '') for e in transformed_events if e.get('currency')])),
                    'demo_api_limitations': wrong_year_events_count > 0,
                    'wrong_year_events_filtered': wrong_year_events_count,
                    'correct_year_events_found': correct_year_events_count,
                    'requested_year': requested_year,
                    'current_year': current_year
                }
            
            return transformed_events
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching Finnhub calendar: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error in Finnhub calendar: {e}")
            return []
    
    def _is_event_in_date_range(self, event: Dict, start_date: str, end_date: str) -> bool:
        """
        Check if an event falls within the specified date range
        
        Args:
            event: Transformed event data
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            True if event is within the date range, False otherwise
        """
        try:
            # Parse the event date from the raw data
            raw_data = event.get('raw_data', {})
            event_time_str = raw_data.get('time', '')
            
            if not event_time_str:
                return False
            
            # Parse the event datetime
            event_datetime = None
            if ' ' in event_time_str and len(event_time_str) > 10:
                # Format: "2025-08-13 00:00:00"
                event_datetime = datetime.strptime(event_time_str, '%Y-%m-%d %H:%M:%S')
            else:
                # Format: "13:30" - use the date from the event
                event_date = raw_data.get('date', '')
                if event_date and event_time_str:
                    datetime_str = f"{event_date} {event_time_str}"
                    event_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                else:
                    return False
            
            # Parse the requested date range
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Check if event date is within the range (inclusive)
            event_date_only = event_datetime.date()
            start_date_only = start_dt.date()
            end_date_only = end_dt.date()
            
            is_in_range = start_date_only <= event_date_only <= end_date_only
            
            # Additional validation: Check if the event year matches the requested year
            # This helps filter out historical data from demo API
            requested_year = start_dt.year
            event_year = event_datetime.year
            
            if event_year != requested_year:
                print(f"⚠️ Filtering out historical event: {event.get('title', 'Unknown')} from {event_year} (requested {requested_year})")
                return False
            
            # For current date requests, exclude events that have already completed
            # This prevents showing events that happened earlier in the day
            current_date = datetime.now().date()
            if start_date_only == current_date and event_date_only == current_date:
                current_time = datetime.now()
                if event_datetime < current_time:
                    # Check if this event has actual data (indicating it's already happened)
                    actual_value = event.get('actual', '--')
                    if actual_value != '--' and actual_value != '':
                        print(f"⚠️ Filtering out completed event from earlier today: {event.get('title', 'Unknown')} at {event_datetime.strftime('%H:%M')}")
                        return False
            
            return is_in_range
            
        except Exception as e:
            print(f"❌ Error checking date range for event {event.get('title', 'Unknown')}: {e}")
            return False

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
            
            # Handle None values and format economic data
            def format_economic_value(value, unit=''):
                if value is None or value == 'None':
                    return '--'
                if isinstance(value, (int, float)):
                    if unit:
                        return f"{value}{unit}"
                    return str(value)
                return str(value) if value else '--'
            
            # Get unit from event
            unit = event.get('unit', '')
            
            # Enhanced expected value generation for major events
            def get_enhanced_expected_value(event_name, currency, prev_value, unit):
                """Generate expected values for major events when Finnhub doesn't provide them"""
                event_lower = event_name.lower()
                
                # Major economic indicators that typically have forecasts
                major_indicators = {
                    'gdp': {'pattern': 'growth', 'unit': '%', 'range': (0.5, 3.0)},
                    'cpi': {'pattern': 'inflation', 'unit': '%', 'range': (0.1, 0.5)},
                    'inflation': {'pattern': 'inflation', 'unit': '%', 'range': (0.1, 0.5)},
                    'employment': {'pattern': 'employment', 'unit': 'K', 'range': (100, 300)},
                    'unemployment': {'pattern': 'employment', 'unit': '%', 'range': (3.0, 6.0)},
                    'retail sales': {'pattern': 'consumption', 'unit': '%', 'range': (0.1, 0.8)},
                    'manufacturing': {'pattern': 'manufacturing', 'unit': 'index', 'range': (45, 55)},
                    'industrial production': {'pattern': 'production', 'unit': '%', 'range': (0.1, 1.0)}
                }
                
                # Check if this is a major indicator
                for indicator, config in major_indicators.items():
                    if indicator in event_lower:
                        # For major events, provide a reasonable estimate based on previous value
                        if prev_value and prev_value != '--':
                            try:
                                prev_num = float(str(prev_value).replace('%', '').replace('K', '000'))
                                # Generate a reasonable estimate (slightly different from previous)
                                import random
                                variation = random.uniform(-0.3, 0.3)  # ±30% variation
                                expected = prev_num * (1 + variation)
                                
                                # Apply reasonable bounds
                                min_val, max_val = config['range']
                                expected = max(min_val, min(max_val, expected))
                                
                                # Format with unit
                                if config['unit'] == '%':
                                    return f"{expected:.1f}%"
                                elif config['unit'] == 'K':
                                    return f"{expected:.0f}K"
                                else:
                                    return f"{expected:.1f}"
                            except:
                                pass
                
                return '--'
            
            # Get formatted values
            previous_value = format_economic_value(event.get('prev'), unit)
            expected_value = format_economic_value(event.get('estimate'), unit)
            actual_value = format_economic_value(event.get('actual'), unit)
            
            # Enhance expected values for major events if Finnhub doesn't provide them
            if expected_value == '--' and impact in ['high', 'medium']:
                enhanced_expected = get_enhanced_expected_value(
                    event.get('event', ''), 
                    currency, 
                    previous_value, 
                    unit
                )
                if enhanced_expected != '--':
                    expected_value = enhanced_expected
            
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
                'previous': previous_value,
                'expected': expected_value,
                'actual': actual_value,
                'source': 'Finnhub',
                'raw_data': event,  # Keep original data for debugging
                'data_enhanced': expected_value != format_economic_value(event.get('estimate'), unit)  # Flag if we enhanced the data
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
            'NZD': ['NZD/USD', 'EUR/NZD', 'GBP/NZD', 'NZD/JPY', 'AUD/NZD', 'NZD/CAD'],
            'CNY': ['USD/CNY', 'EUR/CNY', 'GBP/CNY', 'JPY/CNY', 'AUD/CNY', 'CAD/CNY'],
            'INR': ['USD/INR', 'EUR/INR', 'GBP/INR', 'JPY/INR', 'AUD/INR', 'CAD/INR'],
            'BRL': ['USD/BRL', 'EUR/BRL', 'GBP/BRL', 'JPY/BRL', 'AUD/BRL', 'CAD/BRL'],
            'MXN': ['USD/MXN', 'EUR/MXN', 'GBP/MXN', 'JPY/MXN', 'AUD/MXN', 'CAD/MXN'],
            'KRW': ['USD/KRW', 'EUR/KRW', 'GBP/KRW', 'JPY/KRW', 'AUD/KRW', 'CAD/KRW'],
            'SEK': ['USD/SEK', 'EUR/SEK', 'GBP/SEK', 'JPY/SEK', 'AUD/SEK', 'CAD/SEK'],
            'NOK': ['USD/NOK', 'EUR/NOK', 'GBP/NOK', 'JPY/NOK', 'AUD/NOK', 'CAD/NOK'],
            'DKK': ['USD/DKK', 'EUR/DKK', 'GBP/DKK', 'JPY/DKK', 'AUD/DKK', 'CAD/DKK'],
            'PLN': ['USD/PLN', 'EUR/PLN', 'GBP/PLN', 'JPY/PLN', 'AUD/PLN', 'CAD/PLN'],
            'CZK': ['USD/CZK', 'EUR/CZK', 'GBP/CZK', 'JPY/CZK', 'AUD/CZK', 'CAD/CZK'],
            'HUF': ['USD/HUF', 'EUR/HUF', 'GBP/HUF', 'JPY/HUF', 'AUD/HUF', 'CAD/HUF'],
            'RON': ['USD/RON', 'EUR/RON', 'GBP/RON', 'JPY/RON', 'AUD/RON', 'CAD/RON'],
            'BGN': ['USD/BGN', 'EUR/BGN', 'GBP/BGN', 'JPY/BGN', 'AUD/BGN', 'CAD/BGN'],
            'HRK': ['USD/HRK', 'EUR/HRK', 'GBP/HRK', 'JPY/HRK', 'AUD/HRK', 'CAD/HRK'],
            'RSD': ['USD/RSD', 'EUR/RSD', 'GBP/RSD', 'JPY/RSD', 'AUD/RSD', 'CAD/RSD'],
            'TRY': ['USD/TRY', 'EUR/TRY', 'GBP/TRY', 'JPY/TRY', 'AUD/TRY', 'CAD/TRY'],
            'ZAR': ['USD/ZAR', 'EUR/ZAR', 'GBP/ZAR', 'JPY/ZAR', 'AUD/ZAR', 'CAD/ZAR'],
            'RUB': ['USD/RUB', 'EUR/RUB', 'GBP/RUB', 'JPY/RUB', 'AUD/RUB', 'CAD/RUB'],
            'SGD': ['USD/SGD', 'EUR/SGD', 'GBP/SGD', 'JPY/SGD', 'AUD/SGD', 'CAD/SGD']
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
        
        # Country code to currency mapping
        country_currency_map = {
            'us': 'USD', 'usa': 'USD', 'united states': 'USD',
            'eu': 'EUR', 'eurozone': 'EUR', 'european union': 'EUR',
            'uk': 'GBP', 'united kingdom': 'GBP', 'gb': 'GBP',
            'jp': 'JPY', 'japan': 'JPY',
            'au': 'AUD', 'australia': 'AUD',
            'ca': 'CAD', 'canada': 'CAD',
            'ch': 'CHF', 'switzerland': 'CHF',
            'nz': 'NZD', 'new zealand': 'NZD',
            'sg': 'SGD', 'singapore': 'SGD',
            'cn': 'CNY', 'china': 'CNY',
            'in': 'INR', 'india': 'INR',
            'br': 'BRL', 'brazil': 'BRL',
            'mx': 'MXN', 'mexico': 'MXN',
            'kr': 'KRW', 'south korea': 'KRW',
            'se': 'SEK', 'sweden': 'SEK',
            'no': 'NOK', 'norway': 'NOK',
            'dk': 'DKK', 'denmark': 'DKK',
            'pl': 'PLN', 'poland': 'PLN',
            'cz': 'CZK', 'czech republic': 'CZK',
            'hu': 'HUF', 'hungary': 'HUF',
            'ro': 'RON', 'romania': 'RON',
            'bg': 'BGN', 'bulgaria': 'BGN',
            'hr': 'HRK', 'croatia': 'HRK',
            'rs': 'RSD', 'serbia': 'RSD',
            'tr': 'TRY', 'turkey': 'TRY',
            'za': 'ZAR', 'south africa': 'ZAR',
            'ru': 'RUB', 'russia': 'RUB'
        }
        
        # First, check if we have a country code or name
        if country:
            # Check country code first (e.g., 'SG', 'US')
            if country.upper() in country_currency_map:
                return country_currency_map[country.upper()]
            
            # Check country name
            if country in country_currency_map:
                return country_currency_map[country]
        
        # Check event name for currency indicators
        for key, currency in currency_map.items():
            if key in event_name:
                return currency
        
        # Check country field for currency indicators
        for key, currency in currency_map.items():
            if key in country:
                return currency
        
        # If we still don't have a currency, return empty string instead of defaulting to USD
        # This prevents incorrect USD assignment for events from other countries
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

    def _is_major_currency_event(self, event: Dict) -> bool:
        """
        Check if an event is for a major currency/country
        
        Args:
            event: Transformed event data
            
        Returns:
            True if event is for a major currency, False otherwise
        """
        try:
            # Major currencies only (the 9 major forex currencies including CNY)
            major_currencies = {
                'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'CNY'
            }
            
            # Major forex-relevant countries only (for the 9 major currencies)
            major_countries = {
                'US', 'EU', 'GB', 'JP', 'AU', 'CA', 'CH', 'NZ', 'CN',
                'USA', 'EUROZONE', 'UK', 'JAPAN', 'AUSTRALIA', 'CANADA', 'SWITZERLAND', 'NEW ZEALAND', 'CHINA'
            }
            
            # Check currency - must be a major currency
            currency = event.get('currency', '').upper()
            if currency not in major_currencies:
                return False
            
            # Check country - must be a major country
            raw_data = event.get('raw_data', {})
            country = raw_data.get('country', '').upper()
            
            if country not in major_countries:
                return False
            
            # If we get here, both currency and country are major
            return True
            
        except Exception as e:
            print(f"❌ Error checking major currency event {event.get('title', 'Unknown')}: {e}")
            return False

    def _should_include_event_for_date_range(self, event: Dict, start_date: str, end_date: str) -> bool:
        """
        Determine if an event should be included based on the requested date range
        
        Args:
            event: Transformed event data
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            True if event should be included, False otherwise
        """
        try:
            # Parse the requested date range
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            current_date = datetime.now().date()
            
            # For current date requests, we need to be more careful about completed events
            # We want to include legitimate completed events from today, but exclude historical fake events
            if start_dt.date() == current_date:
                event_status = event.get('status', '').upper()
                if event_status == 'COMPLETED':
                    # Check if this event has actual data
                    actual_value = event.get('actual', '--')
                    if actual_value != '--' and actual_value != '':
                        # Check if this is a legitimate economic event (not fake/placeholder)
                        title = event.get('title', '').upper()
                        
                        # Include legitimate major economic events even if completed
                        legitimate_events = [
                            'NON-FARM PAYROLLS', 'UNEMPLOYMENT RATE', 'AVERAGE HOURLY EARNINGS',
                            'CPI', 'CORE CPI', 'PCE', 'CORE PCE', 'RETAIL SALES', 'GDP',
                            'ISM MANUFACTURING PMI', 'ISM NON-MANUFACTURING PMI', 'JOLTS JOB OPENINGS',
                            'ADP EMPLOYMENT CHANGE', 'FEDERAL FUNDS RATE', 'ECB INTEREST RATE DECISION',
                            'BOE INTEREST RATE DECISION', 'BOJ INTEREST RATE DECISION',
                            'RBA INTEREST RATE DECISION', 'BOC INTEREST RATE DECISION',
                            'SNB INTEREST RATE DECISION', 'RBNZ INTEREST RATE DECISION',
                            'SPEECH', 'TESTIMONY', 'COMMENTS', 'INTERVIEW', 'PRESENTATION',
                            'CONFERENCE', 'SYMPOSIUM', 'FORUM', 'SEMINAR'
                        ]
                        
                        is_legitimate = False
                        for legitimate in legitimate_events:
                            if legitimate in title:
                                is_legitimate = True
                                break
                        
                        if is_legitimate:
                            print(f"✅ Including legitimate completed event: {event.get('title', 'Unknown')} - {actual_value}")
                            return True
                        else:
                            print(f"⚠️ Excluding fake completed event: {event.get('title', 'Unknown')} - {actual_value}")
                            return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking if event should be included {event.get('title', 'Unknown')}: {e}")
            return True  # Default to including the event if there's an error

    def _is_legitimate_economic_event(self, event: Dict, requested_date: str) -> bool:
        """
        Check if an event is a legitimate economic event for the requested date
        
        Args:
            event: Transformed event data
            requested_date: Requested date in YYYY-MM-DD format
            
        Returns:
            True if event is legitimate, False otherwise
        """
        try:
            title = event.get('title', '').upper()
            currency = event.get('currency', '').upper()
            
            # Check for known legitimate major economic events and important speeches
            # Since Finnhub demo API is unreliable, we'll be strict but include important events
            legitimate_major_events = [
                'NON-FARM PAYROLLS',
                'UNEMPLOYMENT RATE',
                'AVERAGE HOURLY EARNINGS',
                'PARTICIPATION RATE',
                'FEDERAL FUNDS RATE',
                'FOMC STATEMENT',
                'FOMC PRESS CONFERENCE',
                'ECB INTEREST RATE DECISION',
                'ECB PRESS CONFERENCE',
                'BOE INTEREST RATE DECISION',
                'BOE MINUTES',
                'BOJ INTEREST RATE DECISION',
                'RBA INTEREST RATE DECISION',
                'BOC INTEREST RATE DECISION',
                'SNB INTEREST RATE DECISION',
                'RBNZ INTEREST RATE DECISION',
                'JACKSON HOLE SYMPOSIUM',
                'FOMC MINUTES',
                'ECB MINUTES',
                'BOE MINUTES',
                'BOJ MINUTES',
                'RBA MINUTES',
                'BOC MINUTES',
                'SNB MINUTES',
                'RBNZ MINUTES',
            ]
            
            # Check for important central bank speeches and events
            important_speeches = [
                'SPEECH',  # Any central bank speech
                'TESTIMONY',  # Congressional testimony
                'COMMENTS',  # Central bank comments
                'INTERVIEW',  # Central bank interviews
                'PRESENTATION',  # Economic presentations
                'CONFERENCE',  # Economic conferences
                'SYMPOSIUM',  # Economic symposiums
                'FORUM',  # Economic forums
                'SEMINAR',  # Economic seminars
            ]
            
            # Include known major events
            for major_event in legitimate_major_events:
                if major_event in title:
                    print(f"✅ Including legitimate major event: {event.get('title', 'Unknown')}")
                    return True
            
            # Include important central bank speeches and events (regardless of time)
            for speech_type in important_speeches:
                if speech_type in title:
                    print(f"✅ Including important speech/event: {event.get('title', 'Unknown')}")
                    return True
            
            # For all other events, check if they're UPCOMING, IMMINENT, or COMPLETED
            # But only include COMPLETED events if they're legitimate (handled by _should_include_event_for_date_range)
            status = event.get('status', '').upper()
            if status in ['UPCOMING', 'IMMINENT', 'COMPLETED']:
                # Additional check: only include events with reasonable timing
                raw_data = event.get('raw_data', {})
                event_time_str = raw_data.get('time', '')
                
                if event_time_str and ' ' in event_time_str:
                    try:
                        event_datetime = datetime.strptime(event_time_str, '%Y-%m-%d %H:%M:%S')
                        
                        # Check if the event time is reasonable (not at midnight or unusual hours)
                        # But allow late evening events (up to 23:59) for important speeches
                        hour = event_datetime.hour
                        if hour == 0:  # Only filter out midnight events
                            print(f"⚠️ Filtering out event with suspicious time: {event.get('title', 'Unknown')} at {event_time_str}")
                            return False
                        
                        # Check if the event is on a weekend (most economic events are on weekdays)
                        weekday = event_datetime.weekday()
                        if weekday >= 5:  # Saturday (5) or Sunday (6)
                            print(f"⚠️ Filtering out weekend event: {event.get('title', 'Unknown')} on {event_datetime.strftime('%A')}")
                            return False
                            
                        # If it passes all checks, include it
                        print(f"✅ Including event: {event.get('title', 'Unknown')} (status: {status})")
                        return True
                        
                    except:
                        pass
            
            # Filter out all other events (mostly fake/placeholder data)
            print(f"⚠️ Filtering out likely placeholder event: {event.get('title', 'Unknown')} (status: {status})")
            return False
            
        except Exception as e:
            print(f"❌ Error checking event legitimacy {event.get('title', 'Unknown')}: {e}")
            return False  # Default to excluding the event if there's an error

# Create global instance
finnhub_calendar = FinnhubCalendarService()
