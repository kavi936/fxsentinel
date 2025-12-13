#!/usr/bin/env python3
"""
Set up online monitoring using external cron service
"""

import requests
import json
from datetime import datetime

def setup_online_monitoring():
    """Set up online monitoring using external services"""
    print("🌐 Setting up Online 24/7 Monitoring")
    print("=" * 50)
    
    # The worker URL
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    main_app_url = "https://fxsentinel-production.up.railway.app"
    
    print("📋 Online Monitoring Options:")
    print()
    
    print("1️⃣ **Cron-job.org (Free)**")
    print("   - URL: https://cron-job.org")
    print("   - Set up a cron job to call this URL every minute:")
    print(f"   - URL: {worker_url}/api/trigger-alerts")
    print("   - Method: POST")
    print("   - Schedule: */1 * * * * (every minute)")
    print()
    
    print("2️⃣ **EasyCron (Free tier)**")
    print("   - URL: https://www.easycron.com")
    print("   - Set up a cron job with the same settings")
    print()
    
    print("3️⃣ **UptimeRobot (Free)**")
    print("   - URL: https://uptimerobot.com")
    print("   - Set up monitoring with POST requests")
    print()
    
    print("4️⃣ **GitHub Actions (Free)**")
    print("   - Create a workflow that runs every minute")
    print("   - Use the trigger-alerts endpoint")
    print()
    
    # Test the current setup
    print("🧪 Testing Current Setup:")
    print("=" * 30)
    
    try:
        response = requests.post(f"{worker_url}/api/trigger-alerts", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Worker trigger successful")
            print(f"   📊 News processed: {result.get('news_alerts_processed', False)}")
            print(f"   📊 Calendar processed: {result.get('calendar_alerts_processed', False)}")
            print(f"   📅 Timestamp: {result.get('timestamp', 'unknown')}")
        else:
            print(f"   ❌ Worker trigger failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("🎯 **Recommended Solution:**")
    print("   Use cron-job.org (free) to call the worker every minute:")
    print(f"   POST {worker_url}/api/trigger-alerts")
    print()
    print("   This will ensure 24/7 monitoring even when your computer is off!")

def create_github_workflow():
    """Create a GitHub Actions workflow for monitoring"""
    workflow_content = """name: FXSentinel Monitoring

on:
  schedule:
    - cron: '*/1 * * * *'  # Every minute
  workflow_dispatch:  # Allow manual trigger

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger FXSentinel Alerts
        run: |
          curl -X POST "https://fxsentinel-background-worker-v2-production.up.railway.app/api/trigger-alerts" \
            -H "Content-Type: application/json" \
            -w "\\nStatus: %{http_code}\\n"
        continue-on-error: true
      
      - name: Log Result
        run: echo "Monitoring check completed at $(date)"
"""
    
    print("📝 GitHub Actions Workflow:")
    print("=" * 30)
    print("Create a file: .github/workflows/monitor.yml")
    print("With this content:")
    print()
    print(workflow_content)

if __name__ == "__main__":
    setup_online_monitoring()
    print()
    create_github_workflow()
