#!/usr/bin/env python3
"""
Send a real high-impact news alert to the user
"""

import sys
import os
sys.path.append('backend')

from backend.services.news_alert_trigger import news_alert_trigger
from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
import asyncio
import requests

async def send_real_alert():
    """Send a real high-impact news alert to the user"""
    print("🚨 Sending Real High-Impact News Alert")
    print("=" * 50)
    
    try:
        # Get current news
        print("📰 Fetching latest news...")
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news", timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to get news: {response.status_code}")
            return False
        
        news_data = response.json()
        news_items = news_data.get('news', [])
        high_impact = [n for n in news_items if n.get('impact') == 'high']
        
        if not high_impact:
            print("ℹ️  No high-impact news found")
            return False
        
        # Get the first high-impact news item
        news_item = high_impact[0]
        print(f"📢 Selected news: {news_item.get('title', '')[:50]}...")
        
        # Check if it's forex high impact
        if not news_alert_trigger.is_forex_high_impact(news_item):
            print("ℹ️  News is not forex high impact")
            return False
        
        # User data
        user_data = {
            'user_id': '0E0xJnQpYzZb8YkfQfSiwKYc8Fz2',
            'chat_id': '8008493413',
            'settings': {
                'telegram_enabled': True,
                'live_news_alerts': True,
                'impact_levels': ['high', 'medium'],
                'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
                'alert_types': ['liveNews', 'economicCalendar'],
                'ai_analysis_enabled': True
            }
        }
        
        print("📱 Sending real alert...")
        print(f"   User ID: {user_data['user_id']}")
        print(f"   Chat ID: {user_data['chat_id']}")
        print(f"   News Title: {news_item.get('title', '')}")
        print(f"   News Source: {news_item.get('source', '')}")
        print(f"   News Impact: {news_item.get('impact', '')}")
        
        # Determine if AI analysis is needed
        needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
        print(f"   AI Analysis: {'Yes' if needs_ai_analysis else 'No'}")
        
        # Send the alert
        success = await news_alert_trigger._send_alert_to_user(user_data, news_item, needs_ai_analysis)
        
        if success:
            print("✅ Real alert sent successfully!")
        else:
            print("❌ Real alert failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error in send_real_alert: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(send_real_alert())
    if success:
        print("\n✅ Real alert test completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Real alert test failed")
        sys.exit(1)
