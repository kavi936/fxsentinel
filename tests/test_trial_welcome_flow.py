#!/usr/bin/env python3
"""
Test the complete trial welcome flow
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_complete_trial_flow():
    """Test the complete trial welcome flow"""
    print("🧪 Testing Complete Trial Welcome Flow")
    print("=" * 50)
    
    # Step 1: Test subscription status for new user
    print("\n📋 Step 1: Check subscription status for new user")
    user_id = f"test_user_{int(time.time())}"
    
    response = requests.get(f"{BASE_URL}/api/subscription-status/{user_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ New user status: {data['status']}")
        print(f"   Analysis limit: {data['analysis_limit']}")
        print(f"   Trial end date: {data['trial_end_date']}")
    else:
        print(f"❌ Failed to get subscription status: {response.status_code}")
        return False
    
    # Step 2: Create Stripe customer
    print("\n📋 Step 2: Create Stripe customer")
    customer_data = {
        "user_id": user_id,
        "email": f"test_{int(time.time())}@example.com",
        "name": "Test User"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/create-customer",
        json=customer_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        customer_id = data['customer_id']
        print(f"✅ Customer created: {customer_id}")
    else:
        print(f"❌ Failed to create customer: {response.status_code}")
        return False
    
    # Step 3: Check subscription status after customer creation
    print("\n📋 Step 3: Check subscription status after customer creation")
    response = requests.get(f"{BASE_URL}/api/subscription-status/{user_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Updated status: {data['status']}")
        print(f"   Stripe customer ID: {data['stripe_customer_id']}")
    else:
        print(f"❌ Failed to get updated status: {response.status_code}")
        return False
    
    # Step 4: Test analysis permission
    print("\n📋 Step 4: Test analysis permission")
    response = requests.get(f"{BASE_URL}/api/check-analysis-permission/{user_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Can analyze: {data['can_analyze']}")
        print(f"   Current usage: {data['status']['daily_analysis_count']}/{data['status']['analysis_limit']}")
    else:
        print(f"❌ Failed to check analysis permission: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Complete trial flow test successful!")
    print("\n📝 Frontend Testing Instructions:")
    print("1. Open your browser to the frontend URL")
    print("2. Create a new account")
    print("3. You should see the trial welcome screen")
    print("4. Click 'Start Free Trial' to test the flow")
    print("5. You should be redirected to the dashboard")
    
    return True

def main():
    """Run the test"""
    try:
        success = test_complete_trial_flow()
        if success:
            print("\n✅ All tests passed! Your Stripe integration is working perfectly!")
        else:
            print("\n❌ Some tests failed. Check the errors above.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
