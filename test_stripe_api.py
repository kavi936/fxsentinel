#!/usr/bin/env python3
"""
Test Stripe API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_subscription_status():
    """Test the subscription status endpoint"""
    print("🔍 Testing subscription status endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/test_user", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Subscription status endpoint working!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing subscription status: {e}")
        return False

def test_create_customer():
    """Test the create customer endpoint"""
    print("\n🔍 Testing create customer endpoint...")
    
    test_data = {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/create-customer",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Create customer endpoint working!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing create customer: {e}")
        return False

def test_analysis_permission():
    """Test the analysis permission endpoint"""
    print("\n🔍 Testing analysis permission endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/check-analysis-permission/test_user", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Analysis permission endpoint working!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing analysis permission: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Stripe API Endpoints")
    print("=" * 50)
    
    tests = [
        ("Subscription Status", test_subscription_status),
        ("Create Customer", test_create_customer),
        ("Analysis Permission", test_analysis_permission),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API endpoints are working!")
        print("\n📝 Next steps:")
        print("1. Complete Stripe dashboard setup (product & webhook)")
        print("2. Test the frontend trial welcome flow")
        print("3. Add subscription status to dashboard")
    else:
        print("⚠️ Some endpoints failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()
