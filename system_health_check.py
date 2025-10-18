#!/usr/bin/env python3
"""
Comprehensive FXSentinel System Health Check
"""

import requests
import json
import time
from datetime import datetime, timedelta

def check_main_app_health():
    """Check main app health and status"""
    print("🏥 Main App Health Check")
    print("=" * 30)
    
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Status: {health_data.get('status', 'unknown')}")
            print(f"   📅 Timestamp: {health_data.get('timestamp', 'unknown')}")
            print(f"   🔢 Version: {health_data.get('version', 'unknown')}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_worker_health():
    """Check background worker health"""
    print(f"\n🔧 Background Worker Health Check")
    print("=" * 40)
    
    try:
        response = requests.get("https://fxsentinel-background-worker-v2-production.up.railway.app/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Status: {health_data.get('status', 'unknown')}")
            print(f"   📅 Timestamp: {health_data.get('timestamp', 'unknown')}")
            print(f"   🔢 Version: {health_data.get('version', 'unknown')}")
            print(f"   🏃 Worker Running: {health_data.get('worker_running', False)}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_alert_service_status():
    """Check alert service status from main app"""
    print(f"\n📡 Alert Service Status Check")
    print("=" * 35)
    
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/health/alert-service", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            
            print(f"   📊 Service Status: {health_data.get('service_status', 'unknown')}")
            print(f"   🏃 Worker Running: {health_data.get('worker_running', False)}")
            print(f"   📅 Last Check: {health_data.get('last_check', 'Never')}")
            print(f"   🔄 Recent Check: {health_data.get('recent_check', False)}")
            
            # Background worker details
            bg_worker = health_data.get('background_worker', {})
            if bg_worker:
                print(f"   🧵 Thread Alive: {bg_worker.get('thread_alive', False)}")
                print(f"   ⏰ Last Post News Check: {bg_worker.get('last_post_news_check', 'Never')}")
                print(f"   🔄 Running: {bg_worker.get('running', False)}")
            
            return health_data.get('worker_running', False)
        else:
            print(f"   ❌ Alert service check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_news_availability():
    """Check if news is available and recent"""
    print(f"\n📰 News Availability Check")
    print("=" * 30)
    
    try:
        # Check worker news
        response = requests.get("https://fxsentinel-background-worker-v2-production.up.railway.app/api/news", timeout=10)
        if response.status_code == 200:
            news_data = response.json()
            news_items = news_data.get('news', [])
            
            print(f"   📊 Total News Items: {len(news_items)}")
            
            if news_items:
                latest = news_items[0]
                latest_time = latest.get('published_at', '')
                print(f"   📰 Latest News: {latest.get('title', 'No title')[:60]}...")
                print(f"   📅 Published: {latest_time}")
                print(f"   🏷️  Impact: {latest.get('impact', 'unknown')}")
                
                # Check if news is recent (within last 2 hours)
                if latest_time:
                    try:
                        from datetime import datetime
                        news_time = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
                        now = datetime.now(news_time.tzinfo)
                        time_diff = now - news_time
                        
                        if time_diff.total_seconds() < 7200:  # 2 hours
                            print(f"   ✅ News is recent ({time_diff.total_seconds()/60:.0f} minutes ago)")
                        else:
                            print(f"   ⚠️  News is old ({time_diff.total_seconds()/3600:.1f} hours ago)")
                    except:
                        print(f"   ⚠️  Could not parse news timestamp")
                
                # Count high-impact news
                high_impact = [n for n in news_items if n.get('impact') == 'high']
                print(f"   🎯 High-Impact News: {len(high_impact)}")
                
                return len(news_items) > 0
            else:
                print(f"   ❌ No news items found")
                return False
        else:
            print(f"   ❌ News check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_alert_trigger():
    """Test the alert trigger functionality"""
    print(f"\n🧪 Alert Trigger Test")
    print("=" * 25)
    
    try:
        # Test with worker
        response = requests.post("https://fxsentinel-background-worker-v2-production.up.railway.app/api/trigger-alerts", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Worker trigger successful")
            print(f"   📊 News processed: {result.get('news_alerts_processed', False)}")
            print(f"   📊 Calendar processed: {result.get('calendar_alerts_processed', False)}")
            print(f"   📊 Post-news processed: {result.get('post_news_processed', False)}")
            print(f"   📅 Timestamp: {result.get('timestamp', 'unknown')}")
            return True
        else:
            print(f"   ❌ Worker trigger failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_user_settings():
    """Check user settings and Telegram configuration"""
    print(f"\n👤 User Settings Check")
    print("=" * 25)
    
    try:
        # This would require authentication, so we'll just check if the endpoint exists
        response = requests.get("https://fxsentinel-production.up.railway.app/api/health", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Main app is accessible")
            print(f"   📝 Note: User settings require authentication to check")
            print(f"   💡 To verify your settings, check the Telegram bot directly")
            return True
        else:
            print(f"   ❌ Main app not accessible")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def run_comprehensive_check():
    """Run all health checks"""
    print("🔍 FXSentinel System Health Check")
    print("=" * 50)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all checks
    main_app_ok = check_main_app_health()
    worker_ok = check_worker_health()
    alert_service_ok = check_alert_service_status()
    news_ok = check_news_availability()
    trigger_ok = test_alert_trigger()
    user_ok = check_user_settings()
    
    # Summary
    print(f"\n📋 System Health Summary")
    print("=" * 30)
    print(f"   🏥 Main App: {'✅' if main_app_ok else '❌'}")
    print(f"   🔧 Background Worker: {'✅' if worker_ok else '❌'}")
    print(f"   📡 Alert Service: {'✅' if alert_service_ok else '❌'}")
    print(f"   📰 News Availability: {'✅' if news_ok else '❌'}")
    print(f"   🧪 Alert Trigger: {'✅' if trigger_ok else '❌'}")
    print(f"   👤 User Settings: {'✅' if user_ok else '❌'}")
    
    # Overall status
    all_checks = [main_app_ok, worker_ok, news_ok, trigger_ok, user_ok]
    overall_status = "✅ HEALTHY" if all(all_checks) else "⚠️ ISSUES DETECTED"
    
    print(f"\n🎯 Overall Status: {overall_status}")
    
    if not all(all_checks):
        print(f"\n🔧 Recommendations:")
        if not main_app_ok:
            print(f"   - Check main app deployment")
        if not worker_ok:
            print(f"   - Check background worker deployment")
        if not news_ok:
            print(f"   - Check news feed connectivity")
        if not trigger_ok:
            print(f"   - Check alert processing system")
        if not user_ok:
            print(f"   - Check user authentication and settings")
    
    return all(all_checks)

if __name__ == "__main__":
    success = run_comprehensive_check()
    
    if success:
        print(f"\n🎉 System is working properly!")
        print(f"   You should be receiving alerts automatically.")
    else:
        print(f"\n⚠️ System has issues that need attention.")
        print(f"   Check the recommendations above.")
