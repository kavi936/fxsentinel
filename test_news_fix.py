#!/usr/bin/env python3
"""
Test script to verify that the news endpoint no longer returns economic calendar events
"""

import requests
import json
from datetime import datetime

def test_news_endpoint():
    """Test the news endpoint to ensure it doesn't return economic calendar events"""
    
    # Test local endpoint
    base_url = "http://localhost:5001"
    
    try:
        print("🔍 Testing news endpoint...")
        response = requests.get(f"{base_url}/api/news", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            
            print(f"✅ News endpoint returned {len(news_items)} items")
            print(f"📊 Sources: {data.get('sources', [])}")
            print(f"💾 Cache status: {data.get('cache_status', 'unknown')}")
            
            # Check for economic calendar events
            economic_events = []
            for item in news_items:
                source = item.get('source', '').lower()
                title = item.get('title', '').lower()
                
                # Check for indicators of economic calendar events
                if (source == 'finnhub' or 
                    'economic calendar' in source or
                    'economic' in source or
                    any(keyword in title for keyword in ['cpi', 'gdp', 'non-farm payrolls', 'interest rate decision'])):
                    economic_events.append({
                        'title': item.get('title'),
                        'source': item.get('source'),
                        'id': item.get('id')
                    })
            
            if economic_events:
                print(f"❌ Found {len(economic_events)} economic calendar events in news feed:")
                for event in economic_events:
                    print(f"   - {event['title']} (Source: {event['source']})")
                return False
            else:
                print("✅ No economic calendar events found in news feed")
                return True
                
        else:
            print(f"❌ News endpoint returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing news endpoint: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_economic_calendar_endpoint():
    """Test that economic calendar endpoint still works separately"""
    
    base_url = "http://localhost:5001"
    
    try:
        print("\n🔍 Testing economic calendar endpoint...")
        response = requests.get(f"{base_url}/api/economic-calendar", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            print(f"✅ Economic calendar endpoint returned {len(events)} events")
            print(f"📊 Source: {data.get('source', 'unknown')}")
            return True
        else:
            print(f"❌ Economic calendar endpoint returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing economic calendar endpoint: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing News Feed Fix")
    print("=" * 50)
    
    # Test news endpoint
    news_test_passed = test_news_endpoint()
    
    # Test economic calendar endpoint
    calendar_test_passed = test_economic_calendar_endpoint()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"   News Feed (no economic events): {'✅ PASSED' if news_test_passed else '❌ FAILED'}")
    print(f"   Economic Calendar (separate): {'✅ PASSED' if calendar_test_passed else '❌ FAILED'}")
    
    if news_test_passed and calendar_test_passed:
        print("\n🎉 All tests passed! The fix is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
