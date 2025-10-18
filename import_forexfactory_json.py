#!/usr/bin/env python3
"""
ForexFactory JSON Import Script
Automatically imports events from ForexFactory JSON export into hybrid_economic_calendar.py
"""

import json
import sys
from datetime import datetime, timedelta

def parse_forexfactory_json(json_file_path):
    """Parse ForexFactory JSON export and format for our calendar"""
    
    with open(json_file_path, 'r') as f:
        ff_data = json.load(f)
    
    print(f'📊 Parsing {len(ff_data)} events from ForexFactory export...')
    
    # Filter for HIGH and MEDIUM impact only (skip LOW and holidays)
    filtered_events = [e for e in ff_data if e.get('impact') in ['High', 'Medium']]
    
    print(f'✅ Found {len(filtered_events)} HIGH/MEDIUM impact events')
    
    # Convert to our format
    formatted_events = []
    
    for event in filtered_events:
        # Parse ISO date: "2025-10-14T12:20:00-04:00"
        date_str = event.get('date', '')
        if not date_str:
            continue
        
        try:
            # Parse datetime (EDT timezone -04:00)
            dt = datetime.fromisoformat(date_str)
            
            # Convert to UTC (EDT is UTC-4, so add 4 hours)
            dt_utc = dt.replace(tzinfo=None) + timedelta(hours=4)
            
            # Format for display
            formatted_date = dt.strftime('%a, %b %d')
            formatted_time = dt_utc.strftime('%H:%M UTC')
            date_yyyy_mm_dd = dt.strftime('%Y-%m-%d')
            
            formatted = {
                'title': event.get('title', ''),
                'date': formatted_date,
                'date_yyyy_mm_dd': date_yyyy_mm_dd,
                'time': formatted_time,
                'currency': event.get('country', 'USD'),
                'impact': event.get('impact', 'Low').lower(),
                'forecast': event.get('forecast', '') or 'N/A',
                'previous': event.get('previous', '') or 'N/A',
                'actual': 'TBD'  # Future events
            }
            
            formatted_events.append(formatted)
            
        except Exception as e:
            print(f'⚠️ Error parsing event {event.get("title")}: {e}')
            continue
    
    return formatted_events

def generate_python_code(events):
    """Generate Python code for hybrid_economic_calendar.py"""
    
    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for e in events:
        by_date[e['date_yyyy_mm_dd']].append(e)
    
    python_code = []
    
    for date in sorted(by_date.keys()):
        day_events = by_date[date]
        dt = datetime.strptime(date, '%Y-%m-%d')
        
        # Add date comment
        python_code.append(f"\n            # {dt.strftime('%A, %B %d').upper()}")
        
        for event in day_events:
            event_code = f"""            {{
                'title': '{event['title']}',
                'date': '{event['date']}',
                'time': '{event['time']}',
                'currency': '{event['currency']}',
                'impact': '{event['impact']}',
                'actual': '{event['actual']}',
                'forecast': '{event['forecast']}',
                'previous': '{event['previous']}'
            }},"""
            
            python_code.append(event_code)
    
    return '\n'.join(python_code)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 import_forexfactory_json.py <json_file>')
        print('Example: python3 import_forexfactory_json.py backend/ff_calendar_thisweek.json')
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # Parse events
    events = parse_forexfactory_json(json_file)
    
    # Generate Python code
    code = generate_python_code(events)
    
    print('\n' + '='*70)
    print('GENERATED PYTHON CODE:')
    print('='*70)
    print(code)
    print('\n' + '='*70)
    print(f'✅ Generated code for {len(events)} events')
    print()
    print('📋 NEXT STEPS:')
    print('1. Copy the code above')
    print('2. Open backend/services/hybrid_economic_calendar.py')
    print('3. Find the _get_curated_events() method (line ~77)')
    print('4. Paste this code into the events list')
    print('5. Save and restart backend')
    print()
    print('Or I can do it automatically - just say the word! 🚀')

