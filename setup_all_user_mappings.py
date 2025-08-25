#!/usr/bin/env python3
"""
Setup mappings for all users in the alert system
Ensures the alert bot works for all users on the online hosted system
"""

import sys
import os
from datetime import datetime
sys.path.append('backend')

from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage

def setup_all_user_mappings():
    """Setup mappings for all users in the alert system"""
    print("🔧 Setting up Mappings for All Users")
    print("=" * 50)
    
    # Initialize Firebase storage
    firebase = FirebaseRealtimeStorage()
    
    # Step 1: Get all users from the alerts directory
    print("\n1️⃣ Scanning for all users...")
    users_path = "alerts/users"
    users_result = firebase._make_request('GET', users_path)
    
    if not users_result or not isinstance(users_result, dict):
        print("❌ No users found in Firebase Realtime Database")
        return False
    
    print(f"✅ Found {len(users_result)} users")
    
    # Step 2: Process each user and create mappings
    print("\n2️⃣ Processing users and creating mappings...")
    mappings_created = 0
    mappings_updated = 0
    
    for safe_user_id, user_data in users_result.items():
        if isinstance(user_data, dict) and 'settings' in user_data:
            settings = user_data['settings']
            
            # Check if user has Telegram settings
            if isinstance(settings, dict) and 'channels' in settings:
                channels = settings['channels']
                if isinstance(channels, dict) and 'telegram' in channels:
                    telegram_settings = channels['telegram']
                    
                    if isinstance(telegram_settings, dict) and telegram_settings.get('chatId'):
                        chat_id = telegram_settings['chatId']
                        username = telegram_settings.get('username', 'Unknown')
                        
                        print(f"   Processing user {safe_user_id} -> chat_id {chat_id}")
                        
                        # Check if mapping already exists
                        mapping_path = f"telegram_mappings/{chat_id}"
                        existing_mapping = firebase._make_request('GET', mapping_path)
                        
                        if existing_mapping and isinstance(existing_mapping, dict) and 'user_id' in existing_mapping:
                            if existing_mapping['user_id'] != safe_user_id:
                                # Update existing mapping
                                mapping_data = {
                                    'user_id': safe_user_id,
                                    'chat_id': chat_id,
                                    'username': username,
                                    'updated_at': datetime.now().isoformat(),
                                    'status': 'active'
                                }
                                firebase._make_request('PUT', mapping_path, mapping_data)
                                mappings_updated += 1
                                print(f"     ✅ Updated mapping")
                            else:
                                print(f"     ✅ Mapping already exists")
                        else:
                            # Create new mapping
                            mapping_data = {
                                'user_id': safe_user_id,
                                'chat_id': chat_id,
                                'username': username,
                                'created_at': datetime.now().isoformat(),
                                'status': 'active'
                            }
                            firebase._make_request('PUT', mapping_path, mapping_data)
                            mappings_created += 1
                            print(f"     ✅ Created new mapping")
    
    # Step 3: Summary
    print(f"\n3️⃣ Summary:")
    print(f"   Total users processed: {len(users_result)}")
    print(f"   New mappings created: {mappings_created}")
    print(f"   Existing mappings updated: {mappings_updated}")
    
    # Step 4: Verify all mappings
    print(f"\n4️⃣ Verifying all mappings...")
    mappings_path = "telegram_mappings"
    all_mappings = firebase._make_request('GET', mappings_path)
    
    if all_mappings and isinstance(all_mappings, dict):
        print(f"   Total mappings in database: {len(all_mappings)}")
        
        # Test a few mappings
        test_count = 0
        for chat_id, mapping_data in all_mappings.items():
            if test_count < 3:  # Test first 3 mappings
                if isinstance(mapping_data, dict) and 'user_id' in mapping_data:
                    user_id = mapping_data['user_id']
                    user_settings = firebase.get_user_alert_settings(user_id)
                    if user_settings:
                        print(f"     ✅ Mapping {chat_id} -> {user_id} verified")
                    else:
                        print(f"     ⚠️  Mapping {chat_id} -> {user_id} (user settings not found)")
                test_count += 1
    else:
        print("   ❌ No mappings found in database")
    
    print(f"\n🎉 User mapping setup completed!")
    print(f"\n📋 System Status:")
    print(f"   • Alert bot should now work for all users")
    print(f"   • /status command should work for all connected users")
    print(f"   • Background alert service should send alerts to all users")
    
    return True

def test_specific_user(chat_id, user_id):
    """Test a specific user mapping"""
    print(f"\n🧪 Testing specific user mapping...")
    print(f"   Chat ID: {chat_id}")
    print(f"   User ID: {user_id}")
    
    firebase = FirebaseRealtimeStorage()
    
    # Test mapping retrieval
    mapping_path = f"telegram_mappings/{chat_id}"
    mapping_result = firebase._make_request('GET', mapping_path)
    
    if mapping_result and isinstance(mapping_result, dict) and 'user_id' in mapping_result:
        print(f"   ✅ Mapping found: {mapping_result['user_id']}")
        
        # Test user settings
        user_settings = firebase.get_user_alert_settings(mapping_result['user_id'])
        if user_settings:
            print(f"   ✅ User settings found")
            print(f"   ✅ Alert types: {user_settings.get('alert_types', [])}")
            print(f"   ✅ Currency pairs: {user_settings.get('currency_pairs', [])}")
        else:
            print(f"   ❌ User settings not found")
    else:
        print(f"   ❌ Mapping not found")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_all_user_mappings()
    
    if success:
        print("\n✅ All user mappings are ready!")
        
        # Test specific user (you)
        test_specific_user("8008493413", "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2")
    else:
        print("\n❌ User mapping setup failed")
        sys.exit(1)
