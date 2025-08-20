#!/usr/bin/env python3
"""
Test script to verify Telegram authentication fix
"""

import requests
import json
import hashlib

def test_telegram_verification():
    """Test the telegram verification endpoint"""
    
    # Test user ID from the logs
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    print(f"Testing telegram verification for user: {user_id}")
    
    # Test the verification endpoint
    try:
        response = requests.post(
            "http://localhost:5001/api/telegram/verify",
            json={"userId": user_id},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Authentication successful!")
                if data.get("connected"):
                    print("✅ Bot is already connected!")
                else:
                    print("ℹ️ User has access but bot not connected yet")
            else:
                print("❌ Authentication failed")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing verification: {e}")

def test_firebase_storage():
    """Test Firebase storage functions"""
    
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    test_chat_id = "123456789"
    
    print(f"\nTesting Firebase storage for user: {user_id}")
    
    try:
        from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase_storage = FirebaseRealtimeStorage()
        
        # Test saving chat_id
        print("Testing save_telegram_chat_id...")
        save_result = firebase_storage.save_telegram_chat_id(user_id, test_chat_id)
        print(f"Save result: {save_result}")
        
        # Test getting chat_id
        print("Testing get_telegram_chat_id...")
        retrieved_chat_id = firebase_storage.get_telegram_chat_id(user_id)
        print(f"Retrieved chat_id: {retrieved_chat_id}")
        
        if retrieved_chat_id == test_chat_id:
            print("✅ Firebase storage test successful!")
        else:
            print("❌ Firebase storage test failed!")
            
    except Exception as e:
        print(f"❌ Error testing Firebase storage: {e}")

if __name__ == "__main__":
    print("🧪 Testing Telegram Authentication Fix")
    print("=" * 50)
    
    test_telegram_verification()
    test_firebase_storage()
    
    print("\n" + "=" * 50)
    print("Test completed!")
