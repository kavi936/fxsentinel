#!/usr/bin/env python3
"""
Test Alert History Endpoint Directly
"""

import requests
import json

def test_history_direct():
    """Test the alert history endpoint directly"""
    
    user_id = "demo_user@example.com"  # User with data in Firebase
    
    print("🧪 Testing Alert History Directly")
    print("=" * 50)
    
    # Test alert history endpoint
    print("\n1. Testing alert history endpoint...")
    try:
        response = requests.get(
            f"http://localhost:5001/api/alerts/history?userId={user_id}&limit=10",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            if data.get("success"):
                history = data.get("history", [])
                print(f"✅ Found {len(history)} alerts in history")
                
                if history:
                    print("\nRecent alerts:")
                    for i, alert in enumerate(history[:3]):
                        print(f"  {i+1}. {alert.get('title', 'No title')}")
                        print(f"     Type: {alert.get('alert_type', 'Unknown')}")
                        print(f"     Status: {alert.get('status', 'Unknown')}")
                        print(f"     Timestamp: {alert.get('timestamp', 'Unknown')}")
                        print()
                else:
                    print("⚠️ No alerts found in history")
            else:
                print(f"❌ History request failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing history: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_history_direct()
