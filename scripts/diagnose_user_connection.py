#!/usr/bin/env python3
"""
Diagnose User Connection Issue
Checks why user is showing as "Not Connected" in /status command
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_user_connection(chat_id: str):
    """Diagnose why a user is not connected"""
    print("\n" + "="*80)
    print("USER CONNECTION DIAGNOSTIC")
    print("="*80)
    print(f"Chat ID: {chat_id}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Check 1: Direct mapping
        print("\n1. CHECKING DIRECT MAPPING")
        print("-" * 80)
        mapping_path = f"telegram_mappings/{chat_id}"
        mapping_result = firebase._make_request('GET', mapping_path)
        
        if mapping_result and isinstance(mapping_result, dict) and 'user_id' in mapping_result:
            user_id = mapping_result['user_id']
            print(f"✅ Found direct mapping:")
            print(f"   User ID: {user_id}")
            print(f"   Username: {mapping_result.get('username', 'N/A')}")
            print(f"   Status: {mapping_result.get('status', 'N/A')}")
            print(f"   Created: {mapping_result.get('created_at', 'N/A')}")
        else:
            print(f"❌ No direct mapping found at telegram_mappings/{chat_id}")
        
        # Check 2: Search through all users
        print("\n2. SEARCHING THROUGH ALL USERS")
        print("-" * 80)
        users_path = "alerts/users"
        users_result = firebase._make_request('GET', users_path)
        
        if not users_result or not isinstance(users_result, dict):
            print("❌ No users found in alerts/users")
            return
        
        print(f"📊 Found {len(users_result)} users in alerts/users")
        
        found_users = []
        for safe_user_id, user_data in users_result.items():
            if isinstance(user_data, dict):
                settings = user_data.get('settings', {})
                
                # Check multiple locations for chat_id
                chat_id_locations = []
                
                # Location 1: settings.channels.telegram.chatId
                if 'channels' in settings:
                    channels = settings['channels']
                    if isinstance(channels, dict) and 'telegram' in channels:
                        telegram = channels['telegram']
                        if isinstance(telegram, dict):
                            tg_chat_id = telegram.get('chatId')
                            if tg_chat_id:
                                chat_id_locations.append(('settings.channels.telegram.chatId', tg_chat_id))
                
                # Location 2: settings.telegram_chat_id
                if 'telegram_chat_id' in settings:
                    chat_id_locations.append(('settings.telegram_chat_id', settings['telegram_chat_id']))
                
                # Location 3: user_data.telegram_chat_id (top level)
                if 'telegram_chat_id' in user_data:
                    chat_id_locations.append(('user_data.telegram_chat_id', user_data['telegram_chat_id']))
                
                # Check if any match
                for location, stored_chat_id in chat_id_locations:
                    if str(stored_chat_id) == str(chat_id):
                        found_users.append({
                            'user_id': safe_user_id,
                            'location': location,
                            'chat_id': stored_chat_id
                        })
                        print(f"✅ Found user {safe_user_id} with chat_id {chat_id} at {location}")
        
        if not found_users:
            print(f"❌ No user found with chat_id {chat_id} in any location")
        else:
            print(f"\n📋 Found {len(found_users)} user(s) with matching chat_id:")
            for user_info in found_users:
                print(f"   User ID: {user_info['user_id']}")
                print(f"   Location: {user_info['location']}")
        
        # Check 3: User settings
        print("\n3. CHECKING USER SETTINGS")
        print("-" * 80)
        if found_users:
            for user_info in found_users:
                user_id = user_info['user_id']
                settings_path = f"alerts/users/{user_id}/settings"
                settings_result = firebase._make_request('GET', settings_path)
                
                if settings_result and isinstance(settings_result, dict):
                    print(f"\n✅ User {user_id} has settings:")
                    
                    # Check Telegram enabled
                    telegram_enabled = (
                        settings_result.get('telegram_enabled', False) or
                        settings_result.get('telegram', False) or
                        settings_result.get('channels', {}).get('telegram', {}).get('enabled', False)
                    )
                    print(f"   Telegram enabled: {telegram_enabled}")
                    
                    # Check alert types
                    preferences = settings_result.get('preferences', {})
                    alert_types = preferences.get('alertTypes', {})
                    print(f"   Alert types: {alert_types}")
                else:
                    print(f"❌ User {user_id} has no settings")
        
        # Check 4: Recommendations
        print("\n4. RECOMMENDATIONS")
        print("-" * 80)
        
        if not mapping_result and not found_users:
            print("❌ CRITICAL: User is not connected!")
            print("\n   To fix:")
            print("   1. Visit https://fxsentinel.io")
            print("   2. Log in to your account")
            print("   3. Go to Alerts tab")
            print("   4. Click 'Connect Telegram Bot'")
            print("   5. Follow the setup instructions")
        elif not mapping_result and found_users:
            print("⚠️  User found but mapping is missing!")
            print("\n   The user exists but the telegram_mappings entry is missing.")
            print("   This can be fixed by:")
            print("   1. Re-connecting via the app (recommended)")
            print("   2. Or manually creating the mapping (see script below)")
        elif mapping_result and found_users:
            print("✅ User is properly connected!")
            print("\n   Both mapping and user settings exist.")
            print("   If /status still shows 'Not Connected', check:")
            print("   1. Firebase permissions")
            print("   2. Alert service initialization")
            print("   3. Webhook handler configuration")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Your chat ID
    chat_id = "8008493413"
    diagnose_user_connection(chat_id)

