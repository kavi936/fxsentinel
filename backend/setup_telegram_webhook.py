#!/usr/bin/env python3
"""
Setup Telegram Webhook for Online Hosting
This script sets up the Telegram bot to use webhooks instead of polling
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_webhook():
    """Setup Telegram webhook for online hosting"""
    
    # Get bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    # Get your domain (you'll need to update this for your hosting)
    domain = os.getenv('DOMAIN_URL', 'https://fxsentinel.io')  # Update this to your actual domain
    
    # Webhook URL
    webhook_url = f"{domain}/api/telegram/webhook"
    
    print(f"🤖 Setting up Telegram webhook...")
    print(f"📱 Bot token: {bot_token[:10]}...")
    print(f"🌐 Webhook URL: {webhook_url}")
    
    try:
        # Set the webhook
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json={'url': webhook_url}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook setup successful!")
                print(f"📡 Webhook URL: {webhook_url}")
                
                # Check webhook info
                info_response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
                if info_response.status_code == 200:
                    info = info_response.json()
                    if info.get('ok'):
                        webhook_info = info.get('result', {})
                        print(f"📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
                        print(f"🔗 Webhook URL: {webhook_info.get('url', 'Not set')}")
                
                return True
            else:
                print(f"❌ Webhook setup failed: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up webhook: {e}")
        return False

def delete_webhook():
    """Delete the webhook (for testing)"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return False
    
    try:
        response = requests.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook deleted successfully!")
                return True
            else:
                print(f"❌ Failed to delete webhook: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")
        return False

def test_webhook():
    """Test if webhook is working"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                webhook_info = result.get('result', {})
                url = webhook_info.get('url', '')
                
                if url:
                    print("✅ Webhook is configured!")
                    print(f"🔗 URL: {url}")
                    print(f"📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
                    return True
                else:
                    print("❌ No webhook URL configured")
                    return False
            else:
                print(f"❌ Failed to get webhook info: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            setup_webhook()
        elif command == "delete":
            delete_webhook()
        elif command == "test":
            test_webhook()
        else:
            print("Usage: python3 setup_telegram_webhook.py [setup|delete|test]")
    else:
        print("🤖 Telegram Webhook Setup")
        print("=" * 40)
        print("Commands:")
        print("  setup  - Set up webhook for online hosting")
        print("  delete - Delete webhook (for testing)")
        print("  test   - Test webhook configuration")
        print()
        print("Example: python3 setup_telegram_webhook.py setup")
