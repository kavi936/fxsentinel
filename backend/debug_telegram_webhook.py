#!/usr/bin/env python3
"""
Debug Telegram Webhook
Test and debug the Telegram webhook functionality
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_webhook_receiving():
    """Test if webhook is receiving messages"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return False
    
    try:
        # Get recent updates
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                updates = result.get('result', [])
                print(f"📊 Found {len(updates)} recent updates")
                
                for i, update in enumerate(updates):
                    message = update.get('message', {})
                    text = message.get('text', 'No text')
                    chat_id = message.get('chat', {}).get('id', 'Unknown')
                    user = message.get('from', {})
                    username = user.get('username', 'Unknown')
                    
                    print(f"Update {i+1}:")
                    print(f"  📝 Text: {text}")
                    print(f"  💬 Chat ID: {chat_id}")
                    print(f"  👤 User: @{username}")
                    print(f"  🆔 User ID: {user.get('id', 'Unknown')}")
                    print()
                
                return True
            else:
                print(f"❌ API error: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return False

def test_webhook_endpoint():
    """Test the webhook endpoint directly"""
    
    # Simulate a Telegram update
    test_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": 1693000000,
            "text": "/start"
        }
    }
    
    try:
        # Test local webhook endpoint
        response = requests.post(
            "http://localhost:5001/api/telegram/webhook",
            json=test_update,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"🔧 Testing webhook endpoint...")
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook endpoint responded successfully")
            return True
        else:
            print("❌ Webhook endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

def test_bot_response():
    """Test if bot can send messages"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return False
    
    # You'll need to provide a chat ID to test with
    chat_id = input("Enter your Telegram chat ID to test bot response (or press Enter to skip): ").strip()
    
    if not chat_id:
        print("⏭️ Skipping bot response test")
        return True
    
    try:
        test_message = {
            "chat_id": chat_id,
            "text": "🧪 Test message from FXSentinel Bot\n\nThis is a test to verify the bot can send messages.",
            "parse_mode": "HTML"
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json=test_message
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Bot can send messages successfully")
                return True
            else:
                print(f"❌ Bot send failed: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot response: {e}")
        return False

def main():
    """Main debug function"""
    print("🔍 Telegram Webhook Debug")
    print("=" * 40)
    
    # Test 1: Check recent updates
    print("\n1️⃣ Checking recent updates...")
    test_webhook_receiving()
    
    # Test 2: Test webhook endpoint
    print("\n2️⃣ Testing webhook endpoint...")
    test_webhook_endpoint()
    
    # Test 3: Test bot response
    print("\n3️⃣ Testing bot response...")
    test_bot_response()
    
    print("\n📋 Debug Summary:")
    print("- If updates are found, the bot is receiving messages")
    print("- If webhook endpoint fails, there's a Flask app issue")
    print("- If bot can't send messages, there's a bot configuration issue")

if __name__ == "__main__":
    main()
