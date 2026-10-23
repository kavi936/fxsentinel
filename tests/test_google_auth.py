#!/usr/bin/env python3
"""
Test Google Authentication Flow
Checks Firebase configuration and authentication setup
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:5001"
FRONTEND_URL = "http://localhost:5173"  # Updated to port 5173

def test_firebase_config():
    """Test Firebase configuration"""
    print("🧪 Testing Firebase Configuration")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv('VITE_FIREBASE_API_KEY')
    auth_domain = os.getenv('VITE_FIREBASE_AUTH_DOMAIN')
    project_id = os.getenv('VITE_FIREBASE_PROJECT_ID')
    
    print(f"📧 API Key: {'✅ Set' if api_key and api_key != 'your_firebase_api_key_here' else '❌ Not set or placeholder'}")
    print(f"🌐 Auth Domain: {'✅ Set' if auth_domain else '❌ Not set'}")
    print(f"📁 Project ID: {'✅ Set' if project_id else '❌ Not set'}")
    
    if api_key and api_key != 'your_firebase_api_key_here':
        print(f"   API Key Preview: {api_key[:10]}...{api_key[-4:]}")
        return True
    else:
        print("❌ Firebase API key is not properly configured")
        print("   Update your .env file with the actual Firebase API key")
        return False

def test_backend_developer_access():
    """Test backend developer access"""
    print("\n🧪 Testing Backend Developer Access")
    print("=" * 50)
    
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

def test_google_auth_endpoints():
    """Test Google authentication endpoints"""
    print("\n🧪 Testing Google Auth Endpoints")
    print("=" * 50)
    
    # Test if there are any Google-specific endpoints
    try:
        # This is a basic test - in reality, Google auth happens client-side
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is ready for authentication")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Google Authentication Flow")
    print("=" * 60)
    
    # Test Firebase configuration
    firebase_ok = test_firebase_config()
    
    # Test backend access
    backend_ok = test_backend_developer_access()
    
    # Test frontend access
    frontend_ok = test_frontend_access()
    
    # Test auth endpoints
    auth_ok = test_google_auth_endpoints()
    
    print("\n📋 Summary:")
    print(f"   Firebase Config: {'✅' if firebase_ok else '❌'}")
    print(f"   Backend Access: {'✅' if backend_ok else '❌'}")
    print(f"   Frontend Access: {'✅' if frontend_ok else '❌'}")
    print(f"   Auth Endpoints: {'✅' if auth_ok else '❌'}")
    
    if not firebase_ok:
        print("\n❌ MAIN ISSUE: Firebase API key not configured")
        print("   Please update your .env file with the actual Firebase API key:")
        print("   VITE_FIREBASE_API_KEY=your_firebase_web_api_key_here")
        return False
    
    if firebase_ok and backend_ok and frontend_ok:
        print("\n🎉 All systems ready for Google authentication!")
        print("\n📋 Next steps:")
        print("   1. Make sure you've updated the .env file with the correct API key")
        print("   2. Restart your frontend server: npm run dev")
        print("   3. Try Google sign-in with a test account allowlisted in Firebase")
        print("   4. Check browser console for any JavaScript errors")
        return True
    else:
        print("\n❌ Some systems are not ready")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
