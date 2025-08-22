#!/usr/bin/env python3
"""
Test script for Stripe webhook functionality
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5001"

def test_webhook_endpoint():
    """Test if the webhook endpoint is accessible"""
    print("🔍 Testing webhook endpoint accessibility...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/stripe-webhook", 
                               json={"test": "data"},
                               headers={"Content-Type": "application/json"})
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 400:
            print("   ✅ Endpoint is accessible (expected 400 for invalid signature)")
            return True
        else:
            print("   ❌ Unexpected response")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to backend server")
        print("   💡 Make sure the Flask server is running: python3 backend/app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_environment_setup():
    """Test if required environment variables are set"""
    print("\n🔍 Testing environment setup...")
    
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'STRIPE_PRICE_ID',
        'STRIPE_PRODUCT_ID'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'SET' if value else 'NOT SET'}")
        else:
            print(f"   ❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def test_backend_connection():
    """Test basic backend connectivity"""
    print("\n🔍 Testing backend connection...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/test_user")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [200, 404, 500]:
            print("   ✅ Backend is responding")
            return True
        else:
            print("   ❌ Unexpected response")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to backend server")
        print("   💡 Make sure the Flask server is running: python3 backend/app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def show_webhook_setup_instructions():
    """Show instructions for setting up webhooks in Stripe"""
    print("\n📋 Webhook Setup Instructions:")
    print("=" * 50)
    print("1. Go to your Stripe Dashboard")
    print("2. Navigate to Developers > Webhooks")
    print("3. Click 'Add endpoint'")
    print("4. Set the endpoint URL to:")
    print(f"   {BASE_URL}/api/stripe-webhook")
    print("5. Select these events to listen for:")
    print("   - customer.subscription.created")
    print("   - customer.subscription.updated")
    print("   - customer.subscription.deleted")
    print("   - invoice.payment_succeeded")
    print("   - invoice.payment_failed")
    print("6. Click 'Add endpoint'")
    print("7. Copy the webhook signing secret")
    print("8. Add it to your .env file as STRIPE_WEBHOOK_SECRET")
    print("\n💡 For local testing, you can use Stripe CLI:")
    print("   stripe listen --forward-to localhost:5001/api/stripe-webhook")

def main():
    """Main test function"""
    print("🧪 Testing Stripe Webhook Functionality")
    print("=" * 50)
    
    # Test environment setup
    env_ok = test_environment_setup()
    
    # Test backend connection
    backend_ok = test_backend_connection()
    
    # Test webhook endpoint
    webhook_ok = test_webhook_endpoint()
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"Environment Setup: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Backend Connection: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Webhook Endpoint: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    
    if not env_ok:
        print("\n⚠️ Environment variables missing!")
        print("Please set the required environment variables in your .env file")
    
    if not backend_ok:
        print("\n⚠️ Backend server not running!")
        print("Please start the Flask server: python3 backend/app.py")
    
    if webhook_ok and env_ok and backend_ok:
        print("\n🎉 All tests passed! Webhook functionality is ready.")
        print("Next step: Set up webhooks in your Stripe dashboard")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
    
    show_webhook_setup_instructions()

if __name__ == "__main__":
    main()
