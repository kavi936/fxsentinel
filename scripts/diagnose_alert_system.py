#!/usr/bin/env python3
"""
Alert System Diagnostic Script
Checks all components of the alert system to identify issues
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def check_worker_status(base_url=None):
    """Check if worker is running and healthy"""
    print("\n" + "="*60)
    print("1. WORKER STATUS CHECK")
    print("="*60)
    
    if not base_url:
        print("   ⚠️  Worker URL not provided - skipping")
        return None
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Worker is running")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Worker Running: {data.get('worker_running', False)}")
            return True
        else:
            print(f"   ❌ Worker returned HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to worker at {base_url}")
        return False
    except Exception as e:
        print(f"   ❌ Error checking worker: {e}")
        return False

def check_main_app_news(base_url):
    """Check if main app news endpoint works"""
    print("\n" + "="*60)
    print("2. MAIN APP NEWS ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{base_url}/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            print(f"   ✅ News endpoint working")
            print(f"   News items returned: {len(news_items)}")
            
            if news_items:
                # Check first few items for structure
                print(f"\n   Sample news items:")
                for i, item in enumerate(news_items[:3], 1):
                    print(f"   {i}. {item.get('title', 'No title')[:50]}")
                    print(f"      Impact: {item.get('impact', 'unknown')}")
                    print(f"      Source: {item.get('source', 'unknown')}")
            
            return news_items
        else:
            print(f"   ❌ News endpoint returned HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Error checking news endpoint: {e}")
        return None

def check_forex_filtering(news_items):
    """Check if news items pass forex filtering"""
    print("\n" + "="*60)
    print("3. FOREX FILTERING CHECK")
    print("="*60)
    
    if not news_items:
        print("   ⚠️  No news items to check")
        return
    
    try:
        from services.news_alert_trigger import news_alert_trigger
        
        high_impact_count = 0
        for item in news_items:
            if news_alert_trigger.is_forex_high_impact(item):
                high_impact_count += 1
        
        print(f"   Total news items: {len(news_items)}")
        print(f"   High-impact forex news: {high_impact_count}")
        print(f"   Filtered out: {len(news_items) - high_impact_count}")
        
        if high_impact_count == 0:
            print("\n   ⚠️  WARNING: No news items pass filtering!")
            print("   This might be why no alerts are being sent.")
            print("\n   Sample filtered items:")
            for item in news_items[:5]:
                title = item.get('title', 'No title')
                print(f"   - {title[:60]}")
        
        return high_impact_count
    except Exception as e:
        print(f"   ❌ Error checking filtering: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_firebase_connection():
    """Check Firebase connection"""
    print("\n" + "="*60)
    print("4. FIREBASE CONNECTION CHECK")
    print("="*60)
    
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        
        firebase = FirebaseRealtimeStorage()
        result = firebase.test_connection()
        
        if result:
            print("   ✅ Firebase connection successful")
            return True
        else:
            print("   ❌ Firebase connection failed")
            print("   Check FIREBASE_PROJECT_ID and FIREBASE_REALTIME_URL")
            return False
    except Exception as e:
        print(f"   ❌ Error checking Firebase: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alert_trigger(base_url):
    """Test alert trigger endpoint"""
    print("\n" + "="*60)
    print("5. ALERT TRIGGER TEST")
    print("="*60)
    
    test_alert = {
        'type': 'news',
        'data': {
            'id': f'diagnostic_test_{int(datetime.now().timestamp())}',
            'title': 'Fed Raises Interest Rates - Diagnostic Test',
            'summary': 'Federal Reserve announces rate changes affecting USD',
            'source': 'Diagnostic Test',
            'url': 'https://test.com/diagnostic',
            'impact': 'high',
            'timestamp': datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/alerts/trigger",
            json=test_alert,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            alerts_sent = result.get('alerts_sent', 0)
            print(f"   ✅ Alert trigger endpoint working")
            print(f"   Alerts sent: {alerts_sent}")
            print(f"   Message: {result.get('message', '')}")
            
            if alerts_sent == 0:
                print("\n   ⚠️  WARNING: 0 alerts sent!")
                print("   Possible reasons:")
                print("   - No users with Telegram enabled")
                print("   - Users have alerts disabled")
                print("   - Invalid chat IDs")
                print("   - Subscription check failed")
            
            return alerts_sent > 0
        else:
            print(f"   ❌ Alert trigger returned HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing alert trigger: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_deduplication():
    """Check deduplication service"""
    print("\n" + "="*60)
    print("6. DEDUPLICATION SERVICE CHECK")
    print("="*60)
    
    try:
        from services.persistent_alert_deduplication import get_persistent_deduplication
        
        dedup = get_persistent_deduplication()
        stats = dedup.get_stats()
        
        print(f"   ✅ Deduplication service initialized")
        print(f"   Total records: {stats.get('total_records', 0)}")
        print(f"   Operations: {stats.get('operations_count', 0)}")
        print(f"   Duplicates prevented: {stats.get('duplicates_prevented', 0)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error checking deduplication: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic checks"""
    print("\n" + "="*60)
    print("ALERT SYSTEM DIAGNOSTIC TOOL")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    worker_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"\nMain App URL: {base_url}")
    if worker_url:
        print(f"Worker URL: {worker_url}")
    
    results = {}
    
    # Run checks
    if worker_url:
        results['worker'] = check_worker_status(worker_url)
    
    results['news'] = check_main_app_news(base_url)
    if results['news']:
        results['filtering'] = check_forex_filtering(results['news'])
    
    results['firebase'] = check_firebase_connection()
    results['deduplication'] = check_deduplication()
    results['alert_trigger'] = test_alert_trigger(base_url)
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for check, result in results.items():
        if result is None:
            status = "⚠️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status}: {check}")
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    print("\nNext steps:")
    print("1. Review failed checks above")
    print("2. Check Railway logs for errors")
    print("3. Verify environment variables")
    print("4. Test with manual alert trigger")

if __name__ == "__main__":
    main()

