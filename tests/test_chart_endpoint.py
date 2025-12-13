#!/usr/bin/env python3
"""
Test script for the economic chart endpoint
"""

import requests
import urllib.parse

def test_chart_endpoint():
    """Test the economic chart endpoint"""
    print("🔍 Testing Economic Chart Endpoint...")
    
    # Test with different event names
    test_events = [
        "CPI",
        "GDP",
        "Unemployment",
        "Employment",
        "Retail Sales"
    ]
    
    base_url = "http://localhost:5001"
    
    for event_name in test_events:
        print(f"\n📊 Testing chart data for: {event_name}")
        
        # Encode the event name
        encoded_event = urllib.parse.quote(event_name)
        url = f"{base_url}/api/economic-chart/{encoded_event}?months=12"
        
        try:
            response = requests.get(url, timeout=15)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'success':
                    chart_data = data['chart_data']
                    print(f"✅ Success! Found {len(chart_data['historical_data'])} data points")
                    print(f"Indicator: {chart_data['indicator']}")
                    print(f"Timeframe: {chart_data['timeframe']}")
                    
                    if chart_data['statistics']:
                        stats = chart_data['statistics']
                        print(f"Statistics:")
                        print(f"  Average: {stats.get('average', 'N/A')}")
                        print(f"  Min/Max: {stats.get('minimum', 'N/A')} / {stats.get('maximum', 'N/A')}")
                        print(f"  Trend: {stats.get('trend', 'N/A')}")
                        print(f"  Latest: {stats.get('latest_value', 'N/A')}")
                    
                    # Show sample data
                    if chart_data['historical_data']:
                        print("Sample historical data:")
                        for i, point in enumerate(chart_data['historical_data'][:3]):
                            print(f"  {i+1}. {point['date']}: {point['value']} {point['unit']}")
                
                else:
                    print(f"❌ No data: {data['message']}")
            
            elif response.status_code == 404:
                print("❌ No data available for this event")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_chart_endpoint_with_months():
    """Test the chart endpoint with different month ranges"""
    print("\n🔍 Testing Chart Endpoint with Different Timeframes...")
    
    base_url = "http://localhost:5001"
    event_name = "CPI"
    encoded_event = urllib.parse.quote(event_name)
    
    timeframes = [6, 12, 24]
    
    for months in timeframes:
        print(f"\n📊 Testing {event_name} with {months} months:")
        
        url = f"{base_url}/api/economic-chart/{encoded_event}?months={months}"
        
        try:
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'success':
                    chart_data = data['chart_data']
                    print(f"✅ Found {len(chart_data['historical_data'])} data points")
                    print(f"Timeframe: {chart_data['timeframe']}")
                else:
                    print(f"❌ No data: {data['message']}")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all chart endpoint tests"""
    print("🚀 Economic Chart Endpoint Test")
    print("=" * 60)
    
    # Test 1: Basic chart endpoint functionality
    test_chart_endpoint()
    
    # Test 2: Different timeframes
    test_chart_endpoint_with_months()
    
    print("\n" + "=" * 60)
    print("✅ Chart endpoint test complete!")
    print("💡 The chart popup should now work in the frontend")

if __name__ == "__main__":
    main()
