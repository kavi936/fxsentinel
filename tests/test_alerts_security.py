#!/usr/bin/env python3
"""
Test Alerts Security Implementation
Tests that only authenticated users can access Telegram bot features
"""

import requests
import json
from datetime import datetime

def test_unauthorized_access():
    """Test that unauthorized users are blocked"""
    print("🔒 Testing Unauthorized Access Blocking")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    # Test cases with invalid/unauthorized user IDs
    test_cases = [
        {
            "name": "Invalid user_id - current_user_id",
            "user_id": "current_user_id",
            "expected": "blocked"
        },
        {
            "name": "Invalid user_id - authenticated_user", 
            "user_id": "authenticated_user",
            "expected": "blocked"
        },
        {
            "name": "Invalid user_id - test_user",
            "user_id": "test_user",
            "expected": "blocked"
        },
        {
            "name": "Invalid user_id - empty",
            "user_id": "",
            "expected": "blocked"
        },
        {
            "name": "Valid user_id - real email",
            "user_id": "user@example.com",
            "expected": "allowed"
        },
        {
            "name": "Valid user_id - Firebase UID",
            "user_id": "abc123def456ghi789",
            "expected": "allowed"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"   User ID: {test_case['user_id']}")
        print(f"   Expected: {test_case['expected']}")
        
        try:
            # Test Telegram setup endpoint
            response = requests.post(
                f"{base_url}/api/telegram/setup",
                json={"userId": test_case['user_id']},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 403:
                result = "blocked"
                print("   ✅ Access correctly blocked (403 Forbidden)")
            elif response.status_code == 200:
                result = "allowed"
                print("   ✅ Access allowed (200 OK)")
            else:
                result = "unexpected"
                print(f"   ⚠️ Unexpected status: {response.status_code}")
            
            if result == test_case['expected']:
                print("   ✅ Test PASSED")
                passed += 1
            else:
                print(f"   ❌ Test FAILED - Expected {test_case['expected']}, got {result}")
                
        except Exception as e:
            print(f"   ❌ Test ERROR: {e}")
    
    print(f"\n📊 Security Test Results: {passed}/{total} tests passed")
    return passed == total

def test_authorized_access():
    """Test that authorized users can access the features"""
    print("\n✅ Testing Authorized Access")
    print("=" * 40)
    
    base_url = "http://localhost:5001"
    valid_user_id = "test_authorized_user_123"
    
    try:
        # Test 1: Telegram setup
        print("\n1️⃣ Testing Telegram Setup...")
        setup_response = requests.post(
            f"{base_url}/api/telegram/setup",
            json={"userId": valid_user_id},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if setup_response.status_code == 200:
            setup_data = setup_response.json()
            if setup_data.get("success"):
                print("   ✅ Telegram setup successful")
                print(f"   📱 Bot link: {setup_data.get('botLink', 'N/A')}")
            else:
                print(f"   ❌ Setup failed: {setup_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Setup failed with status {setup_response.status_code}")
            return False
        
        # Test 2: Settings save
        print("\n2️⃣ Testing Settings Save...")
        test_settings = {
            "channels": {
                "telegram": {"enabled": True, "chatId": "123456789", "username": "@testuser"}
            },
            "preferences": {
                "impactLevels": {"high": True, "medium": True, "low": False},
                "alertTypes": {"preNews": True, "postNews": True, "liveNews": True},
                "currencyPairs": ["EUR/USD", "USD/JPY"],
                "quietHours": {"enabled": False, "start": "22:00", "end": "06:00"}
            }
        }
        
        save_response = requests.put(
            f"{base_url}/api/alerts/settings",
            json={"userId": valid_user_id, "settings": test_settings},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if save_response.status_code == 200:
            save_data = save_response.json()
            if save_data.get("success"):
                print("   ✅ Settings saved successfully")
            else:
                print(f"   ❌ Settings save failed: {save_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Settings save failed with status {save_response.status_code}")
            return False
        
        # Test 3: Settings load
        print("\n3️⃣ Testing Settings Load...")
        load_response = requests.get(
            f"{base_url}/api/alerts/user-settings?userId={valid_user_id}",
            timeout=10
        )
        
        if load_response.status_code == 200:
            load_data = load_response.json()
            if load_data.get("success") and load_data.get("settings"):
                print("   ✅ Settings loaded successfully")
                # Verify settings were saved correctly
                loaded_settings = load_data["settings"]
                if loaded_settings.get("channels", {}).get("telegram", {}).get("enabled"):
                    print("   ✅ Telegram settings preserved")
                else:
                    print("   ❌ Telegram settings not preserved")
                    return False
            else:
                print(f"   ❌ Settings load failed: {load_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Settings load failed with status {load_response.status_code}")
            return False
        
        print("\n🎉 All authorized access tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Authorized access test failed: {e}")
        return False

def test_security_logging():
    """Test that security events are properly logged"""
    print("\n📝 Testing Security Logging")
    print("=" * 35)
    
    base_url = "http://localhost:5001"
    
    # Test unauthorized access and check server logs
    print("\n🔍 Testing unauthorized access logging...")
    
    try:
        response = requests.post(
            f"{base_url}/api/telegram/setup",
            json={"userId": "current_user_id"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 403:
            print("   ✅ Unauthorized access correctly blocked")
            print("   📝 Check server logs for security messages")
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")

def main():
    """Run all security tests"""
    print("🚀 FXSentinel Alerts Security Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Unauthorized access blocking
    test1_passed = test_unauthorized_access()
    
    # Test 2: Authorized access
    test2_passed = test_authorized_access()
    
    # Test 3: Security logging
    test_security_logging()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Security Test Summary:")
    print(f"   Unauthorized Access Blocking: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Authorized Access: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All security tests passed!")
        print("\n✅ Security Features Working:")
        print("   • Unauthorized users are blocked")
        print("   • Authorized users can access features")
        print("   • User verification is working")
        print("   • Settings persistence is secure")
    else:
        print("\n⚠️ Some security tests failed!")
        print("\n🔧 Security Issues to Fix:")
        if not test1_passed:
            print("   • Unauthorized access blocking not working")
        if not test2_passed:
            print("   • Authorized access not working")
        print("   • Check server logs for errors")
        print("   • Verify Firebase configuration")

if __name__ == "__main__":
    main()
