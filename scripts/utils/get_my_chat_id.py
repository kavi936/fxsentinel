#!/usr/bin/env python3
"""Quick script to get your Telegram chat ID"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

# Check Firebase for chat IDs
try:
    from services.firebase_realtime_storage import FirebaseRealtimeStorage
    
    firebase = FirebaseRealtimeStorage()
    
    # Get all telegram mappings
    mappings = firebase._make_request('GET', 'telegram_mappings')
    
    if mappings:
        print("📱 Found Telegram Chat IDs in Firebase:")
        print("=" * 60)
        for chat_id, data in mappings.items():
            if isinstance(data, dict):
                user_id = data.get('user_id', 'Unknown')
                username = data.get('username', 'Unknown')
                print(f"  Chat ID: {chat_id}")
                print(f"  User ID: {user_id}")
                print(f"  Username: @{username}")
                print("-" * 60)
    else:
        print("❌ No Telegram chat IDs found in Firebase")
        print("\nTo connect your Telegram:")
        print("1. Open Telegram and search for your bot")
        print("2. Send /start to your bot")
        print("3. Go to your FXSentinel dashboard → Alerts → Connect Telegram")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

