#!/usr/bin/env python3
"""
Force send test alerts - bypasses deduplication to test alert delivery
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.alert_service import AlertService
from services.firebase_realtime_storage import FirebaseRealtimeStorage
from services.news_alert_trigger import news_alert_trigger
from services.persistent_news_cache import get_persistent_news_cache

async def force_send_test_alert():
    """Force send a test alert to all users, bypassing deduplication"""
    print("=" * 80)
    print("FORCE SENDING TEST ALERTS")
    print("=" * 80)
    
    # Initialize services
    firebase = FirebaseRealtimeStorage()
    alert_service = AlertService()
    news_cache = get_persistent_news_cache()
    
    # Get cached news
    print("\n1. Getting cached news...")
    cached_news = news_cache.load_news()
    if not cached_news:
        print("   ❌ No cached news found")
        return
    
    print(f"   ✅ Found {len(cached_news)} cached news items")
    
    # Get first high-impact news item
    print("\n2. Finding high-impact news...")
    high_impact_item = None
    for item in cached_news[:20]:  # Check top 20
        if news_alert_trigger.is_forex_high_impact(item):
            high_impact_item = item
            print(f"   ✅ Found: {item.get('title', 'Unknown')[:60]}...")
            break
    
    if not high_impact_item:
        print("   ❌ No high-impact news found in top 20 items")
        return
    
    # Get all users with alerts
    print("\n3. Getting users with alerts...")
    users = firebase.get_all_users_with_alerts()
    print(f"   ✅ Found {len(users)} users with alert settings")
    
    if not users:
        print("   ❌ No users found")
        return
    
    # Create test alert message
    print("\n4. Creating test alert...")
    alert_message = news_alert_trigger._create_alert_content(high_impact_item)
    # Prepend test prefix
    test_message = f"[TEST ALERT] This is a test alert to verify the alert system is working.\n\n{alert_message}"
    
    print(f"   ✅ Alert created: {high_impact_item.get('title', 'Unknown')[:60]}...")
    
    # Send to all users (bypassing deduplication)
    print("\n5. Sending test alerts to all users (bypassing deduplication)...")
    success_count = 0
    fail_count = 0
    
    for user_data in users:
        try:
            user_id = user_data.get('user_id')
            if not user_id:
                print(f"   ⚠️  User data missing user_id")
                fail_count += 1
                continue
            
            # Get user settings
            user_settings = user_data.get('settings', {})
            if not user_settings:
                print(f"   ⚠️  User {user_id}: No settings found")
                fail_count += 1
                continue
            
            # Get chat_id
            chat_id = None
            if user_data.get('telegram_chat_id'):
                chat_id = user_data['telegram_chat_id']
            elif user_settings.get('channels', {}).get('telegram', {}).get('chatId'):
                chat_id = user_settings['channels']['telegram']['chatId']
            elif user_settings.get('telegram_chat_id'):
                chat_id = user_settings['telegram_chat_id']
            
            if not chat_id:
                print(f"   ⚠️  User {user_id}: No chat_id found")
                fail_count += 1
                continue
            
            # Check if Telegram is enabled
            telegram_enabled = False
            if user_settings.get('channels', {}).get('telegram', {}).get('enabled'):
                telegram_enabled = True
            elif user_settings.get('telegram_enabled', False):
                telegram_enabled = True
            
            if not telegram_enabled:
                print(f"   ⚠️  User {user_id}: Telegram not enabled")
                fail_count += 1
                continue
            
            # Send alert directly (bypassing deduplication)
            print(f"   📤 Sending to user {user_id} (chat_id: {chat_id})...")
            success = await alert_service.send_telegram_alert(
                chat_id,
                test_message,
                user_id=user_id
            )
            
            if success:
                print(f"   ✅ Sent successfully to user {user_id}")
                success_count += 1
            else:
                print(f"   ❌ Failed to send to user {user_id}")
                fail_count += 1
                
        except Exception as e:
            print(f"   ❌ Error sending to user: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  ✅ Successfully sent: {success_count}")
    print(f"  ❌ Failed: {fail_count}")
    print(f"  📊 Total users: {len(users)}")
    
    if success_count > 0:
        print(f"\n✅ Alert system is working! Check your Telegram for the test alert.")
    else:
        print(f"\n❌ No alerts were sent. Check the errors above.")

if __name__ == '__main__':
    asyncio.run(force_send_test_alert())

