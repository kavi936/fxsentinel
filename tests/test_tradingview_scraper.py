#!/usr/bin/env python3
"""
Test TradingView Economic Calendar Scraper
"""

import sys
import os
sys.path.append('backend')

from services.tradingview_economic_calendar import tradingview_economic_calendar
from datetime import datetime, timedelta

def test_tradingview_scraper():
    print('🧪 TESTING TRADINGVIEW ECONOMIC CALENDAR SCRAPER')
    print('=' * 60)
    
    # Test with current week
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f'Date Range: {start_date} to {end_date}')
    print()
    
    # Clear cache to force fresh data
    tradingview_economic_calendar.clear_cache()
    
    # Test the scraper
    events = tradingview_economic_calendar.get_economic_events(start_date, end_date)
    
    print(f'\n📊 RESULTS:')
    print(f'Total events found: {len(events)}')
    
    if events:
        print(f'\n📋 SAMPLE EVENTS:')
        for i, event in enumerate(events[:5]):  # Show first 5
            print(f'{i+1}. {event["title"]}')
            print(f'   Date: {event["date"]} | Impact: {event["impact"]} | Country: {event["country"]}')
            print(f'   Currency: {event["currency"]} | Status: {event["status"]}')
            print()
    else:
        print('⚠️ No events found - this might mean:')
        print('   1. TradingView API endpoints have changed')
        print('   2. Need to use Selenium for JavaScript-rendered content')
        print('   3. Need to find the correct API endpoints')
        print('   4. Rate limiting or access restrictions')
        
        print('\n🔍 NEXT STEPS:')
        print('   1. Check browser dev tools for actual API calls')
        print('   2. Implement Selenium-based scraping')
        print('   3. Try alternative data sources')

if __name__ == '__main__':
    test_tradingview_scraper()
