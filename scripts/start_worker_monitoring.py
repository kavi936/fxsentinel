#!/usr/bin/env python3
"""
Start the worker monitoring manually
"""

import requests
import json
import time
from datetime import datetime

def start_worker_monitoring():
    """Start the worker monitoring"""
    print("🚀 Starting Worker Monitoring")
    print("=" * 40)
    
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    
    # Try the new start-monitoring endpoint
    try:
        print("🔗 Trying to start monitoring via /api/start-monitoring...")
        response = requests.post(f"{worker_url}/api/start-monitoring", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Monitoring started successfully!")
            print(f"   📋 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"   ❌ Start monitoring failed: {response.status_code}")
            print(f"   📋 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error starting monitoring: {e}")
    
    # Fallback: Use the trigger-alerts endpoint in a loop
    print(f"\n🔄 Fallback: Setting up periodic alert checking...")
    print(f"   This will check for alerts every 60 seconds")
    print(f"   Press Ctrl+C to stop")
    
    try:
        while True:
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking for alerts...")
            
            response = requests.post(f"{worker_url}/api/trigger-alerts", timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Alert check successful")
                print(f"   📊 News processed: {result.get('news_alerts_processed', False)}")
                print(f"   📊 Calendar processed: {result.get('calendar_alerts_processed', False)}")
            else:
                print(f"   ❌ Alert check failed: {response.status_code}")
            
            print(f"   ⏳ Waiting 60 seconds...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped by user")
        return True
    except Exception as e:
        print(f"   ❌ Error in monitoring loop: {e}")
        return False

if __name__ == "__main__":
    success = start_worker_monitoring()
    if success:
        print("\n🎯 Worker monitoring: STARTED")
    else:
        print("\n🔧 Worker monitoring: FAILED")
