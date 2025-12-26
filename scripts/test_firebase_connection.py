#!/usr/bin/env python3
"""
Test Firebase Realtime Database connection for news cache
Verifies that rules are correctly configured
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage
from services.persistent_news_cache import get_persistent_news_cache
import json

def test_firebase_connection():
    """Test Firebase connection and write permissions"""
    print("=" * 60)
    print("FIREBASE CONNECTION TEST")
    print("=" * 60)
    print()
    
    firebase = FirebaseRealtimeStorage()
    print(f"📡 Firebase URL: {firebase.database_url}")
    print(f"📡 Project ID: {firebase.project_id}")
    print()
    
    # Test 1: Read from news_cache/current
    print("1. Testing READ access to news_cache/current...")
    test_path = "news_cache/current"
    result = firebase._make_request('GET', test_path)
    
    if result is None:
        print("   ❌ Connection failed (returned None)")
        return False
    elif isinstance(result, dict):
        if result == {}:
            print("   ✅ READ works (path exists but empty - this is OK)")
        else:
            print(f"   ✅ READ works (found {len(result.get('news', []))} cached items)")
    else:
        print(f"   ⚠️  Unexpected response type: {type(result)}")
    
    # Test 2: Write to news_cache/current
    print("\n2. Testing WRITE access to news_cache/current...")
    test_data = {
        'timestamp': '2025-12-26T18:00:00',
        'news_count': 1,
        'news': [{
            'id': 'test_123',
            'title': 'Test News Item',
            'source': 'Test Source',
            'published_at': '2025-12-26T18:00:00'
        }],
        'max_age_hours': 0.25,
        'last_fetch': '2025-12-26T18:00:00'
    }
    
    write_result = firebase._make_request('PUT', test_path, test_data)
    
    if write_result is None or write_result == {}:
        print("   ❌ WRITE failed (returned None or empty dict)")
        print("   💡 This indicates a 401 Unauthorized error")
        print("   💡 Check Firebase Database Rules allow write to 'news_cache'")
        return False
    elif isinstance(write_result, dict) and 'news' in write_result:
        print("   ✅ WRITE works (data saved successfully)")
        print(f"   ✅ Saved {len(write_result.get('news', []))} items")
    else:
        print(f"   ⚠️  Unexpected response: {write_result}")
    
    # Test 3: Verify we can read what we wrote
    print("\n3. Testing READ after WRITE...")
    verify_result = firebase._make_request('GET', test_path)
    if verify_result and isinstance(verify_result, dict) and verify_result.get('news'):
        print("   ✅ Can read back written data")
        if verify_result.get('news')[0].get('id') == 'test_123':
            print("   ✅ Data integrity verified")
        else:
            print("   ⚠️  Data mismatch")
    else:
        print("   ⚠️  Could not verify written data")
    
    # Test 4: Test using PersistentNewsCache service
    print("\n4. Testing PersistentNewsCache service...")
    cache = get_persistent_news_cache()
    
    test_news = [{
        'id': 'test_456',
        'title': 'Test News from Cache Service',
        'source': 'Test Source',
        'published_at': '2025-12-26T18:00:00',
        'added_to_feed_at': '2025-12-26T18:00:00'
    }]
    
    save_success = cache.save_news(test_news, append=False)
    if save_success:
        print("   ✅ Cache service save_news() works")
    else:
        print("   ❌ Cache service save_news() failed")
        return False
    
    # Test 5: Load from cache
    loaded_news = cache.load_news()
    if loaded_news:
        print(f"   ✅ Cache service load_news() works ({len(loaded_news)} items)")
        if any(item.get('id') == 'test_456' for item in loaded_news):
            print("   ✅ Can load saved data")
        else:
            print("   ⚠️  Saved data not found in loaded cache")
    else:
        print("   ⚠️  Cache service load_news() returned empty")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Firebase connection test completed")
    print("✅ If all tests passed, Firebase rules are correctly configured")
    print("✅ News cache should now work properly")
    print()
    
    return True

if __name__ == '__main__':
    try:
        test_firebase_connection()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

