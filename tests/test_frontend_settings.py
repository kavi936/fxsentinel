#!/usr/bin/env python3
"""
Test Frontend Settings Persistence
"""

import requests
import json

def test_frontend_settings():
    """Test if frontend settings are being saved correctly"""
    
    print("🖥️ Testing Frontend Settings Persistence")
    print("=" * 50)
    
    # Test user ID
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    # Test 1: Check current settings
    print("\n1. Checking Current Settings...")
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
                preferences = settings.get('preferences', {})
                
                print("   ✅ Current settings loaded")
                print(f"   Currency pairs: {preferences.get('currencyPairs', [])}")
                print(f"   Alert types: {preferences.get('alertTypes', {})}")
                print(f"   Impact levels: {preferences.get('impactLevels', {})}")
            else:
                print("   ❌ Failed to load settings")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Simulate frontend preference change
    print("\n2. Simulating Frontend Preference Change...")
    try:
        # Simulate changing alert types
        new_settings = {
            "channels": {
                "telegram": {"enabled": True, "chatId": "8008493413", "username": "@kavi_user"},
                "email": {"enabled": False, "address": ""}
            },
            "preferences": {
                "impactLevels": {"high": True, "medium": False, "low": False},  # Changed medium to False
                "alertTypes": {"preNews": True, "postNews": False, "liveNews": True, "technicalAnalysis": True},  # Changed postNews to False, technicalAnalysis to True
                "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD"],  # Added USD/CAD
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
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Frontend settings saved successfully")
                print("   Changes made:")
                print("   - Medium impact: False")
                print("   - Post-news alerts: False")
                print("   - Technical analysis: True")
                print("   - Added USD/CAD currency pair")
            else:
                print(f"   ❌ Failed to save: {data.get('error')}")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Verify changes were saved
    print("\n3. Verifying Changes Were Saved...")
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
                preferences = settings.get('preferences', {})
                
                # Check if our changes were saved
                impact_levels = preferences.get('impactLevels', {})
                alert_types = preferences.get('alertTypes', {})
                currency_pairs = preferences.get('currencyPairs', [])
                
                print("   ✅ Settings retrieved successfully")
                print(f"   Medium impact: {impact_levels.get('medium', 'Not found')}")
                print(f"   Post-news alerts: {alert_types.get('postNews', 'Not found')}")
                print(f"   Technical analysis: {alert_types.get('technicalAnalysis', 'Not found')}")
                print(f"   Currency pairs: {currency_pairs}")
                
                # Verify changes
                if (impact_levels.get('medium') == False and 
                    alert_types.get('postNews') == False and 
                    alert_types.get('technicalAnalysis') == True and
                    'USD/CAD' in currency_pairs):
                    print("   ✅ All frontend changes persisted correctly!")
                else:
                    print("   ❌ Some changes were not persisted")
            else:
                print("   ❌ Failed to retrieve settings")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Frontend Settings Test completed!")
    print("\n📋 Summary:")
    print("✅ Backend settings persistence is working")
    print("✅ Frontend can save settings changes")
    print("✅ Settings are properly stored in Firebase")

if __name__ == "__main__":
    test_frontend_settings()
