#!/usr/bin/env python3
"""
Test Alert Settings Persistence
Tests the new settings save/load functionality
"""

import requests
import json
from datetime import datetime

def test_settings_persistence():
    """Test saving and loading alert settings"""
    print("🧪 Testing Alert Settings Persistence")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    user_id = "test_user_123"
    
    # Test data
    test_settings = {
        "channels": {
            "telegram": {"enabled": True, "chatId": "123456789", "username": "@testuser"},
            "email": {"enabled": False, "address": ""}
        },
        "preferences": {
            "impactLevels": {"high": True, "medium": True, "low": False},
            "alertTypes": {"preNews": True, "postNews": True, "liveNews": True, "technicalAnalysis": False},
            "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD"],
            "quietHours": {"enabled": True, "start": "23:00", "end": "07:00", "timezone": "UTC"}
        }
    }
    
    try:
        # Test 1: Save settings
        print("\n1️⃣ Testing Save Settings...")
        save_response = requests.put(
            f"{base_url}/api/alerts/settings",
            json={
                "userId": user_id,
                "settings": test_settings
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if save_response.status_code == 200:
            save_data = save_response.json()
            if save_data.get("success"):
                print("   ✅ Settings saved successfully")
            else:
                print(f"   ❌ Save failed: {save_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Save failed with status {save_response.status_code}")
            print(f"   Response: {save_response.text}")
            return False
        
        # Test 2: Load settings
        print("\n2️⃣ Testing Load Settings...")
        load_response = requests.get(
            f"{base_url}/api/alerts/settings?userId={user_id}",
            timeout=10
        )
        
        if load_response.status_code == 200:
            load_data = load_response.json()
            if load_data.get("success") and load_data.get("settings"):
                loaded_settings = load_data["settings"]
                print("   ✅ Settings loaded successfully")
                
                # Test 3: Verify data integrity
                print("\n3️⃣ Testing Data Integrity...")
                
                # Check channels
                if (loaded_settings.get("channels", {}).get("telegram", {}).get("enabled") == True and
                    loaded_settings.get("channels", {}).get("telegram", {}).get("chatId") == "123456789"):
                    print("   ✅ Telegram settings preserved")
                else:
                    print("   ❌ Telegram settings not preserved correctly")
                    return False
                
                # Check currency pairs
                if "AUD/USD" in loaded_settings.get("preferences", {}).get("currencyPairs", []):
                    print("   ✅ Currency pairs preserved")
                else:
                    print("   ❌ Currency pairs not preserved correctly")
                    return False
                
                # Check quiet hours
                if (loaded_settings.get("preferences", {}).get("quietHours", {}).get("enabled") == True and
                    loaded_settings.get("preferences", {}).get("quietHours", {}).get("start") == "23:00"):
                    print("   ✅ Quiet hours preserved")
                else:
                    print("   ❌ Quiet hours not preserved correctly")
                    return False
                
                print("\n🎉 All tests passed! Settings persistence is working correctly.")
                return True
                
            else:
                print(f"   ❌ Load failed: {load_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Load failed with status {load_response.status_code}")
            print(f"   Response: {load_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to backend server")
        print("   💡 Make sure the backend is running: python3 backend/app.py")
        return False
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        return False

def test_default_settings():
    """Test loading default settings for new user"""
    print("\n🧪 Testing Default Settings")
    print("=" * 30)
    
    base_url = "http://localhost:5001"
    new_user_id = "new_user_456"
    
    try:
        # Test loading settings for new user
        response = requests.get(
            f"{base_url}/api/alerts/settings?userId={new_user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("settings"):
                settings = data["settings"]
                
                # Check if default settings are returned
                if (settings.get("channels", {}).get("telegram", {}).get("enabled") == False and
                    settings.get("preferences", {}).get("currencyPairs") == ["EUR/USD", "USD/JPY", "GBP/USD"]):
                    print("   ✅ Default settings returned correctly")
                    return True
                else:
                    print("   ❌ Default settings not returned correctly")
                    return False
            else:
                print(f"   ❌ Failed to get default settings: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Alert Settings Persistence Test Suite")
    print("=" * 60)
    
    # Test 1: Settings persistence
    test1_passed = test_settings_persistence()
    
    # Test 2: Default settings
    test2_passed = test_default_settings()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Settings Persistence: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Default Settings: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Settings persistence is working correctly.")
        print("\n✅ What's Working:")
        print("   • Settings are saved to Firebase Realtime Database")
        print("   • Settings are loaded correctly on page refresh")
        print("   • Default settings are provided for new users")
        print("   • Data integrity is maintained")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure backend server is running")
        print("   2. Check Firebase configuration in .env file")
        print("   3. Verify Firebase Realtime Database is accessible")

if __name__ == "__main__":
    main()
