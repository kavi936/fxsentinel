#!/usr/bin/env python3
"""
Check Telegram Chat ID from Firebase
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage

def check_telegram_chat_id():
    """Check the Telegram chat ID for the user"""
    
    print("🔍 Checking Telegram Chat ID from Firebase")
    print("=" * 50)
    
    try:
        firebase_storage = FirebaseRealtimeStorage()
        
        # Your user ID
        user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
        
        # Get chat ID
        chat_id = firebase_storage.get_telegram_chat_id(user_id)
        print(f"User ID: {user_id}")
        print(f"Telegram Chat ID: {chat_id}")
        
        if chat_id:
            print("✅ Chat ID found!")
            
            # Test if this chat ID is valid by trying to send a test message
            print("\n🧪 Testing Chat ID validity...")
            
            import requests
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if bot_token:
                telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                telegram_data = {
                    'chat_id': chat_id,
                    'text': '🔍 Chat ID validation test - Economic Calendar Alert System is working!',
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(telegram_url, json=telegram_data, timeout=10)
                
                if response.status_code == 200:
                    print("✅ Chat ID is valid! Test message sent successfully.")
                else:
                    print(f"❌ Chat ID validation failed: {response.status_code} - {response.text}")
            else:
                print("❌ Telegram bot token not found")
        else:
            print("❌ No chat ID found")
            
    except Exception as e:
        print(f"❌ Error checking chat ID: {e}")

if __name__ == "__main__":
    check_telegram_chat_id()
