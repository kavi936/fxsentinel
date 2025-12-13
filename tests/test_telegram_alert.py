#!/usr/bin/env python3
"""
Test script to test Telegram alert sending directly
"""

import sys
import os
sys.path.append('backend')

from backend.services.alert_service import AlertService
import asyncio
from datetime import datetime

async def test_telegram_alert():
    """Test Telegram alert sending directly"""
    print("🧪 Testing Telegram Alert Sending")
    print("=" * 50)
    
    # Your user data
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    chat_id = "8008493413"
    
    # Test alert data
    alert_data = {
        'title': 'Test Alert - Federal Reserve News',
        'content': 'This is a test alert to verify Telegram functionality.',
        'type': 'liveNews',
        'impact_level': 'high',
        'currency_pairs': ['EUR/USD', 'USD/JPY'],
        'source': 'Test',
        'url': '',
        'timestamp': datetime.now().isoformat(),
        'ai_analysis': 'This is a test AI analysis.'
    }
    
    # User settings (simplified)
    user_settings = {
        'telegram': True,
        'channels': {
            'telegram': {
                'enabled': True,
                'chatId': chat_id
            }
        },
        'preferences': {
            'alertTypes': {
                'liveNews': True
            }
        }
    }
    
    try:
        print(f"📱 Testing Telegram alert to chat_id: {chat_id}")
        print(f"👤 User ID: {user_id}")
        
        # Create alert service
        alert_service = AlertService()
        
        # Test the alert processing
        success = await alert_service.process_alert(alert_data, user_settings, user_id)
        
        print(f"📤 Alert processing result: {success}")
        
        if success:
            print("✅ Telegram alert sent successfully!")
            return True
        else:
            print("❌ Telegram alert failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Telegram alert: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_telegram_alert())
    if success:
        print("\n🎉 Telegram alert test: PASSED")
    else:
        print("\n🔧 Telegram alert test: FAILED")
