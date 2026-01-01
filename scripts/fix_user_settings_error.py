#!/usr/bin/env python3
"""
Fix "Error retrieving settings" by creating missing mapping and settings
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

def find_or_create_user_id(chat_id: str, username: str = None):
    """Find existing user_id or create new one"""
    print_section("1. FINDING OR CREATING USER ID")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # First, try to find existing user
        mapping_path = f"telegram_mappings/{chat_id}"
        mapping_result = firebase._make_request('GET', mapping_path)
        
        if mapping_result and isinstance(mapping_result, dict) and 'user_id' in mapping_result:
            user_id = mapping_result['user_id']
            print(f"✅ Found existing user_id: {user_id}")
            return user_id
        
        # Search through users
        users_path = "alerts/users"
        users_result = firebase._make_request('GET', users_path)
        
        if users_result and isinstance(users_result, dict):
            for safe_user_id, user_data in users_result.items():
                if isinstance(user_data, dict):
                    if user_data.get('telegram_chat_id') == chat_id:
                        print(f"✅ Found existing user: {safe_user_id}")
                        return safe_user_id
                    
                    settings = user_data.get('settings', {})
                    if isinstance(settings, dict):
                        channels = settings.get('channels', {})
                        if isinstance(channels, dict):
                            telegram = channels.get('telegram', {})
                            if isinstance(telegram, dict) and telegram.get('chatId') == chat_id:
                                print(f"✅ Found existing user: {safe_user_id}")
                                return safe_user_id
        
        # Create new user_id (you'll need to provide your actual user_id from Firebase Auth)
        # For now, we'll use a placeholder - you need to replace this with your actual user_id
        print("⚠️  No existing user found")
        print("   You need to provide your actual user_id from Firebase Auth")
        print("   This is typically found in your app's authentication system")
        
        # Prompt for user_id (in production, get from auth system)
        user_id = input("\nEnter your user_id (from Firebase Auth): ").strip()
        
        if not user_id:
            print("❌ User ID is required")
            return None
        
        return user_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_telegram_mapping(chat_id: str, user_id: str, username: str = None):
    """Create telegram_mappings entry"""
    print_section("2. CREATING TELEGRAM MAPPING")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        mapping_data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'username': username or f"user_{chat_id}",
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        mapping_path = f"telegram_mappings/{chat_id}"
        result = firebase._make_request('PUT', mapping_path, mapping_data)
        
        if result is not None:
            print("✅ Telegram mapping created successfully")
            return True
        else:
            print("❌ Failed to create mapping")
            return False
            
    except Exception as e:
        print(f"❌ Error creating mapping: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_user_settings(user_id: str, chat_id: str, username: str = None):
    """Create user alert settings"""
    print_section("3. CREATING USER SETTINGS")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Hash user_id for Firebase path
        safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
        
        # Default settings structure
        default_settings = {
            "channels": {
                "telegram": {
                    "enabled": True,
                    "chatId": chat_id,
                    "username": username or f"user_{chat_id}"
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
        
        # Save settings
        settings_path = f"alerts/users/{safe_user_id}/settings"
        result = firebase._make_request('PUT', settings_path, default_settings)
        
        if result is not None:
            print("✅ User settings created successfully")
            
            # Also save telegram_chat_id at top level
            chat_id_path = f"alerts/users/{safe_user_id}/telegram_chat_id"
            firebase._make_request('PUT', chat_id_path, chat_id)
            print("✅ Telegram chat ID saved at top level")
            
            return True
        else:
            print("❌ Failed to create settings")
            return False
            
    except Exception as e:
        print(f"❌ Error creating settings: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_fix(chat_id: str, user_id: str):
    """Verify the fix worked"""
    print_section("4. VERIFYING FIX")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Check mapping
        mapping_path = f"telegram_mappings/{chat_id}"
        mapping = firebase._make_request('GET', mapping_path)
        if mapping and mapping.get('user_id') == user_id:
            print("✅ Mapping verified")
        else:
            print("❌ Mapping verification failed")
            return False
        
        # Check settings
        settings = firebase.get_user_alert_settings(user_id)
        if settings:
            print("✅ Settings verified")
            print(f"   Telegram enabled: {settings.get('channels', {}).get('telegram', {}).get('enabled', False)}")
            return True
        else:
            print("❌ Settings verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def main():
    chat_id = "8008493413"
    username = "K7IV_1"
    
    print("\n" + "=" * 70)
    print("  FIX USER SETTINGS ERROR")
    print("=" * 70)
    print(f"Chat ID: {chat_id}")
    print(f"Username: @{username}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Step 1: Find or create user_id
    user_id = find_or_create_user_id(chat_id, username)
    if not user_id:
        print("\n❌ Cannot proceed without user_id")
        print("\nTo find your user_id:")
        print("1. Check your app's authentication system")
        print("2. Check Firebase Authentication console")
        print("3. Check browser localStorage for 'userId' or 'user_id'")
        return
    
    # Step 2: Create mapping
    if not create_telegram_mapping(chat_id, user_id, username):
        print("\n❌ Failed to create mapping")
        return
    
    # Step 3: Create settings
    if not create_user_settings(user_id, chat_id, username):
        print("\n❌ Failed to create settings")
        return
    
    # Step 4: Verify
    if verify_fix(chat_id, user_id):
        print("\n" + "=" * 70)
        print("  ✅ FIX COMPLETE")
        print("=" * 70)
        print("Settings have been created successfully!")
        print("Try refreshing the alert status page.")
    else:
        print("\n" + "=" * 70)
        print("  ⚠️  VERIFICATION FAILED")
        print("=" * 70)
        print("Settings were created but verification failed.")
        print("Check Firebase manually to confirm.")

if __name__ == "__main__":
    main()

