#!/usr/bin/env python3
"""
Test to verify security fix is working
"""

import requests

def test_security_fix():
    """Test if security fix is working"""
    
    print("🔒 Testing Security Fix")
    print("=" * 40)
    
    # Test 1: Invalid user should be blocked
    print("\n1. Testing invalid user...")
    try:
        response = requests.get(
            "http://localhost:5001/api/alerts/user-settings?userId=invalid_user",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status code: {response.status_code}")
        if response.status_code == 403:
            print("   ✅ Security working - invalid user blocked")
        else:
            print(f"   ❌ Security broken - invalid user got {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Test user should be blocked
    print("\n2. Testing test user...")
    try:
        response = requests.get(
            "http://localhost:5001/api/alerts/user-settings?userId=new_user_test_001",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status code: {response.status_code}")
        if response.status_code == 403:
            print("   ✅ Security working - test user blocked")
        else:
            print(f"   ❌ Security broken - test user got {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Valid user should work
    print("\n3. Testing valid user...")
    try:
        response = requests.get(
            "http://localhost:5001/api/alerts/user-settings?userId=0E0xJnQpYzZb8YkfQfSiwKYc8Fz2",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Security working - valid user allowed")
        else:
            print(f"   ❌ Security broken - valid user got {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_security_fix()
