#!/usr/bin/env python3
"""
Comprehensive test script for chart popup functionality
Tests data quality, deduplication, and chart rendering capabilities
"""

import requests
import json
import sys
import os
from datetime import datetime

def test_chart_data_quality():
    """Test the quality of chart data returned by the API"""
    print("🔍 Testing Chart Data Quality...")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    test_events = ["CPI", "GDP", "Unemployment", "Retail Sales"]
    
    for event_name in test_events:
        print(f"\n📊 Testing {event_name} data quality:")
        print("-" * 30)
        
        try:
            # Encode the event name
            import urllib.parse
            encoded_event = urllib.parse.quote(event_name)
            
            # Test with 12 months
            url = f"{base_url}/api/economic-chart/{encoded_event}?months=12"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'success':
                    chart_data = data['chart_data']
                    historical_data = chart_data.get('historical_data', [])
                    
                    print(f"✅ Found {len(historical_data)} data points")
                    
                    # Check for data quality issues
                    issues = []
                    
                    # Check for duplicate dates
                    dates = [point['date'] for point in historical_data]
                    duplicate_dates = [date for date in set(dates) if dates.count(date) > 1]
                    if duplicate_dates:
                        issues.append(f"Duplicate dates found: {len(duplicate_dates)}")
                    
                    # Check for extreme values
                    values = [point['value'] for point in historical_data if point.get('value') is not None]
                    if values:
                        min_val = min(values)
                        max_val = max(values)
                        avg_val = sum(values) / len(values)
                        
                        # Check for reasonable ranges based on indicator type
                        if event_name.lower() == 'cpi':
                            if max_val > 50 or min_val < -20:
                                issues.append(f"Extreme CPI values: min={min_val}, max={max_val}")
                        elif event_name.lower() == 'gdp':
                            if max_val > 100 or min_val < -50:
                                issues.append(f"Extreme GDP values: min={min_val}, max={max_val}")
                        elif event_name.lower() == 'unemployment':
                            if max_val > 50 or min_val < 0:
                                issues.append(f"Extreme unemployment values: min={min_val}, max={max_val}")
                    
                    # Check for missing required fields
                    missing_fields = []
                    for i, point in enumerate(historical_data):
                        if not point.get('date'):
                            missing_fields.append(f"Point {i}: missing date")
                        if point.get('value') is None:
                            missing_fields.append(f"Point {i}: missing value")
                    
                    if missing_fields:
                        issues.append(f"Missing fields: {len(missing_fields)} points affected")
                    
                    # Report results
                    if issues:
                        print(f"⚠️ Data quality issues found:")
                        for issue in issues:
                            print(f"  - {issue}")
                    else:
                        print("✅ No data quality issues detected")
                    
                    # Show sample data
                    if historical_data:
                        print("📈 Sample data points:")
                        for i, point in enumerate(historical_data[:3]):
                            print(f"  {i+1}. {point['date']}: {point['value']} {point.get('unit', '')}")
                    
                    # Show statistics
                    if 'statistics' in chart_data:
                        stats = chart_data['statistics']
                        print("📊 Statistics:")
                        for key, value in stats.items():
                            if isinstance(value, float):
                                print(f"  {key}: {value:.3f}")
                            else:
                                print(f"  {key}: {value}")
                else:
                    print(f"❌ No data: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing {event_name}: {e}")

def test_chart_deduplication():
    """Test that data deduplication is working properly"""
    print("\n🔍 Testing Data Deduplication...")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    event_name = "CPI"
    
    try:
        import urllib.parse
        encoded_event = urllib.parse.quote(event_name)
        
        # Test with different timeframes to see deduplication in action
        timeframes = [6, 12, 24]
        
        for months in timeframes:
            print(f"\n📊 Testing {event_name} with {months} months:")
            print("-" * 30)
            
            url = f"{base_url}/api/economic-chart/{encoded_event}?months={months}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'success':
                    chart_data = data['chart_data']
                    historical_data = chart_data.get('historical_data', [])
                    
                    print(f"✅ Found {len(historical_data)} data points")
                    
                    # Check for duplicates
                    dates = [point['date'] for point in historical_data]
                    unique_dates = set(dates)
                    
                    if len(dates) == len(unique_dates):
                        print("✅ No duplicate dates found")
                    else:
                        print(f"⚠️ Found {len(dates) - len(unique_dates)} duplicate dates")
                        
                        # Show duplicate dates
                        duplicate_dates = [date for date in unique_dates if dates.count(date) > 1]
                        print(f"Duplicate dates: {duplicate_dates[:5]}...")  # Show first 5
                    
                    # Check data consistency
                    if historical_data:
                        # Verify all points have required fields
                        valid_points = 0
                        for point in historical_data:
                            if point.get('date') and point.get('value') is not None:
                                valid_points += 1
                        
                        print(f"✅ {valid_points}/{len(historical_data)} points have valid data")
                        
                        # Show date range
                        if historical_data:
                            dates_sorted = sorted([point['date'] for point in historical_data])
                            print(f"📅 Date range: {dates_sorted[0]} to {dates_sorted[-1]}")
                else:
                    print(f"❌ No data: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error testing deduplication: {e}")

