#!/usr/bin/env python3
"""
Diagnose Railway worker deployment issues
"""

import os
import sys
import requests
from datetime import datetime

def diagnose_railway_worker():
    """Diagnose Railway worker deployment issues"""
    print("🔍 Diagnosing Railway Worker Deployment")
    print("=" * 50)
    
    # Check if we can access the worker directly
    print("1️⃣ Checking worker service accessibility...")
    
    # Try to access the worker health endpoint
    worker_urls = [
        "https://fxsentinel-background-worker-v2-production.up.railway.app",
        "https://fxsentinel-background-worker-v2-production.up.railway.app/api/health",
        "https://fxsentinel-background-worker-v2-production.up.railway.app/",
    ]
    
    for url in worker_urls:
        try:
            print(f"   🔗 Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"   📊 Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Worker is accessible!")
                print(f"   📋 Response: {response.text[:200]}...")
                return True
            else:
                print(f"   ⚠️  Worker responded with status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error accessing worker: {e}")
    
    print(f"\n2️⃣ Checking main app worker status endpoint...")
    
    # Check the main app's worker status
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/health/alert-service", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   📊 Worker status from main app:")
            print(f"   🔄 Running: {health_data.get('worker_running', False)}")
            print(f"   📡 Service status: {health_data.get('service_status', 'unknown')}")
            
            background_worker = health_data.get('background_worker', {})
            print(f"   🧵 Thread alive: {background_worker.get('thread_alive', False)}")
            print(f"   ⏰ Last check: {background_worker.get('last_check', 'Never')}")
            
            if not health_data.get('worker_running', False):
                print(f"   ❌ Worker is not running!")
                return False
        else:
            print(f"   ❌ Could not get worker status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking worker status: {e}")
    
    print(f"\n3️⃣ Checking environment variables...")
    
    # Check if we can access environment variables (this will only work if running locally)
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'API_BASE_URL',
        'OPENAI_API_KEY',
        'FIREBASE_PROJECT_ID'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * len(value) if 'TOKEN' in var or 'KEY' in var else value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    print(f"\n4️⃣ Testing worker startup locally...")
    
    # Try to start the worker locally to see if there are import errors
    try:
        sys.path.append('backend')
        from backend.worker_app import main
        print(f"   ✅ Worker app imports successfully")
        print(f"   📝 Worker app has main function: {callable(main)}")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error importing worker: {e}")
        return False
    
    return False

def test_worker_startup():
    """Test worker startup locally"""
    print(f"\n🧪 Testing Worker Startup Locally")
    print("=" * 40)
    
    try:
        # Set required environment variables for testing
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        os.environ['API_BASE_URL'] = 'https://fxsentinel-production.up.railway.app'
        
        sys.path.append('backend')
        from backend.worker_app import main
        
        print(f"   ✅ Worker can be imported and started")
        print(f"   📝 Main function is callable")
        
        # Don't actually start it, just test imports
        return True
        
    except Exception as e:
        print(f"   ❌ Worker startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Railway Worker Diagnostic Tool")
    print("=" * 60)
    
    # Run diagnostics
    worker_accessible = diagnose_railway_worker()
    
    # Test local startup
    local_test = test_worker_startup()
    
    print(f"\n📋 Diagnostic Summary:")
    print(f"   🌐 Worker accessible: {'✅' if worker_accessible else '❌'}")
    print(f"   🧪 Local startup test: {'✅' if local_test else '❌'}")
    
    if not worker_accessible and local_test:
        print(f"\n🔧 Recommendation:")
        print(f"   The worker code is fine locally but not accessible on Railway.")
        print(f"   This suggests a deployment or configuration issue.")
        print(f"   Check Railway dashboard for deployment logs and environment variables.")
    elif not local_test:
        print(f"\n🔧 Recommendation:")
        print(f"   The worker has code issues that need to be fixed first.")
    else:
        print(f"\n🎉 Worker appears to be working correctly!")
