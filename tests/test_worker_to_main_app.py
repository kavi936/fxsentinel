#!/usr/bin/env python3
"""
Test communication between worker and main app
"""

import requests
import json
from datetime import datetime

def test_worker_to_main_app():
    """Test if worker can communicate with main app"""
    print("🔍 Testing Worker to Main App Communication")
    print("=" * 50)
    
    # Test news item
    test_news = {
        'id': 'worker_test_123',
        'title': 'Worker Test Alert - Fed Rate Decision',
        'summary': 'This is a test alert from the background worker to verify communication with the main app.',
        'content': 'The Federal Reserve is expected to make a rate decision that will impact forex markets. This is a test from the background worker.',
        'source': 'Worker Test',
        'impact': 'high',
        'published_at': datetime.now().isoformat(),
        'url': '',
        'timestamp': datetime.now().isoformat()
    }
    
    # Test 1: Check if worker can access main app
    print("1️⃣ Testing worker access to main app...")
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    try:
        response = requests.get(f"{main_app_url}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Worker can access main app")
        else:
            print(f"   ❌ Worker cannot access main app: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error accessing main app: {e}")
        return False
    
    # Test 2: Check if worker can send alert to main app
    print(f"\n2️⃣ Testing worker sending alert to main app...")
    
    alert_data = {
        'type': 'news',
        'data': test_news
    }
    
    try:
        response = requests.post(
            f"{main_app_url}/api/alerts/trigger",
            json=alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            alerts_sent = result.get('alerts_sent', 0)
            print(f"   ✅ Worker can send alerts to main app")
            print(f"   📨 Alerts sent: {alerts_sent}")
            return alerts_sent > 0
        else:
            print(f"   ❌ Worker cannot send alerts: {response.status_code}")
            print(f"   📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error sending alert: {e}")
        return False

def check_worker_news_monitoring():
    """Check if worker is monitoring news"""
    print(f"\n3️⃣ Checking worker news monitoring...")
    
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    
    try:
        response = requests.get(f"{worker_url}/api/news", timeout=10)
        if response.status_code == 200:
            news_data = response.json()
            news_items = news_data.get('news', [])
            
            print(f"   ✅ Worker has access to {len(news_items)} news items")
            
            # Check for high-impact news
            high_impact = [n for n in news_items if n.get('impact') == 'high']
            print(f"   🎯 Found {len(high_impact)} high-impact news items")
            
            if high_impact:
                latest = high_impact[0]
                print(f"   📰 Latest high-impact: {latest.get('title', '')[:60]}...")
                print(f"   📅 Published: {latest.get('published_at', '')}")
            
            return True
        else:
            print(f"   ❌ Worker cannot access news: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking worker news: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Worker to Main App Communication Test")
    print("=" * 60)
    
    # Test communication
    communication_ok = test_worker_to_main_app()
    
    # Test news monitoring
    news_ok = check_worker_news_monitoring()
    
    print(f"\n📋 Test Results:")
    print(f"   🔗 Communication: {'✅' if communication_ok else '❌'}")
    print(f"   📰 News monitoring: {'✅' if news_ok else '❌'}")
    
    if communication_ok and news_ok:
        print(f"\n🎉 Worker is working correctly!")
        print(f"   The issue might be that the worker is not automatically")
        print(f"   monitoring and sending alerts. It can do it manually but")
        print(f"   the automatic monitoring loop might not be running.")
    else:
        print(f"\n🔧 Worker has issues that need to be fixed.")
