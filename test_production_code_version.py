#!/usr/bin/env python3
"""
Test to check if production server has updated code
"""

import requests
import json

def test_production_code():
    """Test if production has updated code"""
    
    print("🔍 Testing Production Code Version")
    print("=" * 50)
    
    # Test 1: Check if we can get a response that indicates the code version
    print("\n1️⃣ Testing Force Refresh with Detailed Response...")
    try:
        response = requests.post("https://fxsentinel-production.up.railway.app/api/force-refresh-news", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data}")
            
            # Check if the response includes any indication of Telegram processing
            message = data.get('message', '')
            if 'Telegram' in message:
                print("✅ Telegram processing detected in response")
            else:
                print("❌ No Telegram processing detected in response")
                
            # Check if there are any error messages
            alert_results = data.get('alert_results', {})
            errors = alert_results.get('errors', [])
            if errors:
                print(f"⚠️ Errors found: {errors}")
            else:
                print("✅ No errors reported")
                
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Force refresh error: {e}")
    
    # Test 2: Check if we can trigger a fresh news fetch
    print("\n2️⃣ Testing Fresh News Fetch...")
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news?force_refresh=true", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News response: {len(data.get('news', []))} articles")
            print(f"📊 Cache status: {data.get('cache_status', 'unknown')}")
            print(f"📋 Sources: {data.get('sources', [])}")
            
            # Check if Telegram is in sources
            sources = data.get('sources', [])
            if 'Telegram' in sources:
                print("✅ Telegram is in sources list")
            else:
                print("❌ Telegram is not in sources list")
                
        else:
            print(f"❌ News fetch failed: {response.status_code}")
    except Exception as e:
        print(f"❌ News fetch error: {e}")

if __name__ == "__main__":
    test_production_code()
