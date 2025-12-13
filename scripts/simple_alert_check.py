#!/usr/bin/env python3
"""
Simplified alert check script that directly sends alerts to users
"""

import sys
import os
sys.path.append('backend')

from backend.services.news_alert_trigger import news_alert_trigger
from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
import asyncio
import requests
from datetime import datetime

async def simple_alert_check():
    """Simple alert checking that directly sends alerts"""
    print("🚨 Simple Alert Check Started")
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
            return True
        
        print(f"✅ Found {len(high_impact)} high-impact news items")
        
        # Get all telegram mappings
        print("👥 Getting connected users...")
        firebase = FirebaseRealtimeStorage()
        mapping_path = "telegram_mappings"
        all_mappings = firebase._make_request('GET', mapping_path)
        
        if not all_mappings or not isinstance(all_mappings, dict):
            print("❌ No telegram mappings found")
            return False
        
        # Process each mapping
        connected_users = []
        for chat_id, mapping_data in all_mappings.items():
            if isinstance(mapping_data, dict) and 'user_id' in mapping_data:
                user_id = mapping_data['user_id']
                
                # Skip test users with invalid chat IDs
                if chat_id == '123456789':
                    print(f"   ⚠️  Skipping test user with invalid chat_id: {chat_id}")
                    continue
                
                # Get user settings
                user_settings = firebase.get_user_alert_settings(user_id)
                if not user_settings:
                    print(f"⚠️  No settings found for user {user_id}")
                    continue
                
                # Check if user has Telegram enabled
                if user_settings.get('telegram_enabled', False):
                    connected_users.append({
                        'user_id': user_id,
                        'chat_id': chat_id,
                        'settings': user_settings
                    })
                    print(f"   ✅ Found connected user: {user_id} -> {chat_id}")
        
        print(f"✅ Found {len(connected_users)} connected users")
        
        if not connected_users:
            print("ℹ️  No connected users found")
            return True
        
        # Process news for alerts (only first 2 high-impact items)
        alerts_sent = 0
        for news_item in high_impact[:2]:
            # Check if forex high impact
            if not news_alert_trigger.is_forex_high_impact(news_item):
                continue
            
            print(f"📢 Processing news: {news_item.get('title', '')[:50]}...")
            
            # Send to all connected users
            for user in connected_users:
                try:
                    # Create user data with simplified structure
                    user_data = {
                        'user_id': user['user_id'],
                        'chat_id': user['chat_id'],
                        'settings': {
                            'telegram_enabled': True,
                            'live_news_alerts': True,
                            'impact_levels': ['high', 'medium'],
                            'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
                            'alert_types': ['liveNews', 'economicCalendar'],
                            'ai_analysis_enabled': True
                        }
                    }
                    
                    # Determine if AI analysis is needed
                    needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
                    
                    # Send the alert directly
                    success = await news_alert_trigger._send_alert_to_user(user_data, news_item, needs_ai_analysis)
                    
                    if success:
                        alerts_sent += 1
                        print(f"   ✅ Alert sent to user {user['user_id']}")
                    else:
                        print(f"   ❌ Alert failed for user {user['user_id']}")
                    
                except Exception as e:
                    print(f"   ❌ Error sending alert to user {user['user_id']}: {e}")
            
            # Wait a bit between news items
            await asyncio.sleep(2)
        
        print(f"🎉 Sent {alerts_sent} alerts successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in simple_alert_check: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_alert_check())
    if success:
        print("\n✅ Simple alert check completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Simple alert check failed")
        sys.exit(1)
