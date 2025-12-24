#!/usr/bin/env python3
"""
Helper script to manually add actual values to calendar events.
Useful when API data is not available or events are not in the database.
"""

import json
import sys
from datetime import datetime, timezone

def add_actual_values_interactive(file_path: str):
    """Interactively add actual values to events"""
    try:
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        print(f"📅 Found {len(events)} events in file\n")
        
        # Filter to past events without actual values
        past_events = []
        for event in events:
            event_dt = parse_event_date(event.get('date', ''))
            if event_dt:
                now = datetime.now(timezone.utc)
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=timezone.utc)
                
                if event_dt < now:
                    actual = event.get('actual', '')
                    if not actual or actual in ['', '--', None]:
                        past_events.append(event)
        
        if not past_events:
            print("✅ All past events already have actual values, or no past events found.")
            return
        
        print(f"Found {len(past_events)} past events without actual values:\n")
        
        updated_count = 0
        for i, event in enumerate(past_events, 1):
            print(f"\n[{i}/{len(past_events)}] {event.get('title')}")
            print(f"   Date: {event.get('date')}")
            print(f"   Country: {event.get('country')}")
            print(f"   Forecast: {event.get('forecast', 'N/A')}")
            print(f"   Previous: {event.get('previous', 'N/A')}")
            
            actual = input(f"   Enter actual value (or press Enter to skip): ").strip()
            
            if actual:
                event['actual'] = actual
                updated_count += 1
                print(f"   ✅ Updated with: {actual}")
            else:
                print(f"   ⏭️  Skipped")
        
        # Save updated JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Updated {updated_count} events")
        print(f"💾 Saved to {file_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def parse_event_date(date_str: str):
    """Parse event date from various formats"""
    try:
        if 'T' in date_str:
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_actual_values_manual.py <json_file>")
        sys.exit(1)
    
    add_actual_values_interactive(sys.argv[1])

