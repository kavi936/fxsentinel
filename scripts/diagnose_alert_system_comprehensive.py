#!/usr/bin/env python3
"""
Comprehensive Alert System Diagnostic
Tests all components to identify why alerts aren't being sent
"""

import sys
import os
import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_backend_connection():
    """Test if backend is accessible"""
    print_section("1. BACKEND CONNECTION TEST")
    try:
        response = requests.get('http://localhost:5001/api/hello', timeout=5)
        if response.status_code == 200:
            print("✅ Backend is accessible")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is NOT accessible - connection refused")
        print("   Make sure backend is running on port 5001")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False

def test_worker_status():
    """Check if background worker is running"""
    print_section("2. WORKER STATUS CHECK")
    try:
        from services.background_alert_worker import get_background_worker
        worker = get_background_worker()
        status = worker.get_status()
        
        print(f"Worker Running: {status.get('running', False)}")
        print(f"Thread Alive: {status.get('thread_alive', False)}")
        print(f"Last Check: {status.get('last_check', 'Never')}")
        print(f"Check Interval: {status.get('check_interval', 'Unknown')}s")
        
        if not status.get('running', False):
            print("⚠️  Worker is NOT running - alerts won't be checked")
            return False
        else:
            print("✅ Worker is running")
            return True
            
    except Exception as e:
        print(f"❌ Error checking worker status: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_firebase_connection():
    """Test Firebase connection"""
    print_section("3. FIREBASE CONNECTION TEST")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        if firebase.test_connection():
            print("✅ Firebase connection successful")
            return True
        else:
            print("❌ Firebase connection failed")
            return False
    except Exception as e:
        print(f"❌ Error testing Firebase: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_settings(user_id: str = None):
    """Check user alert settings"""
    print_section("4. USER ALERT SETTINGS CHECK")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        if not user_id:
            # Get all users
            all_users = firebase.get_all_users_with_alerts()
            print(f"Found {len(all_users)} users with alert settings")
            
            if not all_users:
                print("❌ No users found with alert settings")
                return False
            
            # Check first user
            user = all_users[0]
            user_id = user.get('user_id')
            print(f"\nChecking first user: {user_id}")
        else:
            settings = firebase.get_user_alert_settings(user_id)
            if not settings:
                print(f"❌ No settings found for user {user_id}")
                return False
            user = {'user_id': user_id, 'settings': settings}
        
        settings = user.get('settings', {})
        print(f"\nUser ID: {user.get('user_id')}")
        print(f"Settings structure: {list(settings.keys())}")
        
        # Check Telegram enabled
        telegram_enabled = (
            settings.get('telegram_enabled', False) or
            settings.get('telegram', False) or
            settings.get('channels', {}).get('telegram', {}).get('enabled', False)
        )
        print(f"Telegram Enabled: {telegram_enabled}")
        
        if not telegram_enabled:
            print("❌ Telegram is NOT enabled for this user")
        
        # Check Telegram chat ID
        chat_id = user.get('telegram_chat_id') or firebase.get_telegram_chat_id(user.get('user_id'))
        print(f"Telegram Chat ID: {chat_id if chat_id else 'NOT SET'}")
        
        if not chat_id:
            print("❌ Telegram chat ID is NOT set - alerts cannot be sent")
            return False
        
        # Check alert types
        alert_types = settings.get('alert_types', {})
        preferences = settings.get('preferences', {})
        pref_alert_types = preferences.get('alertTypes', {})
        
        live_news_enabled = (
            alert_types.get('liveNews', True) if isinstance(alert_types, dict) else True
        ) or (
            pref_alert_types.get('liveNews', True) if isinstance(pref_alert_types, dict) else True
        )
        
        print(f"Live News Alerts Enabled: {live_news_enabled}")
        
        if not live_news_enabled:
            print("⚠️  Live news alerts are disabled")
        
        # Check impact levels
        impact_levels = preferences.get('impactLevels', {})
        high_enabled = impact_levels.get('high', True)
        print(f"High Impact Alerts Enabled: {high_enabled}")
        
        if not high_enabled:
            print("⚠️  High impact alerts are disabled")
        
        return telegram_enabled and chat_id and live_news_enabled
        
    except Exception as e:
        print(f"❌ Error checking user settings: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_availability():
    """Check if high-impact news is available"""
    print_section("5. NEWS AVAILABILITY CHECK")
    try:
        response = requests.get('http://localhost:5001/api/news', timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to get news: {response.status_code}")
            return False
        
        data = response.json()
        news_items = data.get('news', [])
        print(f"Total news items: {len(news_items)}")
        
        if not news_items:
            print("❌ No news items available")
            return False
        
        # Check for high-impact news
        from services.news_alert_trigger import news_alert_trigger
        
        high_impact = []
        for item in news_items:
            if news_alert_trigger.is_forex_high_impact(item):
                high_impact.append(item)
        
        print(f"High-impact forex news: {len(high_impact)}")
        
        if high_impact:
            print("\nSample high-impact news:")
            for i, item in enumerate(high_impact[:3], 1):
                print(f"  {i}. {item.get('title', 'No title')[:60]}...")
                print(f"     Source: {item.get('source')}, Impact: {item.get('impact')}")
        else:
            print("⚠️  No high-impact forex news found")
            print("   This is normal if there's no breaking forex news")
        
        return len(high_impact) > 0
        
    except Exception as e:
        print(f"❌ Error checking news: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deduplication():
    """Test deduplication system"""
    print_section("6. DEDUPLICATION SYSTEM CHECK")
    try:
        from services.persistent_alert_deduplication import get_persistent_deduplication
        dedup = get_persistent_deduplication()
        
        stats = dedup.get_stats()
        print(f"Total deduplication records: {stats.get('total_records', 0)}")
        print(f"Operations count: {stats.get('operations_count', 0)}")
        print(f"Duplicates prevented: {stats.get('duplicates_prevented', 0)}")
        print(f"Alert TTL: {stats.get('alert_ttl_hours', 24)} hours")
        
        # Test with a sample news item
        test_news = {
            'id': 'test_123',
            'title': 'Test News Item',
            'source': 'Test Source'
        }
        test_user_id = 'test_user_123'
        
        should_send = dedup.should_send_news_alert(test_news, test_user_id)
        print(f"\nTest deduplication check: {should_send}")
        
        if should_send:
            print("✅ Deduplication system is working (test item would be sent)")
        else:
            print("⚠️  Deduplication says test item is duplicate (expected for test)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking deduplication: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_bot():
    """Test Telegram bot connection"""
    print_section("7. TELEGRAM BOT CHECK")
    try:
        from services.alert_service import get_alert_service
        import asyncio
        
        alert_service = get_alert_service()
        
        # Check if bot is initialized
        alert_service._ensure_telegram_bot()
        
        if not alert_service.telegram_bot:
            print("❌ Telegram bot is NOT initialized")
            print("   Check TELEGRAM_BOT_TOKEN environment variable")
            return False
        
        print("✅ Telegram bot is initialized")
        
        # Try to get bot info
        async def test_bot():
            try:
                bot_info = await alert_service.telegram_bot.get_me()
                print(f"Bot Username: @{bot_info.username}")
                print(f"Bot ID: {bot_info.id}")
                return True
            except Exception as e:
                print(f"❌ Error getting bot info: {e}")
                return False
        
        result = asyncio.run(test_bot())
        return result
        
    except Exception as e:
        print(f"❌ Error checking Telegram bot: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alert_trigger_endpoint():
    """Test the alert trigger endpoint"""
    print_section("8. ALERT TRIGGER ENDPOINT TEST")
    try:
        # Create a test news item
        test_news = {
            'id': 'test_diagnostic_123',
            'title': 'Test Alert - Diagnostic Check',
            'source': 'Diagnostic',
            'impact': 'high',
            'summary': 'This is a test alert to verify the system is working',
            'url': 'https://example.com',
            'published_at': datetime.now().isoformat()
        }
        
        alert_data = {
            'type': 'news',
            'data': test_news
        }
        
        print("Sending test alert trigger...")
        response = requests.post(
            'http://localhost:5001/api/alerts/trigger',
            json=alert_data,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            alerts_sent = result.get('alerts_sent', 0)
            total_users = result.get('total_users', 0)
            
            print(f"✅ Alert trigger successful")
            print(f"   Alerts sent: {alerts_sent}")
            print(f"   Total users processed: {total_users}")
            
            if alerts_sent == 0:
                print("⚠️  No alerts were sent - check user settings and Telegram connection")
            
            return alerts_sent > 0
        else:
            print(f"❌ Alert trigger failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing alert trigger: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_subscription_validation():
    """Test subscription validation"""
    print_section("9. SUBSCRIPTION VALIDATION CHECK")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        all_users = firebase.get_all_users_with_alerts()
        if not all_users:
            print("No users to check")
            return True
        
        # Check subscription for first user
        user = all_users[0]
        user_id = user.get('user_id')
        
        # Import subscription cache
        try:
            from services.subscription_cache import SubscriptionCache
            cache = SubscriptionCache()
            
            # Check if user has valid subscription
            has_subscription = cache.has_valid_subscription(user_id)
            print(f"User {user_id} has valid subscription: {has_subscription}")
            
            if not has_subscription:
                print("⚠️  User does NOT have valid subscription - alerts may be blocked")
            
            return has_subscription
            
        except Exception as e:
            print(f"⚠️  Could not check subscription (may not be critical): {e}")
            return True  # Subscription check failure shouldn't block alerts entirely
        
    except Exception as e:
        print(f"❌ Error checking subscription: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_news_check():
    """Test if worker can detect news"""
    print_section("10. WORKER NEWS DETECTION TEST")
    try:
        from services.background_alert_worker import BackgroundAlertWorker
        worker = BackgroundAlertWorker()
        
        # Manually trigger news check
        print("Running worker news check...")
        worker._check_news_alerts()
        
        print("✅ Worker news check completed (check logs for details)")
        return True
        
    except Exception as e:
        print(f"❌ Error in worker news check: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 70)
    print("  COMPREHENSIVE ALERT SYSTEM DIAGNOSTIC")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    
    results = {}
    
    # Run all tests
    results['backend'] = test_backend_connection()
    results['worker'] = test_worker_status()
    results['firebase'] = test_firebase_connection()
    results['user_settings'] = test_user_settings()
    results['news'] = test_news_availability()
    results['deduplication'] = test_deduplication()
    results['telegram'] = test_telegram_bot()
    results['subscription'] = test_subscription_validation()
    results['alert_trigger'] = test_alert_trigger_endpoint()
    results['worker_check'] = test_worker_news_check()
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    # Identify likely causes
    print("\n" + "=" * 70)
    print("  LIKELY CAUSES")
    print("=" * 70)
    
    if not results['backend']:
        print("🔴 CRITICAL: Backend is not accessible")
        print("   → Start the backend server")
    
    if not results['worker']:
        print("🔴 CRITICAL: Worker is not running")
        print("   → Worker needs to be started to check for alerts")
    
    if not results['user_settings']:
        print("🔴 CRITICAL: User settings issue")
        print("   → Check Telegram is enabled and chat ID is set")
    
    if not results['telegram']:
        print("🔴 CRITICAL: Telegram bot not configured")
        print("   → Set TELEGRAM_BOT_TOKEN environment variable")
    
    if not results['news']:
        print("⚠️  WARNING: No high-impact news available")
        print("   → This is normal if there's no breaking forex news")
    
    if not results['alert_trigger']:
        print("🔴 CRITICAL: Alert trigger endpoint failed")
        print("   → Check endpoint logs for errors")
    
    if results['backend'] and results['worker'] and results['user_settings'] and results['telegram'] and not results['alert_trigger']:
        print("\n💡 DIAGNOSIS: All components are working, but alerts aren't being sent")
        print("   → Check subscription validation")
        print("   → Check deduplication (may be blocking all alerts)")
        print("   → Check alert processing logs")

if __name__ == "__main__":
    main()

