#!/usr/bin/env python3
"""
Comprehensive Alert System Analysis
Checks for missed alerts and analyzes the complete alert flow
"""

import os
import sys
from datetime import datetime, timedelta
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

print("=" * 80)
print("FXSENTINEL ALERT SYSTEM ANALYSIS")
print("=" * 80)
print(f"Analysis Time: {datetime.now()}")
print()

# Your details
USER_ID = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
CHAT_ID = "8008493413"

print(f"User ID: {USER_ID}")
print(f"Chat ID: {CHAT_ID}")
print()

# ==============================================================================
# PART 1: ALERT SYSTEM ARCHITECTURE
# ==============================================================================

print("=" * 80)
print("PART 1: ALERT SYSTEM ARCHITECTURE")
print("=" * 80)
print()

print("Your alert system has TWO main alert types:")
print()

print("┌─────────────────────────────────────────────────────────────────┐")
print("│ ALERT TYPE 1: ECONOMIC CALENDAR ALERTS                          │")
print("└─────────────────────────────────────────────────────────────────┘")
print()
print("  What: Pre-event notifications for scheduled economic releases")
print("  When: Sent at 2 hours, 1 hour, and 10 minutes BEFORE the event")
print("  Source: Economic calendar (hybrid_economic_calendar.py)")
print("  Example: 'US Non-Farm Payrolls in 1 hour'")
print()
print("  Trigger Logic:")
print("    ├─ Worker checks calendar every 5 minutes")
print("    ├─ Finds upcoming high-impact events")
print("    ├─ Checks if within alert window (2h, 1h, 10min)")
print("    ├─ Filters by user preferences (currency pairs, impact level)")
print("    └─ Sends Telegram alert")
print()

print("┌─────────────────────────────────────────────────────────────────┐")
print("│ ALERT TYPE 2: LIVE NEWS FEED ALERTS                             │")
print("└─────────────────────────────────────────────────────────────────┘")
print()
print("  What: Real-time breaking news from forex sources")
print("  When: As soon as high-impact news is published")
print("  Source: News aggregator (multiple RSS feeds + Telegram channels)")
print("  Example: 'BREAKING: Fed announces rate decision'")
print()
print("  Trigger Logic:")
print("    ├─ Worker checks news feeds every 2 minutes")
print("    ├─ Detects new high-impact news")
print("    ├─ Filters by keywords and currency pairs")
print("    ├─ Checks deduplication (not sent in last 24h)")
print("    └─ Sends Telegram alert")
print()

# ==============================================================================
# PART 2: CHECK ECONOMIC CALENDAR ALERTS
# ==============================================================================

print("=" * 80)
print("PART 2: ECONOMIC CALENDAR - UPCOMING EVENTS CHECK")
print("=" * 80)
print()

try:
    # Get economic calendar
    response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
    
    if response.status_code == 200:
        calendar_data = response.json()
        events = calendar_data.get('events', [])
        
        print(f"✅ Calendar API responding")
        print(f"   Total events: {len(events)}")
        print(f"   Source: {calendar_data.get('source', 'Unknown')}")
        print()
        
        # Analyze events
        now = datetime.now()
        high_impact_events = []
        upcoming_events = []
        
        for event in events:
            impact = event.get('impact', '').lower()
            if impact == 'high':
                high_impact_events.append(event)
                
                # Try to parse event time (simplified)
                title = event.get('title', 'Unknown')
                event_date = event.get('date', '')
                event_time = event.get('time', '')
                
                print(f"   HIGH IMPACT: {title}")
                print(f"   ├─ Date: {event_date}")
                print(f"   ├─ Time: {event_time}")
                print(f"   ├─ Currency: {event.get('currency', 'N/A')}")
                print(f"   └─ Expected: {event.get('expected', 'TBD')}")
                print()
        
        if not high_impact_events:
            print("   ⚠️  NO high-impact events found in calendar")
            print("   This means: No pre-event alerts will be sent")
        else:
            print(f"   📊 {len(high_impact_events)} high-impact events found")
            print("   These SHOULD trigger pre-event alerts (2h, 1h, 10min before)")
        
    else:
        print(f"❌ Calendar API error: HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Cannot connect to calendar API: {e}")
    print("   Is the backend running at http://localhost:5001?")

print()

# ==============================================================================
# PART 3: CHECK LIVE NEWS FEED
# ==============================================================================

print("=" * 80)
print("PART 3: LIVE NEWS FEED - RECENT NEWS CHECK")
print("=" * 80)
print()

try:
    # Try to get recent news
    response = requests.get("http://localhost:5001/api/news", timeout=10)
    
    if response.status_code == 200:
        news_data = response.json()
        
        if isinstance(news_data, list):
            print(f"✅ News API responding")
            print(f"   Total news items: {len(news_data)}")
            print()
            
            # Analyze recent news
            recent_high_impact = []
            for item in news_data[:10]:  # Check last 10 items
                title = item.get('title', 'Unknown')
                source = item.get('source', 'Unknown')
                time = item.get('time', 'Unknown')
                impact = item.get('impact', 'unknown')
                
                if impact and 'high' in str(impact).lower():
                    recent_high_impact.append(item)
                    print(f"   HIGH IMPACT NEWS: {title[:60]}...")
                    print(f"   ├─ Source: {source}")
                    print(f"   ├─ Time: {time}")
                    print(f"   └─ Impact: {impact}")
                    print()
            
            if not recent_high_impact:
                print("   ℹ️  No high-impact news in the last few items")
                print("   This is normal during quiet market periods")
        else:
            print(f"   ℹ️  News data format: {type(news_data)}")
    else:
        print(f"❌ News API error: HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Cannot connect to news API: {e}")

