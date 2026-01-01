#!/usr/bin/env python3
"""
Verify Firebase Setup - Check what's in Firebase and what might need manual updates
"""

import sys
import os
import hashlib
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_telegram_mapping(chat_id: str):
    """Check if telegram mapping exists"""
    print_section(f"1. TELEGRAM MAPPING CHECK (chat_id: {chat_id})")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        mapping_path = f"telegram_mappings/{chat_id}"
        mapping = firebase._make_request('GET', mapping_path)
        
        if mapping and isinstance(mapping, dict):
            print("✅ Telegram mapping exists")
            print(f"   User ID: {mapping.get('user_id', 'Not set')}")
            print(f"   Username: {mapping.get('username', 'Not set')}")
            print(f"   Status: {mapping.get('status', 'Not set')}")
            return mapping.get('user_id')
        else:
            print("❌ Telegram mapping NOT found")
            print("\n   🔧 MANUAL FIX NEEDED:")
            print(f"   Path: telegram_mappings/{chat_id}")
            print("   Create this in Firebase Console with:")
            print("   {")
            print(f'     "user_id": "YOUR_USER_ID_HERE",')
            print(f'     "chat_id": "{chat_id}",')
            print(f'     "username": "K7IV_1",')
            print(f'     "status": "active"')
            print("   }")
            return None
            
    except Exception as e:
        print(f"❌ Error checking mapping: {e}")
        return None

