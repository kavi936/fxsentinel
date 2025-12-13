#!/usr/bin/env python3
"""
Test script for Economic Calendar Alert System
"""

import requests
import json
from datetime import datetime, timedelta

def test_economic_calendar_alerts():
    """Test the economic calendar alert system"""
    
    print("📅 Testing Economic Calendar Alert System")
    print("=" * 50)
    
    # Test 1: Check economic calendar endpoint
    print("\n1. Testing Economic Calendar Endpoint...")
    try:
        response = requests.get(
            "http://localhost:5001/api/economic-calendar",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Economic calendar fetched successfully!")
            print(f"   Total events: {data.get('total_events', 0)}")
            print(f"   Source: {data.get('source', 'unknown')}")
            print(f"   Status: {data.get('status', 'unknown')}")
            
            # Check if we have events
            events = data.get('events', [])
            if events:
                print(f"   First event: {events[0].get('title', 'No title')[:50]}...")
                print(f"   Event type: {events[0].get('type', 'Unknown')}")
                print(f"   Event impact: {events[0].get('impact', 'Unknown')}")
                
                # Check for high-impact events
                high_impact_count = 0
                for event in events[:5]:
                    if event.get('impact', '').lower() == 'high':
                        high_impact_count += 1
                        print(f"   🔴 High-impact event: {event.get('title', '')[:50]}...")
                
                print(f"   High-impact events in first 5: {high_impact_count}")
            else:
                print("   ⚠️ No events found")
        else:
            print(f"❌ Economic calendar fetch failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing economic calendar: {e}")
    
    # Test 2: Test the alert processing service
    print("\n2. Testing Economic Calendar Alert Processing...")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.economic_calendar_alerts import economic_calendar_alerts
        
        # Test with sample event
        sample_event = {
            'id': 'test_economic_001',
            'title': 'US CPI Data Release',
            'type': 'ECONOMIC_RELEASE',
            'currency': 'USD',
            'time': '13:30 UTC',
            'date': (datetime.now() + timedelta(hours=3)).strftime('%a, %b %d'),
            'impact': 'high',
            'previous': '3.2%',
            'expected': '3.1%',
            'currencyPairs': ['EUR/USD', 'USD/JPY']
        }
        
        # Test high impact detection
        is_high_impact = economic_calendar_alerts.is_high_impact_event(sample_event)
        print(f"   High impact detection: {'✅ Yes' if is_high_impact else '❌ No'}")
        
        # Test currency pair extraction
        affected_pairs = economic_calendar_alerts.get_affected_currency_pairs(sample_event)
        print(f"   Affected currency pairs: {affected_pairs}")
        
        # Test pre-event alert decision
        should_alert = economic_calendar_alerts.should_send_pre_event_alert(sample_event)
        print(f"   Should send pre-event alert: {'✅ Yes' if should_alert else '❌ No'}")
        
        if is_high_impact:
            print("   ✅ This event would trigger alerts!")
        else:
            print("   ❌ This event would NOT trigger alerts")
            
    except Exception as e:
        print(f"   ❌ Error testing alert processing: {e}")
    
    # Test 3: Check user alert settings for pre-event alerts
    print("\n3. Checking User Pre-Event Alert Settings...")
    try:
        # Test with your user ID
        test_user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
        
        response = requests.get(
            f"http://localhost:5001/api/alerts/user-settings?userId={test_user_id}",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                settings = data.get('settings', {})
                preferences = settings.get('preferences', {})
                
                # Check pre-news alert preference
                pre_news_enabled = preferences.get('alertTypes', {}).get('preNews', True)
                print(f"   Pre-news alerts enabled: {'✅ Yes' if pre_news_enabled else '❌ No'}")
                
                # Check currency pairs
                currency_pairs = preferences.get('currencyPairs', [])
                print(f"   Currency pairs: {currency_pairs}")
                
                if pre_news_enabled:
                    print("   ✅ User would receive pre-event alerts!")
                else:
                    print("   ❌ User would NOT receive pre-event alerts")
            else:
                print("   ⚠️ No user settings found")
        else:
            print(f"   ❌ User settings request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking user settings: {e}")
    
    # Test 4: Simulate economic calendar alert processing
    print("\n4. Simulating Economic Calendar Alert Processing...")
    try:
        from services.economic_calendar_alerts import economic_calendar_alerts
        
        # Process the economic calendar
        results = economic_calendar_alerts.process_economic_calendar_for_alerts()
        
        print(f"   Results: {results}")
        
        if results.get('high_impact_events', 0) > 0:
            print("   ✅ High-impact events were found!")
        else:
            print("   ⚠️ No high-impact events found")
            
        if results.get('alerts_sent', 0) > 0:
            print("   ✅ Pre-event alerts were sent!")
        else:
            print("   ⚠️ No pre-event alerts were sent")
            
    except Exception as e:
        print(f"   ❌ Error simulating alert processing: {e}")
    
    print("\n" + "=" * 50)
    print("Economic Calendar Alert Test completed!")
    print("\n📱 Check your Telegram for any pre-event alerts")
    print("📊 Monitor backend logs for processing details")

if __name__ == "__main__":
    test_economic_calendar_alerts()
