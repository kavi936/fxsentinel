#!/usr/bin/env python3
"""
Test script for the Stripe Customer Portal session endpoint
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:5001"
TEST_USER_ID = "test_user_123"

def test_create_portal_session():
    """Test creating a Stripe Customer Portal session"""
    print("🧪 Testing Stripe Customer Portal session creation...")
    
    url = f"{BASE_URL}/api/create-portal-session"
    payload = {
        "user_id": TEST_USER_ID,
        "return_url": "http://localhost:3000/dashboard"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            portal_url = data.get('url')
            
            if portal_url and portal_url.startswith('https://billing.stripe.com'):
                print("✅ Portal session created successfully!")
                print(f"   Portal URL: {portal_url}")
                print("   You can visit this URL to test the customer portal")
                return portal_url
            else:
                print("❌ Invalid portal URL returned")
                print(f"   Response: {data}")
                return None
        else:
            print(f"❌ Failed to create portal session")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_backend_connection():
    """Test if backend is running and accessible"""
    print("🌐 Testing backend connection...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 5001")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Stripe Customer Portal Integration")
    print("=" * 50)
    
    # Test 1: Backend connection
    if not test_backend_connection():
        print("\n❌ Backend connection failed. Please start your backend server")
        return
    
    print()
    
    # Test 2: Portal session creation
    portal_url = test_create_portal_session()
    
    print("\n" + "=" * 50)
    if portal_url:
        print("🎉 Portal session test completed!")
        print("\n📋 Next steps:")
        print("   1. Visit the portal URL above to test the customer portal")
        print("   2. Test subscription management features")
        print("   3. Test cancellation flow")
        print("   4. Verify return URL functionality")
    else:
        print("❌ Portal session test failed. Please check the errors above.")
        print("\n💡 Note: This test requires a user with a valid Stripe customer ID")
        print("   You may need to create a test user with a subscription first")

if __name__ == "__main__":
    main()
