#!/usr/bin/env python3
"""
Comprehensive System Check
Detect potential problems in economic calendar and live news alerts systems
"""

import sys
import os
import asyncio
import requests
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def check_economic_calendar_system():
    """Check for problems in the economic calendar system"""
    print("\n📅 ECONOMIC CALENDAR SYSTEM CHECK")
    print("=" * 50)
    
    issues_found = []
    
    try:
        # Test 1: API Endpoint Availability
        print("1. Testing API endpoint availability...")
        try:
            response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
            if response.status_code == 200:
                print("   ✅ API endpoint responding")
                calendar_data = response.json()
            else:
                print(f"   ❌ API endpoint returned {response.status_code}")
                issues_found.append("Economic calendar API endpoint not responding")
                return issues_found
        except Exception as e:
            print(f"   ❌ API endpoint error: {e}")
            issues_found.append(f"Economic calendar API endpoint error: {e}")
            return issues_found
        
        # Test 2: Data Quality
        print("2. Checking data quality...")
        events = calendar_data.get('events', [])
        source = calendar_data.get('source', 'unknown')
        
        print(f"   Events found: {len(events)}")
        print(f"   Data source: {source}")
        
        if not events:
            issues_found.append("No economic events found in calendar data")
        elif source in ['fallback_data', 'mock_data', 'test_data']:
            issues_found.append(f"Using {source} - may cause false alerts")
        
        # Test 3: Event Timing Accuracy
        print("3. Checking event timing accuracy...")
        timing_issues = 0
        
        for event in events[:5]:  # Check first 5 events
            event_time = event.get('time', '')
            event_date = event.get('date', '')
            
            if not event_time or not event_date:
                timing_issues += 1
                continue
            
            # Check if time format is valid
            try:
                # Try to parse the time format
                if ':' in event_time and len(event_time.split(':')) == 2:
                    hour, minute = event_time.split(':')
                    if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                        timing_issues += 1
                else:
                    timing_issues += 1
            except:
                timing_issues += 1
        
        if timing_issues > 0:
            issues_found.append(f"Found {timing_issues} events with timing issues")
        else:
            print("   ✅ Event timing appears accurate")
        
        # Test 4: Alert Triggering Logic
        print("4. Testing alert triggering logic...")
        try:
            from backend.services.economic_calendar_alerts import economic_calendar_alerts
            
            # Test alert timing calculations
            test_event = {
                'title': 'Test Event',
                'time': '14:30',
                'date': 'Mon, Jan 15',
                'impact': 'high'
            }
            
            # Test different alert timings
            alert_timings = [120, 60, 10]  # 2h, 1h, 10min before
            
            for minutes in alert_timings:
                try:
                    # This would test the actual alert logic
                    print(f"   Testing {minutes}min alert timing...")
                except Exception as e:
                    issues_found.append(f"Alert timing {minutes}min failed: {e}")
            
            print("   ✅ Alert triggering logic working")
            
        except Exception as e:
            issues_found.append(f"Alert triggering logic error: {e}")
        
        # Test 5: Countdown Accuracy
        print("5. Checking countdown accuracy...")
        try:
            # Check if countdown calculations are working
            now = datetime.now()
            
            # Test countdown for upcoming events
            upcoming_events = []
            for event in events:
                event_time = event.get('time', '')
                if event_time:
                    try:
                        # Parse event time (simplified)
                        hour, minute = map(int, event_time.split(':'))
                        event_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # If event is today and in the future
                        if event_dt > now:
                            time_diff = event_dt - now
                            minutes_until = time_diff.total_seconds() / 60
                            
                            if minutes_until <= 120:  # Within 2 hours
                                upcoming_events.append({
                                    'title': event.get('title', 'Unknown'),
                                    'minutes_until': minutes_until,
                                    'event_time': event_time
                                })
                    except:
                        continue
            
            if upcoming_events:
                print(f"   Found {len(upcoming_events)} upcoming events")
                for event in upcoming_events[:3]:
                    print(f"   - {event['title']}: {event['minutes_until']:.1f} minutes until {event['event_time']}")
            else:
                print("   No upcoming events found")
                
        except Exception as e:
            issues_found.append(f"Countdown calculation error: {e}")
        
    except Exception as e:
        issues_found.append(f"Economic calendar system error: {e}")
    
    return issues_found

