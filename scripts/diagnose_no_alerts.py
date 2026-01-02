#!/usr/bin/env python3
"""
Diagnose why no alerts are being sent
Checks: background worker, news availability, alert triggers, Firebase
"""

import sys
import os
import requests
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_backend_connection():
    """Check if main app is accessible"""
    print_section("1. BACKEND CONNECTION CHECK")
    try:
        # Try to get the API base URL from environment or use default
        api_url = os.getenv('API_BASE_URL', 'http://localhost:5000')
        if api_url == 'http://localhost:5000':
            print("⚠️  Using localhost - make sure main app is running")
        
        response = requests.get(f"{api_url}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is accessible at {api_url}")
            return api_url
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {api_url}")
        print("   Make sure the main app is running")
        return None
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return None

def check_news_availability(api_url: str):
    """Check if there's news available"""
    print_section("2. NEWS AVAILABILITY CHECK")
    try:
        # Check recent news
        response = requests.get(f"{api_url}/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            
            print(f"✅ News endpoint accessible")
            print(f"Total news items in cache: {len(news_items)}")
            
            if news_items:
                # Check most recent news
                most_recent = news_items[0] if news_items else None
                if most_recent:
                    title = most_recent.get('title', 'Unknown')
                    timestamp = most_recent.get('added_to_feed_at') or most_recent.get('timestamp', '')
                    print(f"\nMost recent news:")
                    print(f"  Title: {title[:60]}...")
                    print(f"  Time: {timestamp}")
                    
                    # Check if news is recent (within last 24 hours)
                    try:
                        if timestamp:
                            if 'T' in timestamp:
                                news_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            else:
                                news_time = datetime.fromisoformat(timestamp)
                            now = datetime.now(news_time.tzinfo) if news_time.tzinfo else datetime.now()
                            age = now - news_time
                            print(f"  Age: {age}")
                            
                            if age.total_seconds() < 3600:  # Less than 1 hour
                                print("  ✅ News is recent (less than 1 hour old)")
                            elif age.total_seconds() < 86400:  # Less than 24 hours
                                print(f"  ⚠️  News is {age} old")
                            else:
                                print(f"  ❌ News is stale ({age} old)")
                    except Exception as e:
                        print(f"  ⚠️  Could not parse timestamp: {e}")
            else:
                print("❌ No news items in cache")
            
            return news_items
        else:
            print(f"❌ News endpoint returned status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error checking news: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_alert_trigger_endpoint(api_url: str):
    """Check if alert trigger endpoint is working"""
    print_section("3. ALERT TRIGGER ENDPOINT CHECK")
    try:
        # Try to trigger alerts manually
        response = requests.post(
            f"{api_url}/api/alerts/trigger",
            json={
                'alert_type': 'liveNews',
                'force': True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alert trigger endpoint is accessible")
            print(f"Response: {data}")
            
            alerts_sent = data.get('alerts_sent', 0)
            users_notified = data.get('users_notified', 0)
            
            print(f"\nAlerts sent: {alerts_sent}")
            print(f"Users notified: {users_notified}")
            
            if alerts_sent == 0:
                print("\n⚠️  No alerts were sent")
                print("   Possible reasons:")
                print("   - No users with alerts enabled")
                print("   - No new news to alert about")
                print("   - All news already sent (deduplication)")
            
            return data
        else:
            print(f"❌ Alert trigger endpoint returned status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error checking alert trigger: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_background_worker_status():
    """Check if background worker is running"""
    print_section("4. BACKGROUND WORKER STATUS CHECK")
    try:
        # Check Railway logs or process status
        # For now, we'll check if there are any recent alert attempts in Firebase
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Try to check alert history or deduplication state
        try:
            # Check if there's a way to see worker activity
            # This is a placeholder - actual implementation depends on your logging
            print("⚠️  Worker status check requires Railway logs or process monitoring")
            print("   Check Railway dashboard for background worker status")
            print("   Look for:")
            print("   - Worker process running")
            print("   - Recent log entries")
            print("   - Error messages")
        except Exception as e:
            print(f"⚠️  Could not check worker status: {e}")
        
        return None
    except Exception as e:
        print(f"❌ Error checking worker status: {e}")
        return None

def check_user_settings():
    """Check if users have alerts enabled"""
    print_section("5. USER SETTINGS CHECK")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        users = firebase.get_all_users_with_alerts()
        
        if users:
            print(f"✅ Found {len(users)} users with alerts enabled")
            
            # Check first user's settings
            if len(users) > 0:
                first_user = users[0]
                user_id = first_user.get('user_id', 'Unknown')
                settings = first_user.get('settings', {})
                
                print(f"\nSample user (ID: {user_id[:8]}...):")
                
                # Check Telegram settings
                channels = settings.get('channels', {})
                telegram = channels.get('telegram', {})
                if telegram.get('enabled'):
                    print(f"  ✅ Telegram alerts enabled")
                    print(f"  Chat ID: {telegram.get('chatId', 'Not set')}")
                else:
                    print(f"  ❌ Telegram alerts disabled")
                
                # Check alert types
                preferences = settings.get('preferences', {})
                alert_types = preferences.get('alertTypes', {})
                print(f"  Alert types:")
                print(f"    Live News: {alert_types.get('liveNews', False)}")
                print(f"    Pre-News: {alert_types.get('preNews', False)}")
                print(f"    Post-News: {alert_types.get('postNews', False)}")
        else:
            print("❌ No users found with alerts enabled")
            print("   This could be why no alerts are being sent")
        
        return users
    except Exception as e:
        print(f"❌ Error checking user settings: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_recent_news_fetch(api_url: str):
    """Check when news was last fetched"""
    print_section("6. RECENT NEWS FETCH CHECK")
    try:
        # Check cache status
        response = requests.get(f"{api_url}/api/cache-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cache status endpoint accessible")
            
            last_fetch = data.get('last_fetch', 'Unknown')
            cache_age = data.get('cache_age_seconds', 0)
            
            print(f"\nLast fetch: {last_fetch}")
            print(f"Cache age: {cache_age} seconds ({cache_age / 3600:.1f} hours)")
            
            if cache_age > 3600:  # More than 1 hour
                print("⚠️  Cache is stale - news may not be updating")
            else:
                print("✅ Cache is recent")
            
            return data
        else:
            print(f"⚠️  Cache status endpoint returned {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  Error checking cache status: {e}")
        return None

def main():
    print("\n" + "=" * 70)
    print("  ALERT SYSTEM DIAGNOSIS")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Checking why no alerts since yesterday 8:46pm")
    
    # Step 1: Check backend
    api_url = check_backend_connection()
    if not api_url:
        print("\n❌ Cannot proceed without backend connection")
        return
    
    # Step 2: Check news availability
    news_items = check_news_availability(api_url)
    
    # Step 3: Check recent news fetch
    cache_status = check_recent_news_fetch(api_url)
    
    # Step 4: Check user settings
    users = check_user_settings()
    
    # Step 5: Check alert trigger
    trigger_result = check_alert_trigger_endpoint(api_url)
    
    # Step 6: Check worker status
    worker_status = check_background_worker_status()
    
    # Summary
    print_section("DIAGNOSIS SUMMARY")
    
    issues = []
    
    if not news_items:
        issues.append("No news items available")
    
    if cache_status and cache_status.get('cache_age_seconds', 0) > 3600:
        issues.append(f"News cache is stale ({cache_status.get('cache_age_seconds', 0) / 3600:.1f} hours old)")
    
    if not users:
        issues.append("No users with alerts enabled")
    
    if trigger_result and trigger_result.get('alerts_sent', 0) == 0:
        issues.append("Alert trigger returned 0 alerts sent")
    
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("✅ No obvious issues found")
        print("   Check Railway logs for background worker activity")
    
    print("\n" + "=" * 70)
    print("  RECOMMENDATIONS")
    print("=" * 70)
    print("1. Check Railway dashboard for background worker status")
    print("2. Check Railway logs for worker errors")
    print("3. Verify news sources are providing updates")
    print("4. Check if deduplication is preventing alerts")
    print("5. Manually trigger alerts to test: POST /api/alerts/trigger")

if __name__ == "__main__":
    main()

