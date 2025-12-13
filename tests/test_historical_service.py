#!/usr/bin/env python3
"""
Test script for the Finnhub Historical Data Service
"""

import sys
sys.path.append('backend')

from services.finnhub_historical import finnhub_historical

def test_historical_service():
    """Test the historical data service"""
    print("🔍 Testing Finnhub Historical Data Service...")
    
    # Test 1: Access test
    print("\n📊 Testing Historical Access:")
    access_result = finnhub_historical.test_historical_access()
    print(f"Status: {access_result['status']}")
    print(f"Message: {access_result['message']}")
    
    # Test 2: CPI Historical Data
    print("\n📈 Testing CPI Historical Data:")
    cpi_data = finnhub_historical.get_cpi_historical_data(months=12)
    print(f"Found {len(cpi_data)} CPI data points")
    
    if cpi_data:
        print("Sample CPI data:")
        for i, point in enumerate(cpi_data[:3]):
            print(f"  {i+1}. {point['date']}: {point['value']} {point['unit']}")
    
    # Test 3: GDP Historical Data
    print("\n📈 Testing GDP Historical Data:")
    gdp_data = finnhub_historical.get_gdp_historical_data(months=12)
    print(f"Found {len(gdp_data)} GDP data points")
    
    if gdp_data:
        print("Sample GDP data:")
        for i, point in enumerate(gdp_data[:3]):
            print(f"  {i+1}. {point['date']}: {point['value']} {point['unit']}")
    
    # Test 4: Chart Data for Event
    print("\n📊 Testing Chart Data for Event:")
    chart_data = finnhub_historical.get_chart_data_for_event("CPI", months=12)
    print(f"Indicator: {chart_data['indicator']}")
    print(f"Data Points: {chart_data['data_points']}")
    print(f"Timeframe: {chart_data['timeframe']}")
    
    if chart_data['statistics']:
        stats = chart_data['statistics']
        print(f"Statistics:")
        print(f"  Average: {stats.get('average', 'N/A')}")
        print(f"  Min/Max: {stats.get('minimum', 'N/A')} / {stats.get('maximum', 'N/A')}")
        print(f"  Trend: {stats.get('trend', 'N/A')}")
        print(f"  Latest: {stats.get('latest_value', 'N/A')}")
    
    # Test 5: Employment Data
    print("\n📈 Testing Employment Historical Data:")
    employment_data = finnhub_historical.get_employment_historical_data(months=6)
    print(f"Found {len(employment_data)} employment data points")
    
    if employment_data:
        print("Sample employment data:")
        for i, point in enumerate(employment_data[:3]):
            print(f"  {i+1}. {point['date']}: {point['value']} {point['unit']}")

def main():
    """Run the historical service test"""
    print("🚀 Finnhub Historical Data Service Test")
    print("=" * 60)
    
    test_historical_service()
    
    print("\n" + "=" * 60)
    print("✅ Historical service test complete!")
    print("💡 This data can be used for charts and AI analysis")

if __name__ == "__main__":
    main()