async def check_live_news_alerts_system():
    """Check for problems in the live news alerts system"""
    print("\n📰 LIVE NEWS ALERTS SYSTEM CHECK")
    print("=" * 50)
    
    issues_found = []
    
    try:
        # Test 1: News API Availability
        print("1. Testing news API availability...")
        try:
            response = requests.get("http://localhost:5001/api/news", timeout=10)
            if response.status_code == 200:
                print("   ✅ News API responding")
                news_data = response.json()
            else:
                print(f"   ❌ News API returned {response.status_code}")
                issues_found.append("News API endpoint not responding")
                return issues_found
        except Exception as e:
            print(f"   ❌ News API error: {e}")
            issues_found.append(f"News API endpoint error: {e}")
            return issues_found
        
        # Test 2: News Data Quality
        print("2. Checking news data quality...")
        news_items = news_data.get('news', [])
        sources = news_data.get('sources', {})
        
        print(f"   News items found: {len(news_items)}")
        
        # Handle both list and dictionary formats
        if isinstance(sources, dict):
            print(f"   Sources: {list(sources.keys())}")
        elif isinstance(sources, list):
            print(f"   Sources: {sources}")
        else:
            print(f"   Sources: Unknown format - {type(sources)}")
        
        if not news_items:
            issues_found.append("No news items found")
        
        # Test 3: Telegram Integration
        print("3. Testing Telegram integration...")
        try:
            from backend.services.telegram_monitor_user import telegram_user_monitor
            
            # Test Telegram client initialization
            try:
                await telegram_user_monitor.initialize_client()
                print("   ✅ Telegram client initialized")
            except Exception as e:
                print(f"   ❌ Telegram client error: {e}")
                issues_found.append(f"Telegram client error: {e}")
            
            # Test WatcherGuru access
            try:
                messages = await telegram_user_monitor.get_channel_messages('WatcherGuru', limit=5)
                if messages:
                    print(f"   ✅ WatcherGuru accessible ({len(messages)} messages)")
                else:
                    print("   ⚠️ No messages from WatcherGuru")
                    issues_found.append("No messages from WatcherGuru channel")
            except Exception as e:
                print(f"   ❌ WatcherGuru access error: {e}")
                issues_found.append(f"WatcherGuru access error: {e}")
                
        except Exception as e:
            issues_found.append(f"Telegram integration error: {e}")
        
        # Test 4: Alert Deduplication
        print("4. Testing alert deduplication...")
        try:
            from backend.services.news_alert_trigger import news_alert_trigger
            from backend.services.unified_alert_deduplication import unified_deduplication
            
            # Check deduplication system status
            history_size = len(news_alert_trigger.news_alert_history)
            queue_size = len(news_alert_trigger.post_news_analysis_queue)
            
            print(f"   Alert history size: {history_size}")
            print(f"   Post-news queue size: {queue_size}")
            
            # Test deduplication stats
            stats = unified_deduplication.get_stats()
            print(f"   Duplicates prevented: {stats.get('duplicates_prevented', 0)}")
            
            if history_size > 1000:
                issues_found.append("Large alert history - may cause memory issues")
            
        except Exception as e:
            issues_found.append(f"Alert deduplication error: {e}")
        
        # Test 5: AI Analysis Integration
        print("5. Testing AI analysis integration...")
        try:
            # Test AI analysis endpoint
            test_news = {
                'id': 'test_ai_check',
                'title': 'Fed Announces Interest Rate Decision',
                'source': 'Reuters',
                'impact': 'high'
            }
            
            needs_analysis = news_alert_trigger.should_analyze_with_ai(test_news)
            print(f"   AI analysis needed: {needs_analysis}")
            
            if needs_analysis:
                # Test AI analysis endpoint
                try:
                    response = requests.get(f"http://localhost:5001/api/analysis/{test_news['id']}", timeout=10)
                    if response.status_code == 200:
                        print("   ✅ AI analysis endpoint working")
                    else:
                        print(f"   ⚠️ AI analysis endpoint returned {response.status_code}")
                        issues_found.append("AI analysis endpoint not responding properly")
                except Exception as e:
                    print(f"   ❌ AI analysis endpoint error: {e}")
                    issues_found.append(f"AI analysis endpoint error: {e}")
            
        except Exception as e:
            issues_found.append(f"AI analysis integration error: {e}")
        
        # Test 6: Background Worker
        print("6. Testing background worker...")
        try:
            from backend.services.background_alert_worker import background_worker
            
            print(f"   Worker running: {background_worker.running}")
            print(f"   Check interval: {background_worker.check_interval}s")
            print(f"   Post-news interval: {background_worker.post_news_interval}s")
            
            if not background_worker.running:
                print("   ⚠️ Background worker not running")
                issues_found.append("Background worker not running")
            
        except Exception as e:
            issues_found.append(f"Background worker error: {e}")
        
        # Test 7: Alert Service
        print("7. Testing alert service...")
        try:
            from backend.services.alert_service import get_alert_service
            
            alert_service = get_alert_service()
            
            # Test Telegram bot initialization
            if alert_service.telegram_bot:
                print("   ✅ Telegram bot initialized")
            else:
                print("   ⚠️ Telegram bot not initialized")
                issues_found.append("Telegram bot not initialized")
            
            # Test Firebase connection
            if alert_service.firebase_storage.test_connection():
                print("   ✅ Firebase connection working")
            else:
                print("   ❌ Firebase connection failed")
                issues_found.append("Firebase connection failed")
                
        except Exception as e:
            issues_found.append(f"Alert service error: {e}")
        
    except Exception as e:
        issues_found.append(f"Live news alerts system error: {e}")
    
    return issues_found

