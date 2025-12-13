#!/usr/bin/env python3
"""
Test alert system compatibility with user settings
"""

import sys
import os
sys.path.append('backend')

from backend.services.alert_service import get_alert_service
import asyncio

async def test_alert_compatibility():
    """Test alert system with actual user settings"""
    print("🧪 Testing Alert System Compatibility")
    print("=" * 50)
    
    # Initialize alert service
    alert_service = get_alert_service()
    
    # Your actual user settings
    user_settings = {
        "ai_analysis_enabled": True,
        "alert_types": ["liveNews", "economicCalendar"],
        "currency_pairs": ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "USD/CAD"],
        "economic_calendar_alerts": True,
        "impact_levels": ["high", "medium"],
        "live_news_alerts": True,
        "notification_frequency": "immediate",
        "quiet_hours": {"enabled": False, "end": "06:00", "start": "22:00", "timezone": "UTC"},
        "telegram_enabled": True
    }
    
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    print(f"👤 User ID: {user_id}")
    print(f"📱 Telegram enabled: {user_settings.get('telegram_enabled')}")
    print(f"📰 Live news alerts: {user_settings.get('live_news_alerts')}")
    print(f"🎯 Alert types: {user_settings.get('alert_types')}")
    
    # Test 1: Check if should send alert
    print("\n1️⃣ Testing _should_send_alert...")
    
    test_alert = {
        'title': 'Test Forex News',
        'type': 'liveNews',
        'impact_level': 'high',
        'currency_pairs': ['EUR/USD', 'USD/JPY']
    }
    
    should_send = alert_service._should_send_alert(test_alert, user_settings)
    print(f"   Should send alert: {should_send}")
    
    if should_send:
        print("   ✅ Alert preferences check passed")
    else:
        print("   ❌ Alert preferences check failed")
        return False
    
    # Test 2: Check quiet hours
    print("\n2️⃣ Testing quiet hours...")
    is_quiet = alert_service._is_quiet_hours(user_settings)
    print(f"   Is quiet hours: {is_quiet}")
    
    if not is_quiet:
        print("   ✅ Not in quiet hours")
    else:
        print("   ⚠️  Currently in quiet hours")
    
    # Test 3: Test process_alert
    print("\n3️⃣ Testing process_alert...")
    
    alert_data = {
        'title': '🧪 Test Alert - FXSentinel',
        'content': 'This is a test alert to verify the system is working correctly.',
        'type': 'liveNews',
        'impact_level': 'high',
        'currency_pairs': ['EUR/USD', 'USD/JPY'],
        'source': 'Test',
        'url': '',
        'timestamp': '2025-08-25T23:50:00Z'
    }
    
    try:
        success = await alert_service.process_alert(alert_data, user_settings, user_id)
        print(f"   Process alert result: {success}")
        
        if success:
            print("   ✅ Alert processed successfully")
        else:
            print("   ❌ Alert processing failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error processing alert: {e}")
        return False
    
    # Test 4: Check subscription status
    print("\n4️⃣ Testing subscription status...")
    try:
        subscription_valid = await alert_service._check_user_subscription(user_id)
        print(f"   Subscription valid: {subscription_valid}")
        
        if subscription_valid:
            print("   ✅ Subscription check passed")
        else:
            print("   ⚠️  Subscription check failed (this might be expected)")
            
    except Exception as e:
        print(f"   ⚠️  Subscription check error: {e}")
    
    print("\n🎉 Alert system compatibility test completed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_alert_compatibility())
    if success:
        print("\n✅ Alert system is compatible with your settings")
    else:
        print("\n❌ Alert system has compatibility issues")
        sys.exit(1)
