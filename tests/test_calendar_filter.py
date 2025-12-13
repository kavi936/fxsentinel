#!/usr/bin/env python3
"""
Test script for calendar filtering functionality
Tests the filtering logic with Finnhub economic calendar data
"""

import requests
import json
from datetime import datetime

def test_calendar_data():
    """Test the economic calendar endpoint"""
    print("🔍 Testing Economic Calendar Data...")
    
    try:
        url = "http://localhost:8000/api/economic-calendar"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            source = data.get('source', 'Unknown')
            
            print(f"✅ Success! Source: {source}")
            print(f"📊 Total events: {len(events)}")
            
            if events:
                # Analyze event distribution
                impact_counts = {}
                currency_counts = {}
                type_counts = {}
                
                for event in events:
                    # Count impact levels
                    impact = event.get('impact', 'unknown')
                    impact_counts[impact] = impact_counts.get(impact, 0) + 1
                    
                    # Count currencies
                    currency = event.get('currency', 'unknown')
                    currency_counts[currency] = currency_counts.get(currency, 0) + 1
                    
                    # Count event types
                    event_type = event.get('type', 'unknown')
                    type_counts[event_type] = type_counts.get(event_type, 0) + 1
                
                print("\n📈 Event Distribution:")
                print(f"  Impact Levels: {impact_counts}")
                print(f"  Currencies: {currency_counts}")
                print(f"  Event Types: {type_counts}")
                
                # Show sample events for each category
                print("\n📅 Sample Events by Impact:")
                for impact in ['high', 'medium', 'low']:
                    impact_events = [e for e in events if e.get('impact') == impact]
                    if impact_events:
                        sample = impact_events[0]
                        print(f"  {impact.upper()}: {sample.get('title', 'Unknown')} ({sample.get('currency', 'Unknown')})")
                
                print("\n📅 Sample Events by Currency:")
                for currency in ['USD', 'EUR', 'GBP', 'JPY']:
                    currency_events = [e for e in events if e.get('currency') == currency]
                    if currency_events:
                        sample = currency_events[0]
                        print(f"  {currency}: {sample.get('title', 'Unknown')} ({sample.get('impact', 'Unknown')})")
                
                return events
            else:
                print("⚠️ No events found")
                return []
        else:
            print(f"❌ API Error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error testing calendar data: {e}")
        return []

def test_filtering_logic(events):
    """Test the filtering logic that would be used in the frontend"""
    print("\n🔍 Testing Filtering Logic...")
    
    if not events:
        print("⚠️ No events to test filtering with")
        return
    
    # Simulate different filter combinations
    filter_tests = [
        {
            'name': 'High Impact Only',
            'impact_levels': {'high': True, 'medium': False, 'low': False},
            'currencies': {'USD': True, 'EUR': True, 'GBP': True, 'JPY': True, 'AUD': True, 'CAD': True, 'CHF': True, 'NZD': True}
        },
        {
            'name': 'USD Events Only',
            'impact_levels': {'high': True, 'medium': True, 'low': True},
            'currencies': {'USD': True, 'EUR': False, 'GBP': False, 'JPY': False, 'AUD': False, 'CAD': False, 'CHF': False, 'NZD': False}
        },
        {
            'name': 'High Impact USD Events',
            'impact_levels': {'high': True, 'medium': False, 'low': False},
            'currencies': {'USD': True, 'EUR': False, 'GBP': False, 'JPY': False, 'AUD': False, 'CAD': False, 'CHF': False, 'NZD': False}
        },
        {
            'name': 'Major Currencies Only',
            'impact_levels': {'high': True, 'medium': True, 'low': True},
            'currencies': {'USD': True, 'EUR': True, 'GBP': True, 'JPY': True, 'AUD': False, 'CAD': False, 'CHF': False, 'NZD': False}
        }
    ]
    
    for test in filter_tests:
        print(f"\n🧪 Testing: {test['name']}")
        
        # Apply filtering logic (same as frontend)
        filtered_events = []
        for event in events:
            impact_match = test['impact_levels'].get(event.get('impact'), False)
            currency_match = test['currencies'].get(event.get('currency'), False)
            
            if impact_match and currency_match:
                filtered_events.append(event)
        
        print(f"  Results: {len(filtered_events)} events (from {len(events)} total)")
        
        if filtered_events:
            print("  Sample filtered events:")
            for i, event in enumerate(filtered_events[:3]):
                print(f"    {i+1}. {event.get('title', 'Unknown')} - {event.get('currency', 'Unknown')} ({event.get('impact', 'Unknown')})")
        else:
            print("  ⚠️ No events match this filter combination")

def test_frontend_filtering():
    """Test the frontend filtering by simulating the getFilteredEvents function"""
    print("\n🔍 Testing Frontend Filtering Simulation...")
    
    # Get events first
    events = test_calendar_data()
    if not events:
        return
    
    # Simulate the getFilteredEvents function from the frontend
    def getFilteredEvents(all_events, filterImpactLevels, filterCurrencies):
        if not all_events:
            return []
        
        return [event for event in all_events if (
            filterImpactLevels.get(event.get('impact'), False) and 
            filterCurrencies.get(event.get('currency'), False)
        )]
    
    # Test different filter scenarios
    scenarios = [
        {
            'name': 'All Filters Enabled',
            'impact_levels': {'high': True, 'medium': True, 'low': True},
            'currencies': {'USD': True, 'EUR': True, 'GBP': True, 'JPY': True, 'AUD': True, 'CAD': True, 'CHF': True, 'NZD': True}
        },
        {
            'name': 'High Impact Major Currencies',
            'impact_levels': {'high': True, 'medium': False, 'low': False},
            'currencies': {'USD': True, 'EUR': True, 'GBP': True, 'JPY': True, 'AUD': False, 'CAD': False, 'CHF': False, 'NZD': False}
        },
        {
            'name': 'USD Only',
            'impact_levels': {'high': True, 'medium': True, 'low': True},
            'currencies': {'USD': True, 'EUR': False, 'GBP': False, 'JPY': False, 'AUD': False, 'CAD': False, 'CHF': False, 'NZD': False}
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎯 Scenario: {scenario['name']}")
        
        filtered = getFilteredEvents(events, scenario['impact_levels'], scenario['currencies'])
        
        print(f"  Total events: {len(events)}")
        print(f"  Filtered events: {len(filtered)}")
        print(f"  Filter efficiency: {len(filtered)/len(events)*100:.1f}%")
        
        if filtered:
            print("  Sample results:")
            for i, event in enumerate(filtered[:2]):
                print(f"    • {event.get('title', 'Unknown')} ({event.get('currency', 'Unknown')} - {event.get('impact', 'Unknown')})")

def main():
    """Run all filter tests"""
    print("🚀 Calendar Filter Testing")
    print("=" * 50)
    
    # Test 1: Get calendar data
    events = test_calendar_data()
    
    # Test 2: Test filtering logic
    test_filtering_logic(events)
    
    # Test 3: Test frontend filtering simulation
    test_frontend_filtering()
    
    print("\n" + "=" * 50)
    print("✅ Filter testing complete!")
    print("💡 The filtering should now work in the frontend")
    print("🔧 Check the browser console for filter status updates")

if __name__ == "__main__":
    main()
