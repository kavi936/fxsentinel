#!/usr/bin/env python3
"""
Test Economic Data Extraction
This script tests the data extraction and caching functionality.
"""

import sys
import os
from datetime import datetime, timedelta, date

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.economic_data_extractor import EconomicDataExtractor
from services.cached_economic_calendar import CachedEconomicCalendarService

def test_api_connection():
    """Test if the Finnhub API is accessible"""
    print("🔍 Testing Finnhub API connection...")
    
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("❌ FINNHUB_API_KEY not set")
        return False
    
    try:
        extractor = EconomicDataExtractor()
        
        # Test with a small date range
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        data = extractor._make_api_request(today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d'))
        
        if data and 'economicCalendar' in data:
            events = data['economicCalendar']
            print(f"✅ API connection successful - found {len(events)} events for test period")
            return True
        else:
            print("⚠️ API connection successful but no data returned")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_small_extraction():
    """Test extraction with a small date range"""
    print("\n🧪 Testing small data extraction...")
    
    try:
        extractor = EconomicDataExtractor()
        
        # Extract just 3 days of data
        today = date.today()
        end_date = today + timedelta(days=2)
        
        print(f"Extracting data from {today} to {end_date}")
        results = extractor.extract_historical_data(today, end_date)
        
        print(f"✅ Small extraction completed:")
        print(f"   Events found: {results['events_found']}")
        print(f"   Events stored: {results['events_stored']}")
        
        return results['events_stored'] > 0
        
    except Exception as e:
        print(f"❌ Small extraction failed: {e}")
        return False

def test_cached_service():
    """Test the cached service functionality"""
    print("\n🗄️ Testing cached service...")
    
    try:
        cached_service = CachedEconomicCalendarService()
        
        if not cached_service.is_cache_available():
            print("❌ Cache not available")
            return False
        
        # Test getting cached data
        events = cached_service.get_economic_calendar()
        
        if events:
            print(f"✅ Cached service working - retrieved {len(events)} events")
            
            # Test cache statistics
            stats = cached_service.get_cache_statistics()
            if 'error' not in stats:
                print(f"   Total cached events: {stats['total_events']}")
                print(f"   Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
            
            return True
        else:
            print("⚠️ Cached service working but no events returned")
            return False
            
    except Exception as e:
        print(f"❌ Cached service test failed: {e}")
        return False

def test_fallback_functionality():
    """Test the fallback functionality in the main service"""
    print("\n🔄 Testing fallback functionality...")
    
    try:
        # Import the main service
        from services.finnhub_calendar import finnhub_calendar
        
        # Temporarily disable API key to test fallback
        original_key = finnhub_calendar.api_key
        finnhub_calendar.api_key = None
        
        # Try to get data (should use cache)
        events = finnhub_calendar.get_economic_calendar()
        
        # Restore API key
        finnhub_calendar.api_key = original_key
        
        if events:
            print(f"✅ Fallback functionality working - retrieved {len(events)} events from cache")
            return True
        else:
            print("⚠️ Fallback functionality working but no events returned")
            return False
            
    except Exception as e:
        print(f"❌ Fallback functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 FXSentinel Economic Data Extraction Tests")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("API Connection", test_api_connection),
        ("Small Extraction", test_small_extraction),
        ("Cached Service", test_cached_service),
        ("Fallback Functionality", test_fallback_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The data extraction system is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())
