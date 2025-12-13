#!/usr/bin/env python3
"""
Debug script to test verification function directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_verification_directly():
    """Test the verification function directly"""
    
    # Import the verification function
    from app import _verify_user_access, _get_user_chat_id
    
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    print(f"Testing verification for user: {user_id}")
    
    # Test user access verification
    print("\n1. Testing _verify_user_access...")
    access_result = _verify_user_access(user_id)
    print(f"Access result: {access_result}")
    
    # Test chat_id retrieval
    print("\n2. Testing _get_user_chat_id...")
    chat_id = _get_user_chat_id(user_id)
    print(f"Chat ID result: {chat_id}")
    
    # Test the full logic
    print("\n3. Testing full verification logic...")
    if access_result:
        if chat_id:
            print("✅ User has access and bot is connected")
            result = {
                "success": True,
                "connected": True,
                "chatId": chat_id,
                "username": f"user_{user_id}"
            }
        else:
            print("✅ User has access but bot not connected yet")
            result = {
                "success": True,
                "connected": False,
                "error": "Bot setup not completed. Please follow the setup instructions."
            }
    else:
        print("❌ User access denied")
        result = {
            "success": False,
            "error": "Access denied. Please log in to the dashboard first."
        }
    
    print(f"Final result: {result}")

if __name__ == "__main__":
    test_verification_directly()
