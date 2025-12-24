#!/usr/bin/env python3
"""
Script to update calendar events JSON file with actual release data from CSV files.
Reads CSV files from Trading Economics (downloaded from Google Sheets) and matches
them to calendar events in the JSON file.
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

class CalendarCSVUpdater:
    """Updates calendar events with actual values from CSV files"""
    
    def __init__(self, csv_dir: str):
        self.csv_dir = csv_dir
        self.csv_data = {}
        self.load_all_csv_files()
    
    def load_all_csv_files(self):
        """Load all CSV files from the directory"""
        csv_path = Path(self.csv_dir)
        if not csv_path.exists():
            print(f"⚠️ CSV directory not found: {self.csv_dir}")
            return
        
        csv_files = list(csv_path.glob("Economies_Indicators - *.csv"))
        print(f"📁 Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            try:
                self.load_csv_file(csv_file)
            except Exception as e:
                print(f"⚠️ Error loading {csv_file.name}: {e}")
    
    def load_csv_file(self, csv_file: Path):
        """Load a single CSV file and parse its data"""
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Extract country and indicator from filename
            filename = csv_file.stem  # Remove .csv extension
            # Format: "Economies_Indicators - US Non Farm Payrolls"
            parts = filename.replace("Economies_Indicators - ", "").split(" ", 1)
            if len(parts) < 2:
                return
            
            country_code = parts[0]  # US, EUR, UK, JP, etc.
            indicator_name = parts[1]  # Non Farm Payrolls, Inflation Rate, etc.
            
            # Read all rows
            for row in reader:
                date_str = row.get('date_of_release', '').strip()
                release_value = row.get('release_value', '').strip()
                unit = row.get('unit', '').strip()
                
                if not date_str or not release_value:
                    continue
                
                # Create key for lookup
                key = (country_code, indicator_name, date_str)
                
                # Format the value with unit if needed
                formatted_value = self.format_value(release_value, unit)
                
                if key not in self.csv_data:
                    self.csv_data[key] = formatted_value
                else:
                    # Keep the most recent if duplicate
                    self.csv_data[key] = formatted_value
        
        print(f"   ✅ Loaded {csv_file.name}")
    
    def format_value(self, value: str, unit: str) -> str:
        """Format economic value consistently"""
        value = str(value).strip()
        if not value or value == 'None':
            return ''
        
        # Remove any existing formatting
        value = value.replace(',', '')
        
        # If value already has unit indicators, return as is
        if any(unit_char in value for unit_char in ['%', 'K', 'M', 'B', 'T']):
            return value
        
        # Try to format based on unit
        try:
            num_value = float(value)
            
            if unit == '%' or '%' in unit:
                return f"{num_value:.1f}%"
            elif unit == 'K' or 'K' in unit:
                return f"{num_value:.0f}K"
            elif unit == 'M' or 'M' in unit:
                return f"{num_value:.1f}M"
            elif unit == 'B' or 'B' in unit:
                return f"{num_value:.1f}B"
            else:
                # Default: try to determine if it's a percentage
                if abs(num_value) < 10:
                    return f"{num_value:.1f}%"
                else:
                    return f"{num_value:.1f}"
        except (ValueError, TypeError):
            return value
    
    def parse_csv_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from CSV format (e.g., 'September, 2025', 'Q3, 2025')"""
        try:
            # Handle monthly format: "September, 2025"
            if ',' in date_str:
                parts = date_str.split(',')
                if len(parts) == 2:
                    month_str = parts[0].strip()
                    year_str = parts[1].strip()
                    
                    # Try to parse as month name
                    month_names = {
                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                    }
                    
                    if month_str in month_names:
                        year = int(year_str)
                        month = month_names[month_str]
                        # Use first day of month as approximation
                        return datetime(year, month, 1)
            
            # Handle quarterly format: "Q3, 2025"
            if date_str.startswith('Q'):
                parts = date_str.split(',')
                if len(parts) == 2:
                    quarter_str = parts[0].strip()
                    year_str = parts[1].strip()
                    
                    quarter = int(quarter_str[1])  # Extract number from "Q3"
                    year = int(year_str)
                    
                    # Map quarter to month (start of quarter)
                    quarter_months = {1: 1, 2: 4, 3: 7, 4: 10}
                    month = quarter_months.get(quarter, 1)
                    
                    return datetime(year, month, 1)
            
            return None
        except Exception as e:
            print(f"⚠️ Error parsing date '{date_str}': {e}")
            return None
    
    def parse_event_date(self, date_str: str) -> Optional[datetime]:
        """Parse event date from JSON format"""
        try:
            if 'T' in date_str:
                # Remove timezone offset for parsing
                if '+' in date_str or (date_str.count('-') > 2 and date_str[-6] == '-'):
                    if date_str.endswith('Z'):
                        date_str = date_str[:-1]
                    else:
                        tz_index = date_str.rfind('-')
                        if tz_index > 10:
                            date_str = date_str[:tz_index]
                return datetime.fromisoformat(date_str.replace('Z', ''))
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None
    
    def match_country(self, json_country: str) -> str:
        """Map JSON country code to CSV country code"""
        country_map = {
            'USD': 'US',
            'EUR': 'EUR',
            'GBP': 'UK',
            'JPY': 'JP',
            'CNY': 'CN',
            'CAD': 'CA',
            'AUD': 'AU',
            'CHF': 'CH',
            'NZD': 'NZ',
        }
        return country_map.get(json_country, json_country)
    
    def match_indicator(self, event_title: str, country: str) -> Optional[str]:
        """Map event title to indicator name in CSV files"""
        title_lower = event_title.lower()
        
        # Country-specific indicator name mappings (based on actual CSV filenames)
        country_indicators = {
            'US': {
                'non farm payrolls': 'Non Farm Payrolls',
                'non-farm payrolls': 'Non Farm Payrolls',
                'nfp': 'Non Farm Payrolls',
                'adp': 'Non Farm Payrolls',  # ADP is related to payrolls
                'unemployment': 'Unemployment Rate',
                'unemployment rate': 'Unemployment Rate',
                'inflation': 'Inflation',
                'cpi': 'Inflation',
                'core inflation': 'Core Inflation YOY',
                'core cpi': 'Core Inflation YOY',
                'gdp': 'GDP Growth Rate',
                'gdp growth': 'GDP Growth Rate',
                'prelim gdp': 'GDP Growth Rate',
                'final gdp': 'GDP Growth Rate',
                'interest rate': 'Interest Rates',
                'federal funds rate': 'Interest Rates',
                'fomc': 'Interest Rates',
            },
            'EUR': {
                'inflation': 'Inflation Rate',
                'cpi': 'Inflation Rate',
                'core inflation': 'Core Inflation YoY',
                'gdp': 'GDP Annual Growth Rate',
                'gdp growth': 'GDP Annual Growth Rate',
                'unemployment': 'Unemployment Rate',
                'interest rate': 'Interest Rate',
                'ecb': 'Interest Rate',
                'current account': 'Current Account',
            },
            'UK': {
                'inflation': 'Inflation Rate',
                'cpi': 'Inflation Rate',
                'core inflation': 'Core Inflation Rate YoY',
                'gdp': 'GDP Annual Growth Rate',
                'gdp growth': 'GDP Annual Growth Rate',
                'final gdp': 'GDP Annual Growth Rate',
                'prelim gdp': 'GDP Annual Growth Rate',
                'unemployment': 'Unemployment Rate',
                'interest rate': 'Interest Rate',
                'boe': 'Interest Rate',
                'current account': 'Current Account',
                'wage': 'Wage Growth',
            },
            'JP': {
                'inflation': 'Inflation Rate YoY',
                'cpi': 'Inflation Rate YoY',
                'core inflation': 'Core Inflation Rate YoY',
                'core cpi': 'Core Inflation Rate YoY',
                'gdp': 'GDP Annual Growth Rate',
                'gdp growth': 'GDP Annual Growth Rate',
                'unemployment': 'Unemployment Rate',
                'interest rate': 'Interest Rate',
                'boj': 'Interest Rate',
                'current account': 'Current Account',
            },
        }
        
        # Get country-specific mappings
        country_map = country_indicators.get(country, {})
        
        # Try exact match first
        for key, indicator in country_map.items():
            if key in title_lower:
                return indicator
        
        # Try generic patterns if no exact match
        if 'gdp' in title_lower:
            if country == 'US':
                return 'GDP Growth Rate'
            elif country in ['EUR', 'UK', 'JP']:
                return 'GDP Annual Growth Rate'
        
        if 'inflation' in title_lower or 'cpi' in title_lower:
            if 'core' in title_lower:
                if country == 'US':
                    return 'Core Inflation YOY'
                elif country == 'EUR':
                    return 'Core Inflation YoY'
                elif country in ['UK', 'JP']:
                    return 'Core Inflation Rate YoY'
            else:
                if country == 'US':
                    return 'Inflation'
                elif country == 'EUR':
                    return 'Inflation Rate'
                elif country == 'UK':
                    return 'Inflation Rate'
                elif country == 'JP':
                    return 'Inflation Rate YoY'
        
        if 'unemployment' in title_lower:
            return 'Unemployment Rate'
        
        if 'current account' in title_lower:
            if country in ['EUR', 'UK', 'JP']:
                return 'Current Account'
        
        if 'interest' in title_lower or 'rate decision' in title_lower or 'monetary policy' in title_lower:
            if country == 'US':
                return 'Interest Rates'
            elif country in ['EUR', 'UK', 'JP']:
                return 'Interest Rate'
        
        return None
    
    def find_matching_csv_value(self, event: Dict) -> Optional[str]:
        """Find matching actual value from CSV data for an event"""
        event_title = event.get('title', '')
        event_country = event.get('country', '')
        event_date = event.get('date', '')
        
        # Map country
        csv_country = self.match_country(event_country)
        
        # Map indicator
        indicator = self.match_indicator(event_title, csv_country)
        if not indicator:
            return None
        
        # Parse event date
        event_dt = self.parse_event_date(event_date)
        if not event_dt:
            return None
        
        # Find all CSV entries for this country+indicator combination
        matching_keys = []
        for key in self.csv_data.keys():
            csv_c, csv_ind, csv_date = key
            if csv_c == csv_country and csv_ind == indicator:
                matching_keys.append((csv_date, self.csv_data[key]))
        
        if not matching_keys:
            return None
        
        # Parse CSV dates and find the closest match to event date
        best_match = None
        best_date_diff = None
        
        for csv_date_str, csv_value in matching_keys:
            csv_dt = self.parse_csv_date(csv_date_str)
            if not csv_dt:
                continue
            
            # Calculate date difference (in days)
            date_diff = abs((event_dt - csv_dt).days)
            
            # For monthly data, accept matches within 45 days (data released in same or next month)
            # For quarterly data, accept matches within 90 days
            max_diff = 90 if 'Q' in csv_date_str else 45
            
            if date_diff <= max_diff:
                if best_date_diff is None or date_diff < best_date_diff:
                    best_match = csv_value
                    best_date_diff = date_diff
        
        return best_match
    
    def update_calendar_file(self, json_file: str) -> bool:
        """Update calendar events in JSON file with actual values from CSV"""
        try:
            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            if not isinstance(events, list):
                print("❌ JSON file should contain an array of events")
                return False
            
            print(f"\n📅 Found {len(events)} events in JSON file")
            print(f"📊 Loaded {len(self.csv_data)} data points from CSV files\n")
            
            updated_count = 0
            matched_count = 0
            
            for event in events:
                # Only update if actual is empty or missing
                current_actual = event.get('actual', '')
                if current_actual and current_actual not in ['', '--', None]:
                    continue
                
                # Try to find matching CSV value
                actual_value = self.find_matching_csv_value(event)
                
                if actual_value:
                    event['actual'] = actual_value
                    updated_count += 1
                    matched_count += 1
                    print(f"✅ {event.get('title')} ({event.get('country')}) -> {actual_value}")
                else:
                    # Check if we at least found a potential match (indicator exists but date doesn't)
                    event_title = event.get('title', '')
                    event_country = event.get('country', '')
                    csv_country = self.match_country(event_country)
                    indicator = self.match_indicator(event_title, csv_country)
                    
                    if indicator:
                        # Found indicator but no date match
                        pass
                    else:
                        # No indicator match at all
                        pass
            
            # Write updated JSON back to file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 Summary:")
            print(f"   Events updated: {updated_count}")
            print(f"   Total events: {len(events)}")
            print(f"💾 Saved to {json_file}")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ File not found: {json_file}")
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
    
    parser = argparse.ArgumentParser(description='Update calendar events with actual values from CSV files')
    parser.add_argument('json_file', help='Path to JSON file with calendar events')
    parser.add_argument('--csv-dir', default='data/raw', help='Directory containing CSV files (default: data/raw)')
    args = parser.parse_args()
    
    # Convert to absolute paths
    json_file = os.path.abspath(args.json_file)
    csv_dir = os.path.abspath(args.csv_dir)
    
    updater = CalendarCSVUpdater(csv_dir)
    success = updater.update_calendar_file(json_file)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