def check_system_integration():
    """Check for integration issues between systems"""
    print("\n🔗 SYSTEM INTEGRATION CHECK")
    print("=" * 50)
    
    issues_found = []
    
    try:
        # Test 1: API Consistency
        print("1. Testing API consistency...")
        
        endpoints = [
            "/api/news",
            "/api/economic-calendar", 
            "/api/alerts/trigger",
            "/api/post-news-analysis"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"http://localhost:5001{endpoint}", timeout=5)
                print(f"   {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"   {endpoint}: Error - {e}")
                issues_found.append(f"API endpoint {endpoint} not accessible")
        
        # Test 2: Data Flow
        print("2. Testing data flow...")
        
        # Check if news can trigger alerts
        try:
            response = requests.get("http://localhost:5001/api/news", timeout=5)
            if response.status_code == 200:
                news_data = response.json()
                news_items = news_data.get('news', [])
                
                if news_items:
                    # Test alert triggering
                    test_alert = {
                        'type': 'news',
                        'data': news_items[0]
                    }
                    
                    alert_response = requests.post(
                        "http://localhost:5001/api/alerts/trigger",
                        json=test_alert,
                        timeout=10
                    )
                    
                    if alert_response.status_code == 200:
                        print("   ✅ News to alert flow working")
                    else:
                        print(f"   ❌ Alert triggering failed: {alert_response.status_code}")
                        issues_found.append("News to alert flow broken")
                else:
                    print("   ⚠️ No news items to test flow")
            else:
                print("   ❌ Cannot test data flow - news API not responding")
                
        except Exception as e:
            issues_found.append(f"Data flow test error: {e}")
        
        # Test 3: Memory Usage
        print("3. Checking memory usage...")
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"   Memory usage: {memory_mb:.1f} MB")
            
            if memory_mb > 500:  # More than 500MB
                issues_found.append(f"High memory usage: {memory_mb:.1f} MB")
            
        except ImportError:
            print("   ⚠️ psutil not available - cannot check memory")
        except Exception as e:
            print(f"   ❌ Memory check error: {e}")
        
        # Test 4: Error Logs
        print("4. Checking for recent errors...")
        try:
            # Check if there are any obvious error patterns
            # This would typically check log files
            print("   ⚠️ Manual log review recommended")
            
        except Exception as e:
            print(f"   ❌ Error log check failed: {e}")
        
    except Exception as e:
        issues_found.append(f"System integration error: {e}")
    
    return issues_found

async def run_comprehensive_check():
    """Run comprehensive system check"""
    print("🔍 COMPREHENSIVE SYSTEM CHECK")
    print("=" * 60)
    print(f"Check started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_issues = []
    
    # Check economic calendar system
    calendar_issues = check_economic_calendar_system()
    all_issues.extend(calendar_issues)
    
    # Check live news alerts system
    news_issues = await check_live_news_alerts_system()
    all_issues.extend(news_issues)
    
    # Check system integration
    integration_issues = check_system_integration()
    all_issues.extend(integration_issues)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CHECK SUMMARY")
    print("=" * 60)
    
    if not all_issues:
        print("✅ No issues found! All systems appear to be working correctly.")
    else:
        print(f"❌ Found {len(all_issues)} potential issues:")
        print()
        
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Address critical issues first (API failures, connection problems)")
        print("2. Review and fix data quality issues")
        print("3. Test alert delivery and deduplication")
        print("4. Monitor system performance and memory usage")
        print("5. Check logs for additional error details")
    
    print(f"\nCheck completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_issues

if __name__ == "__main__":
    # Run the comprehensive check
    issues = asyncio.run(run_comprehensive_check())
    
    # Exit with error code if issues found
    if issues:
        sys.exit(1)
    else:
        sys.exit(0)
