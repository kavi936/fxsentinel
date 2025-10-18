#!/usr/bin/env python3
"""
Test Static Economic Calendar
"""

import sys
import os
sys.path.append('backend')

from services.static_economic_calendar import static_economic_calendar
from datetime import datetime, timedelta

def test_static_economic_calendar():
    print('🧪 TESTING STATIC ECONOMIC CALENDAR')
    print('=' * 60)
    
    # Test with current week
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f'Date Range: {start_date} to {end_date}')
    print()
    
    # Test the calendar
    events = static_economic_calendar.get_economic_events(start_date, end_date)
    
    print(f'\n📊 RESULTS:')
    print(f'Total events found: {len(events)}')
    
    if events:
        print(f'\n📋 SAMPLE EVENTS:')
        for i, event in enumerate(events[:10]):  # Show first 10
            print(f'{i+1}. {event["title"]}')
            print(f'   Date: {event["date"]} | Time: {event["time"]} | Impact: {event["impact"]}')
            print(f'   Country: {event["country"]} | Currency: {event["currency"]}')
            print(f'   Expected: {event["expected"]} | Previous: {event["previous"]}')
            print()
            
        # Get summary statistics
        summary = static_economic_calendar.get_event_summary(start_date, end_date)
        
        print(f'\n📈 SUMMARY STATISTICS:')
        print(f'Total Events: {summary["total_events"]}')
        
        print(f'\n🌍 TOP COUNTRIES:')
        for country, count in list(summary["countries"].items())[:5]:
            print(f'   {country}: {count} events')
            
        print(f'\n⚡ IMPACT BREAKDOWN:')
        for impact, count in summary["impact_levels"].items():
            print(f'   {impact}: {count} events')
            
        print(f'\n📊 EVENT TYPES:')
        for event_type, count in list(summary["event_types"].items())[:5]:
            print(f'   {event_type}: {count} events')
            
        if summary["high_impact_events"]:
            print(f'\n🚨 HIGH IMPACT EVENTS:')
            for event in summary["high_impact_events"][:5]:
                print(f'   • {event["title"]} ({event["country"]}) - {event["date"]} {event["time"]}')
            
    else:
        print('⚠️ No events found!')

if __name__ == '__main__':
    test_static_economic_calendar()
