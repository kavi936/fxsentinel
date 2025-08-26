#!/usr/bin/env python3
"""
Test sending a direct alert to the user
"""

import sys
import os
sys.path.append('backend')

from backend.services.news_alert_trigger import news_alert_trigger
from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
import asyncio

async def test_direct_alert():
    """Test sending a direct alert to the user"""
    print("🧪 Testing Direct Alert to User")
    print("=" * 50)
    
    try:
        # Create a test news item
        test_news = {
            'id': 'test_123',
            'title': 'Test Alert - Fed Rate Cut News',
            'summary': 'This is a test alert to verify the alert system is working correctly.',
            'source': 'Test',
            'impact': 'high',
            'published_at': '2025-08-26T10:00:00',
            'currency_pairs': ['EUR/USD', 'USD/JPY'],
            'type': 'RSS_FEED',
            'url': 'https://test.com'
        }
        
        # User data
        user_data = {
            'user_id': '0E0xJnQpYzZb8YkfQfSiwKYc8Fz2',
            'chat_id': '8008493413',
            'settings': {
                'telegram_enabled': True,
                'live_news_alerts': True,
                'impact_levels': ['high', 'medium'],
                'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
                'alert_types': ['liveNews', 'economicCalendar'],
                'ai_analysis_enabled': True
            }
        }
        
        print("📱 Sending test alert...")
        print(f"   User ID: {user_data['user_id']}")
        print(f"   Chat ID: {user_data['chat_id']}")
        print(f"   News Title: {test_news['title']}")
        
        # Send the alert
        success = await news_alert_trigger._send_alert_to_user(user_data, test_news, needs_ai_analysis=False)
        
        if success:
            print("✅ Test alert sent successfully!")
        else:
            print("❌ Test alert failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error in test_direct_alert: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_alert())
    if success:
        print("\n✅ Direct alert test completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Direct alert test failed")
        sys.exit(1)
