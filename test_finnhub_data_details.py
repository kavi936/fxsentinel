#!/usr/bin/env python3
"""
Test script to examine Finnhub data details
Shows the raw data structure and available fields
"""

import requests
import json
from datetime import datetime, timedelta

def examine_finnhub_raw_data():
    """Examine the raw Finnhub API response to see available fields"""
    print("🔍 Examining Finnhub Raw Data Structure...")
    
    try:
        # Test Finnhub API directly
        api_key = 'd2d51d1r01qjem5j4g9gd2d51d1r01qjem5j4ga0'
        base_url = 'https://finnhub.io/api/v1'
        
        url = f"{base_url}/calendar/economic"
        params = {
            'from': datetime.now().strftime('%Y-%m-%d'),
            'to': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }
        
        headers = {
            'X-Finnhub-Token': api_key,
            'User-Agent': 'FXSentinel/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('economicCalendar', [])
            
            print(f"✅ Found {len(events)} events")
            
            if events:
                # Examine the first few events in detail
                print("\n📊 Raw Event Data Structure:")
                for i, event in enumerate(events[:3]):
                    print(f"\n--- Event {i+1} ---")
                    print(f"Event Name: {event.get('event', 'N/A')}")
                    print(f"Date: {event.get('date', 'N/A')}")
                    print(f"Time: {event.get('time', 'N/A')}")
                    print(f"Currency: {event.get('currency', 'N/A')}")
                    print(f"Impact: {event.get('impact', 'N/A')}")
                    print(f"Country: {event.get('country', 'N/A')}")
                    
                    # Check for economic data fields
                    print(f"Previous: {event.get('previous', 'N/A')}")
                    print(f"Estimate: {event.get('estimate', 'N/A')}")
                    print(f"Actual: {event.get('actual', 'N/A')}")
                    
                    # Check for any other fields that might contain economic data
                    print("All available fields:")
                    for key, value in event.items():
                        if value and value != 'N/A':
                            print(f"  {key}: {value}")
                
                # Look for events with economic data
                print("\n🔍 Searching for events with economic data...")
                events_with_data = []
                
                for event in events:
                    previous = event.get('previous')
                    estimate = event.get('estimate')
                    actual = event.get('actual')
                    
                    if previous or estimate or actual:
                        events_with_data.append(event)
                
                print(f"Found {len(events_with_data)} events with economic data")
                
                if events_with_data:
                    print("\n📈 Sample events with economic data:")
                    for i, event in enumerate(events_with_data[:5]):
                        print(f"\n{i+1}. {event.get('event', 'Unknown')}")
                        print(f"   Previous: {event.get('previous', 'N/A')}")
                        print(f"   Estimate: {event.get('estimate', 'N/A')}")
                        print(f"   Actual: {event.get('actual', 'N/A')}")
                        print(f"   Currency: {event.get('currency', 'N/A')}")
                        print(f"   Date: {event.get('date', 'N/A')} {event.get('time', 'N/A')}")
            else:
                print("⚠️ No events found")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_our_transformation():
    """Test our transformation to see what we're outputting"""
    print("\n🔍 Testing Our Data Transformation...")
    
    try:
        url = "http://localhost:8000/api/economic-calendar"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            print(f"✅ Found {len(events)} transformed events")
            
            if events:
                print("\n📊 Transformed Event Data:")
                for i, event in enumerate(events[:5]):
                    print(f"\n--- Event {i+1} ---")
                    print(f"Title: {event.get('title', 'N/A')}")
                    print(f"Date: {event.get('date', 'N/A')}")
                    print(f"Time: {event.get('time', 'N/A')}")
                    print(f"Currency: {event.get('currency', 'N/A')}")
                    print(f"Impact: {event.get('impact', 'N/A')}")
                    print(f"Previous: {event.get('previous', 'N/A')}")
                    print(f"Expected: {event.get('expected', 'N/A')}")
                    print(f"Actual: {event.get('actual', 'N/A')}")
                    
                    # Check if we have raw data
                    if 'raw_data' in event:
                        raw = event['raw_data']
                        print(f"Raw Previous: {raw.get('previous', 'N/A')}")
                        print(f"Raw Estimate: {raw.get('estimate', 'N/A')}")
                        print(f"Raw Actual: {raw.get('actual', 'N/A')}")
                
                # Count events with economic data
                events_with_data = [e for e in events if e.get('previous') != '--' or e.get('expected') != '--' or e.get('actual') != '--']
                print(f"\n📈 Events with economic data: {len(events_with_data)} out of {len(events)}")
                
                if events_with_data:
                    print("\n📊 Sample events with economic data:")
                    for i, event in enumerate(events_with_data[:3]):
                        print(f"\n{i+1}. {event.get('title', 'Unknown')}")
                        print(f"   Previous: {event.get('previous', 'N/A')}")
                        print(f"   Expected: {event.get('expected', 'N/A')}")
                        print(f"   Actual: {event.get('actual', 'N/A')}")
            else:
                print("⚠️ No events found")
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run the detailed data examination"""
    print("🚀 Finnhub Data Details Examination")
    print("=" * 60)
    
    # Test 1: Examine raw Finnhub data
    examine_finnhub_raw_data()
    
    # Test 2: Test our transformation
    test_our_transformation()
    
    print("\n" + "=" * 60)
    print("✅ Data examination complete!")

if __name__ == "__main__":
    main()
