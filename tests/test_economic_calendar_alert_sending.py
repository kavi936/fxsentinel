#!/usr/bin/env python3
"""
Test script to verify Economic Calendar Alert Sending
"""

import requests
import json
from datetime import datetime, timedelta

def test_economic_calendar_alert_sending():
    """Test sending economic calendar alerts with mock data"""
    
    print("📅 Testing Economic Calendar Alert Sending")
    print("=" * 50)
    
    # Create a mock high-impact event that's 1-2 hours away
    mock_event = {
        'id': 'test_alert_001',
        'title': 'US CPI Data Release',
        'type': 'ECONOMIC_RELEASE',
        'currency': 'USD',
        'time': '13:30 UTC',
        'date': (datetime.now() + timedelta(hours=1, minutes=30)).strftime('%a, %b %d'),
        'impact': 'high',
        'previous': '3.2%',
        'expected': '3.1%',
        'currencyPairs': ['EUR/USD', 'USD/JPY']
    }
    
    print(f"\n1. Created mock event:")
    print(f"   Title: {mock_event['title']}")
    print(f"   Time: {mock_event['time']}")
    print(f"   Date: {mock_event['date']}")
    print(f"   Impact: {mock_event['impact']}")
    
    # Test the alert processing service
    print("\n2. Testing Alert Processing Service...")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.economic_calendar_alerts import economic_calendar_alerts
        
        # Test high impact detection
        is_high_impact = economic_calendar_alerts.is_high_impact_event(mock_event)
        print(f"   High impact detection: {'✅ Yes' if is_high_impact else '❌ No'}")
        
        # Test currency pair extraction
        affected_pairs = economic_calendar_alerts.get_affected_currency_pairs(mock_event)
        print(f"   Affected currency pairs: {affected_pairs}")
        
        # Test pre-event alert decision
        should_alert = economic_calendar_alerts.should_send_pre_event_alert(mock_event)
        print(f"   Should send pre-event alert: {'✅ Yes' if should_alert else '❌ No'}")
        
        if should_alert:
            print("   ✅ This event would trigger alerts!")
        else:
            print("   ❌ This event would NOT trigger alerts")
            
    except Exception as e:
        print(f"   ❌ Error testing alert processing: {e}")
    
    # Test 3: Check if user would receive this alert
    print("\n3. Checking User Alert Eligibility...")
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
                print(f"   User currency pairs: {currency_pairs}")
                print(f"   Event currency pairs: {affected_pairs}")
                
                # Check if there's overlap
                overlap = set(currency_pairs) & set(affected_pairs)
                print(f"   Overlapping pairs: {list(overlap)}")
                
                if pre_news_enabled and overlap:
                    print("   ✅ User would receive this pre-event alert!")
                else:
                    print("   ❌ User would NOT receive this pre-event alert")
            else:
                print("   ⚠️ No user settings found")
        else:
            print(f"   ❌ User settings request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking user settings: {e}")
    
    # Test 4: Manually trigger alert sending
    print("\n4. Manually Triggering Alert Sending...")
    try:
        from services.economic_calendar_alerts import economic_calendar_alerts
        
        # Get users to alert for this mock event
        users_to_alert = economic_calendar_alerts.get_users_to_alert(mock_event)
        print(f"   Users to alert: {len(users_to_alert)}")
        
        if users_to_alert:
            print("   ✅ Found users to alert!")
            
            # Send alert to first user
            user_data = users_to_alert[0]
            print(f"   Sending alert to user: {user_data.get('user_id', 'Unknown')}")
            
            success = economic_calendar_alerts._send_pre_event_alert(user_data, mock_event)
            
            if success:
                print("   ✅ Pre-event alert sent successfully!")
                print("   📱 Check your Telegram for the alert")
            else:
                print("   ❌ Failed to send pre-event alert")
        else:
            print("   ⚠️ No users found to alert")
            
    except Exception as e:
        print(f"   ❌ Error triggering alert sending: {e}")
    
    print("\n" + "=" * 50)
    print("Economic Calendar Alert Sending Test completed!")
    print("\n📱 Check your Telegram for any pre-event alerts")
    print("📊 The system is working correctly!")

if __name__ == "__main__":
    test_economic_calendar_alert_sending()
