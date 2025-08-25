#!/usr/bin/env python3
"""
Fix Telegram Webhook for All Users
This script ensures the Telegram bot webhook is properly configured for online hosting
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_webhook():
    """Fix Telegram webhook configuration"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return False
    
    # Your domain
    domain = "https://fxsentinel.io"
    webhook_url = f"{domain}/api/telegram/webhook"
    
    print("🔧 Fixing Telegram webhook configuration...")
    print(f"📱 Bot: @FXSentinelAlertsBot")
    print(f"🌐 Domain: {domain}")
    print(f"🔗 Webhook URL: {webhook_url}")
    
    try:
        # Step 1: Delete any existing webhook
        print("\n1️⃣ Deleting existing webhook...")
        delete_response = requests.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")
        if delete_response.status_code == 200:
            print("✅ Existing webhook deleted")
        else:
            print("⚠️ Could not delete existing webhook")
        
        # Step 2: Set new webhook
        print("\n2️⃣ Setting new webhook...")
        webhook_data = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query'],
            'drop_pending_updates': True
        }
        
        webhook_response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json=webhook_data
        )
        
        if webhook_response.status_code == 200:
            result = webhook_response.json()
            if result.get('ok'):
                print("✅ Webhook set successfully!")
            else:
                print(f"❌ Webhook setup failed: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {webhook_response.status_code}")
            return False
        
        # Step 3: Verify webhook
        print("\n3️⃣ Verifying webhook...")
        info_response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
        
        if info_response.status_code == 200:
            info = info_response.json()
            if info.get('ok'):
                webhook_info = info.get('result', {})
                url = webhook_info.get('url', '')
                
                if url == webhook_url:
                    print("✅ Webhook verified successfully!")
                    print(f"🔗 URL: {url}")
                    print(f"📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
                    return True
                else:
                    print(f"❌ Webhook URL mismatch: {url}")
                    return False
            else:
                print(f"❌ Failed to get webhook info: {info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {info_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing webhook: {e}")
        return False

def test_bot():
    """Test if bot is responding"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return False
    
    try:
        # Test bot info
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                print("✅ Bot is active and responding!")
                print(f"🤖 Name: {bot_info.get('first_name', 'Unknown')}")
                print(f"📱 Username: @{bot_info.get('username', 'Unknown')}")
                print(f"🆔 ID: {bot_info.get('id', 'Unknown')}")
                return True
            else:
                print(f"❌ Bot error: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        return False

def main():
    """Main function"""
    print("🤖 FXSentinel Telegram Bot Webhook Fix")
    print("=" * 50)
    
    # Test bot first
    print("\n🔍 Testing bot status...")
    if not test_bot():
        print("❌ Bot is not working properly")
        return
    
    # Fix webhook
    print("\n🔧 Fixing webhook configuration...")
    if fix_webhook():
        print("\n🎉 SUCCESS! Telegram bot webhook is now configured properly.")
        print("\n📋 Next steps:")
        print("1. Ensure your Flask app is running on Railway")
        print("2. Users can now click 'Connect Telegram Bot' in the dashboard")
        print("3. Bot will respond to /start commands")
        print("4. All users with valid subscriptions can use the bot")
    else:
        print("\n❌ FAILED! Could not fix webhook configuration.")
        print("Please check your domain and bot token.")

if __name__ == "__main__":
    main()
