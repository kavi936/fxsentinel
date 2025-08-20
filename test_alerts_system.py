#!/usr/bin/env python3
"""
FXSentinel Alerts System Test Script
Tests all components of the alerts system to identify issues
"""

import os
import sys
import asyncio
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.append('backend')

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'FINNHUB_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'FIREBASE_PROJECT_ID',
        'FIREBASE_REALTIME_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"   ❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   💡 Add these to your .env file")
        return False
    else:
        print("   ✅ All required environment variables are set")
        return True

def test_backend_api_endpoints():
    """Test if backend API endpoints are responding"""
    print("\n🔍 Testing Backend API Endpoints...")
    
    base_url = "http://localhost:5001"
    endpoints = [
        "/api/telegram/setup",
        "/api/telegram/verify", 
        "/api/alerts/settings",
        "/api/alerts/history",
        "/api/alerts/test"
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 405]:  # 405 is OK for POST-only endpoints
                working_endpoints.append(endpoint)
            else:
                failed_endpoints.append(endpoint)
        except requests.exceptions.RequestException as e:
            failed_endpoints.append(f"{endpoint} (Connection failed: {e})")
    
    if working_endpoints:
        print(f"   ✅ Working endpoints: {', '.join(working_endpoints)}")
    
    if failed_endpoints:
        print(f"   ❌ Failed endpoints: {', '.join(failed_endpoints)}")
        return False
    
    return True

def test_telegram_setup_endpoint():
    """Test the Telegram setup endpoint specifically"""
    print("\n🔍 Testing Telegram Setup Endpoint...")
    
    try:
        response = requests.post(
            "http://localhost:5001/api/telegram/setup",
            json={"userId": "test_user_123"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("   ✅ Telegram setup endpoint working")
                print(f"   📱 Bot username: {data.get('botUsername', 'N/A')}")
                print(f"   🔗 Bot link: {data.get('botLink', 'N/A')}")
                return True
            else:
                print(f"   ❌ Telegram setup failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing Telegram setup: {e}")
        return False

def test_alert_service_import():
    """Test if alert service can be imported"""
    print("\n🔍 Testing Alert Service Import...")
    
    try:
        from backend.services.alert_service import AlertService
        alert_service = AlertService()
        print("   ✅ Alert service imported successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error importing alert service: {e}")
        return False

def test_firebase_connection():
    """Test Firebase Realtime Database connection"""
    print("\n🔍 Testing Firebase Connection...")
    
    try:
        from backend.services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        if firebase.test_connection():
            print("   ✅ Firebase Realtime Database connected")
            return True
        else:
            print("   ❌ Firebase connection failed")
            return False
    except Exception as e:
        print(f"   ❌ Error testing Firebase connection: {e}")
        return False

def test_alert_triggers():
    """Test alert triggers functionality"""
    print("\n🔍 Testing Alert Triggers...")
    
    try:
        from backend.services.alert_triggers import AlertTriggers
        alert_triggers = AlertTriggers()
        print("   ✅ Alert triggers imported successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error importing alert triggers: {e}")
        return False

def test_frontend_config():
    """Test frontend configuration"""
    print("\n🔍 Testing Frontend Configuration...")
    
    try:
        from src.config import config
        print(f"   ✅ Frontend config loaded")
        print(f"   🌐 API Base URL: {config.API_BASE_URL}")
        return True
    except Exception as e:
        print(f"   ❌ Error loading frontend config: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 FXSentinel Alerts System Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Backend API Endpoints", test_backend_api_endpoints),
        ("Telegram Setup Endpoint", test_telegram_setup_endpoint),
        ("Alert Service Import", test_alert_service_import),
        ("Firebase Connection", test_firebase_connection),
        ("Alert Triggers", test_alert_triggers),
        ("Frontend Config", test_frontend_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Alerts system should be working.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        
        if passed < 3:
            print("\n🔧 Quick Fixes:")
            print("1. Make sure backend server is running: python3 backend/app.py")
            print("2. Check your .env file has all required variables")
            print("3. Verify Firebase project is set up correctly")
            print("4. Ensure Telegram bot token is valid")

if __name__ == "__main__":
    main()
