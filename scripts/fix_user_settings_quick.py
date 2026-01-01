#!/usr/bin/env python3
"""
Quick fix for user settings error - uses the found user_id
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def main():
    chat_id = "8008493413"
    username = "K7IV_1"
    
    # The hashed user_id found in Firebase
    hashed_user_id = "c109c597ebf725f8424269b152d97e5e"
    
    print("=" * 70)
    print("  QUICK FIX FOR USER SETTINGS")
    print("=" * 70)
    print(f"Chat ID: {chat_id}")
    print(f"Username: @{username}")
    print(f"Hashed User ID: {hashed_user_id}")
    print()
    
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Step 1: Create telegram mapping
        print("1. Creating telegram mapping...")
        mapping_path = f"telegram_mappings/{chat_id}"
        mapping_data = {
            'user_id': hashed_user_id,  # Use hashed user_id for now
            'chat_id': chat_id,
            'username': username,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        result = firebase._make_request('PUT', mapping_path, mapping_data)
        if result is not None:
            print("   ✅ Mapping created")
        else:
            print("   ❌ Failed to create mapping")
        
        # Step 2: Create settings at the correct path
        print("\n2. Creating user settings...")
        settings_path = f"alerts/users/{hashed_user_id}/settings"
        settings_data = {
            "channels": {
                "telegram": {
                    "enabled": True,
                    "chatId": chat_id,
                    "username": username
                },
                "email": {
                    "enabled": False,
                    "address": ""
                }
            },
            "preferences": {
                "impactLevels": {
                    "high": True,
                    "medium": True,
                    "low": False
                },
                "alertTypes": {
                    "preNews": True,
                    "postNews": True,
                    "liveNews": True,
                    "technicalAnalysis": False
                },
                "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
                "quietHours": {
                    "enabled": False,
                    "start": "22:00",
                    "end": "06:00",
                    "timezone": "UTC"
                }
            }
        }
        result = firebase._make_request('PUT', settings_path, settings_data)
        if result is not None:
            print("   ✅ Settings created")
        else:
            print("   ❌ Failed to create settings")
        
        # Step 3: Add telegram_chat_id at top level
        print("\n3. Adding telegram_chat_id at top level...")
        chat_id_path = f"alerts/users/{hashed_user_id}/telegram_chat_id"
        result = firebase._make_request('PUT', chat_id_path, chat_id)
        if result is not None:
            print("   ✅ Chat ID saved")
        else:
            print("   ❌ Failed to save chat ID")
        
        # Step 4: Verify
        print("\n4. Verifying...")
        settings = firebase._make_request('GET', settings_path)
        if settings and isinstance(settings, dict):
            print("   ✅ Settings verified")
            print(f"   Telegram enabled: {settings.get('channels', {}).get('telegram', {}).get('enabled', False)}")
        else:
            print("   ⚠️  Settings not found after creation")
        
        print("\n" + "=" * 70)
        print("  ✅ FIX COMPLETE")
        print("=" * 70)
        print("Try refreshing the alert status page now.")
        print("\nNote: If you still see an error, you may need to:")
        print("1. Find your original user_id (not hashed) from Firebase Auth")
        print("2. Update the mapping to use the original user_id")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

