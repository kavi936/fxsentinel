#!/usr/bin/env python3
"""
Test script to inject mock news and test the alert system
"""

import requests
import json
import time
from datetime import datetime

def test_mock_news_alert():
    """Test the alert system with mock news"""
    
    print("🧪 Testing Mock News Alert System")
    print("=" * 50)
    
    # Mock news item that should trigger alerts
    mock_news = {
        'id': 'mock_trump_powell_001',
        'title': 'BREAKING: Trump Issues Arrest Warrant for Jerome Powell - Fed Chair Faces Legal Action',
        'content': 'Former President Donald Trump has issued an arrest warrant for Federal Reserve Chair Jerome Powell, citing alleged misconduct in monetary policy decisions. The unprecedented move has sent shockwaves through financial markets, with the dollar plummeting against major currencies. Traders are scrambling to adjust positions as uncertainty grips the forex markets. The arrest warrant, issued through Trump\'s legal team, alleges that Powell\'s interest rate decisions have caused economic harm to American citizens. Market analysts expect extreme volatility in USD pairs as this political bombshell unfolds.',
        'source': 'Reuters',
        'url': 'https://example.com/mock-news/trump-powell-warrant',
        'timestamp': datetime.now().isoformat(),
        'category': 'breaking_news',
        'impact': 'high'
    }
    
    print(f"\n📰 Mock News Created:")
    print(f"   Title: {mock_news['title']}")
    print(f"   Source: {mock_news['source']}")
    print(f"   Impact: {mock_news['impact']}")
    
    # Test 1: Check if our alert system would detect this as high-impact
    print(f"\n1. Testing High-Impact Detection...")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.news_alert_trigger import news_alert_trigger
        
        # Test forex high-impact detection
        is_forex_high_impact = news_alert_trigger.is_forex_high_impact(mock_news)
        print(f"   Forex High-Impact: {'✅ Yes' if is_forex_high_impact else '❌ No'}")
        
        # Test AI analysis decision
        should_analyze = news_alert_trigger.should_analyze_with_ai(mock_news)
        print(f"   Should Analyze with AI: {'✅ Yes' if should_analyze else '❌ No'}")
        
        # Test currency pair extraction
        affected_pairs = news_alert_trigger.get_affected_currency_pairs(mock_news)
        print(f"   Affected Currency Pairs: {affected_pairs}")
        
        if is_forex_high_impact:
            print("   ✅ This mock news would trigger alerts!")
        else:
            print("   ❌ This mock news would NOT trigger alerts")
            
    except Exception as e:
        print(f"   ❌ Error testing detection: {e}")
    
    # Test 2: Check user alert settings
    print(f"\n2. Checking User Alert Settings...")
    try:
        # Test with your user ID
        test_user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
        
        response = requests.get(
            f"http://localhost:5001/api/alerts/user-settings?userId={test_user_id}",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                settings = data.get('settings', {})
                telegram_enabled = settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                chat_id = settings.get('channels', {}).get('telegram', {}).get('chatId', '')
                
                print(f"   Telegram enabled: {'✅ Yes' if telegram_enabled else '❌ No'}")
                print(f"   Chat ID configured: {'✅ Yes' if chat_id else '❌ No'}")
                
                if telegram_enabled and chat_id:
                    print("   ✅ User would receive alerts!")
                else:
                    print("   ❌ User would NOT receive alerts")
            else:
                print("   ⚠️ No user settings found")
        else:
            print(f"   ❌ User settings request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking user settings: {e}")
    
    # Test 3: Simulate the alert processing
    print(f"\n3. Simulating Alert Processing...")
    try:
        from services.news_alert_trigger import news_alert_trigger
        
        # Process the mock news
        results = news_alert_trigger.process_news_for_alerts([mock_news])
        
        print(f"   Results: {results}")
        
        if results.get('high_impact_count', 0) > 0:
            print("   ✅ Mock news was processed as high-impact!")
        else:
            print("   ❌ Mock news was NOT processed as high-impact")
            
        if results.get('alerts_sent', 0) > 0:
            print("   ✅ Alerts were sent!")
        else:
            print("   ❌ No alerts were sent")
            
    except Exception as e:
        print(f"   ❌ Error simulating alert processing: {e}")
    
    # Test 4: Create a test alert manually
    print(f"\n4. Creating Manual Test Alert...")
    try:
        # Create a test alert using the existing test endpoint
        test_user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
        
        test_alert_data = {
            'userId': test_user_id,
            'alertType': 'mock_news',
            'message': f"""
🚨 **BREAKING FOREX NEWS**

**{mock_news['title']}**

📊 **Details:**
• Source: {mock_news['source']}
• Currency Pairs: USD pairs (EUR/USD, USD/JPY, GBP/USD)
• Time: {datetime.now().strftime('%H:%M UTC')}

🤖 **AI Analysis:**
This unprecedented political development targeting the Federal Reserve Chair has created extreme market uncertainty. The dollar is expected to face significant downward pressure as traders react to potential Fed leadership changes. USD pairs should see increased volatility with potential bearish moves across the board.

🔗 [Read Full Article]({mock_news['url']})
📱 Check dashboard for detailed analysis

*This is a test alert to verify the system is working correctly.*
            """.strip()
        }
        
        response = requests.post(
            "http://localhost:5001/api/alerts/test",
            headers={"Content-Type": "application/json"},
            json=test_alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Test alert sent successfully!")
                print("   📱 Check your Telegram for the test alert")
            else:
                print(f"   ❌ Test alert failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Test alert request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error sending test alert: {e}")
    
    print(f"\n" + "=" * 50)
    print("Mock news alert test completed!")
    print("\n📱 Check your Telegram for the test alert")
    print("📊 Monitor backend logs for processing details")

if __name__ == "__main__":
    test_mock_news_alert()