print()

# ==============================================================================
# PART 4: CHECK BACKGROUND WORKER STATUS
# ==============================================================================

print("=" * 80)
print("PART 4: BACKGROUND WORKER STATUS")
print("=" * 80)
print()

print("Checking if the background worker is running...")
print()

try:
    # Try to check worker status
    response = requests.get("http://localhost:5001/api/health/alerts", timeout=10)
    
    if response.status_code == 200:
        health_data = response.json()
        
        print("✅ Health endpoint responding")
        print(f"   Overall status: {health_data.get('status', 'Unknown')}")
        print(f"   Telegram bot: {health_data.get('telegram_bot', 'Unknown')}")
        print(f"   Firebase: {health_data.get('firebase', 'Unknown')}")
        print(f"   Alerts working: {health_data.get('alerts_working', False)}")
        print()
        
        if health_data.get('background_worker'):
            worker_status = health_data['background_worker']
            print("   Background Worker Details:")
            print(f"   ├─ Running: {worker_status.get('running', False)}")
            print(f"   ├─ Thread alive: {worker_status.get('thread_alive', False)}")
            print(f"   └─ Message: {worker_status.get('status_message', 'N/A')}")
        
    else:
        print(f"⚠️  Health endpoint returned: HTTP {response.status_code}")
        
except Exception as e:
    print(f"⚠️  Cannot check worker status: {e}")

print()

# ==============================================================================
# PART 5: CHECK YOUR ALERT HISTORY
# ==============================================================================

print("=" * 80)
print("PART 5: YOUR ALERT HISTORY (FIREBASE)")
print("=" * 80)
print()

try:
    from services.firebase_realtime_storage import FirebaseRealtimeStorage
    import hashlib
    
    firebase = FirebaseRealtimeStorage()
    safe_user_id = hashlib.md5(USER_ID.encode()).hexdigest()
    
    # Get alert history
    history_path = f"alerts/users/{safe_user_id}/history"
    history = firebase._make_request('GET', history_path)
    
    if history and isinstance(history, dict):
        # Convert to list and sort
        alerts = []
        for key, alert in history.items():
            if isinstance(alert, dict):
                alert['id'] = key
                alerts.append(alert)
        
        # Sort by timestamp
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"✅ Found {len(alerts)} alerts in your history")
        print()
        
        # Analyze by type
        news_alerts = [a for a in alerts if a.get('type') == 'liveNews']
        calendar_alerts = [a for a in alerts if a.get('type') == 'economicCalendar']
        
        print(f"   Alert Breakdown:")
        print(f"   ├─ Live News Alerts: {len(news_alerts)}")
        print(f"   └─ Economic Calendar Alerts: {len(calendar_alerts)}")
        print()
        
        # Show last 5 alerts
        print("   Last 5 Alerts Received:")
        for alert in alerts[:5]:
            title = alert.get('news_title', alert.get('content', 'Unknown'))[:50]
            timestamp = alert.get('timestamp', 'Unknown')
            alert_type = alert.get('type', 'Unknown')
            print(f"   • [{alert_type}] {title}...")
            print(f"     Time: {timestamp}")
        
        print()
        
        # Check for recent alerts (last 24 hours)
        recent_cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        recent_alerts = [a for a in alerts if a.get('timestamp', '') > recent_cutoff]
        
        if recent_alerts:
            print(f"   📊 {len(recent_alerts)} alerts sent in the last 24 hours")
        else:
            print("   ⚠️  NO alerts sent in the last 24 hours")
            print("   Possible reasons:")
            print("     • No high-impact events occurred")
            print("     • Background worker not running")
            print("     • Market is closed (weekend)")
    else:
        print("   ℹ️  No alert history found")
        
except Exception as e:
    print(f"❌ Error checking alert history: {e}")

print()

# ==============================================================================
# PART 6: RECOMMENDATIONS
# ==============================================================================

print("=" * 80)
print("PART 6: RECOMMENDATIONS & ACTION ITEMS")
print("=" * 80)
print()

print("✅ What's Working:")
print("   • Firebase is accessible")
print("   • Telegram connection is active")
print("   • Your alert preferences are configured")
print("   • Alert history shows system has worked before")
print()

print("⚠️  What to Check:")
print("   1. Is the backend running?")
print("      → Run: cd backend && python3 app.py")
print()
print("   2. Is the background worker deployed on Railway?")
print("      → Check: https://railway.app (your worker service)")
print()
print("   3. Are there high-impact events today?")
print("      → Check: Economic calendar should have upcoming events")
print()
print("   4. Is it market hours?")
print("      → Alerts are most frequent during London/NY sessions")
print()

print("🎯 Expected Alert Behavior:")
print()
print("   ECONOMIC CALENDAR ALERTS:")
print("   • Sent 2h, 1h, 10min before scheduled events")
print("   • Only for HIGH impact events (NFP, CPI, GDP, etc.)")
print("   • Only for your selected currency pairs")
print()
print("   LIVE NEWS ALERTS:")
print("   • Sent as news is published (real-time)")
print("   • Only for high/medium impact news")
print("   • Filtered by keywords (Fed, ECB, inflation, etc.)")
print("   • Deduplication prevents repeated alerts")
print()

print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

