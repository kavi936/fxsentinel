#!/usr/bin/env python3
"""
Test script that simulates the exact logic from the main app's alert trigger endpoint
"""

import sys
import os
sys.path.append('backend')

from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
from backend.services.news_alert_trigger import news_alert_trigger
import asyncio
from datetime import datetime

def test_main_app_logic():
    """Test the exact logic from the main app's alert trigger endpoint"""
    print("🧪 Testing Main App Alert Logic")
    print("=" * 50)
    
    # Test news item
    test_news_item = {
        'id': 'test_news_main_app_123',
        'title': 'Federal Reserve Announces Interest Rate Decision',
        'summary': 'The Federal Reserve has announced a significant interest rate change that will impact forex markets.',
        'content': 'Breaking news: The Federal Reserve has made a major monetary policy decision affecting USD pairs.',
        'source': 'Reuters',
        'impact': 'high',
        'published_at': datetime.now().isoformat(),
        'url': 'https://example.com/news/fed-rate-decision',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Simulate the main app logic
        print("1️⃣ Getting telegram mappings...")
        firebase = FirebaseRealtimeStorage()
        mapping_path = "telegram_mappings"
        all_mappings = firebase._make_request('GET', mapping_path)
        
        if not all_mappings or not isinstance(all_mappings, dict):
            print("   ❌ No telegram mappings found")
            return False
        
        print(f"   📊 Found {len(all_mappings)} telegram mappings")
        
        # Process each mapping (exact logic from main app)
        alerts_sent = 0
        for chat_id, mapping_data in all_mappings.items():
            if isinstance(mapping_data, dict) and 'user_id' in mapping_data:
                user_id = mapping_data['user_id']
                
                print(f"\n   👤 Processing user: {user_id}")
                print(f"   💬 Chat ID: {chat_id}")
                
                # Skip test users with invalid chat IDs (only if they're actually test users)
                if chat_id == '123456789' and user_id.startswith('test_'):
                    print(f"   ⏭️  Skipping test user")
                    continue
                
                # Get user settings
                user_settings = firebase.get_user_alert_settings(user_id)
                if not user_settings:
                    print(f"   ❌ No user settings found")
                    continue
                
                print(f"   ✅ User settings found")
                
                # Check if user has Telegram enabled (handle multiple settings structures)
                telegram_enabled = (
                    user_settings.get('telegram_enabled', False) or  # Old structure
                    user_settings.get('telegram', False) or  # Direct telegram setting
                    user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)  # New structure
                )
                
                print(f"   📱 Telegram enabled: {telegram_enabled}")
                
                if not telegram_enabled:
                    print(f"   ❌ Telegram disabled - skipping")
                    continue
                
                # Check if user has liveNews alerts enabled (handle multiple settings structures)
                live_news_enabled = False
                
                # Check direct alert_types structure
                alert_types = user_settings.get('alert_types', {})
                if isinstance(alert_types, dict):
                    live_news_enabled = alert_types.get('liveNews', True)  # Default to True
                    print(f"   🚨 Alert types (dict): {alert_types}")
                elif isinstance(alert_types, list):
                    live_news_enabled = 'liveNews' in alert_types or 'news' in alert_types
                    print(f"   🚨 Alert types (list): {alert_types}")
                else:
                    live_news_enabled = True  # Default to True if no alert_types
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
                    print(f"   ❌ Live news disabled - skipping")
                    continue
                
                # Create user data (exact structure from main app)
                user_data = {
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'settings': user_settings
                }
                
                print(f"   🧪 Testing alert sending...")
                
                # Determine if AI analysis is needed
                needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(test_news_item)
                print(f"   🤖 AI analysis needed: {needs_ai_analysis}")
                
                # Send the alert using async handling (exact logic from main app)
                try:
                    import asyncio
                    # Use asyncio.run to properly handle the async function
                    success = asyncio.run(news_alert_trigger._send_alert_to_user(user_data, test_news_item, needs_ai_analysis))
                    
                    print(f"   📤 Alert send result: {success}")
                    
                    if success:
                        alerts_sent += 1
                        print(f"   ✅ Successfully sent alert to user {user_id}")
                    else:
                        print(f"   ❌ Failed to send alert to user {user_id}")
                        
                except Exception as e:
                    print(f"   ❌ Error sending alert to user {user_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        print(f"\n📋 Summary:")
        print(f"   📨 Total alerts sent: {alerts_sent}")
        
        if alerts_sent > 0:
            print(f"   🎉 SUCCESS: Main app logic is working!")
            return True
        else:
            print(f"   ⚠️  WARNING: No alerts sent - issue found in main app logic")
            return False
            
    except Exception as e:
        print(f"❌ Error in main app logic test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_main_app_logic()
    if success:
        print("\n🎯 Main app logic test: PASSED")
    else:
        print("\n🔧 Main app logic test: FAILED")
