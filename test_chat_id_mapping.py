#!/usr/bin/env python3
"""
Test script to verify chat_id mapping functionality
"""

import sys
import os
sys.path.append('backend')

from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage

def test_chat_id_mapping():
    """Test the chat_id mapping functionality"""
    print("🧪 Testing Chat ID Mapping Functionality")
    print("=" * 50)
    
    # Initialize Firebase storage
    firebase = FirebaseRealtimeStorage()
    
    # Test data
    test_chat_id = "8008493413"
    test_user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    print(f"📱 Test Chat ID: {test_chat_id}")
    print(f"👤 Test User ID: {test_user_id}")
    
    # Test 1: Store mapping
    print("\n1️⃣ Testing mapping storage...")
    mapping_data = {
        'user_id': test_user_id,
        'chat_id': test_chat_id,
        'created_at': '2025-08-25T23:30:00'
    }
    
    mapping_path = f"telegram_mappings/{test_chat_id}"
    result = firebase._make_request('PUT', mapping_path, mapping_data)
    
    if result is not None:
        print("✅ Mapping stored successfully")
    else:
        print("❌ Failed to store mapping")
        return False
    
    # Test 2: Retrieve mapping
    print("\n2️⃣ Testing mapping retrieval...")
    retrieved_mapping = firebase._make_request('GET', mapping_path)
    
    if retrieved_mapping and isinstance(retrieved_mapping, dict) and 'user_id' in retrieved_mapping:
        print(f"✅ Mapping retrieved: {retrieved_mapping['user_id']}")
        if retrieved_mapping['user_id'] == test_user_id:
            print("✅ User ID matches expected value")
        else:
            print("❌ User ID doesn't match")
            return False
    else:
        print("❌ Failed to retrieve mapping")
        return False
    
    # Test 3: Test user settings retrieval
    print("\n3️⃣ Testing user settings retrieval...")
    user_settings = firebase.get_user_alert_settings(test_user_id)
    
    if user_settings:
        print("✅ User settings retrieved successfully")
        print(f"   Settings keys: {list(user_settings.keys())}")
    else:
        print("❌ Failed to retrieve user settings")
        return False
    
    # Test 4: Clean up test data
    print("\n4️⃣ Cleaning up test data...")
    cleanup_result = firebase._make_request('DELETE', mapping_path)
    if cleanup_result is not None:
        print("✅ Test data cleaned up")
    else:
        print("⚠️  Could not clean up test data (this is okay)")
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = test_chat_id_mapping()
    if success:
        print("\n✅ Chat ID mapping functionality is working correctly")
    else:
        print("\n❌ Chat ID mapping functionality has issues")
        sys.exit(1)
