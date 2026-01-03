#!/usr/bin/env python3
"""
Check unified alert processor health endpoint
"""

import sys
import os
import requests
import json

def check_health_endpoint(base_url: str = None):
    """Check the health endpoint for unified alert processor"""
    if not base_url:
        # Try to get from environment or use default
        base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        # For production, try Railway URL
        if 'localhost' in base_url:
            print("⚠️  Using localhost. For production, set API_BASE_URL environment variable")
            print("   Example: export API_BASE_URL=https://your-app.railway.app")
    
    health_url = f"{base_url}/api/health/unified-alert-processor"
    
    print("=" * 80)
    print("CHECKING UNIFIED ALERT PROCESSOR HEALTH")
    print("=" * 80)
    print(f"\nEndpoint: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("\n✅ Health Check Successful")
                print("\nStatus Details:")
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                print("\n⚠️  Response is not JSON")
                print(f"Response text: {response.text[:500]}")
                print("\nThis might indicate the endpoint doesn't exist or returns HTML")
                return
            
            # Analyze status
            print("\n" + "=" * 80)
            print("ANALYSIS")
            print("=" * 80)
            
            if data.get('status') == 'running':
                print("✅ Processor Status: RUNNING")
            else:
                print(f"⚠️  Processor Status: {data.get('status', 'UNKNOWN')}")
            
            if data.get('thread_alive'):
                print("✅ Background Thread: ALIVE")
            else:
                print("❌ Background Thread: NOT ALIVE (processor may not be working)")
            
            if data.get('last_check'):
                print(f"✅ Last Check: {data.get('last_check')}")
            else:
                print("⚠️  Last Check: NEVER (processor may not be checking)")
            
            # Check intervals
            if data.get('economic_calendar_interval'):
                print(f"📅 Economic Calendar Interval: {data.get('economic_calendar_interval')}s")
            if data.get('post_news_interval'):
                print(f"📰 Post-News Interval: {data.get('post_news_interval')}s")
                
        else:
            print(f"\n❌ Health Check Failed")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error")
        print(f"   Could not connect to {base_url}")
        print(f"   Make sure the server is running and accessible")
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout Error")
        print(f"   Request took too long (>10s)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Check unified alert processor health')
    parser.add_argument('--url', type=str, help='Base URL (e.g., https://your-app.railway.app)')
    args = parser.parse_args()
    
    check_health_endpoint(args.url)

