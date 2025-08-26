#!/usr/bin/env python3
"""
Simple script to check for alerts and send them to users
Can be called periodically via cron or external scheduler
"""

import sys
import os
sys.path.append('backend')

from backend.services.news_alert_trigger import news_alert_trigger
from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
import asyncio
import requests
from datetime import datetime

async def check_and_send_alerts():
    """Check for new alerts and send them to users"""
    print("🚨 Checking for new alerts...")
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
        
        # Get all connected users from mappings
        print("👥 Getting connected users from mappings...")
        firebase = FirebaseRealtimeStorage()
        
        # Get all telegram mappings
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
                
                # Get user settings
                user_settings = firebase.get_user_alert_settings(user_id)
                if not user_settings:
                    print(f"⚠️  No settings found for user {user_id}")
                    continue
                
                # Check if user has Telegram enabled (handle both old and new settings structure)
                telegram_enabled = False
                
                # New structure: telegram_enabled (direct)
                if user_settings.get('telegram_enabled', False):
                    telegram_enabled = True
                # Old structure: channels.telegram.enabled
                elif user_settings.get('channels', {}).get('telegram', {}).get('enabled', False):
                    telegram_enabled = True
                
                if telegram_enabled:
                    connected_users.append({
                        'user_id': user_id,
                        'chat_id': chat_id,
                        'settings': user_settings
                    })
                    print(f"   ✅ Found connected user: {user_id} -> {chat_id}")
                else:
                    print(f"   ⚠️  User {user_id} has Telegram disabled")
        
        print(f"✅ Found {len(connected_users)} connected users")
        
        if not connected_users:
            print("ℹ️  No connected users found")
            return True
        
        # Process news for alerts
        alerts_sent = 0
        for news_item in high_impact[:3]:  # Process first 3 high-impact items
            news_id = str(news_item.get('id', ''))
            
            # Check if forex high impact
            if not news_alert_trigger.is_forex_high_impact(news_item):
                continue
            
            print(f"📢 Processing news: {news_item.get('title', '')[:50]}...")
            
            # Send to all connected users
            for user in connected_users:
                try:
                    # Create user data with correct structure
                    user_data = {
                        'user_id': user['user_id'],
                        'chat_id': user['chat_id'],
                        'settings': user['settings']
                    }
                    
                    # Determine if AI analysis is needed
                    needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
                    
                    # Send the alert
                    success = await news_alert_trigger._send_alert_to_user(user_data, news_item, needs_ai_analysis)
                    
                    if success:
                        alerts_sent += 1
                        print(f"   ✅ Alert sent to user {user['user_id']}")
                    else:
                        print(f"   ❌ Alert failed for user {user['user_id']}")
                    
                except Exception as e:
                    print(f"   ❌ Error sending alert to user {user['user_id']}: {e}")
            
            # Wait a bit between news items
            await asyncio.sleep(1)
        
        print(f"🎉 Sent {alerts_sent} alerts successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in check_and_send_alerts: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(check_and_send_alerts())
    if success:
        print("\n✅ Alert check completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Alert check failed")
        sys.exit(1)
