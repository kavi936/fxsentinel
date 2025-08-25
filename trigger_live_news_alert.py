#!/usr/bin/env python3
"""
Trigger a live news alert to test the system
"""

import sys
import os
sys.path.append('backend')

from backend.services.news_alert_trigger import news_alert_trigger
import asyncio

async def trigger_live_news_alert():
    """Trigger a live news alert for testing"""
    print("🚨 Triggering Live News Alert Test")
    print("=" * 50)
    
    # Test news data
    test_news = {
        'id': 'test_alert_123',
        'title': '🧪 Test Live News Alert - FXSentinel',
        'summary': 'This is a test live news alert to verify the system is working correctly.',
        'content': 'The forex market is showing increased volatility as traders react to recent economic data. This test alert confirms that the FXSentinel alert system is functioning properly.',
        'source': 'FXSentinel Test',
        'url': 'https://fxsentinel.io',
        'timestamp': '2025-08-25T23:50:00Z',
        'impact': 'high',
        'category': 'forex'
    }
    
    # User data
    user_data = {
        'user_id': '0E0xJnQpYzZb8YkfQfSiwKYc8Fz2',
        'chat_id': '8008493413',
        'settings': {
            'telegram_enabled': True,
            'live_news_alerts': True,
            'alert_types': ['liveNews', 'economicCalendar'],
            'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
            'impact_levels': ['high', 'medium'],
            'notification_frequency': 'immediate'
        }
    }
    
    print(f"📰 News Title: {test_news['title']}")
    print(f"👤 User ID: {user_data['user_id']}")
    print(f"📱 Chat ID: {user_data['chat_id']}")
    
    # Test 1: Check if news is forex high impact
    print("\n1️⃣ Checking if news is forex high impact...")
    is_forex_high_impact = news_alert_trigger.is_forex_high_impact(test_news)
    print(f"   Is forex high impact: {is_forex_high_impact}")
    
    if is_forex_high_impact:
        print("   ✅ News qualifies for alert")
    else:
        print("   ⚠️  News doesn't qualify (this is expected for test data)")
    
    # Test 2: Check if AI analysis is needed
    print("\n2️⃣ Checking if AI analysis is needed...")
    needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(test_news)
    print(f"   Needs AI analysis: {needs_ai_analysis}")
    
    # Test 3: Send the alert
    print("\n3️⃣ Sending alert...")
    try:
        success = await news_alert_trigger._send_alert_to_user(user_data, test_news, needs_ai_analysis)
        
        if success:
            print("   ✅ Alert sent successfully")
            print("   📱 Check your Telegram for the alert")
        else:
            print("   ❌ Alert failed to send")
            return False
            
    except Exception as e:
        print(f"   ❌ Error sending alert: {e}")
        return False
    
    # Test 4: Check alert history
    print("\n4️⃣ Checking alert history...")
    try:
        from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Get alert history
        history = firebase.get_user_alert_history(user_data['user_id'], limit=5)
        
        if history:
            print(f"   ✅ Found {len(history)} recent alerts in history")
            latest_alert = history[0] if history else None
            if latest_alert:
                print(f"   📝 Latest alert: {latest_alert.get('title', 'Unknown')[:50]}...")
        else:
            print("   ⚠️  No alert history found")
            
    except Exception as e:
        print(f"   ⚠️  Error checking history: {e}")
    
    print("\n🎉 Live news alert test completed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(trigger_live_news_alert())
    if success:
        print("\n✅ Live news alert system is working")
    else:
        print("\n❌ Live news alert system has issues")
        sys.exit(1)
