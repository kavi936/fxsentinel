#!/usr/bin/env python3
"""
Test script to verify alert processing for the real user (not test user)
"""

import requests
import json
from datetime import datetime

def test_real_user_alert():
    """Test alert processing for the real user"""
    print("🧪 Testing Alert Processing for Real User")
    print("=" * 50)
    
    # Test data - simulate a high-impact news item
    test_news_item = {
        'id': 'test_news_real_user_123',
        'title': 'Federal Reserve Announces Interest Rate Decision',
        'summary': 'The Federal Reserve has announced a significant interest rate change that will impact forex markets.',
        'content': 'Breaking news: The Federal Reserve has made a major monetary policy decision affecting USD pairs.',
        'source': 'Reuters',
        'impact': 'high',
        'published_at': datetime.now().isoformat(),
        'url': 'https://example.com/news/fed-rate-decision',
        'timestamp': datetime.now().isoformat()
    }
    
    # Test alert data
    alert_data = {
        'type': 'news',
        'data': test_news_item
    }
    
    # Main app URL
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    try:
        print(f"📡 Sending test alert to: {main_app_url}/api/alerts/trigger")
        print(f"📰 News title: {test_news_item['title']}")
        print(f"🏷️  Impact level: {test_news_item['impact']}")
        print(f"ℹ️  Note: Test user with chat_id 123456789 will be automatically skipped")
        
        # Send the test alert
        response = requests.post(
            f"{main_app_url}/api/alerts/trigger",
            json=alert_data,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            alerts_sent = result.get('alerts_sent', 0)
            
            print(f"✅ Test completed successfully!")
            print(f"📨 Alerts sent: {alerts_sent}")
            print(f"📋 Full response: {json.dumps(result, indent=2)}")
            
            if alerts_sent > 0:
                print("🎉 SUCCESS: Alert processing fix is working!")
                print("✅ Real user is receiving alerts correctly")
                return True
            else:
                print("⚠️  WARNING: 0 alerts sent")
                print("🔍 This could mean:")
                print("   • Real user has alerts disabled")
                print("   • Real user is not subscribed")
                print("   • There's still an issue with the alert processing")
                return False
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"📋 Response content: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_real_user_alert()
    if success:
        print("\n🎯 Real user alert test: PASSED")
    else:
        print("\n🔧 Real user alert test: NEEDS INVESTIGATION")
