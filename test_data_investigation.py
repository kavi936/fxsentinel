#!/usr/bin/env python3
"""
Test script to investigate the actual data structure from the chart API
"""

import requests
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_chart_data():
    """Test the chart data API to see what we're actually getting"""
    
    # Test with a simple event name
    test_events = [
        "CPI",
        "GDP",
        "Unemployment Rate",
        "Retail Sales"
    ]
    
    base_url = "http://localhost:5000"
    
    print("🔍 INVESTIGATING CHART DATA STRUCTURE")
    print("=" * 50)
    
    for event_name in test_events:
        print(f"\n📊 Testing event: {event_name}")
        print("-" * 30)
        
        try:
            # Encode the event name
            import urllib.parse
            encoded_event = urllib.parse.quote(event_name)
            
            # Make the API call
            url = f"{base_url}/api/economic-chart/{encoded_event}?months=12"
            print(f"URL: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ SUCCESS - Data structure:")
                
                # Print the overall structure
                print(f"Response keys: {list(data.keys())}")
                
                if 'chart_data' in data:
                    chart_data = data['chart_data']
                    print(f"Chart data keys: {list(chart_data.keys())}")
                    
                    if 'historical_data' in chart_data:
                        historical_data = chart_data['historical_data']
                        print(f"Historical data points: {len(historical_data)}")
                        
                        if historical_data:
                            # Show first few data points
                            print("\n📈 Sample data points:")
                            for i, point in enumerate(historical_data[:3]):
                                print(f"  Point {i+1}:")
                                print(f"    Date: {point.get('date')}")
                                print(f"    Value: {point.get('value')} (type: {type(point.get('value'))})")
                                print(f"    Unit: {point.get('unit')}")
                                print(f"    Previous: {point.get('previous')}")
                                print(f"    Expected: {point.get('expected')}")
                                print(f"    Event: {point.get('event_name')}")
                                print(f"    Country: {point.get('country')}")
                                print(f"    Raw value: {point.get('raw_value')}")
                                print()
                            
                            # Show statistics
                            if 'statistics' in chart_data:
                                stats = chart_data['statistics']
                                print("📊 Statistics:")
                                for key, value in stats.items():
                                    print(f"  {key}: {value}")
                        
                        else:
                            print("❌ No historical data points found")
                    
                    else:
                        print("❌ No 'historical_data' key in chart_data")
                
                else:
                    print("❌ No 'chart_data' key in response")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error message: {error_data}")
                except:
                    print(f"Error text: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 DATA INVESTIGATION COMPLETE")

def test_backend_service_directly():
    """Test the backend service directly to see what data it returns"""
    
    print("\n🔍 TESTING BACKEND SERVICE DIRECTLY")
    print("=" * 50)
    
    try:
        from services.finnhub_historical import finnhub_historical
        
        test_indicators = ["CPI", "GDP", "Unemployment"]
        
        for indicator in test_indicators:
            print(f"\n📊 Testing indicator: {indicator}")
            print("-" * 30)
            
            # Test the service directly
            historical_data = finnhub_historical.get_historical_data_for_indicator(indicator, months=6)
            
            print(f"Found {len(historical_data)} data points")
            
            if historical_data:
                print("Sample data points:")
                for i, point in enumerate(historical_data[:2]):
                    print(f"  Point {i+1}:")
                    print(f"    Date: {point.get('date')}")
                    print(f"    Value: {point.get('value')} (type: {type(point.get('value'))})")
                    print(f"    Unit: {point.get('unit')}")
                    print(f"    Event: {point.get('event_name')}")
                    print(f"    Country: {point.get('country')}")
                    print()
            
            # Test chart data function
            chart_data = finnhub_historical.get_chart_data_for_event(indicator, months=6)
            print(f"Chart data structure: {list(chart_data.keys())}")
            if 'statistics' in chart_data:
                print(f"Statistics: {chart_data['statistics']}")
                
    except Exception as e:
        print(f"❌ Error testing backend service: {e}")

if __name__ == "__main__":
    print("🚀 Starting Chart Data Investigation")
    
    # Test the API endpoint
    test_chart_data()
    
    # Test the backend service directly
    test_backend_service_directly()
    
    print("\n✅ Investigation complete!")
