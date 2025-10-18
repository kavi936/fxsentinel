#!/usr/bin/env python3
"""
Manually trigger the worker's monitoring function to test if it works
"""

import requests
import json
from datetime import datetime

def trigger_worker_monitoring():
    """Manually trigger the worker's monitoring function"""
    print("🔄 Triggering Worker Monitoring Manually")
    print("=" * 50)
    
    # Try to trigger the worker's monitoring via API
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    
    # Check if there's a trigger endpoint
    trigger_endpoints = [
        "/api/trigger-monitoring",
        "/api/check-news",
        "/api/trigger-alerts",
        "/api/health/trigger"
    ]
    
    for endpoint in trigger_endpoints:
        try:
            print(f"🔗 Testing endpoint: {endpoint}")
            response = requests.post(f"{worker_url}{endpoint}", timeout=10)
            print(f"   📊 Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Endpoint exists and responded")
                print(f"   📋 Response: {response.text[:200]}...")
            else:
                print(f"   ⚠️  Endpoint returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Try to trigger via main app's trigger endpoint
    print(f"\n🔄 Triggering via main app...")
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    try:
        response = requests.post(f"{main_app_url}/api/trigger-alerts", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Main app trigger successful")
            print(f"   📋 Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Main app trigger failed: {response.status_code}")
            print(f"   📋 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error triggering via main app: {e}")

def check_worker_status_detailed():
    """Check detailed worker status"""
    print(f"\n🔍 Detailed Worker Status Check")
    print("=" * 40)
    
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    
    # Check health endpoint
    try:
        response = requests.get(f"{worker_url}/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   📊 Worker health: {json.dumps(health_data, indent=2)}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking health: {e}")
    
    # Check if there are any status endpoints
    status_endpoints = [
        "/api/status",
        "/api/worker-status",
        "/api/monitoring-status"
    ]
    
    for endpoint in status_endpoints:
        try:
            response = requests.get(f"{worker_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Status endpoint {endpoint} exists")
                print(f"   📋 Response: {response.text[:200]}...")
        except:
            pass

if __name__ == "__main__":
    print("🧪 Worker Monitoring Trigger Test")
    print("=" * 60)
    
    # Check detailed status
    check_worker_status_detailed()
    
    # Try to trigger monitoring
    trigger_worker_monitoring()
    
    print(f"\n📋 Summary:")
    print(f"   If the worker is not automatically monitoring, we may need to:")
    print(f"   1. Check the worker logs for errors")
    print(f"   2. Verify the BackgroundAlertWorker thread is starting")
    print(f"   3. Add a manual trigger endpoint to the worker")
    print(f"   4. Set up a cron job to trigger monitoring periodically")
