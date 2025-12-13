#!/usr/bin/env python3
"""
Check user's Telegram connection and settings
"""

import requests
import json
from datetime import datetime

def check_user_connection():
    """Check user's Telegram connection and settings"""
    print("👤 Checking User Connection and Settings")
    print("=" * 50)
    print(f"📅 Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    # Check if we can access user data through different endpoints
    endpoints_to_check = [
        "/api/user/profile",
        "/api/user/settings", 
        "/api/alerts/settings",
        "/api/telegram/status",
        "/api/subscription/status"
    ]
    
    print("🔍 **Checking Available User Endpoints:**")
    print("=" * 40)
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(f"{main_app_url}{endpoint}", timeout=10)
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"      📊 Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    print()
    
    # Try to get user info through the dashboard data
    print("📊 **Checking Dashboard Data for User Info:**")
    print("=" * 45)
    
    try:
        response = requests.get(f"{main_app_url}/api/dashboard-data", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ Dashboard data accessible")
            
            # Look for user-related information
            user_info = data.get('user', {})
            if user_info:
                print(f"👤 User info found: {list(user_info.keys())}")
                print(f"📱 Telegram enabled: {user_info.get('telegram_enabled', 'unknown')}")
                print(f"🔔 Alerts enabled: {user_info.get('alerts_enabled', 'unknown')}")
            else:
                print("❌ No user info in dashboard data")
            
            # Check for alert settings
            alert_settings = data.get('alert_settings', {})
            if alert_settings:
                print(f"🔔 Alert settings found: {list(alert_settings.keys())}")
            else:
                print("❌ No alert settings in dashboard data")
                
        else:
            print(f"❌ Dashboard data failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting dashboard data: {e}")
    
    print()
    
    # Check if there's a way to test with a specific user ID
    print("🧪 **Testing Alert with Known User ID:**")
    print("=" * 40)
    
    # Try to trigger an alert and see what happens
    test_news = {
        'title': 'Test Alert - Federal Reserve Interest Rate Decision',
        'summary': 'Test alert to check user connection and settings',
        'source': 'Test Source',
        'published_at': datetime.now().isoformat(),
        'impact': 'high'
    }
    
    alert_data = {
        'type': 'news',
        'data': test_news
    }
    
    try:
        response = requests.post(
            f"{main_app_url}/api/alerts/trigger",
            json=alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Alert trigger successful")
            print(f"📊 Alerts sent: {result.get('alerts_sent', 0)}")
            print(f"📋 Message: {result.get('message', '')}")
            
            if result.get('alerts_sent', 0) == 0:
                print()
                print("❌ **DIAGNOSIS:** 0 alerts sent")
                print("🔍 **This means:**")
                print("   1. Either no users are connected to Telegram")
                print("   2. Or connected users have alerts disabled")
                print("   3. Or there are subscription issues")
                print()
                print("💡 **SOLUTION:**")
                print("   - Check if you're properly connected to the Telegram bot")
                print("   - Verify your alert settings in the dashboard")
                print("   - Ensure your subscription is active")
                print("   - Try reconnecting to the Telegram bot")
            else:
                print(f"✅ **SUCCESS:** {result.get('alerts_sent', 0)} alerts sent!")
                
        else:
            print(f"❌ Alert trigger failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing alert: {e}")

def check_telegram_bot_status():
    """Check if the Telegram bot is working"""
    print()
    print("🤖 **Checking Telegram Bot Status:**")
    print("=" * 35)
    
    # Try to get bot info (this might not work without proper auth)
    try:
        # This is a generic check - the actual bot token would be needed
        print("📱 Telegram bot status check:")
        print("   - Bot should be running and accessible")
        print("   - Users should be able to connect via /start command")
        print("   - Bot should respond to commands")
        print()
        print("🔍 **To verify your Telegram connection:**")
        print("   1. Open Telegram and find the FXSentinel bot")
        print("   2. Send /start command")
        print("   3. Check if you receive a confirmation")
        print("   4. Verify your alert settings in the bot")
        
    except Exception as e:
        print(f"❌ Error checking bot status: {e}")

if __name__ == "__main__":
    check_user_connection()
    check_telegram_bot_status()
