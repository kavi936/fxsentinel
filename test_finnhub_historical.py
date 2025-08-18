#!/usr/bin/env python3
"""
Test script to explore Finnhub's historical data capabilities
Checks what economic indicators have historical data available
"""

import os
import requests
import json
from datetime import datetime, timedelta

def test_finnhub_historical_endpoints():
    """Test various Finnhub endpoints for historical data"""
    print("🔍 Testing Finnhub Historical Data Endpoints...")
    
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("❌ FINNHUB_API_KEY environment variable not set!")
        return
    base_url = 'https://finnhub.io/api/v1'
    
    # Test different historical data endpoints
    endpoints = [
        {
            'name': 'Economic Calendar (Historical)',
            'url': f"{base_url}/calendar/economic",
            'params': {
                'from': (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d'),  # 5 years ago
                'to': datetime.now().strftime('%Y-%m-%d')
            }
        },
        {
            'name': 'Economic Indicators',
            'url': f"{base_url}/economic",
            'params': {
                'indicator': 'cpi',
                'from': (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            }
        },
        {
            'name': 'Economic Calendar (Last Year)',
            'url': f"{base_url}/calendar/economic",
            'params': {
                'from': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            }
        }
    ]
    
    headers = {
        'X-Finnhub-Token': api_key,
        'User-Agent': 'FXSentinel/1.0'
    }
    
    for endpoint in endpoints:
        print(f"\n📊 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        print(f"Params: {endpoint['params']}")
        
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], headers=headers, timeout=15)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'economicCalendar' in data:
                    events = data['economicCalendar']
                    print(f"✅ Found {len(events)} historical events")
                    
                    if events:
                        # Look for events with economic data
                        events_with_data = [e for e in events if e.get('prev') or e.get('estimate') or e.get('actual')]
                        print(f"📈 Events with economic data: {len(events_with_data)}")
                        
                        if events_with_data:
                            print("📅 Sample historical events with data:")
                            for i, event in enumerate(events_with_data[:3]):
                                print(f"  {i+1}. {event.get('event', 'Unknown')}")
                                print(f"     Date: {event.get('date', 'N/A')} {event.get('time', 'N/A')}")
                                print(f"     Previous: {event.get('prev', 'N/A')}")
                                print(f"     Estimate: {event.get('estimate', 'N/A')}")
                                print(f"     Actual: {event.get('actual', 'N/A')}")
                                print(f"     Unit: {event.get('unit', 'N/A')}")
                
                elif 'data' in data:
                    # Economic indicators endpoint
                    indicator_data = data['data']
                    print(f"✅ Found {len(indicator_data)} historical data points")
                    
                    if indicator_data:
                        print("📈 Sample historical data:")
                        for i, point in enumerate(indicator_data[:5]):
                            print(f"  {i+1}. Date: {point.get('date', 'N/A')}, Value: {point.get('value', 'N/A')}")
                
                else:
                    print(f"📄 Response structure: {list(data.keys())}")
                    print(f"📄 Sample data: {str(data)[:200]}...")
            
            elif response.status_code == 401:
                print("❌ Unauthorized - API key may not have access to this endpoint")
            elif response.status_code == 403:
                print("❌ Forbidden - This endpoint may require a paid plan")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_specific_indicators():
    """Test specific economic indicators for historical data"""
    print("\n🔍 Testing Specific Economic Indicators...")
    
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("❌ FINNHUB_API_KEY environment variable not set!")
        return
    base_url = 'https://finnhub.io/api/v1'
    
    # Common economic indicators to test
    indicators = [
        'cpi', 'gdp', 'unemployment', 'retail_sales', 'industrial_production',
        'consumer_confidence', 'business_confidence', 'trade_balance'
    ]
    
    headers = {
        'X-Finnhub-Token': api_key,
        'User-Agent': 'FXSentinel/1.0'
    }
    
    for indicator in indicators:
        print(f"\n📊 Testing: {indicator.upper()}")
        
        try:
            url = f"{base_url}/economic"
            params = {
                'indicator': indicator,
                'from': (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d'),  # 2 years
                'to': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and data['data']:
                    points = data['data']
                    print(f"✅ Found {len(points)} data points")
                    
                    # Show sample data
                    print("📈 Sample data:")
                    for i, point in enumerate(points[:3]):
                        print(f"  {i+1}. {point.get('date', 'N/A')}: {point.get('value', 'N/A')}")
                    
                    # Check if we have enough data for charts
                    if len(points) >= 12:  # At least 1 year of monthly data
                        print(f"✅ Sufficient data for charts ({len(points)} points)")
                    else:
                        print(f"⚠️ Limited data for charts ({len(points)} points)")
                
                else:
                    print("❌ No data available")
            
            elif response.status_code == 401:
                print("❌ Unauthorized")
            elif response.status_code == 403:
                print("❌ Forbidden - May require paid plan")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_calendar_historical_range():
    """Test calendar endpoint with different historical ranges"""
    print("\n🔍 Testing Calendar Historical Ranges...")
    
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("❌ FINNHUB_API_KEY environment variable not set!")
        return
    base_url = 'https://finnhub.io/api/v1'
    
    # Test different time ranges
    ranges = [
        {'name': 'Last 6 months', 'days': 180},
        {'name': 'Last 1 year', 'days': 365},
        {'name': 'Last 2 years', 'days': 365*2},
        {'name': 'Last 5 years', 'days': 365*5}
    ]
    
    headers = {
        'X-Finnhub-Token': api_key,
        'User-Agent': 'FXSentinel/1.0'
    }
    
    for range_info in ranges:
        print(f"\n📅 Testing: {range_info['name']}")
        
        try:
            url = f"{base_url}/calendar/economic"
            params = {
                'from': (datetime.now() - timedelta(days=range_info['days'])).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('economicCalendar', [])
                
                print(f"✅ Found {len(events)} events")
                
                # Count events with economic data
                events_with_data = [e for e in events if e.get('prev') or e.get('estimate') or e.get('actual')]
                print(f"📈 Events with economic data: {len(events_with_data)}")
                
                # Count unique indicators
                unique_indicators = set()
                for event in events_with_data:
                    indicator = event.get('event', '').lower()
                    if any(keyword in indicator for keyword in ['cpi', 'gdp', 'unemployment', 'retail', 'employment']):
                        unique_indicators.add(indicator)
                
                print(f"📊 Unique major indicators: {len(unique_indicators)}")
                if unique_indicators:
                    print(f"📋 Indicators: {list(unique_indicators)[:5]}...")
            
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all historical data tests"""
    print("🚀 Finnhub Historical Data Exploration")
    print("=" * 60)
    
    # Test 1: Historical endpoints
    test_finnhub_historical_endpoints()
    
    # Test 2: Specific indicators
    test_specific_indicators()
    
    # Test 3: Calendar historical ranges
    test_calendar_historical_range()
    
    print("\n" + "=" * 60)
    print("✅ Historical data exploration complete!")
    print("💡 Check which endpoints provide historical data for charts and AI analysis")

if __name__ == "__main__":
    main()
