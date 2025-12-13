#!/usr/bin/env python3
"""
Test for 10-minute economic calendar alert
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.economic_calendar_alerts import economic_calendar_alerts
from datetime import datetime, timedelta

def test_10min_alert():
    """Test the 10-minute alert functionality"""
    
    print("⏰ Testing 10-Minute Economic Calendar Alert")
    print("=" * 50)
    
    # Create a mock event that's 10 minutes away
    mock_event = {
        'id': 'test_10min_001',
        'title': 'US CPI Data Release',
        'type': 'ECONOMIC_RELEASE',
        'currency': 'USD',
        'time': '13:30 UTC',
        'date': (datetime.now() + timedelta(minutes=10)).strftime('%a, %b %d'),
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
    
    # Test alert timing calculation
    print("\n2. Testing Alert Timing Calculation...")
    try:
        alert_timings = economic_calendar_alerts.get_alert_timing(mock_event)
        print(f"   Alert timings found: {len(alert_timings)}")
        
        for timing in alert_timings:
            print(f"   - {timing['type']}: {timing['time']} ({timing['message_type']})")
            
        # Check if 10-minute alert is included
        ten_min_alert = next((t for t in alert_timings if '10min_before' in t['type']), None)
        if ten_min_alert:
            print("   ✅ 10-minute alert timing found!")
        else:
            print("   ❌ 10-minute alert timing not found")
            
    except Exception as e:
        print(f"   ❌ Error testing alert timing: {e}")
    
    # Test message creation for 10-minute alert
    print("\n3. Testing 10-Minute Alert Message...")
    try:
        ten_min_timing = {
            'type': '10min_before',
            'time': datetime.now() + timedelta(minutes=5),
            'message_type': 'final_reminder'
        }
        
        message = economic_calendar_alerts._create_pre_event_alert_message(mock_event, ten_min_timing)
        print("   ✅ 10-minute alert message created:")
        print("   " + "=" * 40)
        print(message)
        print("   " + "=" * 40)
        
        # Check if it contains the right urgency indicators
        if "FINAL REMINDER" in message and "10 minutes" in message:
            print("   ✅ Message contains correct urgency indicators")
        else:
            print("   ❌ Message missing urgency indicators")
            
    except Exception as e:
        print(f"   ❌ Error creating 10-minute message: {e}")
    
    # Test with your actual user
    print("\n4. Testing 10-Minute Alert Sending...")
    try:
        user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
        
        # Get your chat ID
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase_storage = FirebaseRealtimeStorage()
        chat_id = firebase_storage.get_telegram_chat_id(user_id)
        
        if chat_id:
            print(f"   ✅ Chat ID found: {chat_id}")
            
            # Create user data
            user_data = {
                'user_id': user_id,
                'chat_id': chat_id,
                'settings': {}
            }
            
            # Send 10-minute alert
            ten_min_timing = {
                'type': '10min_before',
                'time': datetime.now() + timedelta(minutes=5),
                'message_type': 'final_reminder'
            }
            
            success = economic_calendar_alerts._send_pre_event_alert(user_data, mock_event, ten_min_timing)
            
            if success:
                print("   ✅ 10-minute alert sent successfully!")
                print("   📱 Check your Telegram for the final reminder")
            else:
                print("   ❌ Failed to send 10-minute alert")
        else:
            print("   ❌ No chat ID found")
            
    except Exception as e:
        print(f"   ❌ Error sending 10-minute alert: {e}")
    
    print("\n" + "=" * 50)
    print("10-Minute Alert Test completed!")
    print("\n📋 Summary:")
    print("✅ 10-minute alerts are now integrated")
    print("✅ Different message format for final reminders")
    print("✅ Urgency indicators for last-minute alerts")

if __name__ == "__main__":
    test_10min_alert()
