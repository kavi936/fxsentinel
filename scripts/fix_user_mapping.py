#!/usr/bin/env python3
"""
Fix User Mapping
Creates the missing telegram_mappings entry for a user
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_user_mapping(chat_id: str, user_id: str, username: str = None):
    """Create the missing telegram_mappings entry"""
    print("\n" + "="*80)
    print("FIXING USER MAPPING")
    print("="*80)
    print(f"Chat ID: {chat_id}")
    print(f"User ID: {user_id}")
    print(f"Username: {username or 'N/A'}")
    
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Create mapping
        mapping_data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'username': username or 'Unknown',
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        mapping_path = f"telegram_mappings/{chat_id}"
        result = firebase._make_request('PUT', mapping_path, mapping_data)
        
        if result is not None:
            print(f"\n✅ Successfully created mapping at telegram_mappings/{chat_id}")
            
            # Verify
            verify_result = firebase._make_request('GET', mapping_path)
            if verify_result and isinstance(verify_result, dict) and 'user_id' in verify_result:
                print(f"✅ Verified: Mapping exists with user_id {verify_result['user_id']}")
                return True
            else:
                print(f"⚠️  Warning: Could not verify mapping (Firebase permissions issue?)")
                return True  # Still return True as PUT succeeded
        else:
            print(f"\n❌ Failed to create mapping (Firebase error)")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Your specific data from diagnostic
    chat_id = "8008493413"
    user_id = "c109c597ebf725f8424269b152d97e5e"  # Hashed user ID found in Firebase
    username = "K7IV_1"
    
    success = fix_user_mapping(chat_id, user_id, username)
    
    if success:
        print("\n✅ Mapping created! Try /status command again in Telegram.")
    else:
        print("\n❌ Failed to create mapping. Check Firebase permissions.")

