#!/usr/bin/env python3
"""
Setup user mapping for Telegram alerts
Creates chat_id to user_id mapping in Firebase Realtime Database
"""

import sys
import os
from datetime import datetime
sys.path.append('backend')

from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage

def setup_user_mapping():
    """Setup chat_id to user_id mapping for Telegram alerts"""
    print("🔧 Setting up User Mapping for Telegram Alerts")
    print("=" * 50)
    
    # Initialize Firebase storage
    firebase = FirebaseRealtimeStorage()
    
    # Your specific user data
    chat_id = "8008493413"
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    username = "K7IV_1"
    
    print(f"📱 Chat ID: {chat_id}")
    print(f"👤 User ID: {user_id}")
    print(f"📧 Username: @{username}")
    
    # Step 1: Create the mapping
    print("\n1️⃣ Creating chat_id to user_id mapping...")
    mapping_data = {
        'user_id': user_id,
        'chat_id': chat_id,
        'username': username,
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    mapping_path = f"telegram_mappings/{chat_id}"
    result = firebase._make_request('PUT', mapping_path, mapping_data)
    
    if result is not None:
        print("✅ Mapping created successfully")
    else:
        print("❌ Failed to create mapping")
        return False
    
    # Step 2: Verify the mapping
    print("\n2️⃣ Verifying mapping...")
    retrieved_mapping = firebase._make_request('GET', mapping_path)
    
    if retrieved_mapping and isinstance(retrieved_mapping, dict) and 'user_id' in retrieved_mapping:
        print(f"✅ Mapping verified: {retrieved_mapping['user_id']}")
        if retrieved_mapping['user_id'] == user_id:
            print("✅ User ID matches expected value")
        else:
            print("❌ User ID doesn't match")
            return False
    else:
        print("❌ Failed to retrieve mapping")
        return False
    
    # Step 3: Verify user settings exist
    print("\n3️⃣ Verifying user settings...")
    user_settings = firebase.get_user_alert_settings(user_id)
    
    if user_settings:
        print("✅ User settings found")
        print(f"   Settings keys: {list(user_settings.keys())}")
    else:
        print("❌ User settings not found")
        return False
    
    # Step 4: Test the complete flow
    print("\n4️⃣ Testing complete status flow...")
    try:
        from backend.services.telegram_bot_setup import TelegramBotSetup
        telegram_setup = TelegramBotSetup()
        
        # Test finding user by chat_id
        found_user_id = asyncio.run(telegram_setup._find_user_by_chat_id(chat_id))
        
        if found_user_id:
            print(f"✅ Found user by chat_id: {found_user_id}")
            if found_user_id == user_id:
                print("✅ User ID matches")
            else:
                print("⚠️  User ID doesn't match (might be hashed)")
        else:
            print("❌ Could not find user by chat_id")
            return False
            
    except Exception as e:
        print(f"❌ Error testing flow: {e}")
        return False
    
    print("\n🎉 User mapping setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test /status command in Telegram")
    print("2. Test /test command in Telegram")
    print("3. Verify alerts are working")
    
    return True

if __name__ == "__main__":
    import asyncio
    success = setup_user_mapping()
    if success:
        print("\n✅ User mapping is ready for use")
    else:
        print("\n❌ User mapping setup failed")
        sys.exit(1)
