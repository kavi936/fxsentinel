#!/usr/bin/env python3
"""
Migration Script: Consolidate Chat IDs to Single Location
Migrates all chat IDs from multiple locations to single source of truth:
alerts/users/{user_id}/telegram_chat_id

This script:
1. Finds all chat IDs in various locations
2. Migrates them to the single location
3. Preserves all existing data
4. Reports migration statistics
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_user_id(user_id: str) -> str:
    """Hash user_id to create safe Firebase path"""
    return hashlib.md5(user_id.encode()).hexdigest()

def migrate_chat_ids():
    """Migrate all chat IDs to single location"""
    firebase = FirebaseRealtimeStorage()
    
    print("=" * 60)
    print("CHAT ID MIGRATION: Consolidate to Single Location")
    print("=" * 60)
    print()
    
    # Statistics
    stats = {
        'users_processed': 0,
        'chat_ids_migrated': 0,
        'chat_ids_already_correct': 0,
        'chat_ids_found_in_settings': 0,
        'chat_ids_found_in_mappings': 0,
        'errors': 0
    }
    
    # Step 1: Get all users from alerts/users
    print("Step 1: Getting all users from alerts/users...")
    users_path = "alerts/users"
    all_users = firebase._make_request('GET', users_path)
    
    if not all_users or not isinstance(all_users, dict):
        print("❌ No users found in alerts/users")
        return stats
    
    print(f"✅ Found {len(all_users)} users")
    print()
    
    # Step 2: Process each user
    print("Step 2: Processing users...")
    for safe_user_id, user_data in all_users.items():
        if not isinstance(user_data, dict):
            continue
        
        stats['users_processed'] += 1
        
        # Check if chat_id already exists in dedicated location
        chat_id_path = f"alerts/users/{safe_user_id}/telegram_chat_id"
        existing_chat_id = firebase._make_request('GET', chat_id_path)
        
        if existing_chat_id:
            # Already in correct location
            stats['chat_ids_already_correct'] += 1
            continue
        
        # Look for chat_id in other locations
        chat_id = None
        source_location = None
        
        # Location 1: settings.channels.telegram.chatId (new structure)
        if 'settings' in user_data:
            settings = user_data['settings']
            if isinstance(settings, dict):
                if 'channels' in settings:
                    channels = settings.get('channels', {})
                    if isinstance(channels, dict) and 'telegram' in channels:
                        telegram_settings = channels.get('telegram', {})
                        if isinstance(telegram_settings, dict):
                            tg_chat_id = telegram_settings.get('chatId')
                            if tg_chat_id:
                                chat_id = str(tg_chat_id)
                                source_location = 'settings.channels.telegram.chatId'
                                stats['chat_ids_found_in_settings'] += 1
        
        # Location 2: settings.telegram_chat_id (old structure)
        if not chat_id and 'settings' in user_data:
            settings = user_data['settings']
            if isinstance(settings, dict) and 'telegram_chat_id' in settings:
                tg_chat_id = settings.get('telegram_chat_id')
                if tg_chat_id:
                    chat_id = str(tg_chat_id)
                    source_location = 'settings.telegram_chat_id'
                    stats['chat_ids_found_in_settings'] += 1
        
        # Location 3: telegram_mappings (mapping table)
        if not chat_id:
            # Search through telegram_mappings
            mappings_path = "telegram_mappings"
            all_mappings = firebase._make_request('GET', mappings_path)
            
            if all_mappings and isinstance(all_mappings, dict):
                for cid, mapping_data in all_mappings.items():
                    if isinstance(mapping_data, dict):
                        # Try to match by user_id (may be hashed or not)
                        mapping_user_id = mapping_data.get('user_id')
                        if mapping_user_id:
                            # Check if it matches (could be hashed or original)
                            if mapping_user_id == safe_user_id or hash_user_id(mapping_user_id) == safe_user_id:
                                chat_id = str(cid)
                                source_location = 'telegram_mappings'
                                stats['chat_ids_found_in_mappings'] += 1
                                break
        
        # If chat_id found, migrate it
        if chat_id:
            print(f"  Migrating chat_id {chat_id} from {source_location} to dedicated location...")
            result = firebase._make_request('PUT', chat_id_path, chat_id)
            
            if result is not None:
                stats['chat_ids_migrated'] += 1
                print(f"    ✅ Migrated successfully")
            else:
                stats['errors'] += 1
                print(f"    ❌ Failed to migrate")
        else:
            # No chat_id found anywhere
            print(f"  User {safe_user_id}: No chat_id found in any location")
    
    print()
    print("=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"Users processed: {stats['users_processed']}")
    print(f"Chat IDs already in correct location: {stats['chat_ids_already_correct']}")
    print(f"Chat IDs migrated: {stats['chat_ids_migrated']}")
    print(f"  - From settings: {stats['chat_ids_found_in_settings']}")
    print(f"  - From mappings: {stats['chat_ids_found_in_mappings']}")
    print(f"Errors: {stats['errors']}")
    print()
    
    return stats

if __name__ == "__main__":
    try:
        migrate_chat_ids()
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)

