#!/usr/bin/env python3
"""
Test script to verify test alert functionality
"""

import requests
import json

def test_alert_endpoint():
    """Test the test alert endpoint"""
    
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"  # Test user ID
    
    print("🧪 Testing Alert Functionality")
    print("=" * 50)
    
    # Test 1: Send test alert
    print("\n1. Testing test alert endpoint...")
    try:
        response = requests.post(
            "http://localhost:5001/api/alerts/test",
            json={
                "userId": user_id,
                "alertType": "test",
                "message": "This is a test alert from the test script!"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Test alert sent successfully!")
                print(f"Chat ID: {data.get('chatId', 'Not provided')}")
            else:
                print(f"❌ Test alert failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing alert endpoint: {e}")
    
    # Test 2: Check if alert appears in history
    print("\n2. Testing alert history...")
    try:
        response = requests.get(
            f"http://localhost:5001/api/alerts/history?userId={user_id}&limit=5",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"History response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                alerts = data.get("alerts", [])
                print(f"✅ Found {len(alerts)} alerts in history")
                
                # Look for test alert
                test_alerts = [alert for alert in alerts if alert.get("type") == "test"]
                if test_alerts:
                    print("✅ Test alert found in history!")
                    latest_test = test_alerts[0]
                    print(f"   Timestamp: {latest_test.get('timestamp', 'Unknown')}")
                    print(f"   Status: {latest_test.get('status', 'Unknown')}")
                else:
                    print("⚠️ No test alerts found in history")
            else:
                print(f"❌ History request failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ History request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing alert history: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_alert_endpoint()
