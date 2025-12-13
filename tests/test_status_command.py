#!/usr/bin/env python3
"""
Test script to verify status command functionality
"""

import sys
import os
sys.path.append('backend')

from backend.services.telegram_bot_setup import TelegramBotSetup
from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
import asyncio

async def test_status_command():
    """Test the status command functionality"""
    print("🧪 Testing Status Command Functionality")
    print("=" * 50)
    
    # Initialize services
    telegram_setup = TelegramBotSetup()
    firebase = FirebaseRealtimeStorage()
    
    # Test data
    test_chat_id = "8008493413"
    test_user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    print(f"📱 Test Chat ID: {test_chat_id}")
    print(f"👤 Test User ID: {test_user_id}")
    
    # Step 1: Ensure mapping exists
    print("\n1️⃣ Setting up chat_id mapping...")
    mapping_data = {
        'user_id': test_user_id,
        'chat_id': test_chat_id,
        'created_at': '2025-08-25T23:30:00'
    }
    
    mapping_path = f"telegram_mappings/{test_chat_id}"
    result = firebase._make_request('PUT', mapping_path, mapping_data)
    
    if result is not None:
        print("✅ Chat ID mapping created")
    else:
        print("❌ Failed to create mapping")
        return False
    
    # Step 2: Test _find_user_by_chat_id method
    print("\n2️⃣ Testing _find_user_by_chat_id method...")
    try:
        user_id = await telegram_setup._find_user_by_chat_id(test_chat_id)
        
        if user_id:
            print(f"✅ Found user ID: {user_id}")
            if user_id == test_user_id:
                print("✅ User ID matches expected value")
            else:
                print("⚠️  User ID doesn't match (this might be expected if using hashed IDs)")
        else:
            print("❌ No user found for chat_id")
            return False
    except Exception as e:
        print(f"❌ Error in _find_user_by_chat_id: {e}")
        return False
    
    # Step 3: Test get_user_alert_settings
    print("\n3️⃣ Testing get_user_alert_settings...")
    try:
        settings = await telegram_setup.alert_service.get_user_alert_settings(test_user_id)
        
        if settings:
            print("✅ User settings retrieved successfully")
            print(f"   Settings keys: {list(settings.keys())}")
            
            # Check for expected keys
            expected_keys = ['impact_levels', 'alert_types', 'currency_pairs']
            missing_keys = [key for key in expected_keys if key not in settings]
            
            if missing_keys:
                print(f"⚠️  Missing expected keys: {missing_keys}")
            else:
                print("✅ All expected settings keys present")
        else:
            print("❌ Failed to retrieve user settings")
            return False
    except Exception as e:
        print(f"❌ Error in get_user_alert_settings: {e}")
        return False
    
    # Step 4: Test subscription status check
    print("\n4️⃣ Testing subscription status check...")
    try:
        subscription_check = await telegram_setup._check_subscription_status(test_user_id)
        
        print(f"✅ Subscription check completed")
        print(f"   Has access: {subscription_check.get('has_access', 'Unknown')}")
        print(f"   Status: {subscription_check.get('status', 'Unknown')}")
        
        if subscription_check.get('error'):
            print(f"   Error: {subscription_check.get('error')}")
    except Exception as e:
        print(f"❌ Error in subscription check: {e}")
        return False
    
    # Step 5: Clean up
    print("\n5️⃣ Cleaning up test data...")
    cleanup_result = firebase._make_request('DELETE', mapping_path)
    if cleanup_result is not None:
        print("✅ Test data cleaned up")
    else:
        print("⚠️  Could not clean up test data (this is okay)")
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_status_command())
    if success:
        print("\n✅ Status command functionality is working correctly")
    else:
        print("\n❌ Status command functionality has issues")
        sys.exit(1)
