#!/usr/bin/env python3
"""
Detailed test script to debug the alert processing pipeline
This will help identify exactly where the issue is occurring
"""

import sys
import os
sys.path.append('backend')

from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
from backend.services.news_alert_trigger import news_alert_trigger
import asyncio
import requests
from datetime import datetime

def test_alert_processing_detailed():
    """Test the alert processing pipeline step by step"""
    print("🔍 Detailed Alert Processing Test")
    print("=" * 60)
    
    try:
        firebase = FirebaseRealtimeStorage()
        
        # 1. Test news item
        test_news_item = {
            'id': 'test_news_detailed_123',
            'title': 'Federal Reserve Announces Interest Rate Decision',
            'summary': 'The Federal Reserve has announced a significant interest rate change that will impact forex markets.',
            'content': 'Breaking news: The Federal Reserve has made a major monetary policy decision affecting USD pairs.',
            'source': 'Reuters',
            'impact': 'high',
            'published_at': datetime.now().isoformat(),
            'url': 'https://example.com/news/fed-rate-decision',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"📰 Test News Item: {test_news_item['title']}")
        print(f"🏷️  Impact Level: {test_news_item['impact']}")
        
        # 2. Check telegram mappings
        print(f"\n1️⃣ Checking Telegram Mappings...")
        mapping_path = "telegram_mappings"
        all_mappings = firebase._make_request('GET', mapping_path)
        
        if not all_mappings or not isinstance(all_mappings, dict):
            print("   ❌ No telegram mappings found")
            return False
        
        print(f"   📊 Found {len(all_mappings)} telegram mappings")
        
        # 3. Process each mapping step by step
        print(f"\n2️⃣ Processing Each Mapping Step by Step...")
        valid_users = 0
        
        for chat_id, mapping_data in all_mappings.items():
            if isinstance(mapping_data, dict) and 'user_id' in mapping_data:
                user_id = mapping_data['user_id']
                
                print(f"\n   👤 Processing User: {user_id}")
                print(f"   💬 Chat ID: {chat_id}")
                
                # Get user settings
                user_settings = firebase.get_user_alert_settings(user_id)
                if not user_settings:
                    print(f"   ❌ No user settings found")
                    continue
                
                print(f"   ✅ User settings found")
                
                # Check telegram enabled
                telegram_enabled = (
                    user_settings.get('telegram_enabled', False) or
                    user_settings.get('telegram', False) or
                    user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                )
                
                print(f"   📱 Telegram enabled: {telegram_enabled}")
                
                if not telegram_enabled:
                    print(f"   ❌ Telegram disabled - skipping user")
                    continue
                
                # Check liveNews alerts enabled
                live_news_enabled = False
                
                # Check direct alert_types structure
                alert_types = user_settings.get('alert_types', {})
                if isinstance(alert_types, dict):
                    live_news_enabled = alert_types.get('liveNews', True)
                    print(f"   🚨 Alert types (dict): {alert_types}")
                elif isinstance(alert_types, list):
                    live_news_enabled = 'liveNews' in alert_types or 'news' in alert_types
                    print(f"   🚨 Alert types (list): {alert_types}")
                else:
                    live_news_enabled = True
                    print(f"   🚨 Alert types: {alert_types} (defaulting to True)")
                
                # Also check preferences structure
                preferences = user_settings.get('preferences', {})
                if preferences and 'alertTypes' in preferences:
                    pref_alert_types = preferences['alertTypes']
                    if isinstance(pref_alert_types, dict):
                        live_news_enabled = pref_alert_types.get('liveNews', live_news_enabled)
                        print(f"   🎯 Preferences alert types: {pref_alert_types}")
                
                print(f"   📢 Live news enabled: {live_news_enabled}")
                
                if not live_news_enabled:
                    print(f"   ❌ Live news disabled - skipping user")
                    continue
                
                # Test the actual alert sending
                print(f"   🧪 Testing alert sending...")
                
                user_data = {
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'settings': user_settings
                }
                
                # Determine if AI analysis is needed
                needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(test_news_item)
                print(f"   🤖 AI analysis needed: {needs_ai_analysis}")
                
                # Try to send the alert
                try:
                    success = asyncio.run(news_alert_trigger._send_alert_to_user(user_data, test_news_item, needs_ai_analysis))
                    print(f"   📤 Alert send result: {success}")
                    
                    if success:
                        valid_users += 1
                        print(f"   ✅ User {user_id} can receive alerts")
                    else:
                        print(f"   ❌ User {user_id} failed to receive alert")
                        
                except Exception as e:
                    print(f"   ❌ Error sending alert to user {user_id}: {e}")
        
        # 4. Summary
        print(f"\n3️⃣ Summary:")
        print(f"   ✅ Valid users who can receive alerts: {valid_users}")
        print(f"   📊 Total mappings processed: {len(all_mappings)}")
        
        if valid_users > 0:
            print(f"\n🎉 SUCCESS: Found {valid_users} users who can receive alerts!")
            return True
        else:
            print(f"\n⚠️  WARNING: No users can receive alerts")
            return False
            
    except Exception as e:
        print(f"❌ Error during detailed test: {e}")
        return False

if __name__ == "__main__":
    success = test_alert_processing_detailed()
    if success:
        print("\n🎯 Detailed test: Users can receive alerts")
    else:
        print("\n🔧 Detailed test: Issues found with alert processing")
