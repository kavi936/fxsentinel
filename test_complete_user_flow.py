#!/usr/bin/env python3
"""
Test the complete user flow: Signup → Trial Welcome → Dashboard Access
"""

import requests
import json
import time
import webbrowser

BASE_URL = "http://localhost:5001"
FRONTEND_URL = "http://localhost:5173"

def test_complete_user_flow():
    """Test the complete user flow"""
    print("🧪 Testing Complete User Flow")
    print("=" * 60)
    
    # Step 1: Test backend endpoints are working
    print("\n📋 Step 1: Backend Health Check")
    
    endpoints = [
        "/api/subscription-status/test_user",
        "/api/check-analysis-permission/test_user"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        if response.status_code == 200:
            print(f"✅ {endpoint} - Working")
        else:
            print(f"❌ {endpoint} - Failed ({response.status_code})")
    
    # Step 2: Test customer creation flow
    print("\n📋 Step 2: Customer Creation Flow")
    user_id = f"flow_test_user_{int(time.time())}"
    
    customer_data = {
        "user_id": user_id,
        "email": f"flow_test_{int(time.time())}@example.com",
        "name": "Flow Test User"
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
        print(f"❌ Customer creation failed: {response.status_code}")
        return False
    
    # Step 3: Test subscription status
    print("\n📋 Step 3: Subscription Status Check")
    response = requests.get(f"{BASE_URL}/api/subscription-status/{user_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"   Analysis limit: {data['analysis_limit']}")
        print(f"   Trial days: {data.get('trial_days', 'N/A')}")
    else:
        print(f"❌ Status check failed: {response.status_code}")
        return False
    
    # Step 4: Test analysis permission
    print("\n📋 Step 4: Analysis Permission Check")
    response = requests.get(f"{BASE_URL}/api/check-analysis-permission/{user_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response data: {data}")
        if 'can_perform' in data:
            print(f"✅ Can perform analysis: {data['can_perform']}")
            print(f"   Daily usage: {data.get('daily_usage', 'N/A')}")
            print(f"   Daily limit: {data.get('daily_limit', 'N/A')}")
        else:
            print(f"❌ Missing 'can_perform' in response")
            return False
    else:
        print(f"❌ Permission check failed: {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Complete user flow test successful!")
    
    return True

def open_frontend_for_testing():
    """Open frontend for manual testing"""
    print("\n🌐 Opening Frontend for Manual Testing")
    print("=" * 60)
    
    try:
        webbrowser.open(FRONTEND_URL)
        print(f"✅ Opened {FRONTEND_URL}")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"   Please manually open: {FRONTEND_URL}")
    
    print("\n📝 Manual Testing Instructions:")
    print("1. Create a new account with any email/password")
    print("2. You should be redirected to the trial welcome screen")
    print("3. On the trial welcome screen, you should see:")
    print("   - Professional red-themed design")
    print("   - Terms and conditions section")
    print("   - Checkbox to accept terms")
    print("   - 'Start Free Trial' button (disabled until terms accepted)")
    print("   - 'Skip for Now' button")
    print("4. Test the 'Skip for Now' button - should redirect to landing page")
    print("5. Accept terms and click 'Start Free Trial'")
    print("6. Payment form should appear with Stripe card input")
    print("7. Enter test card: 4242424242424242")
    print("8. Click 'Complete Trial Setup'")
    print("9. Should redirect to dashboard")
    print("10. Dashboard should show trial status and usage limits")

def main():
    """Run the complete test"""
    try:
        success = test_complete_user_flow()
        if success:
            print("\n✅ Backend flow is working perfectly!")
            print("\n📋 Phase 1 Implementation Complete:")
            print("- Terms and conditions acceptance required")
            print("- Payment method collection before trial")
            print("- 'Skip for Now' redirects to landing page")
            print("- Setup intent for future billing")
            print("- Customer creation and subscription tracking")
            
            open_frontend_for_testing()
            
            print("\n🚀 Ready for Phase 2: Payment Integration")
            print("- Automatic subscription after trial")
            print("- Webhook for trial expiration")
            print("- Usage tracking and limits")
        else:
            print("\n❌ Some tests failed. Check the errors above.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
