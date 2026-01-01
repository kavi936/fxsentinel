#!/usr/bin/env python3
"""
Diagnose "Error retrieving settings" issue
Checks Firebase for chat_id mapping and user settings
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

def find_user_by_chat_id(chat_id: str):
    """Find user_id by chat_id"""
    print_section(f"1. FINDING USER BY CHAT ID: {chat_id}")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Method 1: Check telegram_mappings
        print("\nChecking telegram_mappings...")
        mapping_path = f"telegram_mappings/{chat_id}"
        mapping_result = firebase._make_request('GET', mapping_path)
        
        if mapping_result and isinstance(mapping_result, dict) and 'user_id' in mapping_result:
            user_id = mapping_result['user_id']
            print(f"✅ Found user_id in telegram_mappings: {user_id}")
            return user_id
        else:
            print("❌ No mapping found in telegram_mappings")
        
        # Method 2: Search through all users
        print("\nSearching through all users...")
        users_path = "alerts/users"
        users_result = firebase._make_request('GET', users_path)
        
        if not users_result or not isinstance(users_result, dict):
            print("❌ No users found in alerts/users")
            return None
        
        print(f"Found {len(users_result)} users, searching for chat_id {chat_id}...")
        
        for safe_user_id, user_data in users_result.items():
            if isinstance(user_data, dict):
                # Check telegram_chat_id at top level
                if user_data.get('telegram_chat_id') == chat_id:
                    print(f"✅ Found user with chat_id in top level: {safe_user_id}")
                    # Need to reverse hash to get original user_id
                    # For now, return the safe_user_id (hashed)
                    return safe_user_id
                
                # Check in settings
                settings = user_data.get('settings', {})
                if isinstance(settings, dict):
                    channels = settings.get('channels', {})
                    if isinstance(channels, dict):
                        telegram = channels.get('telegram', {})
                        if isinstance(telegram, dict) and telegram.get('chatId') == chat_id:
                            print(f"✅ Found user with chat_id in settings: {safe_user_id}")
                            return safe_user_id
        
        print("❌ User not found with this chat_id")
        return None
        
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_user_settings(user_id: str):
    """Check if user settings exist"""
    print_section(f"2. CHECKING USER SETTINGS FOR: {user_id}")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Try to get settings using the user_id directly (might be hashed)
        settings = firebase.get_user_alert_settings(user_id)
        
        if settings:
            print("✅ User settings found")
            print(f"   Settings keys: {list(settings.keys())}")
            
            # Check for Telegram settings
            if 'channels' in settings:
                telegram = settings['channels'].get('telegram', {})
                print(f"   Telegram enabled: {telegram.get('enabled', False)}")
                print(f"   Telegram chatId: {telegram.get('chatId', 'Not set')}")
            
            return settings
        else:
            print("❌ User settings not found")
            print("   This is the root cause of 'Error retrieving settings'")
            return None
            
    except Exception as e:
        print(f"❌ Error checking settings: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_all_users():
    """Check all users to see structure"""
    print_section("3. CHECKING ALL USERS STRUCTURE")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        users = firebase.get_all_users_with_alerts()
        
        if not users:
            print("❌ No users found")
            return
        
        print(f"Found {len(users)} users")
        print("\nSample user structure:")
        if users:
            user = users[0]
            print(f"  User ID: {user.get('user_id')}")
            print(f"  Telegram Chat ID: {user.get('telegram_chat_id')}")
            print(f"  Has Settings: {bool(user.get('settings'))}")
            if user.get('settings'):
                print(f"  Settings keys: {list(user.get('settings', {}).keys())}")
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        import traceback
        traceback.print_exc()

def main():
    chat_id = "8008493413"  # Your chat ID
    
    print("\n" + "=" * 70)
    print("  USER SETTINGS ERROR DIAGNOSIS")
    print("=" * 70)
    print(f"Chat ID: {chat_id}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Step 1: Find user by chat_id
    user_id = find_user_by_chat_id(chat_id)
    
    if not user_id:
        print("\n" + "=" * 70)
        print("  DIAGNOSIS: USER NOT FOUND")
        print("=" * 70)
        print("❌ No user found with chat_id 8008493413")
        print("\nPossible causes:")
        print("1. User never connected Telegram bot")
        print("2. Mapping was never created")
        print("3. User ID is different than expected")
        print("\nSolution:")
        print("1. Run fix script to create mapping and settings")
        print("2. Or manually create in Firebase (see instructions)")
        return
    
    # Step 2: Check settings
    settings = check_user_settings(user_id)
    
    if not settings:
        print("\n" + "=" * 70)
        print("  DIAGNOSIS: SETTINGS NOT FOUND")
        print("=" * 70)
        print(f"❌ User {user_id} exists but has no settings")
        print("\nSolution:")
        print("1. Run fix script to create default settings")
        print("2. Or manually create in Firebase (see instructions)")
    
    # Step 3: Check all users structure
    check_all_users()
    
    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    if user_id and settings:
        print("✅ User and settings found - issue may be elsewhere")
        print("   Check backend logs for specific error")
    elif user_id and not settings:
        print("❌ User found but settings missing - this is the issue")
    else:
        print("❌ User not found - need to create mapping and settings")

if __name__ == "__main__":
    main()