def check_user_settings(user_id: str, chat_id: str):
    """Check if user settings exist"""
    print_section(f"2. USER SETTINGS CHECK (user_id: {user_id})")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Check if user_id is hashed
        import re
        if re.match(r'^[a-f0-9]{32}$', user_id):
            # Already hashed
            hashed_user_id = user_id
            print(f"   User ID is already hashed: {hashed_user_id}")
        else:
            # Hash it
            hashed_user_id = hashlib.md5(user_id.encode()).hexdigest()
            print(f"   Original user_id: {user_id}")
            print(f"   Hashed user_id: {hashed_user_id}")
        
        settings_path = f"alerts/users/{hashed_user_id}/settings"
        settings = firebase._make_request('GET', settings_path)
        
        if settings and isinstance(settings, dict):
            print("✅ User settings exist")
            print(f"   Path: alerts/users/{hashed_user_id}/settings")
            
            # Check structure
            channels = settings.get('channels', {})
            telegram = channels.get('telegram', {})
            
            print(f"\n   Telegram Settings:")
            print(f"   - Enabled: {telegram.get('enabled', False)}")
            print(f"   - Chat ID: {telegram.get('chatId', 'Not set')}")
            print(f"   - Username: {telegram.get('username', 'Not set')}")
            
            if telegram.get('chatId') != chat_id:
                print(f"\n   ⚠️  WARNING: Chat ID mismatch!")
                print(f"   Expected: {chat_id}")
                print(f"   Found: {telegram.get('chatId')}")
                print("\n   🔧 MANUAL FIX NEEDED:")
                print(f"   Update alerts/users/{hashed_user_id}/settings/channels/telegram/chatId")
                print(f"   Set to: {chat_id}")
            
            preferences = settings.get('preferences', {})
            if preferences:
                print(f"\n   Preferences found:")
                print(f"   - Alert Types: {list(preferences.get('alertTypes', {}).keys())}")
                print(f"   - Impact Levels: {list(preferences.get('impactLevels', {}).keys())}")
                print(f"   - Currency Pairs: {len(preferences.get('currencyPairs', []))} pairs")
            
            return True
        else:
            print("❌ User settings NOT found")
            print(f"\n   🔧 MANUAL FIX NEEDED:")
            print(f"   Path: alerts/users/{hashed_user_id}/settings")
            print("   Create this structure in Firebase Console:")
            print("   {")
            print('     "channels": {')
            print('       "telegram": {')
            print(f'         "enabled": true,')
            print(f'         "chatId": "{chat_id}",')
            print(f'         "username": "K7IV_1"')
            print('       }')
            print('     },')
            print('     "preferences": {')
            print('       "impactLevels": {"high": true, "medium": true, "low": false},')
            print('       "alertTypes": {"liveNews": true, "preNews": true, "postNews": true},')
            print('       "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"]')
            print('     }')
            print("   }")
            return False
            
    except Exception as e:
        print(f"❌ Error checking settings: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_telegram_chat_id_top_level(user_id: str, chat_id: str):
    """Check if telegram_chat_id exists at top level"""
    print_section(f"3. TELEGRAM CHAT ID (TOP LEVEL) CHECK")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Hash user_id if needed
        import re
        if re.match(r'^[a-f0-9]{32}$', user_id):
            hashed_user_id = user_id
        else:
            hashed_user_id = hashlib.md5(user_id.encode()).hexdigest()
        
        chat_id_path = f"alerts/users/{hashed_user_id}/telegram_chat_id"
        stored_chat_id = firebase._make_request('GET', chat_id_path)
        
        if stored_chat_id == chat_id:
            print(f"✅ Telegram chat ID exists at top level")
            print(f"   Path: alerts/users/{hashed_user_id}/telegram_chat_id")
            print(f"   Value: {stored_chat_id}")
            return True
        else:
            print("⚠️  Telegram chat ID missing or incorrect at top level")
            print(f"\n   🔧 OPTIONAL FIX:")
            print(f"   Path: alerts/users/{hashed_user_id}/telegram_chat_id")
            print(f"   Set value to: {chat_id}")
            print("   (This is optional but helps with lookups)")
            return False
            
    except Exception as e:
        print(f"❌ Error checking chat ID: {e}")
        return False

def check_firebase_rules():
    """Check Firebase database rules (informational)"""
    print_section("4. FIREBASE DATABASE RULES CHECK")
    print("⚠️  This requires manual verification in Firebase Console")
    print("\n   Go to: Firebase Console → Realtime Database → Rules")
    print("\n   Required rules (should allow read/write):")
    print("   {")
    print('     "rules": {')
    print('       "telegram_mappings": {')
    print('         ".read": true,')
    print('         ".write": true')
    print('       },')
    print('       "alerts": {')
    print('         ".read": true,')
    print('         ".write": true')
    print('       },')
    print('       "news_cache": {')
    print('         ".read": true,')
    print('         ".write": true')
    print('       }')
    print('     }')
    print("   }")
    print("\n   ⚠️  Note: These rules allow public read/write.")
    print("   For production, consider adding authentication-based rules.")

def main():
    chat_id = "8008493413"
    username = "K7IV_1"
    
    print("\n" + "=" * 70)
    print("  FIREBASE SETUP VERIFICATION")
    print("=" * 70)
    print(f"Chat ID: {chat_id}")
    print(f"Username: @{username}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Step 1: Check mapping
    user_id = check_telegram_mapping(chat_id)
    
    if not user_id:
        print("\n" + "=" * 70)
        print("  ⚠️  ACTION REQUIRED")
        print("=" * 70)
        print("Telegram mapping not found. You need to:")
        print("1. Find your user_id from Firebase Authentication")
        print("2. Create the mapping manually in Firebase Console")
        print("\nSee instructions above for the exact path and structure.")
        return
    
    # Step 2: Check settings
    settings_ok = check_user_settings(user_id, chat_id)
    
    # Step 3: Check top-level chat_id
    check_telegram_chat_id_top_level(user_id, chat_id)
    
    # Step 4: Rules info
    check_firebase_rules()
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    if user_id and settings_ok:
        print("✅ Firebase setup looks good!")
        print("   - Telegram mapping exists")
        print("   - User settings exist")
        print("   - Structure is correct")
        print("\n   No manual updates needed in Firebase Console.")
    else:
        print("⚠️  Some issues found:")
        if not user_id:
            print("   ❌ Telegram mapping missing")
        if not settings_ok:
            print("   ❌ User settings missing or incorrect")
        print("\n   Follow the manual fix instructions above.")
    
    print("\n" + "=" * 70)
    print("  NEXT STEPS")
    print("=" * 70)
    print("1. If everything is ✅: No action needed!")
    print("2. If issues found: Follow the 🔧 MANUAL FIX instructions above")
    print("3. Test /status command in Telegram after any fixes")

if __name__ == "__main__":
    main()

