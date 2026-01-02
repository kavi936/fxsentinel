#!/usr/bin/env python3
"""
Enable Telegram for a specific user
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage

def enable_telegram_for_user(user_id: str, chat_id: str):
    """Enable Telegram alerts for a user"""
    print("=" * 80)
    print("ENABLING TELEGRAM FOR USER")
    print("=" * 80)
    
    firebase = FirebaseRealtimeStorage()
    
    # Get user settings
    print(f"\n1. Getting settings for user {user_id}...")
    user_settings = firebase.get_user_alert_settings(user_id)
    
    if not user_settings:
        print("   ⚠️  No settings found, creating default settings...")
        user_settings = firebase.default_settings.copy()
    
    # Enable Telegram
    print("\n2. Enabling Telegram...")
    if 'channels' not in user_settings:
        user_settings['channels'] = {}
    if 'telegram' not in user_settings['channels']:
        user_settings['channels']['telegram'] = {}
    
    user_settings['channels']['telegram']['enabled'] = True
    user_settings['channels']['telegram']['chatId'] = chat_id
    
    # Also set legacy fields for compatibility
    user_settings['telegram_enabled'] = True
    user_settings['telegram_chat_id'] = chat_id
    
    print(f"   ✅ Telegram enabled: {user_settings['channels']['telegram']['enabled']}")
    print(f"   ✅ Chat ID: {user_settings['channels']['telegram']['chatId']}")
    
    # Save settings
    print("\n3. Saving settings...")
    try:
        import hashlib
        safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
        settings_path = f"alerts/users/{safe_user_id}/settings"
        firebase._make_request('PUT', settings_path, user_settings)
        print(f"   ✅ Settings saved successfully")
    except Exception as e:
        print(f"   ❌ Failed to save settings: {e}")
        return
    
    # Also update user_data.telegram_chat_id
    print("\n4. Updating user_data.telegram_chat_id...")
    try:
        import hashlib
        safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
        user_path = f"alerts/users/{safe_user_id}"
        user_data = firebase._make_request('GET', user_path)
        
        if user_data and isinstance(user_data, dict):
            user_data['telegram_chat_id'] = chat_id
            firebase._make_request('PUT', user_path, user_data)
            print(f"   ✅ Updated user_data.telegram_chat_id")
        else:
            print(f"   ⚠️  User data not found, creating...")
            user_data = {
                'telegram_chat_id': chat_id,
                'settings': user_settings
            }
            firebase._make_request('PUT', user_path, user_data)
            print(f"   ✅ Created user data")
    except Exception as e:
        print(f"   ⚠️  Error updating user_data: {e}")
    
    # Create telegram_mappings entry
    print("\n5. Creating telegram_mappings entry...")
    try:
        mapping_path = f"telegram_mappings/{chat_id}"
        mapping_data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'status': 'active',
            'created_at': firebase._get_current_timestamp()
        }
        firebase._make_request('PUT', mapping_path, mapping_data)
        print(f"   ✅ Created telegram_mappings entry")
    except Exception as e:
        print(f"   ⚠️  Error creating mapping: {e}")
    
    print("\n" + "=" * 80)
    print("TELEGRAM ENABLED")
    print("=" * 80)
    print(f"\n✅ Telegram has been enabled for user {user_id}")
    print(f"   Chat ID: {chat_id}")
    print(f"\nThe user should now receive alerts when high-impact news is detected.")

if __name__ == '__main__':
    # Real user: c109c597ebf725f8424269b152d97e5e, chat_id: 8008493413
    enable_telegram_for_user('c109c597ebf725f8424269b152d97e5e', '8008493413')

