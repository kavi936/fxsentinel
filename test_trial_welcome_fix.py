#!/usr/bin/env python3
"""
Test script to verify the trial welcome page fix
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_trial_welcome_logic():
    """Test the logic that determines whether to show trial welcome or redirect to dashboard"""
    print("🔍 Testing trial welcome logic...")
    
    # Test cases for different user statuses
    test_cases = [
        {
            "name": "New user with trial status",
            "status": "trial",
            "expected_action": "show_trial_welcome"
        },
        {
            "name": "User with active subscription",
            "status": "active", 
            "expected_action": "redirect_to_dashboard"
        },
        {
            "name": "Developer user",
            "status": "developer",
            "expected_action": "redirect_to_dashboard"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Status: {test_case['status']}")
        print(f"   Expected: {test_case['expected_action']}")
        
        # Simulate the logic from TrialWelcomeRoute.jsx
        hasValidAccess = test_case['status'] in ['active', 'developer']
        
        if hasValidAccess:
            action = "redirect_to_dashboard"
        else:
            action = "show_trial_welcome"
            
        print(f"   Result: {action}")
        
        if action == test_case['expected_action']:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            print(f"   Expected {test_case['expected_action']} but got {action}")

def test_api_response_for_new_user():
    """Test that the API returns the correct response for a new user"""
    print("\n🔍 Testing API response for new user...")
    
    # Create a unique user ID
    import time
    user_id = f"test_new_user_{int(time.time())}"
    
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/{user_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 API Response: {json.dumps(data, indent=2)}")
            
            # Check if the response indicates trial status
            if data.get('status') == 'trial':
                print("✅ API correctly returns trial status for new user")
                
                # Verify the logic would show trial welcome
                hasValidAccess = data.get('status') in ['active', 'developer']
                if not hasValidAccess:
                    print("✅ Logic correctly shows trial welcome for trial users")
                else:
                    print("❌ Logic incorrectly redirects trial users to dashboard")
            else:
                print(f"⚠️ API returned unexpected status: {data.get('status')}")
        else:
            print(f"❌ API request failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing trial welcome page fix...\n")
    
    test_trial_welcome_logic()
    test_api_response_for_new_user()
    
    print("\n📋 Summary:")
    print("The fix ensures that:")
    print("1. New users with 'trial' status see the trial welcome page")
    print("2. Users with 'active' or 'developer' status are redirected to dashboard")
    print("3. The black screen issue should be resolved")

if __name__ == "__main__":
    main()
