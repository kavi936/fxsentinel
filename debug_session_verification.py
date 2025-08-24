#!/usr/bin/env python3
"""
Debug script to test session verification and user data
"""

import requests
import json

BASE_URL = "https://fxsentinel-production.up.railway.app"

def test_session_verification():
    """Test session verification with the actual session ID"""
    print("🧪 Testing Session Verification...")
    
    # Use the actual session ID from the URL
    session_id = "cs_live_a10ftVgxBilCKfsdkJ3A0y2D2rXI4f9rXVsOrMtMZoAeTiIenKk2j8NyQD"
    
    print(f"Session ID: {session_id}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/verify-checkout-session", 
                               json={"session_id": session_id}, 
                               timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Session verification successful!")
            print(f"   Subscription Status: {data.get('subscription_status')}")
            print(f"   Trial End Date: {data.get('trial_end_date')}")
        else:
            print("❌ Session verification failed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_user_creation():
    """Test if user creation is working"""
    print("\n🧪 Testing User Creation...")
    
    test_data = {
        "user_id": "test_user_debug",
        "email": "test@example.com",
        "name": "Test User"
    }
    
    try:
        # Test checkout session creation
        response = requests.post(f"{BASE_URL}/api/create-checkout-session", 
                               json=test_data, 
                               timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Checkout session creation successful!")
        else:
            print("❌ Checkout session creation failed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_firebase_status():
    """Test Firebase availability"""
    print("\n🧪 Testing Firebase Status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Server Status: {data.get('status')}")
            print(f"Firebase Available: {'firebase' in str(data).lower()}")
        else:
            print("❌ Health check failed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    print("🚀 Debugging Session Verification and User Data")
    print("=" * 60)
    
    # Test Firebase status
    test_firebase_status()
    
    # Test user creation
    test_user_creation()
    
    # Test session verification
    test_session_verification()
    
    print("\n" + "=" * 60)
    print("📋 Summary:")
    print("   If Firebase is not available, users won't be stored")
    print("   If users aren't stored, session verification fails")
    print("   If session verification fails, trial status isn't updated")
    print("\n   Solution: Fix Firebase configuration in Railway")

if __name__ == "__main__":
    main()
