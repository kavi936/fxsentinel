#!/usr/bin/env python3
"""
Test script to verify both frontend and backend servers are working
"""

import requests
import json
import time

def test_backend_direct():
    """Test backend server directly"""
    print("🔧 Testing backend server directly...")
    
    try:
        response = requests.get("http://localhost:5001/api/subscription-status/test_user", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend working correctly")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Backend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def test_frontend_proxy():
    """Test frontend proxy to backend"""
    print("\n📱 Testing frontend proxy...")
    
    try:
        response = requests.get("http://localhost:5173/api/subscription-status/test_user", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Frontend proxy working correctly")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Frontend proxy returned status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Frontend proxy test failed: {e}")
        return False

def test_frontend_page():
    """Test if frontend page loads"""
    print("\n🌐 Testing frontend page...")
    
    try:
        response = requests.get("http://localhost:5173/", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend page loads correctly")
            return True
        else:
            print(f"❌ Frontend page returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend page test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing FXSentinel servers...\n")
    
    backend_ok = test_backend_direct()
    frontend_proxy_ok = test_frontend_proxy()
    frontend_page_ok = test_frontend_page()
    
    print("\n📋 Summary:")
    if backend_ok and frontend_proxy_ok and frontend_page_ok:
        print("🎉 All servers working correctly!")
        print("✅ Backend API responding")
        print("✅ Frontend proxy working")
        print("✅ Frontend page loading")
        print("\n💡 You can now test the trial-welcome page without black screen issues!")
    else:
        print("⚠️ Some issues detected:")
        if not backend_ok:
            print("❌ Backend server not working - run: cd backend && python3 app.py")
        if not frontend_proxy_ok:
            print("❌ Frontend proxy not working - check if both servers are running")
        if not frontend_page_ok:
            print("❌ Frontend page not loading - run: npm run dev")

if __name__ == "__main__":
    main()
