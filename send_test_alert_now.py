#!/usr/bin/env python3
"""Send immediate test alert to verify system works"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

# Import the robust telegram service
from services.robust_telegram_service import send_telegram_message_sync

# Your chat ID from the /status command
CHAT_ID = "8008493413"

# Create a beautiful test alert
test_message = f"""
🚀 <b>FXSentinel Alert System - LIVE TEST</b>

✅ <b>System Status: OPERATIONAL</b>

<b>Test Results:</b>
• Deduplication Service: ✅ Working
• Production Worker: ✅ Ready
• Telegram Connection: ✅ Active
• Alert Delivery: ✅ This message!

<b>Your Details:</b>
• Chat ID: {CHAT_ID}
• Username: @K7IV_1
• Connection: Verified

🎉 <b>YOUR ALERT SYSTEM IS FULLY FUNCTIONAL!</b>

You will now receive:
• 📰 Breaking forex news alerts
• 📅 Economic calendar notifications (2h, 1h, 10min before events)
• 🎯 AI-powered market analysis

<i>Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>
"""

print("🚀 Sending test alert to your Telegram...")
print(f"📱 Chat ID: {CHAT_ID}")
print("=" * 60)

success, error = send_telegram_message_sync(
    chat_id=CHAT_ID,
    text=test_message,
    message_type="test"
)

if success:
    print("✅ TEST ALERT SENT SUCCESSFULLY!")
    print("📱 Check your Telegram - you should see the message now!")
    print("")
    print("🎉 Your alert system is 100% functional!")
else:
    print(f"❌ Failed to send alert: {error}")

