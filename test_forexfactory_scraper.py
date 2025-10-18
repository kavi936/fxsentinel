#!/usr/bin/env python3
"""
Test ForexFactory Scraper
"""

import sys
import os
sys.path.append('backend')

from services.forexfactory_scraper import forexfactory_scraper
from datetime import datetime, timedelta

def test_forexfactory_scraper():
    print('🧪 TESTING FOREXFACTORY SCRAPER')
    print('=' * 60)
    
    # Test with current week
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f'Date Range: {start_date} to {end_date}')
    print()
    
    # Clear cache to force fresh data
    forexfactory_scraper.clear_cache()
    
    # Test the scraper
    events = forexfactory_scraper.get_economic_events(start_date, end_date)
    
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
            
        # Show breakdown by country
        countries = {}
        for event in events:
            country = event['country']
            countries[country] = countries.get(country, 0) + 1
            
        print(f'\n🌍 EVENTS BY COUNTRY:')
        for country, count in sorted(countries.items()):
            print(f'   {country}: {count} events')
            
        # Show breakdown by impact
        impacts = {}
        for event in events:
            impact = event['impact']
            impacts[impact] = impacts.get(impact, 0) + 1
            
        print(f'\n⚡ EVENTS BY IMPACT:')
        for impact, count in sorted(impacts.items()):
            print(f'   {impact}: {count} events')
            
    else:
        print('⚠️ No events found!')

if __name__ == '__main__':
    test_forexfactory_scraper()
