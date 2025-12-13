#!/usr/bin/env python3
"""
Test script for date filtering functionality
Tests the economic calendar with specific date ranges
"""

import requests
import json
from datetime import datetime, timedelta

def test_date_filtering():
    """Test the economic calendar with different date ranges"""
    print("🔍 Testing Date Filtering...")
    
    # Test different date ranges
    date_ranges = [
        {
            'name': 'Today Only',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': 'This Week',
            'start_date': (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d'),
            'end_date': (datetime.now() + timedelta(days=6-datetime.now().weekday())).strftime('%Y-%m-%d')
        },
        {
            'name': 'Next Week',
            'start_date': (datetime.now() + timedelta(days=7-datetime.now().weekday())).strftime('%Y-%m-%d'),
            'end_date': (datetime.now() + timedelta(days=13-datetime.now().weekday())).strftime('%Y-%m-%d')
        },
        {
            'name': 'This Month',
            'start_date': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'end_date': ((datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        }
    ]
    
    for date_range in date_ranges:
        print(f"\n📅 Testing: {date_range['name']}")
        print(f"  Date Range: {date_range['start_date']} to {date_range['end_date']}")
        
        try:
            url = f"http://localhost:8000/api/economic-calendar?start_date={date_range['start_date']}&end_date={date_range['end_date']}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                source = data.get('source', 'Unknown')
                
                print(f"  ✅ Success! Source: {source}")
                print(f"  📊 Events found: {len(events)}")
                
                if events:
                    # Analyze the events
                    impact_counts = {}
                    currency_counts = {}
                    
                    for event in events:
                        impact = event.get('impact', 'unknown')
                        impact_counts[impact] = impact_counts.get(impact, 0) + 1
                        
                        currency = event.get('currency', 'unknown')
                        currency_counts[currency] = currency_counts.get(currency, 0) + 1
                    
                    print(f"  📈 Impact distribution: {impact_counts}")
                    print(f"  💰 Currency distribution: {currency_counts}")
                    
                    # Show sample events
                    print("  📅 Sample events:")
                    for i, event in enumerate(events[:3]):
                        print(f"    {i+1}. {event.get('title', 'Unknown')} - {event.get('currency', 'Unknown')} ({event.get('impact', 'Unknown')})")
                        print(f"       Date: {event.get('date', 'Unknown')} | Time: {event.get('time', 'Unknown')}")
                else:
                    print("  ⚠️ No events found for this date range")
            else:
                print(f"  ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_default_vs_filtered():
    """Compare default response vs date-filtered response"""
    print("\n🔍 Testing Default vs Date-Filtered...")
    
    try:
        # Test default endpoint (no date parameters)
        print("📅 Testing default endpoint (no date parameters):")
        default_response = requests.get("http://localhost:8000/api/economic-calendar", timeout=10)
        
        if default_response.status_code == 200:
            default_data = default_response.json()
            default_events = default_data.get('events', [])
            print(f"  📊 Default events: {len(default_events)}")
            
            # Test today's events
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"\n📅 Testing today's events ({today}):")
            today_response = requests.get(f"http://localhost:8000/api/economic-calendar?start_date={today}&end_date={today}", timeout=10)
            
            if today_response.status_code == 200:
                today_data = today_response.json()
                today_events = today_data.get('events', [])
                print(f"  📊 Today's events: {len(today_events)}")
                
                if today_events:
                    print("  📅 Today's sample events:")
                    for i, event in enumerate(today_events[:3]):
                        print(f"    {i+1}. {event.get('title', 'Unknown')} - {event.get('currency', 'Unknown')} ({event.get('impact', 'Unknown')})")
                        print(f"       Date: {event.get('date', 'Unknown')} | Time: {event.get('time', 'Unknown')}")
                
                # Calculate filtering efficiency
                if default_events:
                    efficiency = len(today_events) / len(default_events) * 100
                    print(f"  📊 Filtering efficiency: {efficiency:.1f}%")
                    
                    if efficiency < 10:
                        print("  ✅ Date filtering is working well (showing focused results)")
                    elif efficiency > 50:
                        print("  ⚠️ Date filtering might not be working (showing too many results)")
                    else:
                        print("  ℹ️ Date filtering is working moderately")
            else:
                print(f"  ❌ Today's API Error: {today_response.status_code}")
        else:
            print(f"  ❌ Default API Error: {default_response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    """Run all date filtering tests"""
    print("🚀 Date Filtering Test")
    print("=" * 50)
    
    # Test 1: Different date ranges
    test_date_filtering()
    
    # Test 2: Compare default vs filtered
    test_default_vs_filtered()
    
    print("\n" + "=" * 50)
    print("✅ Date filtering test complete!")
    print("💡 Check if the date ranges are properly filtering events")

if __name__ == "__main__":
    main()
