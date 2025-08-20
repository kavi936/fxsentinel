#!/usr/bin/env python3
"""
Test Settings Persistence
"""

import requests
import json

def test_settings_persistence():
    """Test if settings are being saved and loaded correctly"""
    
    print("⚙️ Testing Settings Persistence")
    print("=" * 50)
    
    # Test user ID
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    # Test 1: Load current settings
    print("\n1. Loading Current Settings...")
    try:
        response = requests.get(
            f"http://localhost:5001/api/alerts/settings?userId={user_id}",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                settings = data.get('settings', {})
                print("   ✅ Settings loaded successfully")
                print(f"   Currency pairs: {settings.get('preferences', {}).get('currencyPairs', [])}")
                print(f"   Alert types: {settings.get('preferences', {}).get('alertTypes', {})}")
            else:
                print("   ❌ Failed to load settings")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error loading settings: {e}")
    
    # Test 2: Save new settings
    print("\n2. Saving New Settings...")
    try:
        new_settings = {
            "channels": {
                "telegram": {"enabled": True, "chatId": "8008493413", "username": "@kavi_user"},
                "email": {"enabled": False, "address": ""}
            },
            "preferences": {
                "impactLevels": {"high": True, "medium": True, "low": False},
                "alertTypes": {"preNews": True, "postNews": True, "liveNews": True, "technicalAnalysis": False},
                "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD"],
                "quietHours": {"enabled": True, "start": "23:00", "end": "07:00", "timezone": "UTC"}
            }
        }
        
        response = requests.put(
            "http://localhost:5001/api/alerts/settings",
            json={
                "userId": user_id,
                "settings": new_settings
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Settings saved successfully")
            else:
                print(f"   ❌ Failed to save settings: {data.get('error')}")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error saving settings: {e}")
    
    # Test 3: Verify settings were saved
    print("\n3. Verifying Settings Were Saved...")
    try:
        response = requests.get(
            f"http://localhost:5001/api/alerts/settings?userId={user_id}",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                settings = data.get('settings', {})
                currency_pairs = settings.get('preferences', {}).get('currencyPairs', [])
                quiet_hours = settings.get('preferences', {}).get('quietHours', {})
                
                print("   ✅ Settings retrieved successfully")
                print(f"   Currency pairs: {currency_pairs}")
                print(f"   Quiet hours enabled: {quiet_hours.get('enabled', False)}")
                
                # Check if our changes were saved
                if "AUD/USD" in currency_pairs and quiet_hours.get('enabled'):
                    print("   ✅ Settings persistence confirmed!")
                else:
                    print("   ❌ Settings not persisted correctly")
            else:
                print("   ❌ Failed to retrieve settings")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error verifying settings: {e}")
    
    # Test 4: Test frontend endpoint
    print("\n4. Testing Frontend Endpoint...")
    try:
        response = requests.get(
            f"http://localhost:5001/api/alerts/user-settings?userId={user_id}",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Frontend endpoint working")
            else:
                print("   ❌ Frontend endpoint failed")
        else:
            print(f"   ❌ Frontend endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing frontend endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("Settings Persistence Test completed!")

if __name__ == "__main__":
    test_settings_persistence()
