#!/usr/bin/env python3
"""
Clear deduplication cache to allow alerts to be sent again
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage

def clear_deduplication_cache():
    """Clear global content hash deduplication cache"""
    print("=" * 80)
    print("CLEARING DEDUPLICATION CACHE")
    print("=" * 80)
    
    firebase = FirebaseRealtimeStorage()
    
    # Clear global content hashes
    print("\n1. Clearing global content hashes...")
    try:
        content_hashes_path = "alert_deduplication/content_hashes"
        result = firebase._make_request('GET', content_hashes_path)
        
        if result and isinstance(result, dict):
            count = len(result)
            print(f"   Found {count} content hashes")
            
            # Delete all content hashes
            for content_hash in list(result.keys()):
                hash_path = f"{content_hashes_path}/{content_hash}"
                firebase._make_request('DELETE', hash_path)
                print(f"   ✅ Deleted: {content_hash[:20]}...")
            
            print(f"   ✅ Cleared {count} global content hashes")
        else:
            print("   ℹ️  No content hashes found")
    except Exception as e:
        print(f"   ❌ Error clearing content hashes: {e}")
    
    # Clear per-user alert history
    print("\n2. Clearing per-user alert history...")
    try:
        users_path = "alert_deduplication/users"
        result = firebase._make_request('GET', users_path)
        
        if result and isinstance(result, dict):
            count = len(result)
            print(f"   Found {count} users with alert history")
            
            # Delete all user alert history
            for user_id in list(result.keys()):
                user_path = f"{users_path}/{user_id}"
                firebase._make_request('DELETE', user_path)
                print(f"   ✅ Deleted alert history for user: {user_id[:20]}...")
            
            print(f"   ✅ Cleared alert history for {count} users")
        else:
            print("   ℹ️  No user alert history found")
    except Exception as e:
        print(f"   ❌ Error clearing user alert history: {e}")
    
    print("\n" + "=" * 80)
    print("CACHE CLEARED")
    print("=" * 80)
    print("\n✅ Deduplication cache has been cleared.")
    print("   Alerts should now be sent for news items that were previously blocked.")
    print("\n⚠️  Note: This will allow alerts to be sent again, even if they were")
    print("   already sent before. Users may receive duplicate alerts for old news.")

if __name__ == '__main__':
    clear_deduplication_cache()

