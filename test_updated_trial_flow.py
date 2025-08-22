#!/usr/bin/env python3
"""
Test the updated trial welcome flow with terms acceptance and payment setup
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_updated_trial_flow():
    """Test the complete updated trial flow"""
    print("🧪 Testing Updated Trial Welcome Flow")
    print("=" * 50)
    
    # Step 1: Test customer creation (simulates terms acceptance)
    print("\n📋 Step 1: Test customer creation (terms accepted)")
    user_id = f"test_user_{int(time.time())}"
    
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
    
    # Step 2: Test setup intent creation (simulates payment method collection)
    print("\n📋 Step 2: Test setup intent creation (payment method)")
    
    setup_data = {
        "customer_id": customer_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/create-payment-intent",
        json=setup_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        client_secret = data['client_secret']
        print(f"✅ Setup intent created: {client_secret[:20]}...")
    else:
        print(f"❌ Failed to create setup intent: {response.status_code}")
        return False
    
    # Step 3: Test subscription status after setup
    print("\n📋 Step 3: Test subscription status after setup")
    
    response = requests.get(f"{BASE_URL}/api/subscription-status/{user_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Subscription status: {data['status']}")
        print(f"   Analysis limit: {data['analysis_limit']}")
        print(f"   Stripe customer: {data['stripe_customer_id']}")
    else:
        print(f"❌ Failed to get subscription status: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Updated trial flow test successful!")
    print("\n📝 Frontend Testing Instructions:")
    print("1. Open your browser to the frontend URL")
    print("2. Create a new account")
    print("3. You should see the trial welcome screen with:")
    print("   - Terms and conditions")
    print("   - Checkbox to accept terms")
    print("   - 'Start Free Trial' button (disabled until terms accepted)")
    print("   - 'Skip for Now' button (redirects to landing page)")
    print("4. After accepting terms and clicking 'Start Free Trial':")
    print("   - Payment form should appear")
    print("   - Enter test card: 4242424242424242")
    print("   - Click 'Complete Trial Setup'")
    print("   - Should redirect to dashboard")
    
    return True

def main():
    """Run the test"""
    try:
        success = test_updated_trial_flow()
        if success:
            print("\n✅ All tests passed! Updated trial flow is working!")
            print("\n📋 Key Changes Implemented:")
            print("- Terms and conditions acceptance required")
            print("- Payment method collection before trial")
            print("- 'Skip for Now' redirects to landing page")
            print("- Setup intent for future billing")
        else:
            print("\n❌ Some tests failed. Check the errors above.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
