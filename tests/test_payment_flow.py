#!/usr/bin/env python3
"""
Test Payment Flow for FXSentinel
This script tests the complete payment flow from trial setup to subscription management.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5001"  # Update this to your backend URL
TEST_USER_ID = "test_user_payment_flow"
TEST_EMAIL = "test@fxsentinel.com"
TEST_NAME = "Test User"

def test_payment_flow():
    """Test the complete payment flow"""
    print("🧪 Testing FXSentinel Payment Flow")
    print("=" * 50)
    
    # Test 1: Create Customer
    print("\n1. Testing Customer Creation...")
    customer_data = {
        "user_id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "name": TEST_NAME
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/create-customer", 
                               json=customer_data, timeout=10)
        if response.status_code == 200:
            customer_result = response.json()
            customer_id = customer_result.get('customer_id')
            print(f"✅ Customer created successfully: {customer_id}")
        else:
            print(f"❌ Customer creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Customer creation error: {e}")
        return False
    
    # Test 2: Get Subscription Status
    print("\n2. Testing Subscription Status...")
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/{TEST_USER_ID}", 
                              timeout=10)
        if response.status_code == 200:
            status_result = response.json()
            print(f"✅ Subscription status retrieved:")
            print(f"   Status: {status_result.get('status')}")
            print(f"   Analysis Limit: {status_result.get('analysis_limit')}")
            print(f"   Daily Count: {status_result.get('daily_analysis_count')}")
        else:
            print(f"❌ Subscription status failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Subscription status error: {e}")
    
    # Test 3: Check Analysis Permission
    print("\n3. Testing Analysis Permission...")
    try:
        response = requests.get(f"{BASE_URL}/api/check-analysis-permission/{TEST_USER_ID}", 
                              timeout=10)
        if response.status_code == 200:
            permission_result = response.json()
            print(f"✅ Analysis permission check:")
            print(f"   Can Perform: {permission_result.get('can_analyze')}")
            print(f"   Daily Usage: {permission_result.get('daily_usage')}")
            print(f"   Daily Limit: {permission_result.get('daily_limit')}")
            print(f"   Status: {permission_result.get('status')}")
        else:
            print(f"❌ Analysis permission failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Analysis permission error: {e}")
    
    # Test 4: Test Payment Intent Creation (Setup Intent)
    print("\n4. Testing Payment Intent Creation...")
    payment_data = {
        "customer_id": customer_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/create-payment-intent", 
                               json=payment_data, timeout=10)
        if response.status_code == 200:
            payment_result = response.json()
            client_secret = payment_result.get('client_secret')
            print(f"✅ Payment intent created successfully")
            print(f"   Client Secret: {client_secret[:20]}...")
        else:
            print(f"❌ Payment intent creation failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Payment intent creation error: {e}")
    
    # Test 5: Test Trial Subscription Setup (Mock)
    print("\n5. Testing Trial Subscription Setup...")
    trial_data = {
        "user_id": TEST_USER_ID,
        "customer_id": customer_id,
        "payment_method_id": "pm_test_payment_method"  # Mock payment method ID
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/setup-trial-subscription", 
                               json=trial_data, timeout=10)
        if response.status_code == 200:
            trial_result = response.json()
            subscription_id = trial_result.get('subscription_id')
            print(f"✅ Trial subscription setup successful")
            print(f"   Subscription ID: {subscription_id}")
            print(f"   Trial End Date: {trial_result.get('trial_end_date')}")
        else:
            print(f"❌ Trial subscription setup failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Trial subscription setup error: {e}")
    
    # Test 6: Test Upgrade Subscription
    print("\n6. Testing Upgrade Subscription...")
    upgrade_data = {
        "user_id": TEST_USER_ID,
        "customer_id": customer_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/upgrade-subscription", 
                               json=upgrade_data, timeout=10)
        if response.status_code == 200:
            upgrade_result = response.json()
            subscription_id = upgrade_result.get('subscription_id')
            print(f"✅ Upgrade subscription successful")
            print(f"   Subscription ID: {subscription_id}")
        else:
            print(f"❌ Upgrade subscription failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Upgrade subscription error: {e}")
    
    # Test 7: Final Status Check
    print("\n7. Final Status Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/{TEST_USER_ID}", 
                              timeout=10)
        if response.status_code == 200:
            final_status = response.json()
            print(f"✅ Final subscription status:")
            print(f"   Status: {final_status.get('status')}")
            print(f"   Analysis Limit: {final_status.get('analysis_limit')}")
            print(f"   Daily Count: {final_status.get('daily_analysis_count')}")
        else:
            print(f"❌ Final status check failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Final status check error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Payment Flow Test Complete!")
    print("\nNext Steps:")
    print("1. Test the frontend trial welcome flow")
    print("2. Verify Stripe webhook handling")
    print("3. Test actual payment processing")
    print("4. Verify subscription management in Stripe dashboard")
    
    return True

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔧 Testing Environment Variables...")
    
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'STRIPE_PRODUCT_ID',
        'STRIPE_PRICE_ID',
        'TRIAL_DAYS',
        'TRIAL_ANALYSIS_LIMIT',
        'PAID_ANALYSIS_LIMIT',
        'MONTHLY_PRICE'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'SET' if var.endswith('_KEY') else value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("\n✅ All required environment variables are set!")
    return True

if __name__ == "__main__":
    import os
    
    print("🚀 FXSentinel Payment Flow Test")
    print("=" * 50)
    
    # Test environment variables first
    if not test_environment_variables():
        print("\n❌ Environment test failed. Please fix missing variables.")
        exit(1)
    
    # Test payment flow
    try:
        test_payment_flow()
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
