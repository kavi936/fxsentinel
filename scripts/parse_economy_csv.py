#!/usr/bin/env python3
"""
Parse economy indicator CSV files and convert to JSON format
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

def parse_date(date_str):
    """Convert date from 'December 10, 2025', 'September, 2025', or 'Q2, 2025' format to ISO '2025-12-10'"""
    try:
        date_str = date_str.strip('"').strip()
        # Try full date format first (e.g., "December 10, 2025")
        try:
            dt = datetime.strptime(date_str, '%B %d, %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            # Try month-year only format (e.g., "September, 2025") - use first day of month
            try:
                dt = datetime.strptime(date_str, '%B, %Y')
                return dt.strftime('%Y-%m-01')
            except ValueError:
                # Try quarter format (e.g., "Q2, 2025") - use middle of quarter
                try:
                    import re
                    match = re.match(r'Q(\d), (\d{4})', date_str)
                    if match:
                        quarter = int(match.group(1))
                        year = int(match.group(2))
                        # Map quarter to month (middle of quarter)
                        quarter_months = {1: 2, 2: 5, 3: 8, 4: 11}  # Feb, May, Aug, Nov
                        month = quarter_months[quarter]
                        return f'{year}-{month:02d}-15'
                except (ValueError, AttributeError):
                    pass
                # Try alternative format
                try:
                    dt = datetime.strptime(date_str, '%B %Y')
                    return dt.strftime('%Y-%m-01')
                except ValueError:
                    pass
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}", file=sys.stderr)
        return date_str

def parse_economy_csv(csv_path):
    """Parse a single economy indicator CSV file"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        return None
    
    # Extract metadata from first data row
    first_row = rows[0]
    country = first_row['indicator_country']
    indicator_name = first_row['indicator_name']
    unit = first_row['unit']
    current_value = first_row['current value']
    as_of = first_row['date_of_release']
    
    # Collect all historical data points
    history = []
    seen_dates = set()
    
    # Add current value entry (use release_value if available, otherwise current_value)
    first_release_value = first_row.get('release_value', '').strip()
    value_to_use = first_release_value if first_release_value else current_value
    
    if as_of and value_to_use:
        iso_date = parse_date(as_of)
        if iso_date not in seen_dates:
            try:
                history.append({
                    'date': iso_date,
                    'value': float(value_to_use)
                })
                seen_dates.add(iso_date)
            except ValueError:
                pass
    
    # Add historical data from subsequent rows
    for row in rows[1:]:
        date_str = row.get('date_of_release', '').strip('"').strip()
        value_str = row.get('release_value', '').strip()
        
        if date_str and value_str:
            # Fix obvious date errors (future dates that should be past)
            # If we see August 31, 2025 with a high rate (5.5), it's likely 2024
            if 'August 31, 2025' in date_str:
                try:
                    val = float(value_str)
                    if val >= 5.0:  # High rates were in 2024, not 2025
                        date_str = 'August 31, 2024'
                except ValueError:
                    pass
            
            iso_date = parse_date(date_str)
            if iso_date and iso_date not in seen_dates:
                try:
                    history.append({
                        'date': iso_date,
                        'value': float(value_str)
                    })
                    seen_dates.add(iso_date)
                except ValueError:
                    pass
    
    # Sort by date (oldest first)
    history.sort(key=lambda x: x['date'])
    
    # Include ALL data points (component will handle collapsed vs expanded view)
    chart_data = history
    
    # Get the latest value for current value display
    latest_value = history[-1]['value'] if history else float(value_to_use) if value_to_use else 0
    latest_date = history[-1]['date'] if history else parse_date(as_of)
    
    # Format current value based on unit
    if unit and 'K' in unit.upper():
        # For thousands (like NFP), format as "119K" instead of percentage
        current_value_str = f"{latest_value:.0f}K" if latest_value >= 0 else f"{latest_value:.0f}K"
    else:
        # Default to percentage format
        current_value_str = f"{latest_value}%"
    
    # Determine indicator ID from filename or name
    csv_filename = Path(csv_path).stem.lower()
    indicator_name_lower = indicator_name.lower()
    
    if 'core inflation' in csv_filename or 'core inflation' in indicator_name_lower:
        indicator_id = 'core-inflation-YoY'
    elif 'inflation' in csv_filename or 'inflation' in indicator_name_lower:
        indicator_id = 'inflation-YoY'
    elif 'unemployment' in csv_filename or 'unemployment' in indicator_name_lower:
        indicator_id = 'unemployment'
    elif 'non farm' in csv_filename or 'non farm' in indicator_name_lower or 'nonfarm' in indicator_name_lower or 'payroll' in indicator_name_lower:
        indicator_id = 'nonfarm-payrolls'
    elif 'gdp' in csv_filename or 'gdp' in indicator_name_lower:
        indicator_id = 'gdp-growth'
    elif 'interest' in csv_filename or 'interest' in indicator_name_lower or ('rate' in indicator_name_lower and 'gdp' not in indicator_name_lower and 'unemployment' not in indicator_name_lower):
        indicator_id = 'interest-rate'
    else:
        indicator_id = 'interest-rate'  # Default
    
    # Create result structure
    result = {
        country: {
            'indicators': {
                indicator_id: {
                    'currentValue': current_value_str,
                    'asOf': latest_date,
                    'chartData': [item['value'] for item in chart_data],
                    'chartDates': [item['date'] for item in chart_data],
                    'source': 'Federal Reserve' if country == 'US' else 'Official Source',
                    'notes': f'{indicator_name} - {unit}'
                }
            }
        }
    }
    
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 parse_economy_csv.py <csv_file>", file=sys.stderr)
        sys.exit(1)
    
    csv_path = sys.argv[1]
    result = parse_economy_csv(csv_path)
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Error: Could not parse CSV file", file=sys.stderr)
        sys.exit(1)

