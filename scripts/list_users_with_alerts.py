#!/usr/bin/env python3
"""
List all users with alerts enabled
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage

def main():
    print("=" * 80)
    print("USERS WITH ALERTS ENABLED")
    print("=" * 80)
    
    firebase = FirebaseRealtimeStorage()
    users = firebase.get_all_users_with_alerts()
    
    if not users:
        print("No users found with alerts enabled")
        return
    
    print(f"\nTotal users: {len(users)}\n")
    
    for i, user_data in enumerate(users, 1):
        user_id = user_data.get('user_id', 'Unknown')
        chat_id = user_data.get('telegram_chat_id', 'Not set')
        settings = user_data.get('settings', {})
        
        # Get preferences
        preferences = settings.get('preferences', {})
        alert_types = preferences.get('alertTypes', {})
        
        # Get channels
        channels = settings.get('channels', {})
        telegram_enabled = channels.get('telegram', {}).get('enabled', False)
        
        print(f"{i}. User ID: {user_id}")
        print(f"   Telegram Chat ID: {chat_id}")
        print(f"   Telegram Enabled: {telegram_enabled}")
        print(f"   Alert Types:")
        print(f"     - Live News: {alert_types.get('liveNews', False)}")
        print(f"     - Pre-News: {alert_types.get('preNews', False)}")
        print(f"     - Post-News: {alert_types.get('postNews', False)}")
        print(f"     - Technical Analysis: {alert_types.get('technicalAnalysis', False)}")
        
        # Get currency pairs
        currency_pairs = preferences.get('currencyPairs', [])
        if currency_pairs:
            print(f"   Currency Pairs: {', '.join(currency_pairs[:5])}")
            if len(currency_pairs) > 5:
                print(f"     ... and {len(currency_pairs) - 5} more")
        
        print()
    
    print("=" * 80)

if __name__ == '__main__':
    main()

