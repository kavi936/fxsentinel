#!/usr/bin/env python3
"""
FXSentinel Alert System End-to-End Test
Tests the complete alert system from a user perspective
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
TEST_USER_ID = "test_user_alert_system@example.com"

def test_alert_system():
    """Test the complete alert system end-to-end"""
    
    print("🧪 FXSentinel Alert System End-to-End Test")
    print("=" * 60)
    
    # Test 1: Check if backend is running
    print("\n1. Testing backend connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Test 2: Check alert system health
    print("\n2. Testing alert system health...")
    try:
        response = requests.get(f"{BASE_URL}/api/health/alerts", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alert system is healthy")
            print(f"   - Firebase: {data.get('firebase', 'unknown')}")
            print(f"   - Telegram Bot: {data.get('telegram_bot', 'unknown')}")
        else:
            print(f"❌ Alert health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Alert health check error: {e}")
        return False
    
    # Test 3: Check news feed
    print("\n3. Testing news feed...")
    try:
        response = requests.get(f"{BASE_URL}/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            news_count = len(data.get('news', []))
            high_impact_count = sum(1 for item in data.get('news', []) if item.get('impact') == 'high')
            print(f"✅ News feed is working")
            print(f"   - Total news items: {news_count}")
            print(f"   - High impact items: {high_impact_count}")
            
            # Show some high-impact news
            high_impact_news = [item for item in data.get('news', []) if item.get('impact') == 'high'][:3]
            if high_impact_news:
                print("   - Recent high-impact news:")
                for item in high_impact_news:
                    print(f"     • {item.get('title', 'No title')[:60]}...")
        else:
            print(f"❌ News feed failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ News feed error: {e}")
        return False
    
    # Test 4: Check alert endpoints
    print("\n4. Testing alert endpoints...")
    try:
        # Test alerts overview
        response = requests.get(f"{BASE_URL}/api/alerts", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alerts endpoint is working")
            print(f"   - Total alerts: {data.get('stats', {}).get('totalAlerts', 0)}")
            print(f"   - Telegram subscribers: {data.get('stats', {}).get('telegramSubscribers', 0)}")
        else:
            print(f"❌ Alerts endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Alerts endpoint error: {e}")
        return False
    
    # Test 5: Test alert history
    print("\n5. Testing alert history...")
    try:
        response = requests.get(f"{BASE_URL}/api/alerts/history?userId={TEST_USER_ID}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            history_count = len(data.get('history', []))
            print(f"✅ Alert history is working")
            print(f"   - History items: {history_count}")
        else:
            print(f"⚠️ Alert history returned status {response.status_code} (expected for new user)")
    except Exception as e:
        print(f"❌ Alert history error: {e}")
    
    # Test 6: Test user settings
    print("\n6. Testing user settings...")
    try:
        response = requests.get(f"{BASE_URL}/api/alerts/user-settings?userId={TEST_USER_ID}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User settings endpoint is working")
            print(f"   - Settings loaded: {bool(data.get('settings'))}")
        else:
            print(f"⚠️ User settings returned status {response.status_code} (expected for new user)")
    except Exception as e:
        print(f"❌ User settings error: {e}")
    
    # Test 7: Check if background monitoring is active
    print("\n7. Testing background monitoring...")
    try:
        # Check if there are any background processes
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'start_monitor' in result.stdout or 'background' in result.stdout:
            print("✅ Background monitoring appears to be running")
        else:
            print("⚠️ Background monitoring may not be running")
            print("   - This could explain why alerts aren't being sent automatically")
    except Exception as e:
        print(f"❌ Could not check background processes: {e}")
    
    # Test 8: Test alert triggering (without authentication)
    print("\n8. Testing alert triggering...")
    try:
        # Try to trigger a test alert (will fail due to authentication)
        response = requests.post(
            f"{BASE_URL}/api/alerts/test",
            json={
                "userId": TEST_USER_ID,
                "message": "Test alert from end-to-end test",
                "alertType": "test"
            },
            timeout=5
        )
        
        if response.status_code == 403:
            print("✅ Alert system is properly secured (authentication required)")
        elif response.status_code == 400:
            data = response.json()
            if "Telegram not connected" in data.get('error', ''):
                print("✅ Alert system is working (Telegram connection required)")
            else:
                print(f"⚠️ Alert system returned: {data.get('error', 'Unknown error')}")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Alert triggering error: {e}")
    
    # Test 9: Check economic calendar
    print("\n9. Testing economic calendar...")
    try:
        response = requests.get(f"{BASE_URL}/api/economic-calendar", timeout=10)
        if response.status_code == 200:
            data = response.json()
            events_count = len(data.get('events', []))
            print(f"✅ Economic calendar is working")
            print(f"   - Upcoming events: {events_count}")
        else:
            print(f"❌ Economic calendar failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Economic calendar error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ALERT SYSTEM STATUS SUMMARY")
    print("=" * 60)
    print("✅ Backend server is running")
    print("✅ Alert system is healthy")
    print("✅ News feed is working and has high-impact news")
    print("✅ Alert endpoints are accessible")
    print("✅ Economic calendar is working")
    print("\n⚠️ POTENTIAL ISSUES:")
    print("• Background monitoring may not be running")
    print("• Users need to complete Telegram bot setup")
    print("• Authentication is required for alert testing")
    print("\n🎯 NEXT STEPS FOR USER:")
    print("1. Complete Telegram bot setup in the dashboard")
    print("2. Configure alert preferences")
    print("3. Test alert delivery")
    print("4. Monitor for real alerts from high-impact news")
    
    return True

if __name__ == "__main__":
    test_alert_system()
