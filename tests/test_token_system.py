#!/usr/bin/env python3
"""
Test Token Encoding/Decoding System
"""

import base64
import time

def _generate_setup_token(user_id):
    """Generate unique setup token for user"""
    # Create a unique token based on user_id and timestamp
    token_data = f"{user_id}_{int(time.time())}"
    # Use base64 encoding to make it URL-safe and reversible
    return base64.urlsafe_b64encode(token_data.encode()).decode()

def _decode_setup_token(token):
    """Decode setup token back to user_id"""
    try:
        # Decode the base64 token
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        # Extract user_id (everything before the last underscore)
        user_id = decoded.rsplit('_', 1)[0]
        return user_id
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def test_token_system():
    """Test the token encoding/decoding system"""
    print("🔐 Testing Token Encoding/Decoding System")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        "user@example.com",
        "abc123def456ghi789",  # Firebase UID
        "test.user@gmail.com",
        "very_long_firebase_uid_123456789"
    ]
    
    for user_id in test_cases:
        print(f"\n🧪 Testing user_id: {user_id}")
        
        # Generate token
        token = _generate_setup_token(user_id)
        print(f"   Generated token: {token}")
        
        # Decode token
        decoded_user_id = _decode_setup_token(token)
        print(f"   Decoded user_id: {decoded_user_id}")
        
        # Verify
        if decoded_user_id == user_id:
            print(f"   ✅ SUCCESS: Token encoding/decoding works")
        else:
            print(f"   ❌ FAILED: Token encoding/decoding failed")
            print(f"      Expected: {user_id}")
            print(f"      Got: {decoded_user_id}")
    
    print("\n🎉 Token system test completed!")

if __name__ == "__main__":
    test_token_system()