def test_chart_api_endpoints():
    """Test all chart-related API endpoints"""
    print("\n🔍 Testing Chart API Endpoints...")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    # Test endpoints
    endpoints = [
        ("Economic Calendar", "/api/economic-calendar"),
        ("Chart Data - CPI", "/api/economic-chart/CPI?months=12"),
        ("Chart Data - GDP", "/api/economic-chart/GDP?months=12"),
        ("Chart Data - Unemployment", "/api/economic-chart/Unemployment?months=12"),
    ]
    
    for name, endpoint in endpoints:
        print(f"\n📊 Testing {name}:")
        print("-" * 30)
        
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=15)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'events' in data:
                    print(f"✅ Calendar events: {len(data['events'])}")
                    print(f"Source: {data.get('source', 'unknown')}")
                elif 'chart_data' in data:
                    chart_data = data['chart_data']
                    historical_data = chart_data.get('historical_data', [])
                    print(f"✅ Chart data points: {len(historical_data)}")
                    print(f"Indicator: {chart_data.get('indicator', 'unknown')}")
                    print(f"Timeframe: {chart_data.get('timeframe', 'unknown')}")
                else:
                    print("✅ Endpoint working (unknown response format)")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_chart_data_structure():
    """Test the structure of chart data to ensure it's frontend-compatible"""
    print("\n🔍 Testing Chart Data Structure...")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    event_name = "CPI"
    
    try:
        import urllib.parse
        encoded_event = urllib.parse.quote(event_name)
        url = f"{base_url}/api/economic-chart/{encoded_event}?months=12"
        
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            print("📊 Response structure:")
            print(f"  Status: {data.get('status')}")
            print(f"  Message: {data.get('message')}")
            
            if 'chart_data' in data:
                chart_data = data['chart_data']
                print("\n📈 Chart data structure:")
                print(f"  Indicator: {chart_data.get('indicator')}")
                print(f"  Data points: {chart_data.get('data_points')}")
                print(f"  Timeframe: {chart_data.get('timeframe')}")
                print(f"  Last updated: {chart_data.get('last_updated')}")
                
                if 'statistics' in chart_data:
                    stats = chart_data['statistics']
                    print("\n📊 Statistics structure:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                
                if 'historical_data' in chart_data:
                    historical_data = chart_data['historical_data']
                    if historical_data:
                        sample_point = historical_data[0]
                        print("\n📅 Sample data point structure:")
                        for key, value in sample_point.items():
                            print(f"  {key}: {value} (type: {type(value).__name__})")
                        
                        # Check for required fields
                        required_fields = ['date', 'value']
                        missing_fields = []
                        for field in required_fields:
                            if field not in sample_point:
                                missing_fields.append(field)
                        
                        if missing_fields:
                            print(f"⚠️ Missing required fields: {missing_fields}")
                        else:
                            print("✅ All required fields present")
                        
                        # Check data types
                        if not isinstance(sample_point['date'], str):
                            print("⚠️ Date field is not a string")
                        if not isinstance(sample_point['value'], (int, float)):
                            print("⚠️ Value field is not numeric")
                        if not isinstance(sample_point.get('unit', ''), str):
                            print("⚠️ Unit field is not a string")
            else:
                print("❌ No chart_data in response")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing data structure: {e}")

def main():
    """Run all chart functionality tests"""
    print("🚀 Chart Popup Functionality Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test_chart_data_quality()
    test_chart_deduplication()
    test_chart_api_endpoints()
    test_chart_data_structure()
    
    print("\n" + "=" * 60)
    print("✅ Chart functionality test suite complete!")
    print("💡 If all tests pass, the chart popup should work properly in the frontend")

if __name__ == "__main__":
    main()
