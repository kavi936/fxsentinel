#!/usr/bin/env python3
"""
Test script to debug black screen issue on trial-welcome page
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_subscription_status_endpoint():
    """Test the subscription status endpoint that might be causing the black screen"""
    print("🔍 Testing subscription status endpoint...")
    
    # Test with a non-existent user (simulating new user)
    test_user_id = "new_user_123"
    
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/{test_user_id}", timeout=10)
        print(f"📡 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_backend_health():
    """Test if the backend is running and healthy"""
    print("\n🏥 Testing backend health...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"📡 Backend status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"⚠️ Backend returned status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")

def test_firebase_connection():
    """Test if Firebase connection is working"""
    print("\n🔥 Testing Firebase connection...")
    
    try:
        # Test a simple endpoint that uses Firebase
        response = requests.get(f"{BASE_URL}/api/subscription-status/test_user", timeout=10)
        print(f"📡 Firebase test response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Firebase connection working: {json.dumps(data, indent=2)}")
        else:
            print(f"⚠️ Firebase test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Firebase test error: {e}")

def simulate_new_user_flow():
    """Simulate the exact flow a new user would experience"""
    print("\n👤 Simulating new user flow...")
    
    # Step 1: Check if user exists (should not exist)
    user_id = "new_user_" + str(int(time.time()))
    print(f"🆔 Testing with user ID: {user_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/subscription-status/{user_id}", timeout=10)
        print(f"📡 New user check response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 New user data: {json.dumps(data, indent=2)}")
            
            # Check if this would cause the black screen
            if data is None:
                print("⚠️ WARNING: API returned None - this could cause black screen!")
            elif 'error' in data:
                print(f"⚠️ WARNING: API returned error - this could cause black screen!")
                print(f"   Error: {data['error']}")
            else:
                print("✅ API returned valid data")
                
        elif response.status_code == 404:
            print("✅ Expected 404 for new user")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ New user flow test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting trial-welcome black screen debug tests...\n")
    
    test_backend_health()
    test_subscription_status_endpoint()
    test_firebase_connection()
    simulate_new_user_flow()
    
    print("\n📋 Summary:")
    print("If you see any 'WARNING' messages above, those could be causing the black screen.")
    print("The most likely causes are:")
    print("1. API endpoint returning None or error for new users")
    print("2. Firebase connection issues")
    print("3. Network timeouts")
    print("4. CORS issues")

if __name__ == "__main__":
    main()
