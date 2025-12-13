#!/usr/bin/env python3
"""
Direct test for Economic Calendar Alert with actual user
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.economic_calendar_alerts import economic_calendar_alerts
from services.firebase_realtime_storage import FirebaseRealtimeStorage
from datetime import datetime, timedelta

def test_direct_economic_alert():
    """Test economic calendar alert directly with the user"""
    
    print("📅 Direct Economic Calendar Alert Test")
    print("=" * 50)
    
    # Your actual user ID
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    print(f"Testing with user ID: {user_id}")
    
    # Create a mock high-impact event that's 1-2 hours away
    mock_event = {
        'id': 'test_direct_001',
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
    
    print(f"\n1. Mock event created:")
    print(f"   Title: {mock_event['title']}")
    print(f"   Time: {mock_event['time']}")
    print(f"   Date: {mock_event['date']}")
    
    # Get user's chat ID directly
    print("\n2. Getting user's chat ID...")
    try:
        firebase_storage = FirebaseRealtimeStorage()
        chat_id = firebase_storage.get_telegram_chat_id(user_id)
        
        if chat_id:
            print(f"   ✅ Chat ID found: {chat_id}")
        else:
            print("   ❌ No chat ID found")
            return
    except Exception as e:
        print(f"   ❌ Error getting chat ID: {e}")
        return
    
    # Get user settings
    print("\n3. Getting user settings...")
    try:
        response = requests.get(
            f"http://localhost:5001/api/alerts/user-settings?userId={user_id}",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                settings = data.get('settings', {})
                print("   ✅ User settings found")
                
                # Check if user would receive this alert
                preferences = settings.get('preferences', {})
                pre_news_enabled = preferences.get('alertTypes', {}).get('preNews', True)
                currency_pairs = preferences.get('currencyPairs', [])
                
                print(f"   Pre-news enabled: {pre_news_enabled}")
                print(f"   Currency pairs: {currency_pairs}")
                
                if pre_news_enabled:
                    print("   ✅ User has pre-news alerts enabled")
                else:
                    print("   ❌ User has pre-news alerts disabled")
            else:
                print("   ⚠️ No user settings found")
        else:
            print(f"   ❌ Failed to get user settings: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting user settings: {e}")
    
    # Send the alert directly
    print("\n4. Sending economic calendar alert...")
    try:
        user_data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'settings': {}
        }
        
        success = economic_calendar_alerts._send_pre_event_alert(user_data, mock_event)
        
        if success:
            print("   ✅ Economic calendar alert sent successfully!")
            print("   📱 Check your Telegram for the pre-event alert")
        else:
            print("   ❌ Failed to send economic calendar alert")
            
    except Exception as e:
        print(f"   ❌ Error sending alert: {e}")
    
    print("\n" + "=" * 50)
    print("Direct Economic Calendar Alert Test completed!")

if __name__ == "__main__":
    import requests
    test_direct_economic_alert()
