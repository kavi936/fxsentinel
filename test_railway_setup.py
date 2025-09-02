#!/usr/bin/env python3
"""
Test Railway Setup for FXSentinel
Verifies that the background worker can connect to the main app
"""

import os
import requests
import json
from datetime import datetime

def test_railway_connectivity():
    """Test connectivity between Railway services"""
    print("🧪 Testing FXSentinel Railway Setup")
    print("=" * 50)
    
    # Get API base URL from environment
    api_base_url = os.getenv('API_BASE_URL')
    if not api_base_url:
        print("❌ API_BASE_URL not set in environment")
        print("   Please set this to your main app URL")
        return False
    
    print(f"🌐 Testing connection to: {api_base_url}")
    
    # Test 1: Health Check
    print("\n1️⃣ Testing main app health...")
    try:
        response = requests.get(f"{api_base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Main app is healthy")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'Unknown')}")
        else:
            print(f"❌ Main app health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to main app: {e}")
        return False
    
    # Test 2: News API
    print("\n2️⃣ Testing news API...")
    try:
        response = requests.get(f"{api_base_url}/api/news", timeout=10)
        if response.status_code == 200:
            news_data = response.json()
            news_count = len(news_data.get('news', []))
            print(f"✅ News API working - {news_count} articles available")
        else:
            print(f"❌ News API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ News API error: {e}")
        return False
    
    # Test 3: Economic Calendar API
    print("\n3️⃣ Testing economic calendar API...")
    try:
        response = requests.get(f"{api_base_url}/api/economic-calendar", timeout=10)
        if response.status_code == 200:
            calendar_data = response.json()
            events_count = len(calendar_data.get('events', []))
            print(f"✅ Economic calendar API working - {events_count} events available")
        else:
            print(f"❌ Economic calendar API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Economic calendar API error: {e}")
        return False
    
    # Test 4: Alert Trigger API
    print("\n4️⃣ Testing alert trigger API...")
    try:
        test_data = {
            'user_id': 'test_user_railway',
            'chat_id': '8008493413'  # Your chat ID
        }
        response = requests.post(
            f"{api_base_url}/api/trigger-alerts",
            json=test_data,
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ Alert trigger API working")
            print(f"   Alerts processed: {result.get('alerts_processed', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
        else:
            print(f"❌ Alert trigger API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Alert trigger API error: {e}")
        return False
    
    # Test 5: Environment Variables
    print("\n5️⃣ Checking environment variables...")
    required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   These need to be set in Railway for full functionality")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    if not missing_vars:
        print("🎉 All tests passed! Your Railway setup is working correctly.")
        print("\n✅ Your background worker should now be able to:")
        print("   - Connect to the main app")
        print("   - Fetch news and economic calendar data")
        print("   - Process alerts for all users")
        print("   - Send Telegram notifications")
        
        print("\n🚀 Next steps:")
        print("   1. Deploy the background worker to Railway")
        print("   2. Set API_BASE_URL to point to your main app")
        print("   3. Monitor Railway logs for worker activity")
        print("   4. Test with real alerts")
        
    else:
        print("⚠️  Setup partially working but missing some configuration.")
        print("   Please set the missing environment variables in Railway.")
    
    return True

def test_background_worker_import():
    """Test if background worker can be imported correctly"""
    print("\n🔧 Testing background worker import...")
    try:
        import sys
        sys.path.append('backend')
        
        from services.background_alert_trigger import NewsAlertTrigger
        print("✅ NewsAlertTrigger imported successfully")
        
        from services.background_alert_worker import BackgroundAlertWorker
        print("✅ BackgroundAlertWorker imported successfully")
        
        # Test worker initialization
        worker = BackgroundAlertWorker()
        print("✅ BackgroundAlertWorker initialized successfully")
        
        # Check API base URL
        api_url = worker.api_base_url
        print(f"   API Base URL: {api_url}")
        
        if 'localhost' in api_url:
            print("⚠️  Warning: Still using localhost URL")
            print("   Make sure to set API_BASE_URL environment variable")
        else:
            print("✅ Using production API URL")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FXSentinel Railway Setup Test")
    print("This script tests your Railway deployment configuration")
    print()
    
    # Test 1: Service connectivity
    connectivity_ok = test_railway_connectivity()
    
    # Test 2: Background worker import
    worker_ok = test_background_worker_import()
    
    print("\n" + "=" * 50)
    if connectivity_ok and worker_ok:
        print("🎉 All tests passed! Ready for Railway deployment.")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    print("=" * 50)
