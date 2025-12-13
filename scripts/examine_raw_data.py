#!/usr/bin/env python3
"""
Examine raw Finnhub data structure to find expected values
"""

import requests
import json

def examine_raw_finnhub_data():
    """Examine the raw Finnhub API response"""
    print("🔍 Examining Raw Finnhub Data Structure...")
    
    # Get data from our API
    try:
        response = requests.get("http://localhost:5001/api/economic-calendar")
        data = response.json()
        events = data.get('events', [])
        
        print(f"✅ Found {len(events)} events")
        
        if events:
            # Examine first few events in detail
            for i, event in enumerate(events[:10]):
                print(f"\n--- Event {i+1} ---")
                print(f"Title: {event.get('title', 'N/A')}")
                print(f"Currency: {event.get('currency', 'N/A')}")
                print(f"Impact: {event.get('impact', 'N/A')}")
                
                # Check our transformed data
                print(f"Our Previous: {event.get('previous', 'N/A')}")
                print(f"Our Expected: {event.get('expected', 'N/A')}")
                print(f"Our Actual: {event.get('actual', 'N/A')}")
                
                # Check raw data
                raw_data = event.get('raw_data', {})
                print(f"Raw data fields: {list(raw_data.keys())}")
                
                # Look for any field that might contain expected values
                for key, value in raw_data.items():
                    if value is not None and value != 'None':
                        print(f"  {key}: {value}")
                
                # Check if there are any other fields that might be expected values
                potential_expected_fields = ['forecast', 'projection', 'consensus', 'survey', 'prediction']
                for field in potential_expected_fields:
                    if field in raw_data:
                        print(f"  Found potential expected field '{field}': {raw_data[field]}")
                
                print("---")
        
        # Look for events with different data patterns
        print("\n🔍 Looking for events with different data patterns...")
        
        events_with_estimate = [e for e in events if e.get('raw_data', {}).get('estimate') is not None]
        events_without_estimate = [e for e in events if e.get('raw_data', {}).get('estimate') is None]
        
        print(f"Events with 'estimate' field: {len(events_with_estimate)}")
        print(f"Events without 'estimate' field: {len(events_without_estimate)}")
        
        if events_with_estimate:
            print("\nSample events WITH estimate:")
            for e in events_with_estimate[:3]:
                raw = e.get('raw_data', {})
                print(f"  {e.get('title')}: estimate={raw.get('estimate')}, prev={raw.get('prev')}, actual={raw.get('actual')}")
        
        if events_without_estimate:
            print("\nSample events WITHOUT estimate:")
            for e in events_without_estimate[:3]:
                raw = e.get('raw_data', {})
                print(f"  {e.get('title')}: prev={raw.get('prev')}, actual={raw.get('actual')}")
                print(f"    All fields: {list(raw.keys())}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    examine_raw_finnhub_data()
