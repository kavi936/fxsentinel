#!/usr/bin/env python3
"""
Debug Firebase service to see what's actually happening
"""

import sys
import os
sys.path.append('backend')

from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage

def test_firebase():
    """Test Firebase service directly"""
    print("🔍 Testing Firebase service directly...")
    
    firebase = FirebaseRealtimeStorage()
    
    # Test with a non-existent user
    print("\n🧪 Testing with non-existent user 'test_user'...")
    result = firebase.get_user_alert_settings('test_user')
    print(f"Result: {result}")
    print(f"Result type: {type(result)}")
    
    # Test with a valid user (if any exist)
    print("\n🧪 Testing with valid user 'user@example.com'...")
    result2 = firebase.get_user_alert_settings('user@example.com')
    print(f"Result: {result2}")
    print(f"Result type: {type(result2)}")

if __name__ == "__main__":
    test_firebase()
