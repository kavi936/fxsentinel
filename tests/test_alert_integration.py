#!/usr/bin/env python3
"""
Integration test for alert system
Tests the full alert flow from worker to main app
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_alert_trigger_endpoint(base_url="http://localhost:5001"):
    """Test the /api/alerts/trigger endpoint"""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Alert Trigger Endpoint")
    print("="*60)
    
    # Create test alert data
    test_alert = {
        'type': 'news',
        'data': {
            'id': f'integration_test_{int(time.time())}',
            'title': 'Fed Raises Interest Rates - Integration Test',
            'summary': 'Federal Reserve announces rate hike affecting USD pairs',
            'source': 'Test Source',
            'url': 'https://test.com/news',
            'impact': 'high',
            'timestamp': datetime.now().isoformat()
        }
    }
    
    print(f"\n1. Sending test alert to {base_url}/api/alerts/trigger...")
    print(f"   Alert: {test_alert['data']['title']}")
    
    try:
        response = requests.post(
            f"{base_url}/api/alerts/trigger",
            json=test_alert,
            timeout=30
        )
        
        print(f"\n2. Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Alerts Sent: {result.get('alerts_sent', 0)}")
            print(f"   Message: {result.get('message', '')}")
            
            if result.get('success'):
                print("\n   ✅ TEST PASSED: Alert trigger endpoint works")
                return True
            else:
                print("\n   ⚠️  Alert trigger returned success=False")
                print(f"   Error: {result.get('error', 'Unknown')}")
                return False
        else:
            print(f"\n   ❌ TEST FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n   ⚠️  Could not connect to server")
        print("   Make sure the Flask app is running on", base_url)
        return None
    except Exception as e:
        print(f"\n   ❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_duplicate_prevention(base_url="http://localhost:5001"):
    """Test that duplicate alerts are prevented"""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Duplicate Prevention")
    print("="*60)
    
    # Create test alert with unique ID
    alert_id = f'duplicate_test_{int(time.time())}'
    test_alert = {
        'type': 'news',
        'data': {
            'id': alert_id,
            'title': 'Duplicate Test Alert',
            'summary': 'Testing duplicate prevention',
            'source': 'Test Source',
            'url': 'https://test.com/duplicate',
            'impact': 'high',
            'timestamp': datetime.now().isoformat()
        }
    }
    
    print(f"\n1. Sending first alert (ID: {alert_id})...")
    try:
        response1 = requests.post(
            f"{base_url}/api/alerts/trigger",
            json=test_alert,
            timeout=30
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            alerts_sent_1 = result1.get('alerts_sent', 0)
            print(f"   First alert: {alerts_sent_1} alerts sent")
        else:
            print(f"   First alert failed: HTTP {response1.status_code}")
            return False
        
        # Wait a moment
        time.sleep(1)
        
        print(f"\n2. Sending duplicate alert (same ID: {alert_id})...")
        response2 = requests.post(
            f"{base_url}/api/alerts/trigger",
            json=test_alert,
            timeout=30
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            alerts_sent_2 = result2.get('alerts_sent', 0)
            print(f"   Duplicate alert: {alerts_sent_2} alerts sent")
            
            if alerts_sent_2 == 0:
                print("\n   ✅ TEST PASSED: Duplicate was prevented")
                return True
            else:
                print("\n   ❌ TEST FAILED: Duplicate was not prevented")
                return False
        else:
            print(f"   Duplicate alert failed: HTTP {response2.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n   ⚠️  Could not connect to server")
        return None
    except Exception as e:
        print(f"\n   ❌ TEST FAILED: {e}")
        return False

def test_health_endpoint(base_url="http://localhost:5001"):
    """Test health endpoint"""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Status: {result.get('status', 'unknown')}")
            print("\n   ✅ TEST PASSED: Health endpoint works")
            return True
        else:
            print(f"   ❌ TEST FAILED: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n   ⚠️  Could not connect to server")
        return None
    except Exception as e:
        print(f"\n   ❌ TEST FAILED: {e}")
        return False

def run_integration_tests(base_url="http://localhost:5001"):
    """Run all integration tests"""
    print("\n" + "="*60)
    print("ALERT SYSTEM - INTEGRATION TESTS")
    print("="*60)
    print(f"Testing against: {base_url}")
    print(f"Started at: {datetime.now().isoformat()}")
    
    tests = [
        ("Health Check", lambda: test_health_endpoint(base_url)),
        ("Alert Trigger", lambda: test_alert_trigger_endpoint(base_url)),
        ("Duplicate Prevention", lambda: test_duplicate_prevention(base_url)),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if result is None:
                print(f"\n⚠️  Skipping remaining tests (server not available)")
                break
        except Exception as e:
            print(f"\n   ❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result is True)
    total = sum(1 for _, result in results if result is not None)
    
    for test_name, result in results:
        if result is None:
            status = "⚠️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    return passed == total

if __name__ == "__main__":
    import sys
    
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    success = run_integration_tests(base_url)
    sys.exit(0 if success else 1)

