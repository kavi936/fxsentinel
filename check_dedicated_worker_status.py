#!/usr/bin/env python3
"""
Check the status of the dedicated background worker
"""

import requests
import json
from datetime import datetime

def check_dedicated_worker_status():
    """Check if the dedicated worker is running and processing news"""
    print("🔍 Checking Dedicated Worker Status")
    print("=" * 50)
    
    try:
        # Check the main app's health endpoint
        print("1️⃣ Checking main app health...")
        response = requests.get("https://fxsentinel-production.up.railway.app/api/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Main app is healthy")
            print(f"   📊 Health data: {json.dumps(health_data, indent=2)}")
        else:
            print(f"   ❌ Main app health check failed: {response.status_code}")
        
        # Check if there's a dedicated worker health endpoint
        print(f"\n2️⃣ Checking dedicated worker health...")
        try:
            response = requests.get("https://fxsentinel-production.up.railway.app/api/health/alert-service", timeout=10)
            if response.status_code == 200:
                alert_health = response.json()
                print(f"   ✅ Alert service health: {json.dumps(alert_health, indent=2)}")
            else:
                print(f"   ⚠️  Alert service health check failed: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Could not check alert service health: {e}")
        
        # Check recent news processing
        print(f"\n3️⃣ Checking recent news processing...")
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news", timeout=10)
        
        if response.status_code == 200:
            news_data = response.json()
            news_items = news_data.get('news', [])
            
            print(f"   📊 Found {len(news_items)} news items")
            
            # Check the most recent news
            if news_items:
                latest_news = news_items[0]
                print(f"   📰 Latest news: {latest_news.get('title', '')[:60]}...")
                print(f"   📅 Published: {latest_news.get('published_at', '')}")
                print(f"   🏷️  Impact: {latest_news.get('impact', '')}")
                
                # Check if this news should have triggered an alert
                if latest_news.get('impact') == 'high':
                    print(f"   ⚠️  This high-impact news should have triggered an alert!")
        
        # Test the alert trigger endpoint
        print(f"\n4️⃣ Testing alert trigger endpoint...")
        test_news = {
            'id': 'test_worker_check_123',
            'title': 'Test Alert - Worker Status Check',
            'summary': 'This is a test to check if the dedicated worker is processing alerts.',
            'content': 'Test content for worker status check.',
            'source': 'Test',
            'impact': 'high',
            'published_at': datetime.now().isoformat(),
            'url': '',
            'timestamp': datetime.now().isoformat()
        }
        
        alert_data = {
            'type': 'news',
            'data': test_news
        }
        
        response = requests.post(
            "https://fxsentinel-production.up.railway.app/api/alerts/trigger",
            json=alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            alerts_sent = result.get('alerts_sent', 0)
            print(f"   ✅ Alert trigger test successful: {alerts_sent} alerts sent")
        else:
            print(f"   ❌ Alert trigger test failed: {response.status_code}")
            print(f"   📋 Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking worker status: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_dedicated_worker_status()
    if success:
        print("\n🎯 Worker status check: COMPLETED")
    else:
        print("\n🔧 Worker status check: FAILED")
