#!/usr/bin/env python3
"""
Test script for the new Stripe Checkout flow
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:5001"  # Update if your backend runs on different port
TEST_USER_ID = "test_user_123"
TEST_EMAIL = "test@example.com"
TEST_NAME = "Test User"

def test_create_checkout_session():
    """Test creating a Stripe Checkout Session"""
    print("🧪 Testing Stripe Checkout Session creation...")
    
    url = f"{BASE_URL}/api/create-checkout-session"
    payload = {
        "user_id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "name": TEST_NAME
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            session_url = data.get('session_url')
            
            if session_url and session_url.startswith('https://checkout.stripe.com'):
                print("✅ Checkout session created successfully!")
                print(f"   Session URL: {session_url}")
                print("   You can visit this URL to test the payment flow")
                return session_url
            else:
                print("❌ Invalid session URL returned")
                print(f"   Response: {data}")
                return None
        else:
            print(f"❌ Failed to create checkout session")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_environment_setup():
    """Test if environment variables are properly configured"""
    print("🔧 Testing environment configuration...")
    
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY', 
        'STRIPE_PRICE_ID',
        'TRIAL_DAYS'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"   ✅ {var}: {'SET' if var.endswith('_KEY') else value}")
    
    if missing_vars:
        print(f"   ❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

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
    print("🚀 Testing Stripe Checkout Integration")
    print("=" * 50)
    
    # Test 1: Environment setup
    if not test_environment_setup():
        print("\n❌ Environment setup failed. Please check your .env file")
        return
    
    print()
    
    # Test 2: Backend connection
    if not test_backend_connection():
        print("\n❌ Backend connection failed. Please start your backend server")
        return
    
    print()
    
    # Test 3: Checkout session creation
    session_url = test_create_checkout_session()
    
    print("\n" + "=" * 50)
    if session_url:
        print("🎉 All tests passed! Your Stripe Checkout integration is working.")
        print("\n📋 Next steps:")
        print("   1. Visit the session URL above to test the payment flow")
        print("   2. Use Stripe test card: 4242 4242 4242 4242")
        print("   3. Complete the checkout to test the full flow")
        print("   4. Check your backend logs for webhook events")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
