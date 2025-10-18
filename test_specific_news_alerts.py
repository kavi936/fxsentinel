#!/usr/bin/env python3
"""
Test specific high-impact news items to see if they trigger alerts
"""

import requests
import json
from datetime import datetime

def test_specific_news_alerts():
    """Test the specific high-impact news items found"""
    print("🧪 Testing Specific High-Impact News Items")
    print("=" * 50)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Get the news items
    main_app_url = "https://fxsentinel-production.up.railway.app"
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    
    try:
        response = requests.get(f"{main_app_url}/api/dashboard-data", timeout=30)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            
            # Find the high-impact news items
            high_impact_news = []
            for item in news_items:
                title = item.get('title', '')
                impact = item.get('impact', '')
                
                # Check for the specific high-impact items we found
                if ('interest rate' in title.lower() and 'fed' in title.lower()) or \
                   ('federal reserve' in title.lower()) or \
                   (impact == 'high'):
                    high_impact_news.append(item)
            
            print(f"🎯 Found {len(high_impact_news)} high-impact news items to test")
            print()
            
            for i, news_item in enumerate(high_impact_news, 1):
                title = news_item.get('title', '')
                source = news_item.get('source', '')
                published = news_item.get('published_at', '')
                
                print(f"🧪 **Testing News Item {i}:**")
                print(f"   📰 Title: {title}")
                print(f"   📰 Source: {source}")
                print(f"   📅 Published: {published}")
                print()
                
                # Test if this news item would trigger an alert
                test_news_alert_trigger(news_item, worker_url)
                print()
                
        else:
            print(f"❌ Failed to fetch news: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_news_alert_trigger(news_item, worker_url):
    """Test if a specific news item triggers an alert"""
    try:
        # Create alert data
        alert_data = {
            'type': 'news',
            'data': news_item
        }
        
        print(f"   🔄 Sending to worker trigger endpoint...")
        
        response = requests.post(
            f"{worker_url}/api/trigger-alerts",
            json=alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Worker response successful")
            print(f"   📊 News processed: {result.get('news_alerts_processed', False)}")
            print(f"   📊 Calendar processed: {result.get('calendar_alerts_processed', False)}")
            print(f"   📅 Timestamp: {result.get('timestamp', '')}")
            
            if result.get('news_alerts_processed'):
                print(f"   🚨 **ALERT SHOULD HAVE BEEN SENT!**")
            else:
                print(f"   ⚠️  News processed but no alert sent")
        else:
            print(f"   ❌ Worker response failed: {response.status_code}")
            print(f"   📋 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error testing alert trigger: {e}")

def check_alert_history():
    """Check if there's any alert history or logs"""
    print("📋 **Checking Alert History and Logs:**")
    print("=" * 40)
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    # Try to get alert history
    try:
        response = requests.get(f"{main_app_url}/api/alerts/history", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alert history endpoint accessible")
            print(f"📊 Alert history data: {list(data.keys())}")
        else:
            print(f"❌ Alert history endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Alert history endpoint error: {e}")
    
    # Check if there are any recent alerts in the system
    print()
    print("🔍 **Checking Recent Alert Activity:**")
    print("=" * 35)
    
    # Test the main app's alert trigger endpoint directly
    try:
        test_news = {
            'title': 'Test Federal Reserve Interest Rate Alert',
            'summary': 'Test alert for Federal Reserve interest rate decision',
            'source': 'Test Source',
            'published_at': datetime.now().isoformat(),
            'impact': 'high'
        }
        
        alert_data = {
            'type': 'news',
            'data': test_news
        }
        
        response = requests.post(
            f"{main_app_url}/api/alerts/trigger",
            json=alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Main app alert trigger successful")
            print(f"📊 Alerts sent: {result.get('alerts_sent', 0)}")
            print(f"📊 Success: {result.get('success', False)}")
            print(f"📋 Message: {result.get('message', '')}")
            
            if result.get('alerts_sent', 0) > 0:
                print(f"🚨 **ALERT SYSTEM IS WORKING!**")
            else:
                print(f"⚠️  Alert system processed but sent 0 alerts")
        else:
            print(f"❌ Main app alert trigger failed: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error testing main app alert trigger: {e}")

if __name__ == "__main__":
    test_specific_news_alerts()
    print()
    check_alert_history()
