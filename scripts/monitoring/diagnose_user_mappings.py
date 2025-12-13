#!/usr/bin/env python3
"""
Diagnostic script to check user mappings and settings
This will help identify why alerts are not being sent
"""

import sys
import os
sys.path.append('backend')

from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage

def diagnose_user_mappings():
    """Diagnose user mappings and settings"""
    print("🔍 Diagnosing User Mappings and Settings")
    print("=" * 60)
    
    try:
        firebase = FirebaseRealtimeStorage()
        
        # 1. Check telegram mappings
        print("\n1️⃣ Checking Telegram Mappings...")
        mapping_path = "telegram_mappings"
        all_mappings = firebase._make_request('GET', mapping_path)
        
        if not all_mappings or not isinstance(all_mappings, dict):
            print("   ❌ No telegram mappings found")
            return False
        
        print(f"   📊 Found {len(all_mappings)} telegram mappings")
        
        # 2. Check each mapping
        print("\n2️⃣ Analyzing Each Mapping...")
        valid_users = 0
        invalid_users = 0
        
        for chat_id, mapping_data in all_mappings.items():
            if isinstance(mapping_data, dict) and 'user_id' in mapping_data:
                user_id = mapping_data['user_id']
                
                print(f"\n   👤 User: {user_id}")
                print(f"   💬 Chat ID: {chat_id}")
                
                # Get user settings
                user_settings = firebase.get_user_alert_settings(user_id)
                if not user_settings:
                    print(f"   ❌ No user settings found")
                    invalid_users += 1
                    continue
                
                print(f"   ✅ User settings found")
                
                # Check telegram enabled status
                telegram_enabled = False
                telegram_structure = "none"
                
                # Check different telegram setting structures
                if user_settings.get('telegram_enabled', False):
                    telegram_enabled = True
                    telegram_structure = "telegram_enabled (direct)"
                elif user_settings.get('telegram', False):
                    telegram_enabled = True
                    telegram_structure = "telegram (direct)"
                elif user_settings.get('channels', {}).get('telegram', {}).get('enabled', False):
                    telegram_enabled = True
                    telegram_structure = "channels.telegram.enabled"
                
                print(f"   📱 Telegram enabled: {telegram_enabled}")
                print(f"   🏗️  Structure: {telegram_structure}")
                
                if telegram_enabled:
                    # Check alert types
                    alert_types = user_settings.get('alert_types', [])
                    print(f"   🚨 Alert types: {alert_types}")
                    
                    # Check if user has news alerts enabled
                    if 'liveNews' in alert_types or 'news' in alert_types or not alert_types:
                        print(f"   ✅ News alerts enabled")
                        valid_users += 1
                    else:
                        print(f"   ⚠️  News alerts not enabled")
                        invalid_users += 1
                else:
                    print(f"   ❌ Telegram disabled")
                    invalid_users += 1
            else:
                print(f"   ❌ Invalid mapping data for chat_id {chat_id}")
                invalid_users += 1
        
        # 3. Summary
        print(f"\n3️⃣ Summary:")
        print(f"   ✅ Valid users (can receive alerts): {valid_users}")
        print(f"   ❌ Invalid users (cannot receive alerts): {invalid_users}")
        print(f"   📊 Total mappings: {len(all_mappings)}")
        
        if valid_users == 0:
            print(f"\n⚠️  WARNING: No valid users found!")
            print(f"   This explains why 0 alerts are being sent.")
            print(f"   Possible issues:")
            print(f"   • Users have telegram disabled")
            print(f"   • Users don't have news alerts enabled")
            print(f"   • User settings structure is incorrect")
        else:
            print(f"\n✅ Found {valid_users} valid users who should receive alerts")
        
        return valid_users > 0
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        return False

if __name__ == "__main__":
    success = diagnose_user_mappings()
    if success:
        print("\n🎯 Diagnosis: Users are properly configured")
    else:
        print("\n🔧 Diagnosis: User configuration issues found")
