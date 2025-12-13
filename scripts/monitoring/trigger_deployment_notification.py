#!/usr/bin/env python3
"""
Script to trigger deployment notification and force all users to clear cache
"""

import requests
import json
from datetime import datetime

def trigger_deployment_notification(message="System update deployed - clearing cache and refreshing news feed", version="1.0.0"):
    """Trigger deployment notification on production server"""
    
    # Production server URL
    url = "https://fxsentinel-production.up.railway.app/api/deployment-notification"
    
    # Data to send
    data = {
        "message": message,
        "version": version,
        "requires_cache_clear": True
    }
    
    try:
        print(f"🚀 Triggering deployment notification...")
        print(f"   Message: {message}")
        print(f"   Version: {version}")
        print(f"   Cache Clear: Required")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Deployment notification triggered successfully!")
            print(f"   Response: {result.get('message', 'Unknown')}")
            
            if 'force_refresh_result' in result:
                refresh_result = result['force_refresh_result']
                print(f"   Force Refresh: {refresh_result.get('articles_count', 0)} articles")
                print(f"   Refresh Status: {refresh_result.get('success', False)}")
            
            return True
        else:
            print(f"❌ Failed to trigger deployment notification")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error triggering deployment notification: {e}")
        return False

def clear_deployment_notification():
    """Clear deployment notification"""
    
    url = "https://fxsentinel-production.up.railway.app/api/clear-deployment-notification"
    
    try:
        print("🧹 Clearing deployment notification...")
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Deployment notification cleared successfully!")
            return True
        else:
            print(f"❌ Failed to clear deployment notification: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing deployment notification: {e}")
        return False

def check_deployment_status():
    """Check current deployment notification status"""
    
    url = "https://fxsentinel-production.up.railway.app/api/deployment-notification"
    
    try:
        print("🔍 Checking deployment notification status...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print("📊 Current Deployment Status:")
            print(f"   Active: {status.get('active', False)}")
            print(f"   Message: {status.get('message', 'None')}")
            print(f"   Version: {status.get('version', 'Unknown')}")
            print(f"   Timestamp: {status.get('timestamp', 'None')}")
            print(f"   Cache Clear Required: {status.get('requires_cache_clear', False)}")
            return status
        else:
            print(f"❌ Failed to check status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking deployment status: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "trigger":
            message = sys.argv[2] if len(sys.argv) > 2 else "System update deployed - clearing cache and refreshing news feed"
            version = sys.argv[3] if len(sys.argv) > 3 else "1.0.0"
            trigger_deployment_notification(message, version)
            
        elif command == "clear":
            clear_deployment_notification()
            
        elif command == "status":
            check_deployment_status()
            
        else:
            print("Usage:")
            print("  python3 trigger_deployment_notification.py trigger [message] [version]")
            print("  python3 trigger_deployment_notification.py clear")
            print("  python3 trigger_deployment_notification.py status")
    else:
        # Default: trigger deployment notification
        trigger_deployment_notification()
