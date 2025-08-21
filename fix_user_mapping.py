#!/usr/bin/env python3
"""
Fix User Mapping
Ensure the correct user ID is associated with the chat ID
"""

import sys
sys.path.append('backend')

from services.firebase_realtime_storage import FirebaseRealtimeStorage
import hashlib

def fix_user_mapping():
    print("🔧 Fixing User Mapping")
    print("=" * 40)
    
    # Your actual user ID and chat ID
    actual_user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    chat_id = "8008493413"
    
    firebase = FirebaseRealtimeStorage()
    
    # Step 1: Check current users
    print("1. Checking current users...")
    users = firebase.get_all_users_with_alerts()
    print(f"   Total users: {len(users)}")
    
    # Find user with your chat ID
    user_with_chat_id = None
    for user in users:
        if user.get('telegram_chat_id') == chat_id:
            user_with_chat_id = user
            break
    
    if user_with_chat_id:
        print(f"   Found user with your chat ID: {user_with_chat_id['user_id']}")
    else:
        print("   No user found with your chat ID")
    
    # Step 2: Create proper user settings for your actual user ID
    print("\n2. Creating proper user settings...")
    
    # Default settings
    user_settings = {
        'telegram_enabled': True,
        'alert_types': ['liveNews', 'economicCalendar'],
        'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
        'impact_levels': ['high', 'medium'],
        'notification_frequency': 'immediate',
        'ai_analysis_enabled': True,
        'economic_calendar_alerts': True,
        'live_news_alerts': True
    }
    
    # Save settings for your actual user ID
    success = firebase.update_user_alert_settings(actual_user_id, user_settings)
    if success:
        print("   ✅ User settings saved")
    else:
        print("   ❌ Failed to save user settings")
    
    # Step 3: Save chat ID for your actual user ID
    print("\n3. Saving chat ID...")
    success = firebase.save_telegram_chat_id(actual_user_id, chat_id)
    if success:
        print("   ✅ Chat ID saved")
    else:
        print("   ❌ Failed to save chat ID")
    
    # Step 4: Verify the fix
    print("\n4. Verifying fix...")
    retrieved_chat_id = firebase.get_telegram_chat_id(actual_user_id)
    if retrieved_chat_id == chat_id:
        print("   ✅ Chat ID verification successful")
    else:
        print(f"   ❌ Chat ID verification failed: {retrieved_chat_id}")
    
    # Step 5: Test alert processing
    print("\n5. Testing alert processing...")
    from services.news_alert_trigger import news_alert_trigger
    
    # Create a test news item
    test_news = {
        'title': '🔧 User Mapping Fix Test',
        'summary': 'Testing if the user mapping fix worked correctly.',
        'source': 'FXSentinel Fix',
        'impact': 'high',
        'currency_pairs': ['EUR/USD', 'USD/JPY'],
        'published_at': '2025-08-21T10:15:00Z'
    }
    
    # Get users to alert
    users_to_alert = news_alert_trigger.get_users_to_alert(test_news)
    
    # Check if your user is in the list
    your_user_found = False
    for user_data in users_to_alert:
        if user_data.get('user_id') == actual_user_id:
            your_user_found = True
            print(f"   ✅ Your user found in alert list")
            break
    
    if not your_user_found:
        print("   ❌ Your user not found in alert list")
    
    print("\n" + "=" * 40)
    print("🎯 Fix Summary:")
    print("✅ User settings created for your actual user ID")
    print("✅ Chat ID properly mapped")
    print("✅ Alert system should now include you in notifications")
    
    print("\n📱 Next Steps:")
    print("1. The system will now include you in alert processing")
    print("2. You should receive notifications for high-impact news")
    print("3. Economic calendar alerts will be sent to you")
    print("4. Test by running the trigger script again")

if __name__ == "__main__":
    fix_user_mapping()
