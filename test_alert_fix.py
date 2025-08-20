#!/usr/bin/env python3
"""
Test script to verify the test alert fix
"""

import requests
import json

def test_alert_endpoint():
    """Test the fixed test alert endpoint"""
    
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"  # Test user ID
    
    print("🧪 Testing Fixed Alert Endpoint")
    print("=" * 50)
    
    # Test the test alert endpoint
    print("\n1. Testing test alert endpoint...")
    try:
        response = requests.post(
            "http://localhost:5001/api/alerts/test",
            json={
                "userId": user_id,
                "alertType": "test",
                "message": "This is a test alert from the fixed endpoint!"
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Test alert sent successfully!")
                print(f"Chat ID: {data.get('chatId', 'Not provided')}")
                print("📱 Check your Telegram for the test message!")
            else:
                print(f"❌ Test alert failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing alert endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_alert_endpoint()
