#!/usr/bin/env python3
"""
Test script for the hybrid economic calendar service
This script tests all the free API sources to ensure they work
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.hybrid_economic_calendar import hybrid_economic_calendar

def test_individual_sources():
    """Test each source individually"""
    print("🧪 TESTING INDIVIDUAL SOURCES")
    print("=" * 50)
    
    # Test 1: ForexFactory
    print("\n1. Testing ForexFactory...")
    try:
        ff_events = hybrid_economic_calendar.get_forex_factory_events()
        print(f"✅ ForexFactory: {len(ff_events)} events")
        if ff_events:
            print(f"   Sample event: {ff_events[0].get('title', 'No title')}")
    except Exception as e:
        print(f"❌ ForexFactory failed: {e}")
    
    # Test 2: Financial Modeling Prep
    print("\n2. Testing Financial Modeling Prep...")
    try:
        fmp_events = hybrid_economic_calendar.get_fmp_events(
            datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        )
        print(f"✅ FMP: {len(fmp_events)} events")
        if fmp_events:
            print(f"   Sample event: {fmp_events[0].get('title', 'No title')}")
    except Exception as e:
        print(f"❌ FMP failed: {e}")
    
    # Test 3: Trading Economics
    print("\n3. Testing Trading Economics...")
    try:
        te_events = hybrid_economic_calendar.get_trading_economics_events()
        print(f"✅ Trading Economics: {len(te_events)} events")
        if te_events:
            print(f"   Sample event: {te_events[0].get('title', 'No title')}")
    except Exception as e:
        print(f"❌ Trading Economics failed: {e}")
    
    # Test 4: FRED API
    print("\n4. Testing FRED API...")
    try:
        fred_indicators = hybrid_economic_calendar.get_fred_economic_indicators()
        print(f"✅ FRED: {len(fred_indicators)} indicators")
        if fred_indicators:
            print(f"   Sample indicator: {fred_indicators[0].get('title', 'No title')}")
    except Exception as e:
        print(f"❌ FRED failed: {e}")
    
    # Test 5: World Bank
    print("\n5. Testing World Bank...")
    try:
        wb_data = hybrid_economic_calendar.get_world_bank_data()
        print(f"✅ World Bank: {len(wb_data)} data points")
        if wb_data:
            print(f"   Sample data: {wb_data[0].get('title', 'No title')}")
    except Exception as e:
        print(f"❌ World Bank failed: {e}")

def test_hybrid_service():
    """Test the complete hybrid service"""
    print("\n🧪 TESTING HYBRID SERVICE")
    print("=" * 50)
    
    try:
        # Test with date range
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        print(f"📅 Fetching events from {start_date} to {end_date}")
        
        events = hybrid_economic_calendar.get_economic_events(start_date, end_date)
        
        print(f"✅ Hybrid service returned {len(events)} events")
        
        if events:
            print("\n📊 EVENT BREAKDOWN:")
            sources = {}
            currencies = {}
            impacts = {}
            
            for event in events:
                source = event.get('source', 'Unknown')
                currency = event.get('currency', 'Unknown')
                impact = event.get('impact', 'Unknown')
                
                sources[source] = sources.get(source, 0) + 1
                currencies[currency] = currencies.get(currency, 0) + 1
                impacts[impact] = impacts.get(impact, 0) + 1
            
            print(f"   Sources: {sources}")
            print(f"   Currencies: {currencies}")
            print(f"   Impact levels: {impacts}")
            
            print("\n🎯 SAMPLE EVENTS:")
            for i, event in enumerate(events[:5]):  # Show first 5 events
                print(f"   {i+1}. {event.get('title', 'No title')}")
                print(f"      Currency: {event.get('currency', 'N/A')}")
                print(f"      Date: {event.get('date', 'N/A')}")
                print(f"      Impact: {event.get('impact', 'N/A')}")
                print(f"      Source: {event.get('source', 'N/A')}")
                print()
        
        return events
        
    except Exception as e:
        print(f"❌ Hybrid service failed: {e}")
        return []

def test_api_keys():
    """Check if API keys are configured"""
    print("\n🔑 CHECKING API KEYS")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env')  # Explicitly load .env file
    
    fmp_key = os.getenv('FMP_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')
    
    print(f"FMP API Key: {'✅ Set' if fmp_key and fmp_key != 'your_fmp_api_key_here' else '❌ Not set'}")
    print(f"FRED API Key: {'✅ Set' if fred_key and fred_key != 'your_fred_api_key_here' else '❌ Not set'}")
    
    if not fmp_key or fmp_key == 'your_fmp_api_key_here':
        print("\n⚠️  FMP API Key not set. Get it from: https://site.financialmodelingprep.com/developer")
    
    if not fred_key or fred_key == 'your_fred_api_key_here':
        print("\n⚠️  FRED API Key not set. Get it from: https://fred.stlouisfed.org/docs/api/api_key.html")
    
    return fmp_key, fred_key

def main():
    """Main test function"""
    print("🚀 HYBRID ECONOMIC CALENDAR TEST")
    print("=" * 50)
    
    # Test API keys
    fmp_key, fred_key = test_api_keys()
    
    # Test individual sources
    test_individual_sources()
    
    # Test hybrid service
    events = test_hybrid_service()
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 50)
    
    if events:
        print("✅ Hybrid economic calendar is working!")
        print(f"   Total events found: {len(events)}")
        print("   Sources used: ForexFactory, FMP, Trading Economics, FRED, World Bank")
        print("   Cost: $0/month")
    else:
        print("❌ Hybrid economic calendar needs configuration")
        print("   Make sure to set up your API keys")
        print("   Check your internet connection")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Set up your API keys in .env file")
    print("2. Deploy the updated backend")
    print("3. Test the /api/economic-calendar endpoint")
    print("4. Verify events appear in your frontend")

if __name__ == "__main__":
    main()
