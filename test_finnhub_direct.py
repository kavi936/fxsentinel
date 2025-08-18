#!/usr/bin/env python3
"""
Test Finnhub API directly to see if we can get better expected values
"""

import os
import requests
import json
from datetime import datetime, timedelta

def test_finnhub_direct():
    """Test Finnhub API directly"""
    print("🔍 Testing Finnhub API Directly...")
    
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("❌ FINNHUB_API_KEY environment variable not set!")
        return
    base_url = 'https://finnhub.io/api/v1'
    
    # Test different date ranges and parameters
    test_configs = [
        {
            'name': 'Current Week',
            'params': {
                'from': datetime.now().strftime('%Y-%m-%d'),
                'to': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            }
        },
        {
            'name': 'Next Week',
            'params': {
                'from': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'to': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            }
        },
        {
            'name': 'Last Week',
            'params': {
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            }
        }
    ]
    
    headers = {
        'X-Finnhub-Token': api_key,
        'User-Agent': 'FXSentinel/1.0'
    }
    
    for config in test_configs:
        print(f"\n📅 Testing: {config['name']}")
        print(f"Date range: {config['params']['from']} to {config['params']['to']}")
        
        try:
            url = f"{base_url}/calendar/economic"
            response = requests.get(url, params=config['params'], headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('economicCalendar', [])
                
                print(f"✅ Found {len(events)} events")
                
                # Count events with different data
                events_with_estimate = [e for e in events if e.get('estimate') is not None]
                events_with_actual = [e for e in events if e.get('actual') is not None]
                events_with_prev = [e for e in events if e.get('prev') is not None]
                
                print(f"Events with estimate: {len(events_with_estimate)}")
                print(f"Events with actual: {len(events_with_actual)}")
                print(f"Events with previous: {len(events_with_prev)}")
                
                # Show sample events with estimates
                if events_with_estimate:
                    print("Sample events with estimates:")
                    for e in events_with_estimate[:5]:
                        print(f"  {e.get('event', 'Unknown')}: estimate={e.get('estimate')}, prev={e.get('prev')}, actual={e.get('actual')}")
                
                # Check for major currency events
                major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF']
                major_events = [e for e in events if e.get('currency') in major_currencies]
                major_events_with_estimate = [e for e in major_events if e.get('estimate') is not None]
                
                print(f"Major currency events: {len(major_events)}")
                print(f"Major currency events with estimates: {len(major_events_with_estimate)}")
                
                if major_events_with_estimate:
                    print("Major currency events with estimates:")
                    for e in major_events_with_estimate[:5]:
                        print(f"  {e.get('event', 'Unknown')} ({e.get('currency')}): estimate={e.get('estimate')}")
                
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test if there are other endpoints that might have better data
    print("\n🔍 Testing other potential endpoints...")
    
    other_endpoints = [
        '/economic',
        '/calendar/earnings',
        '/calendar/ipo'
    ]
    
    for endpoint in other_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            params = {
                'from': datetime.now().strftime('%Y-%m-%d'),
                'to': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            print(f"{endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

if __name__ == "__main__":
    test_finnhub_direct()
