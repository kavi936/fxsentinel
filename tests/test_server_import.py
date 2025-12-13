#!/usr/bin/env python3
"""
Test Server Import Context
"""

import sys
import os

# Add backend to path (same as server)
sys.path.append('backend')

def test_server_import():
    """Test if Firebase import works in server context"""
    
    print("🧪 Testing Server Import Context")
    print("=" * 50)
    
    try:
        print("1. Testing Firebase import...")
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        print("✅ Firebase import successful")
        
        print("2. Testing Firebase instantiation...")
        firebase_storage = FirebaseRealtimeStorage()
        print("✅ Firebase instantiation successful")
        
        print("3. Testing Firebase connection...")
        test_result = firebase_storage._make_request('GET', 'test')
        print(f"✅ Firebase connection test: {test_result}")
        
        print("4. Testing alert history retrieval...")
        user_id = "demo_user@example.com"
        history = firebase_storage.get_user_alert_history(user_id, 10)
        print(f"✅ Retrieved {len(history)} alerts from Firebase")
        
        if history:
            print("   Sample alert:")
            alert = history[0]
            print(f"     Title: {alert.get('title', 'No title')}")
            print(f"     Type: {alert.get('alert_type', 'No type')}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_server_import()
