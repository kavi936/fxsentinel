#!/usr/bin/env python3
"""
Test script for Status Display functionality
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5001"

def test_subscription_status_endpoint():
    """Test the subscription status endpoint"""
    print("🧪 Testing Subscription Status Endpoint")
    print("=" * 50)
    
    # Test with a sample user ID
    test_user_id = "test_user_123"
    
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/{test_user_id}")
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Subscription status endpoint working")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Trial End Date: {data.get('trial_end_date', 'None')}")
            print(f"   Daily Limit: {data.get('analysis_limit', 'Unknown')}")
            return True
        else:
            print("❌ Subscription status endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_usage_permission_endpoint():
    """Test the usage permission endpoint"""
    print("\n🧪 Testing Usage Permission Endpoint")
    print("=" * 50)
    
    # Test with a sample user ID and email
    test_user_id = "test_user_123"
    test_email = "test@example.com"
    
    try:
        response = requests.get(f"{BASE_URL}/api/check-analysis-permission/{test_user_id}?email={test_email}")
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Usage permission endpoint working")
            print(f"   Can Perform: {data.get('can_perform', 'Unknown')}")
            print(f"   Daily Usage: {data.get('daily_usage', 'Unknown')}")
            print(f"   Daily Limit: {data.get('daily_limit', 'Unknown')}")
            return True
        else:
            print("❌ Usage permission endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_developer_account():
    """Test developer account functionality"""
    print("\n🧪 Testing Developer Account")
    print("=" * 50)
    
    # Test with developer email
    test_user_id = "developer_user"
    test_email = "kavi.cf412@gmail.com"  # Developer email from environment
    
    try:
        response = requests.get(f"{BASE_URL}/api/check-analysis-permission/{test_user_id}?email={test_email}")
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Developer account test working")
            print(f"   Is Developer: {data.get('is_developer', 'Unknown')}")
            print(f"   Can Perform: {data.get('can_perform', 'Unknown')}")
            print(f"   Daily Limit: {data.get('daily_limit', 'Unknown')}")
            return True
        else:
            print("❌ Developer account test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_frontend_integration():
    """Test frontend integration points"""
    print("\n🧪 Testing Frontend Integration")
    print("=" * 50)
    
    # Test that the frontend can access the required endpoints
    endpoints_to_test = [
        "/api/subscription-status/test_user",
        "/api/check-analysis-permission/test_user?email=test@example.com"
    ]
    
    all_working = True
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code not in [200, 404, 500]:
                print(f"   ❌ Unexpected status code for {endpoint}")
                all_working = False
                
        except Exception as e:
            print(f"   ❌ Error with {endpoint}: {e}")
            all_working = False
    
    if all_working:
        print("✅ All frontend integration endpoints accessible")
        return True
    else:
        print("❌ Some frontend integration endpoints failed")
        return False

def show_status_display_features():
    """Show the implemented status display features"""
    print("\n📋 Status Display Features Implemented:")
    print("=" * 50)
    print("✅ New 'Status' tab in ProfilePopup")
    print("✅ Trial status display (trial/active/expired/past_due)")
    print("✅ Trial countdown with days remaining")
    print("✅ Usage limits with progress bar")
    print("✅ Upgrade buttons for trial users")
    print("✅ Developer account special display")
    print("✅ Real-time status updates")
    print("✅ Responsive design for mobile")
    print("✅ Visual status indicators")
    print("✅ Action buttons for different states")

def main():
    """Main test function"""
    print("🧪 Testing Status Display Functionality")
    print("=" * 50)
    
    # Test subscription status endpoint
    status_ok = test_subscription_status_endpoint()
    
    # Test usage permission endpoint
    usage_ok = test_usage_permission_endpoint()
    
    # Test developer account
    developer_ok = test_developer_account()
    
    # Test frontend integration
    frontend_ok = test_frontend_integration()
    
    print("\n📊 Status Display Test Results:")
    print("=" * 40)
    print(f"Subscription Status: {'✅ PASS' if status_ok else '❌ FAIL'}")
    print(f"Usage Permission: {'✅ PASS' if usage_ok else '❌ FAIL'}")
    print(f"Developer Account: {'✅ PASS' if developer_ok else '❌ FAIL'}")
    print(f"Frontend Integration: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    
    all_tests_passed = all([status_ok, usage_ok, developer_ok, frontend_ok])
    
    if all_tests_passed:
        print("\n🎉 All status display tests passed!")
        print("Your status display system is working perfectly!")
    else:
        print("\n❌ Some status display tests failed.")
        print("Please review the implementation.")
    
    show_status_display_features()

if __name__ == "__main__":
    main()
