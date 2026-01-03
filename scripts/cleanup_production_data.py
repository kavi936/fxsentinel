#!/usr/bin/env python3
"""
Production Data Cleanup Script
Removes test users and validates chat IDs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Invalid chat IDs (placeholders/test values)
INVALID_CHAT_IDS = [
    '123456789',
    '987654321',
    '000000000',
    '111111111',
    'test',
    'mock',
    'placeholder'
]

# Test user ID patterns
TEST_USER_PATTERNS = [
    'test_',
    'new_user_',
    'mock_',
    'demo_'
]

def is_test_user(user_id: str) -> bool:
    """Check if user_id is a test user"""
    if not user_id:
        return False
    
    user_id_lower = user_id.lower()
    return any(user_id_lower.startswith(pattern) for pattern in TEST_USER_PATTERNS)

def is_invalid_chat_id(chat_id: str) -> bool:
    """Check if chat_id is invalid (placeholder/test value)"""
    if not chat_id:
        return False
    
    chat_id_str = str(chat_id).strip()
    
    # Check against known invalid values
    if chat_id_str.lower() in [cid.lower() for cid in INVALID_CHAT_IDS]:
        return True
    
    # Check if it's a placeholder pattern
    if chat_id_str.startswith('mock_') or chat_id_str.startswith('test_'):
        return True
    
    # Check if it's too short (likely invalid)
    if len(chat_id_str) < 5:
        return True
    
    return False

def cleanup_production_data(dry_run: bool = True):
    """
    Clean up production data
    
    Args:
        dry_run: If True, only report what would be done without making changes
    """
    firebase = FirebaseRealtimeStorage()
    
    print("=" * 60)
    print("PRODUCTION DATA CLEANUP")
    print("=" * 60)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be made)'}")
    print()
    
    # Statistics
    stats = {
        'users_checked': 0,
        'test_users_found': 0,
        'test_users_removed': 0,
        'invalid_chat_ids_found': 0,
        'invalid_chat_ids_cleaned': 0,
        'errors': 0
    }
    
    # Step 1: Get all users
    print("Step 1: Getting all users...")
    users_path = "alerts/users"
    all_users = firebase._make_request('GET', users_path)
    
    if not all_users or not isinstance(all_users, dict):
        print("❌ No users found")
        return stats
    
    print(f"✅ Found {len(all_users)} users")
    print()
    
    # Step 2: Process each user
    print("Step 2: Processing users...")
    for safe_user_id, user_data in all_users.items():
        if not isinstance(user_data, dict):
            continue
        
        stats['users_checked'] += 1
        user_id = safe_user_id
        
        # Check if test user
        if is_test_user(user_id):
            stats['test_users_found'] += 1
            print(f"  Test user found: {user_id}")
            
            if not dry_run:
                # Remove test user
                user_path = f"alerts/users/{user_id}"
                result = firebase._make_request('DELETE', user_path)
                
                if result is not None:
                    stats['test_users_removed'] += 1
                    print(f"    ✅ Removed test user")
                else:
                    stats['errors'] += 1
                    print(f"    ❌ Failed to remove test user")
            else:
                print(f"    [DRY RUN] Would remove test user")
        
        # Check chat ID
        chat_id_path = f"alerts/users/{user_id}/telegram_chat_id"
        chat_id = firebase._make_request('GET', chat_id_path)
        
        if chat_id and is_invalid_chat_id(str(chat_id)):
            stats['invalid_chat_ids_found'] += 1
            print(f"  Invalid chat ID found for user {user_id}: {chat_id}")
            
            if not dry_run:
                # Remove invalid chat ID
                result = firebase._make_request('DELETE', chat_id_path)
                
                if result is not None:
                    stats['invalid_chat_ids_cleaned'] += 1
                    print(f"    ✅ Removed invalid chat ID")
                else:
                    stats['errors'] += 1
                    print(f"    ❌ Failed to remove invalid chat ID")
            else:
                print(f"    [DRY RUN] Would remove invalid chat ID")
    
    # Step 3: Clean up telegram_mappings
    print()
    print("Step 3: Cleaning up telegram_mappings...")
    mappings_path = "telegram_mappings"
    all_mappings = firebase._make_request('GET', mappings_path)
    
    if all_mappings and isinstance(all_mappings, dict):
        for chat_id, mapping_data in all_mappings.items():
            if isinstance(mapping_data, dict):
                # Check if chat_id is invalid
                if is_invalid_chat_id(chat_id):
                    stats['invalid_chat_ids_found'] += 1
                    print(f"  Invalid chat ID in mappings: {chat_id}")
                    
                    if not dry_run:
                        mapping_path_full = f"{mappings_path}/{chat_id}"
                        result = firebase._make_request('DELETE', mapping_path_full)
                        
                        if result is not None:
                            stats['invalid_chat_ids_cleaned'] += 1
                            print(f"    ✅ Removed invalid mapping")
                        else:
                            stats['errors'] += 1
                            print(f"    ❌ Failed to remove invalid mapping")
                    else:
                        print(f"    [DRY RUN] Would remove invalid mapping")
    
    print()
    print("=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"Users checked: {stats['users_checked']}")
    print(f"Test users found: {stats['test_users_found']}")
    print(f"Test users removed: {stats['test_users_removed']}")
    print(f"Invalid chat IDs found: {stats['invalid_chat_ids_found']}")
    print(f"Invalid chat IDs cleaned: {stats['invalid_chat_ids_cleaned']}")
    print(f"Errors: {stats['errors']}")
    print()
    
    if dry_run:
        print("⚠️  This was a DRY RUN - no changes were made")
        print("Run with --live flag to actually make changes")
    else:
        print("✅ Cleanup completed")
    
    return stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up production data')
    parser.add_argument('--live', action='store_true', help='Actually make changes (default is dry run)')
    args = parser.parse_args()
    
    try:
        cleanup_production_data(dry_run=not args.live)
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        sys.exit(1)

