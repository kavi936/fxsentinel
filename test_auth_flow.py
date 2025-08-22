#!/usr/bin/env python3
"""
Test Authentication Flow and Developer Bypass
Tests the complete authentication flow including developer bypass
"""

import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:5001"
FRONTEND_URL = "http://localhost:5173"

def test_backend_developer_access():
    """Test backend developer access"""
    print("🧪 Testing Backend Developer Access")
    print("=" * 50)
    
    # Test with developer email
    developer_email = "kavi.cf412@gmail.com"
    print(f"📧 Testing developer email: {developer_email}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/subscription-status/test_user",
            params={'email': developer_email},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Subscription status: {data.get('status')}")
            print(f"   Is developer: {data.get('is_developer', False)}")
            print(f"   Daily limit: {data.get('analysis_limit')}")
            
            if data.get('status') == 'developer' and data.get('is_developer'):
                print("✅ Backend developer access confirmed!")
                return True
            else:
                print("❌ Backend developer access not working")
                return False
        else:
            print(f"❌ Failed to get subscription status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing backend developer access: {e}")
        return False

def test_frontend_access():
    """Test frontend accessibility"""
    print("\n🧪 Testing Frontend Access")
    print("=" * 50)
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing frontend: {e}")
        return False

def test_backend_health():
    """Test backend health"""
    print("\n🧪 Testing Backend Health")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data.get('status')}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking backend health: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Authentication Flow and Developer Bypass")
    print("=" * 60)
    
    # Test backend health first
    if not test_backend_health():
        print("\n❌ Backend is not healthy. Please start the backend server.")
        return False
    
    # Test frontend access
    if not test_frontend_access():
        print("\n❌ Frontend is not accessible. Please start the frontend server.")
        return False
    
    # Test backend developer access
    if not test_backend_developer_access():
        print("\n❌ Backend developer access is not working.")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📋 Next steps:")
    print("   1. Open http://localhost:5173 in your browser")
    print("   2. Try logging in with your developer email: kavi.cf412@gmail.com")
    print("   3. You should be redirected directly to the dashboard (bypassing trial welcome)")
    print("   4. Try logging in with a non-developer email to see the trial welcome screen")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
