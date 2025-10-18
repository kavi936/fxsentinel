#!/usr/bin/env python3
"""
Setup your alert settings in Firebase
"""

import os
import sys
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

from services.firebase_realtime_storage import FirebaseRealtimeStorage

firebase = FirebaseRealtimeStorage()

# Your details
USER_ID = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
CHAT_ID = "8008493413"
USERNAME = "@K7IV_1"

print("=" * 60)
print("SETTING UP YOUR ALERTS")
print("=" * 60)
print(f"User ID: {USER_ID}")
print(f"Chat ID: {CHAT_ID}")
print(f"Username: {USERNAME}")
print()

# Hash the user ID (Firebase uses MD5 hash for paths)
safe_user_id = hashlib.md5(USER_ID.encode()).hexdigest()
print(f"Hashed User ID: {safe_user_id}")
print()

# Check current settings
print("1. Checking your current alert settings...")
user_path = f"alerts/users/{safe_user_id}"
current_settings = firebase._make_request('GET', user_path)

if current_settings:
    print("   ✅ Found existing settings:")
    print(f"   {current_settings}")
else:
    print("   ℹ️  No settings found, will create new ones")

print()

# Create/Update alert settings with Telegram enabled
print("2. Setting up your alert preferences...")

alert_settings = {
    "settings": {
        "telegram": True,
        "telegram_chat_id": CHAT_ID,
        "telegram_username": USERNAME,
        "preferences": {
            "alertTypes": {
                "liveNews": True,
                "preNews": True,
                "postNews": True,
                "economicCalendar": True,
                "technicalAnalysis": False
            },
            "impactLevels": {
                "high": True,
                "medium": True,
                "low": False
            },
            "currencyPairs": [
                "EUR/USD",
                "GBP/USD",
                "USD/JPY",
                "USD/CHF",
                "AUD/USD",
                "USD/CAD"
            ],
            "quietHours": {
                "enabled": False,
                "start": "22:00",
                "end": "06:00",
                "timezone": "UTC"
            }
        },
        "channels": {
            "telegram": {
                "enabled": True,
                "chatId": CHAT_ID,
                "username": USERNAME
            },
            "email": {
                "enabled": False,
                "address": ""
            }
        }
    }
}

# Update settings
result = firebase._make_request('PUT', user_path, alert_settings)

if result:
    print("   ✅ Alert settings saved!")
else:
    print("   ❌ Failed to save settings")

print()

# Update telegram mapping with username
print("3. Updating Telegram mapping...")
mapping_data = {
    "user_id": USER_ID,
    "username": USERNAME,
    "connected_at": datetime.now().isoformat()
}

mapping_result = firebase._make_request('PUT', f'telegram_mappings/{CHAT_ID}', mapping_data)

if mapping_result:
    print("   ✅ Telegram mapping updated!")
else:
    print("   ❌ Failed to update mapping")

print()

# Verify
print("4. Verifying setup...")
verify_settings = firebase._make_request('GET', user_path)
verify_mapping = firebase._make_request('GET', f'telegram_mappings/{CHAT_ID}')

if verify_settings and verify_mapping:
    print("   ✅ VERIFICATION SUCCESSFUL!")
    print()
    print("=" * 60)
    print("YOUR ALERTS ARE NOW CONFIGURED!")
    print("=" * 60)
    print()
    print("You will receive alerts for:")
    print("  ✅ Live breaking news")
    print("  ✅ Pre-event warnings (2h, 1h, 10min before)")
    print("  ✅ Post-event analysis")
    print("  ✅ Economic calendar events")
    print()
    print("Impact levels:")
    print("  ✅ High impact events")
    print("  ✅ Medium impact events")
    print("  ❌ Low impact events (filtered)")
    print()
    print("Currency pairs monitored:")
    for pair in alert_settings["settings"]["preferences"]["currencyPairs"]:
        print(f"  • {pair}")
else:
    print("   ❌ Verification failed")
    print("   Please check Firebase console")

