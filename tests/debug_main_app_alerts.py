#!/usr/bin/env python3
"""
Debug the main app's alert processing to find why 0 alerts are sent
"""

import requests
import json
from datetime import datetime

def debug_main_app_alerts():
    """Debug why the main app is sending 0 alerts"""
    print("🔍 Debugging Main App Alert Processing")
    print("=" * 50)
    print(f"📅 Debug Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    # Test with a specific high-impact news item
    test_news = {
        'title': 'Global 36-Hour Interest-Rate Spree Heralds First US Cut of 2025',
        'summary': 'The first US interest rate cut since Donald Trump became president again is likely to seize the spotlight in a week that will determine policy settings for half of the world\'s 10 most traded currencies.',
        'source': 'Bloomberg',
        'published_at': '2025-09-13T20:00:00',
        'impact': 'high',
        'url': 'https://example.com/news/1',
        'id': 'test_123'
    }
    
    alert_data = {
        'type': 'news',
        'data': test_news
    }
    
    print("🧪 **Testing Main App Alert Processing:**")
    print("=" * 40)
    print(f"📰 News Title: {test_news['title']}")
    print(f"📰 Source: {test_news['source']}")
    print(f"🎯 Impact: {test_news['impact']}")
    print()
    
    try:
        print("🔄 Sending alert to main app...")
        response = requests.post(
            f"{main_app_url}/api/alerts/trigger",
            json=alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Main app response successful")
            print(f"📊 Success: {result.get('success', False)}")
            print(f"📊 Alerts sent: {result.get('alerts_sent', 0)}")
            print(f"📋 Message: {result.get('message', '')}")
            print(f"📋 Full response: {json.dumps(result, indent=2)}")
            
            if result.get('alerts_sent', 0) == 0:
                print()
                print("❌ **PROBLEM IDENTIFIED:** Main app is sending 0 alerts")
                print("🔍 **Possible causes:**")
                print("   1. No telegram mappings found")
                print("   2. User has Telegram disabled")
                print("   3. User has liveNews alerts disabled")
                print("   4. User subscription issues")
                print("   5. Telegram service issues")
                
        else:
            print(f"❌ Main app response failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_user_settings():
    """Check user settings and mappings"""
    print()
    print("👤 **Checking User Settings and Mappings:**")
    print("=" * 45)
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    # Try to get user settings (this might not work without auth, but let's try)
    try:
        # Check if there's a way to get user info
        response = requests.get(f"{main_app_url}/api/user/settings", timeout=10)
        if response.status_code == 200:
            print("✅ User settings endpoint accessible")
        else:
            print(f"❌ User settings endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ User settings endpoint error: {e}")
    
    # Check telegram mappings endpoint
    try:
        response = requests.get(f"{main_app_url}/api/telegram/mappings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Telegram mappings endpoint accessible")
            print(f"📊 Mappings data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        else:
            print(f"❌ Telegram mappings endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram mappings endpoint error: {e}")

def test_telegram_service():
    """Test if the Telegram service is working"""
    print()
    print("📱 **Testing Telegram Service:**")
    print("=" * 30)
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    # Try to test telegram service
    try:
        test_data = {
            'chat_id': 'test_chat_id',
            'message': 'Test message from FXSentinel'
        }
        
        response = requests.post(
            f"{main_app_url}/api/telegram/test",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Telegram test endpoint accessible")
        else:
            print(f"❌ Telegram test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram test endpoint error: {e}")

def check_system_health():
    """Check overall system health"""
    print()
    print("🏥 **System Health Check:**")
    print("=" * 25)
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    try:
        response = requests.get(f"{main_app_url}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Main app health check successful")
            print(f"📊 Health data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Main app health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Main app health check error: {e}")

if __name__ == "__main__":
    debug_main_app_alerts()
    check_user_settings()
    test_telegram_service()
    check_system_health()
