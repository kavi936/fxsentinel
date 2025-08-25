#!/usr/bin/env python3
"""
Fix Telegram Webhook for Railway Backend
This script helps find your Railway URL and fix the webhook configuration
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def find_railway_url():
    """Try to find your Railway URL"""
    
    # Common Railway URL patterns
    possible_urls = [
        "https://fxsentinel-backend.railway.app",
        "https://fxsentinel.railway.app", 
        "https://fxsentinel-backend.up.railway.app",
        "https://fxsentinel.up.railway.app"
    ]
    
    print("🔍 Searching for your Railway backend URL...")
    
    for url in possible_urls:
        try:
            print(f"Testing: {url}")
            response = requests.get(f"{url}/api/health", timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'healthy':
                    print(f"✅ Found working Railway URL: {url}")
                    return url
                else:
                    print(f"❌ URL responds but not healthy: {url}")
            else:
                print(f"❌ URL not responding: {url}")
                
        except Exception as e:
            print(f"❌ Error testing {url}: {e}")
    
    return None

def fix_webhook_for_railway(railway_url):
    """Fix webhook to point to Railway backend"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return False
    
    webhook_url = f"{railway_url}/api/telegram/webhook"
    
    print(f"\n🔧 Fixing webhook for Railway backend...")
    print(f"📱 Bot: @FXSentinelAlertsBot")
    print(f"🌐 Railway URL: {railway_url}")
    print(f"🔗 Webhook URL: {webhook_url}")
    
    try:
        # Step 1: Delete existing webhook
        print("\n1️⃣ Deleting existing webhook...")
        delete_response = requests.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")
        if delete_response.status_code == 200:
            print("✅ Existing webhook deleted")
        else:
            print("⚠️ Could not delete existing webhook")
        
        # Step 2: Set new webhook to Railway URL
        print("\n2️⃣ Setting new webhook to Railway...")
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
                print("✅ Webhook set to Railway successfully!")
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

def test_railway_webhook(railway_url):
    """Test if Railway webhook endpoint is working"""
    
    webhook_url = f"{railway_url}/api/telegram/webhook"
    
    # Simulate a Telegram update
    test_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": 1693000000,
            "text": "/start"
        }
    }
    
    try:
        print(f"\n🧪 Testing Railway webhook endpoint...")
        print(f"📡 URL: {webhook_url}")
        
        response = requests.post(
            webhook_url,
            json=test_update,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Railway webhook endpoint is working!")
            return True
        else:
            print("❌ Railway webhook endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Railway webhook: {e}")
        return False

def main():
    """Main function"""
    print("🚂 Railway Telegram Webhook Fix")
    print("=" * 50)
    
    # Step 1: Find Railway URL
    railway_url = find_railway_url()
    
    if not railway_url:
        print("\n❌ Could not find your Railway URL automatically.")
        print("Please provide your Railway URL manually:")
        railway_url = input("Enter your Railway URL (e.g., https://fxsentinel-backend.railway.app): ").strip()
        
        if not railway_url:
            print("❌ No Railway URL provided. Cannot continue.")
            return
    
    # Step 2: Test Railway health
    print(f"\n🔍 Testing Railway backend health...")
    try:
        response = requests.get(f"{railway_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Railway backend is healthy!")
        else:
            print(f"❌ Railway backend not healthy: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot reach Railway backend: {e}")
        return
    
    # Step 3: Fix webhook
    if fix_webhook_for_railway(railway_url):
        print("\n🎉 SUCCESS! Webhook is now pointing to Railway backend.")
        
        # Step 4: Test webhook
        if test_railway_webhook(railway_url):
            print("\n✅ Everything is working!")
            print("\n📋 Next steps:")
            print("1. Go to your bot: https://t.me/FXSentinelAlertsBot")
            print("2. Send /start - it should now respond!")
            print("3. All users can now use the bot through the dashboard")
        else:
            print("\n⚠️ Webhook is configured but endpoint needs testing")
    else:
        print("\n❌ Failed to fix webhook configuration.")

if __name__ == "__main__":
    main()
