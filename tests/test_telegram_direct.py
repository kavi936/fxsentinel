#!/usr/bin/env python3
"""
Direct test of Telegram bot functionality
"""

import sys
import os
sys.path.append('backend')

from backend.services.alert_service import get_alert_service
import asyncio

async def test_telegram_direct():
    """Test Telegram bot directly"""
    print("🧪 Testing Telegram Bot Directly")
    print("=" * 50)
    
    # Initialize alert service
    alert_service = get_alert_service()
    
    # Test data
    chat_id = "8008493413"
    test_message = "🧪 Test Alert - FXSentinel\n\nThis is a direct test to verify Telegram bot functionality.\n\nIf you receive this message, the bot is working correctly!\n\n⏰ " + datetime.now().strftime('%H:%M UTC')
    
    print(f"📱 Chat ID: {chat_id}")
    print(f"📝 Test Message: {test_message[:50]}...")
    
    # Test 1: Check if Telegram bot is initialized
    print("\n1️⃣ Checking Telegram bot initialization...")
    if alert_service.telegram_bot:
        print("✅ Telegram bot is initialized")
        try:
            bot_info = await alert_service.telegram_bot.get_me()
            print(f"✅ Bot info: @{bot_info.username}")
        except Exception as e:
            print(f"❌ Error getting bot info: {e}")
            return False
    else:
        print("❌ Telegram bot is not initialized")
        return False
    
    # Test 2: Send test message
    print("\n2️⃣ Sending test message...")
    try:
        success = await alert_service.send_telegram_alert(
            chat_id,
            test_message,
            parse_mode='HTML'
        )
        
        if success:
            print("✅ Test message sent successfully")
        else:
            print("❌ Failed to send test message")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False
    
    # Test 3: Check user settings
    print("\n3️⃣ Checking user settings...")
    try:
        user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
        user_settings = await alert_service.get_user_alert_settings(user_id)
        
        if user_settings:
            print("✅ User settings found")
            print(f"   Telegram enabled: {user_settings.get('telegram_enabled', False)}")
            print(f"   Live news alerts: {user_settings.get('live_news_alerts', False)}")
            print(f"   Alert types: {user_settings.get('alert_types', [])}")
        else:
            print("❌ User settings not found")
            return False
            
    except Exception as e:
        print(f"❌ Error getting user settings: {e}")
        return False
    
    print("\n🎉 Telegram bot test completed successfully!")
    return True

if __name__ == "__main__":
    from datetime import datetime
    success = asyncio.run(test_telegram_direct())
    if success:
        print("\n✅ Telegram bot is working correctly")
    else:
        print("\n❌ Telegram bot has issues")
        sys.exit(1)
