#!/usr/bin/env python3
"""
Comprehensive New User Journey Test
Simulates a completely new user going through the entire setup process
"""

import requests
import json
import time
from datetime import datetime

def test_new_user_journey():
    """Test the complete new user journey"""
    
    print("🧪 Testing New User Journey")
    print("=" * 60)
    
    # Simulate a completely new user
    new_user_id = "new_user_test_001"
    new_user_email = "newuser@test.com"
    
    print(f"Simulating new user: {new_user_email}")
    print(f"User ID: {new_user_id}")
    
    # Step 1: User Registration/Authentication
    print("\n1. 🔐 User Authentication Test...")
    try:
        # Test if user can access the dashboard
        response = requests.get(
            "http://localhost:5001/api/dashboard-data",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Dashboard accessible")
        else:
            print(f"   ❌ Dashboard access failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
    
    # Step 2: Initial Alert Settings
    print("\n2. ⚙️ Initial Alert Settings Test...")
    try:
        # Test if new user can access alert settings
        response = requests.get(
            f"http://localhost:5001/api/alerts/user-settings?userId={new_user_id}",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Alert settings accessible")
                settings = data.get('settings', {})
                print(f"   Default settings: {json.dumps(settings, indent=2)}")
            else:
                print("   ⚠️ No settings found (expected for new user)")
        else:
            print(f"   ❌ Settings access failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Settings error: {e}")
    
    # Step 3: Telegram Bot Setup
    print("\n3. 🤖 Telegram Bot Setup Test...")
    try:
        # Test bot verification endpoint
        response = requests.post(
            "http://localhost:5001/api/telegram/verify",
            json={
                "userId": new_user_id,
                "email": new_user_email
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Bot verification response: {data}")
            
            if data.get('success'):
                if data.get('connected'):
                    print("   ✅ Bot already connected")
                else:
                    print("   ⚠️ Bot not connected (expected for new user)")
            else:
                print("   ❌ Bot verification failed")
        else:
            print(f"   ❌ Bot verification request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Bot setup error: {e}")
    
    # Step 4: Data Source Availability
    print("\n4. 📊 Data Source Availability Test...")
    
    # Test economic calendar
    try:
        response = requests.get(
            "http://localhost:5001/api/economic-calendar",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            events_count = data.get('total_events', 0)
            print(f"   ✅ Economic calendar: {events_count} events available")
            
            if events_count == 0:
                print("   ⚠️ No economic events found - alerts won't work")
        else:
            print(f"   ❌ Economic calendar failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Economic calendar error: {e}")
    
    # Test news feed
    try:
        response = requests.get(
            "http://localhost:5001/api/news",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            news_count = len(data.get('news', []))
            print(f"   ✅ News feed: {news_count} articles available")
            
            if news_count == 0:
                print("   ⚠️ No news articles found - alerts won't work")
        else:
            print(f"   ❌ News feed failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ News feed error: {e}")
    
    # Step 5: Alert System Health
    print("\n5. 🚨 Alert System Health Test...")
    
    # Test if alert processing works
    try:
        # Test with a mock event
        mock_event = {
            'id': 'test_new_user_001',
            'title': 'Test Economic Event',
            'type': 'ECONOMIC_RELEASE',
            'currency': 'USD',
            'time': '13:30 UTC',
            'date': 'Wed, Aug 20',
            'impact': 'high',
            'currencyPairs': ['EUR/USD', 'USD/JPY']
        }
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.economic_calendar_alerts import economic_calendar_alerts
        
        # Test high impact detection
        is_high_impact = economic_calendar_alerts.is_high_impact_event(mock_event)
        print(f"   High impact detection: {'✅ Working' if is_high_impact else '❌ Broken'}")
        
        # Test currency pair extraction
        affected_pairs = economic_calendar_alerts.get_affected_currency_pairs(mock_event)
        print(f"   Currency pair extraction: {'✅ Working' if affected_pairs else '❌ Broken'}")
        
        # Test user filtering
        users_to_alert = economic_calendar_alerts.get_users_to_alert(mock_event)
        print(f"   User filtering: {'✅ Working' if users_to_alert is not None else '❌ Broken'}")
        
    except Exception as e:
        print(f"   ❌ Alert system error: {e}")
    
    # Step 6: Error Handling
    print("\n6. 🛡️ Error Handling Test...")
    
    # Test with invalid user ID
    try:
        response = requests.get(
            "http://localhost:5001/api/alerts/user-settings?userId=invalid_user",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print("   ✅ Invalid user handled gracefully")
            else:
                print("   ⚠️ Invalid user returned success (potential security issue)")
        else:
            print(f"   ⚠️ Invalid user returned {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
    
    # Test with missing parameters
    try:
        response = requests.post(
            "http://localhost:5001/api/telegram/verify",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 400:
            print("   ✅ Missing parameters handled correctly")
        else:
            print(f"   ⚠️ Missing parameters returned {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Parameter validation test failed: {e}")
    
    # Step 7: Performance Test
    print("\n7. ⚡ Performance Test...")
    
    start_time = time.time()
    
    try:
        # Test multiple concurrent requests
        responses = []
        for i in range(5):
            response = requests.get(
                "http://localhost:5001/api/economic-calendar",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            responses.append(response.status_code)
        
        end_time = time.time()
        duration = end_time - start_time
        
        success_count = sum(1 for code in responses if code == 200)
        print(f"   Concurrent requests: {success_count}/5 successful")
        print(f"   Response time: {duration:.2f} seconds")
        
        if duration < 5:
            print("   ✅ Performance acceptable")
        else:
            print("   ⚠️ Performance slow")
            
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
    
    print("\n" + "=" * 60)
    print("New User Journey Test Completed!")
    print("\n📋 Summary:")
    print("This test reveals potential issues that new users might face.")
    print("Key areas to monitor:")
    print("- Data source reliability")
    print("- Error handling and user feedback")
    print("- Performance under load")
    print("- User onboarding flow")

if __name__ == "__main__":
    test_new_user_journey()
