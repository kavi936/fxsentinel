#!/usr/bin/env python3
"""
Direct test of the chart data endpoint
"""

import os
import sys
sys.path.append('backend')

from services.finnhub_historical import finnhub_historical

def test_chart_endpoint_direct():
    """Test the chart data endpoint directly"""
    print("🔍 Testing Chart Data Endpoint Directly...")
    
    # Set API key
    os.environ['FINNHUB_API_KEY'] = 'd2d51d1r01qjem5j4g9gd2d51d1r01qjem5j4ga0'
    
    # Test different event names
    test_events = ['CPI', 'GDP', 'Unemployment', 'Employment', 'Retail Sales']
    
    for event_name in test_events:
        print(f"\n📊 Testing chart data for: {event_name}")
        try:
            chart_data = finnhub_historical.get_chart_data_for_event(event_name, 12)
            
            if chart_data and chart_data.get('historical_data'):
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
                print(f"❌ No data: {chart_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chart_endpoint_direct()
