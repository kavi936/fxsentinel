#!/usr/bin/env python3
"""
Debug script to test server response and see what's happening
"""

import requests
import json

def test_server_response():
    """Test the server response and add debug info"""
    
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    print(f"Testing server response for user: {user_id}")
    
    try:
        response = requests.post(
            "http://localhost:5001/api/telegram/verify",
            json={"userId": user_id},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response data: {response.json()}")
        
        # Check if the response matches our expected format
        data = response.json()
        
        if data.get("success") == True:
            print("✅ Server returned success=True as expected")
            if data.get("connected") == True:
                print("✅ Bot is connected")
            elif data.get("connected") == False:
                print("ℹ️ User has access but bot not connected yet")
        elif data.get("success") == False:
            print("❌ Server returned success=False (old behavior)")
            print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print("⚠️ Unexpected response format")
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")

if __name__ == "__main__":
    test_server_response()
