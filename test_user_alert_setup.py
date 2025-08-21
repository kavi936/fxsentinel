#!/usr/bin/env python3
"""
Test User Alert Setup
Check user settings and manually trigger alerts
"""

import requests
import json
from datetime import datetime

def test_user_alert_setup():
    print("🔍 Testing User Alert Setup")
    print("=" * 50)
    
    # Your user ID from the previous test
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    # Test 1: Check if user settings exist
    print("1. Checking user settings...")
    try:
        response = requests.get(f"http://localhost:5001/api/user/settings/{user_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            settings = response.json()
            print(f"   ✅ User settings found")
            print(f"   Telegram enabled: {settings.get('telegram_enabled', False)}")
            print(f"   Alert types: {settings.get('alert_types', [])}")
            print(f"   Currency pairs: {settings.get('currency_pairs', [])}")
        else:
            print(f"   ❌ User settings not found: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Get recent news to test with
    print("\n2. Getting recent news...")
    try:
        response = requests.get("http://localhost:5001/api/news")
        if response.status_code == 200:
            news_data = response.json()
            news_items = news_data.get('news', [])
            high_impact = [n for n in news_items if n.get('impact') == 'high']
            print(f"   ✅ Found {len(news_items)} total news items")
            print(f"   High impact: {len(high_impact)}")
            
            if high_impact:
                test_news = high_impact[0]
                print(f"   Test news: {test_news.get('title', 'No title')[:50]}...")
            else:
                print("   ❌ No high-impact news found")
                return
        else:
            print(f"   ❌ Failed to get news: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 3: Manually trigger an alert
    print("\n3. Manually triggering alert...")
    try:
        alert_data = {
            'user_id': user_id,
            'news_item': test_news,
            'ai_analysis': {
                'summary': 'This is a test AI analysis for debugging purposes.',
                'market_impact': 'High impact on EUR/USD and USD/JPY',
                'key_levels': 'Support: 1.0850, Resistance: 1.0950'
            }
        }
        
        response = requests.post(
            "http://localhost:5001/api/test-alert",
            json=alert_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Alert test successful")
            print(f"   Message length: {result.get('alert_message', '')[:100]}...")
        else:
            print(f"   ❌ Alert test failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Check if user has default settings
    print("\n4. Setting up default user settings...")
    try:
        default_settings = {
            'user_id': user_id,
            'telegram_enabled': True,
            'alert_types': ['liveNews', 'economicCalendar'],
            'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF'],
            'impact_levels': ['high', 'medium'],
            'notification_frequency': 'immediate'
        }
        
        response = requests.post(
            "http://localhost:5001/api/user/settings",
            json=default_settings,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Default settings saved")
        else:
            print(f"   ❌ Failed to save settings: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Check your Telegram bot for test messages")
    print("2. Configure alert preferences in the dashboard")
    print("3. Monitor for real alerts from high-impact news")

if __name__ == "__main__":
    test_user_alert_setup()
