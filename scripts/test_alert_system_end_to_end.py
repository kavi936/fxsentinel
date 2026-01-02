#!/usr/bin/env python3
"""
End-to-End Test for Unified Alert System
Tests the complete flow: news fetch → alert trigger → user delivery
"""

import sys
import os
import time
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_news_fetch_with_alert_trigger():
    """Test that news fetch triggers alerts"""
    print_section("END-TO-END TEST: News Fetch → Alert Trigger")
    
    # Note: This test requires the Flask app to be running
    # Start the app in another terminal: python backend/app.py
    
    api_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
    
    print(f"Testing against: {api_url}")
    print("⚠️  Make sure Flask app is running: python backend/app.py")
    
    try:
        # Test 1: Check health endpoint
        print("\n1. Checking health endpoint...")
        response = requests.get(f"{api_url}/api/health/unified-alert-processor", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Processor running: {data.get('processor', {}).get('running')}")
        else:
            print(f"⚠️  Health check returned {response.status_code}")
            print("   App might not be running or endpoint not available")
            return False
        
        # Test 2: Fetch news (should trigger alerts)
        print("\n2. Fetching news (should trigger alerts)...")
        response = requests.get(f"{api_url}/api/news?force_refresh=true", timeout=30)
        if response.status_code == 200:
            data = response.json()
            news_count = len(data.get('news', []))
            print(f"✅ News fetched: {news_count} items")
            print(f"   Check logs for: 'Triggered alert check for X fresh news items'")
            return True
        else:
            print(f"⚠️  News fetch returned {response.status_code}")
            return False
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {api_url}")
        print("   Make sure Flask app is running: python backend/app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processor_status():
    """Test processor status endpoint"""
    print_section("PROCESSOR STATUS TEST")
    
    api_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
    
    try:
        response = requests.get(f"{api_url}/api/health/unified-alert-processor", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Processor status:")
            print(f"   Status: {data.get('status')}")
            processor = data.get('processor', {})
            print(f"   Running: {processor.get('running')}")
            print(f"   Thread alive: {processor.get('thread_alive')}")
            print(f"   Last check: {processor.get('last_check')}")
            return True
        else:
            print(f"⚠️  Status check returned {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("  UNIFIED ALERT SYSTEM - END-TO-END TEST")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    print("\n⚠️  IMPORTANT: Start Flask app first:")
    print("   python backend/app.py")
    print("\nThen run this test in another terminal.")
    
    input("\nPress Enter when Flask app is running...")
    
    # Test processor status
    test_processor_status()
    
    # Test end-to-end flow
    result = test_news_fetch_with_alert_trigger()
    
    print_section("TEST SUMMARY")
    if result:
        print("✅ End-to-end test completed")
        print("   Check Flask app logs for alert processing details")
    else:
        print("⚠️  End-to-end test had issues")
        print("   Make sure Flask app is running and check logs")

if __name__ == "__main__":
    main()

