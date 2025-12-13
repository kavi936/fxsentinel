#!/usr/bin/env python3
"""
Diagnose Telegram Connection Issue
Check Firebase mappings and user settings
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

from services.firebase_realtime_storage import FirebaseRealtimeStorage

firebase = FirebaseRealtimeStorage()

print("=" * 60)
print("TELEGRAM CONNECTION DIAGNOSIS")
print("=" * 60)
print()

# Your details
CHAT_ID = "8008493413"
USERNAME = "@K7IV_1"

print(f"Your Chat ID: {CHAT_ID}")
print(f"Your Username: {USERNAME}")
print()

# Check 1: Look for telegram mappings
print("1. Checking telegram_mappings...")
try:
    mappings = firebase._make_request('GET', 'telegram_mappings')
    if mappings:
        print(f"   Found {len(mappings)} mappings:")
        for chat_id, data in mappings.items():
            print(f"   - Chat ID: {chat_id}")
            if isinstance(data, dict):
                print(f"     User ID: {data.get('user_id', 'Unknown')}")
                print(f"     Username: {data.get('username', 'Unknown')}")
    else:
        print("   ❌ NO mappings found in Firebase!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Check 2: Look for your specific mapping
print(f"2. Checking mapping for your chat ID ({CHAT_ID})...")
try:
    mapping = firebase._make_request('GET', f'telegram_mappings/{CHAT_ID}')
    if mapping and isinstance(mapping, dict):
        print(f"   ✅ Found mapping:")
        print(f"   User ID: {mapping.get('user_id', 'Unknown')}")
        print(f"   Username: {mapping.get('username', 'Unknown')}")
        print(f"   Connected at: {mapping.get('connected_at', 'Unknown')}")
    else:
        print(f"   ❌ NO mapping found for your chat ID!")
        print(f"   This is why you see 'Not Connected'")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Check 3: Look at all users
print("3. Checking all users in alerts/users...")
try:
    users = firebase._make_request('GET', 'alerts/users')
    if users:
        print(f"   Found {len(users)} users:")
        for user_hash, user_data in users.items():
            if isinstance(user_data, dict):
                settings = user_data.get('settings', {})
                print(f"   - User Hash: {user_hash}")
                # Check if this user has telegram enabled
                telegram_enabled = settings.get('telegram', False) or \
                                 settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                if telegram_enabled:
                    print(f"     Telegram: ✅ Enabled")
                else:
                    print(f"     Telegram: ❌ Not enabled")
    else:
        print("   ❌ NO users found!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
print()

print("WHAT TO DO:")
print("1. If NO mapping exists → Need to connect via dashboard")
print("2. If mapping exists but wrong → Need to update it")
print("3. If NO users exist → Need to set up user in Firebase")

