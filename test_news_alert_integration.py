#!/usr/bin/env python3
"""
Test script to verify news alert integration
"""

import requests
import json
import time

def test_news_alert_integration():
    """Test the news alert integration"""
    
    print("🧪 Testing News Alert Integration")
    print("=" * 50)
    
    # Test 1: Fetch news and check if alert processing is triggered
    print("\n1. Testing news fetch with alert processing...")
    try:
        response = requests.get(
            "http://localhost:5001/api/news",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News fetched successfully!")
            print(f"   Total articles: {data.get('total_articles', 0)}")
            print(f"   Sources: {data.get('sources', [])}")
            print(f"   Cache status: {data.get('cache_status', 'unknown')}")
            
            # Check if we have news items
            news_items = data.get('news', [])
            if news_items:
                print(f"   First news item: {news_items[0].get('title', 'No title')[:50]}...")
                print(f"   News source: {news_items[0].get('source', 'Unknown')}")
                
                # Check for high-impact keywords in first few items
                high_impact_count = 0
                for item in news_items[:5]:
                    title = item.get('title', '').lower()
                    if any(keyword in title for keyword in ['fed', 'ecb', 'boe', 'nfp', 'cpi', 'gdp']):
                        high_impact_count += 1
                        print(f"   🚨 High-impact news found: {item.get('title', '')[:50]}...")
                
                print(f"   High-impact news items in first 5: {high_impact_count}")
            else:
                print("   ⚠️ No news items found")
        else:
            print(f"❌ News fetch failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing news fetch: {e}")
    
    # Test 2: Check if alert processing is working
    print("\n2. Testing alert processing service...")
    try:
        # Import and test the alert trigger service directly
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.news_alert_trigger import news_alert_trigger
        
        # Test with sample news item
        sample_news = {
            'id': 'test_123',
            'title': 'Fed Announces Interest Rate Decision - Breaking News',
            'content': 'The Federal Reserve has announced a major interest rate decision that will impact EUR/USD and USD/JPY.',
            'source': 'Reuters',
            'url': 'https://example.com',
            'timestamp': '2025-08-20T10:00:00Z'
        }
        
        # Test high impact detection
        is_high_impact = news_alert_trigger.is_high_impact_news(sample_news)
        print(f"   High impact detection: {'✅ Yes' if is_high_impact else '❌ No'}")
        
        # Test currency pair extraction
        affected_pairs = news_alert_trigger.get_affected_currency_pairs(sample_news)
        print(f"   Affected currency pairs: {affected_pairs}")
        
        # Test AI analysis decision
        should_analyze = news_alert_trigger.should_analyze_with_ai(sample_news)
        print(f"   Should analyze with AI: {'✅ Yes' if should_analyze else '❌ No'}")
        
        print("✅ Alert processing service tests completed!")
        
    except Exception as e:
        print(f"❌ Error testing alert processing: {e}")
    
    # Test 3: Check user alert settings
    print("\n3. Testing user alert settings...")
    try:
        # Test with a sample user ID
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
                print(f"   Telegram alerts enabled: {'✅ Yes' if telegram_enabled else '❌ No'}")
                
                if telegram_enabled:
                    chat_id = settings.get('channels', {}).get('telegram', {}).get('chatId', '')
                    print(f"   Chat ID configured: {'✅ Yes' if chat_id else '❌ No'}")
                
                # Check alert preferences
                preferences = settings.get('preferences', {})
                live_news_enabled = preferences.get('alertTypes', {}).get('liveNews', True)
                print(f"   Live news alerts enabled: {'✅ Yes' if live_news_enabled else '❌ No'}")
                
                currency_pairs = preferences.get('currencyPairs', [])
                print(f"   Currency pairs: {currency_pairs}")
            else:
                print("   ⚠️ No user settings found")
        else:
            print(f"   ⚠️ User settings request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing user settings: {e}")
    
    print("\n" + "=" * 50)
    print("Integration test completed!")
    print("\n📱 Next steps:")
    print("1. Check your Telegram for any alerts")
    print("2. Monitor the backend logs for alert processing")
    print("3. Test with real breaking news events")

if __name__ == "__main__":
    test_news_alert_integration()
