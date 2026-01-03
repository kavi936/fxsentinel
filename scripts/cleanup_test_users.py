#!/usr/bin/env python3
"""
Clean up test users from production Firebase
Removes users with invalid/placeholder chat IDs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage

# Invalid/placeholder chat IDs to identify test users
INVALID_CHAT_IDS = ['987654321', '123456789', '000000000', '111111111']

def cleanup_test_users():
    """Remove test users with invalid chat IDs"""
    print("=" * 80)
    print("CLEANING UP TEST USERS")
    print("=" * 80)
    
    firebase = FirebaseRealtimeStorage()
    
    # Get all users
    print("\n1. Getting all users...")
    users_path = "alerts/users"
    all_users = firebase._make_request('GET', users_path)
    
    if not all_users or not isinstance(all_users, dict):
        print("   ⚠️  No users found")
        return
    
    print(f"   ✅ Found {len(all_users)} users")
    
    # Identify test users
    print("\n2. Identifying test users...")
    test_users = []
    real_users = []
    
    for user_id, user_data in all_users.items():
        if not isinstance(user_data, dict):
            continue
        
        # Check for invalid chat IDs
        chat_id = None
        if user_data.get('telegram_chat_id'):
            chat_id = str(user_data['telegram_chat_id'])
        elif user_data.get('settings', {}).get('channels', {}).get('telegram', {}).get('chatId'):
            chat_id = str(user_data['settings']['channels']['telegram']['chatId'])
        elif user_data.get('settings', {}).get('telegram_chat_id'):
            chat_id = str(user_data['settings']['telegram_chat_id'])
        
        # Check if chat_id is invalid
        if chat_id and chat_id in INVALID_CHAT_IDS:
            test_users.append((user_id, chat_id))
            print(f"   ⚠️  Test user found: {user_id} (chat_id: {chat_id})")
        elif user_id.startswith('test_'):
            test_users.append((user_id, chat_id or 'N/A'))
            print(f"   ⚠️  Test user found: {user_id} (user_id starts with 'test_')")
        else:
            real_users.append((user_id, chat_id))
    
    print(f"\n   Found {len(test_users)} test users")
    print(f"   Found {len(real_users)} real users")
    
    if not test_users:
        print("\n✅ No test users found - nothing to clean up")
        return
    
    # Confirm deletion
    print("\n3. Test users to be deleted:")
    for user_id, chat_id in test_users:
        print(f"   - {user_id} (chat_id: {chat_id})")
    
    response = input("\n⚠️  Delete these test users? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled - no users deleted")
        return
    
    # Delete test users
    print("\n4. Deleting test users...")
    deleted_count = 0
    
    for user_id, chat_id in test_users:
        try:
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            user_path = f"alerts/users/{safe_user_id}"
            firebase._make_request('DELETE', user_path)
            
            # Also delete from telegram_mappings if exists
            if chat_id and chat_id != 'N/A':
                mapping_path = f"telegram_mappings/{chat_id}"
                firebase._make_request('DELETE', mapping_path)
            
            print(f"   ✅ Deleted: {user_id}")
            deleted_count += 1
        except Exception as e:
            print(f"   ❌ Error deleting {user_id}: {e}")
    
    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print(f"\n✅ Deleted {deleted_count} test users")
    print(f"✅ Kept {len(real_users)} real users")

if __name__ == '__main__':
    cleanup_test_users()

