#!/usr/bin/env python3
"""
Check Why Live News Alerts Weren't Sent
Diagnose the news → alert pipeline
"""

import os
import sys
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

print("=" * 80)
print("LIVE NEWS ALERTS - DIAGNOSIS")
print("=" * 80)
print(f"Analysis Time: {datetime.now()}")
print()

# Check 1: Get recent news from the feed
print("1. Checking Live News Feed...")
print("─" * 80)

try:
    response = requests.get("http://localhost:5001/api/news", timeout=10)
    
    if response.status_code == 200:
        news_data = response.json()
        
        if isinstance(news_data, dict) and 'news' in news_data:
            news_items = news_data['news']
        elif isinstance(news_data, list):
            news_items = news_data
        else:
            news_items = []
        
        print(f"   ✅ News feed accessible")
        print(f"   Total items: {len(news_items)}")
        print()
        
        if news_items:
            print("   Recent news items:")
            for i, item in enumerate(news_items[:10], 1):
                title = item.get('title', 'Unknown')[:60]
                source = item.get('source', 'Unknown')
                time = item.get('time', item.get('timestamp', 'Unknown'))
                impact = item.get('impact', 'unknown')
                
                print(f"   {i}. {title}...")
                print(f"      Source: {source} | Time: {time} | Impact: {impact}")
            
            print()
            
            # Count by impact
            high_impact = [i for i in news_items if 'high' in str(i.get('impact', '')).lower()]
            medium_impact = [i for i in news_items if 'medium' in str(i.get('impact', '')).lower()]
            
            print(f"   Impact Breakdown:")
            print(f"   ├─ High impact: {len(high_impact)}")
            print(f"   ├─ Medium impact: {len(medium_impact)}")
            print(f"   └─ Low/Unknown: {len(news_items) - len(high_impact) - len(medium_impact)}")
            print()
            
            if high_impact:
                print(f"   🔴 {len(high_impact)} HIGH IMPACT news items found!")
                print(f"   These SHOULD have triggered alerts!")
                print()
        else:
            print("   ⚠️  No news items in feed")
    else:
        print(f"   ❌ News API error: HTTP {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Cannot connect to news API: {e}")

print()

# Check 2: Is the background worker running?
print("2. Checking Background Worker Status...")
print("─" * 80)

# Check locally
try:
    from services.production_alert_worker import get_production_worker
    
    worker = get_production_worker()
    status = worker.get_status()
    
    print(f"   Local Worker Status:")
    print(f"   ├─ Running: {status['running']}")
    print(f"   ├─ Thread alive: {status['thread_alive']}")
    print(f"   ├─ Alerts sent: {status['alerts_sent']}")
    print(f"   └─ Last news check: {status['last_news_check']}")
    print()
    
    if not status['running']:
        print("   ⚠️  LOCAL worker is NOT running")
        print("   This is expected - we need the RAILWAY worker to run")
    
except Exception as e:
    print(f"   ℹ️  Local worker check: {e}")

print()

# Check Railway worker via API
print("   Checking RAILWAY worker via health endpoint...")
try:
    response = requests.get("http://localhost:5001/api/health/alerts", timeout=10)
    
    if response.status_code == 200:
        health = response.json()
        
        print(f"   Health Check Results:")
        print(f"   ├─ Overall status: {health.get('status', 'Unknown')}")
        print(f"   ├─ Alerts working: {health.get('alerts_working', False)}")
        print(f"   ├─ Message: {health.get('message', 'N/A')}")
        print()
        
        bg_worker = health.get('background_worker', {})
        if bg_worker:
            print(f"   Background Worker Details:")
            print(f"   ├─ Running: {bg_worker.get('running', False)}")
            print(f"   ├─ Thread alive: {bg_worker.get('thread_alive', False)}")
            print(f"   └─ Message: {bg_worker.get('status_message', 'N/A')}")
            print()
            
            if not bg_worker.get('running'):
                print("   🚨 FOUND THE ISSUE!")
                print("   ═══════════════════════════════════════")
                print("   Background worker is NOT running!")
                print()
                print("   This is WHY you're not receiving alerts:")
                print("   • Worker checks news every 2 minutes")
                print("   • Worker sends alerts to users")
                print("   • If worker isn't running, NO alerts are sent")
                print()
                print("   FIX:")
                print("   1. Go to Railway dashboard")
                print("   2. Find your 'Background Worker' service")
                print("   3. Check if it's deployed and running")
                print("   4. Check logs for errors")
                print("   5. Redeploy if needed")
        
except Exception as e:
    print(f"   ⚠️  Health check failed: {e}")

print()

# Check 3: Check alert deduplication state
print("3. Checking Alert Deduplication...")
print("─" * 80)

try:
    from services.alert_deduplication import get_deduplication_stats
    
    stats = get_deduplication_stats()
    
    print(f"   Deduplication Stats:")
    print(f"   ├─ Total checks: {stats['total_checks']}")
    print(f"   ├─ Duplicates prevented: {stats['duplicates_prevented']}")
    print(f"   ├─ Processed alerts: {stats['processed_alerts_count']}")
    print(f"   └─ Economic alerts: {stats['economic_alerts_count']}")
    print()
    
    if stats['duplicates_prevented'] > 0:
        print(f"   ℹ️  {stats['duplicates_prevented']} duplicates were prevented")
        print(f"   This is good - prevents spam")
    
except Exception as e:
    print(f"   ⚠️  Cannot check deduplication: {e}")

print()

# Summary
print("=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)
print()

print("MOST LIKELY CAUSE:")
print("  The Railway background worker is NOT running")
print()
print("HOW TO VERIFY:")
print("  1. Go to: https://railway.app")
print("  2. Click your project → Background Worker service")
print("  3. Check 'Deployments' tab - should show recent deployment")
print("  4. Check 'Logs' tab - should show activity every 2-5 minutes")
print()
print("WHAT TO LOOK FOR IN LOGS:")
print("  ✅ '📊 Worker main loop started'")
print("  ✅ '📰 Checking for news alerts...'")
print("  ✅ '📅 Checking for economic calendar alerts...'")
print("  ✅ '💓 Heartbeat: Uptime XXs, Alerts sent: X'")
print()
print("IF NOT RUNNING:")
print("  → Click 'Redeploy' button")
print("  → Wait 2-3 minutes")
print("  → Check logs again")
print()

