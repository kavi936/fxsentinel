#!/usr/bin/env python3
"""
Comprehensive Alert System Diagnostic v2
Checks news alerts and economic calendar alerts
Compares what should be sent vs what is actually being sent
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_unified_processor_status():
    """Check if unified processor is running"""
    print("\n" + "="*80)
    print("1. UNIFIED PROCESSOR STATUS")
    print("="*80)
    
    try:
        from services.unified_alert_processor import get_unified_processor
        processor = get_unified_processor()
        status = processor.get_status()
        
        print(f"✅ Unified processor found")
        print(f"   Running: {status.get('running', False)}")
        print(f"   Thread alive: {status.get('thread_alive', False)}")
        print(f"   Last check: {status.get('last_check', 'Never')}")
        print(f"   Last economic calendar check: {status.get('last_economic_calendar_check', 'Never')}")
        print(f"   Last post-news check: {status.get('last_post_news_check', 'Never')}")
        
        if not status.get('running', False):
            print("⚠️  WARNING: Unified processor is not running!")
            return False
        
        return True
    except Exception as e:
        print(f"❌ ERROR: Could not check unified processor: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_news_alerts():
    """Check news alerts - what should be sent vs what is available"""
    print("\n" + "="*80)
    print("2. NEWS ALERTS DIAGNOSTIC")
    print("="*80)
    
    try:
        # Get news from cache
        from services.persistent_news_cache import get_persistent_news_cache
        news_cache = get_persistent_news_cache()
        cached_news = news_cache.load_news(allow_stale=True)
        
        if not cached_news:
            print("⚠️  No cached news found")
            return
        
        print(f"📰 Found {len(cached_news)} news items in cache")
        
        # Check which news items are high-impact
        from services.news_alert_trigger import news_alert_trigger
        
        high_impact = []
        for news_item in cached_news[:20]:  # Check first 20
            if news_alert_trigger.is_forex_high_impact(news_item):
                high_impact.append(news_item)
        
        print(f"🔥 Found {len(high_impact)} high-impact forex news items")
        
        if high_impact:
            print("\n📋 High-impact news items:")
            for i, item in enumerate(high_impact[:5], 1):
                title = item.get('title', 'Unknown')[:60]
                source = item.get('source', 'Unknown')
                timestamp = item.get('timestamp', 'Unknown')
                print(f"   {i}. {title}...")
                print(f"      Source: {source}, Time: {timestamp}")
        
        # Check deduplication
        from services.persistent_alert_deduplication import get_persistent_deduplication
        dedup = get_persistent_deduplication()
        
        print("\n🔍 Checking deduplication status:")
        new_items = []
        already_sent_items = []
        
        for news_item in high_impact[:5]:
            content_hash = dedup._get_news_content_hash(news_item)
            if content_hash:
                if dedup._check_global_content_hash(content_hash):
                    new_items.append(news_item)
                else:
                    already_sent_items.append(news_item)
        
        print(f"   ✅ New items (should send alerts): {len(new_items)}")
        print(f"   ❌ Already sent (should skip): {len(already_sent_items)}")
        
        # Check users
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        users = firebase.get_all_users_with_alerts()
        
        print(f"\n👥 Users with alerts enabled: {len(users) if users else 0}")
        
        if users:
            eligible_users = 0
            for user_data in users:
                user_id = user_data.get('user_id')
                user_settings = user_data.get('settings', {})
                
                # Check Telegram enabled
                telegram_enabled = (
                    user_settings.get('telegram_enabled', False) or
                    user_settings.get('telegram', False) or
                    user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                )
                
                # Check liveNews enabled
                preferences = user_settings.get('preferences', {})
                alert_types = preferences.get('alertTypes', {})
                live_news_enabled = alert_types.get('liveNews', True)
                
                if telegram_enabled and live_news_enabled:
                    eligible_users += 1
            
            print(f"   ✅ Eligible users (Telegram + liveNews enabled): {eligible_users}")
        
        # Summary
        print("\n📊 NEWS ALERTS SUMMARY:")
        if new_items and users:
            eligible_count = sum(1 for u in users if (
                (u.get('settings', {}).get('telegram_enabled', False) or
                 u.get('settings', {}).get('channels', {}).get('telegram', {}).get('enabled', False)) and
                u.get('settings', {}).get('preferences', {}).get('alertTypes', {}).get('liveNews', True)
            ))
            expected_alerts = len(new_items) * eligible_count
            print(f"   Expected alerts to send: {expected_alerts} ({len(new_items)} news × {eligible_count} users)")
        else:
            print("   ⚠️  No alerts should be sent (no new items or no eligible users)")
    
    except Exception as e:
        print(f"❌ ERROR checking news alerts: {e}")
        import traceback
        traceback.print_exc()

def check_economic_calendar_alerts():
    """Check economic calendar alerts - what should be sent vs what is available"""
    print("\n" + "="*80)
    print("3. ECONOMIC CALENDAR ALERTS DIAGNOSTIC")
    print("="*80)
    
    try:
        # Get economic calendar events
        from services.finnhub_calendar import finnhub_calendar
        events = finnhub_calendar.get_economic_calendar()
        
        if not events:
            print("⚠️  No economic calendar events found")
            return
        
        print(f"📅 Found {len(events)} economic calendar events")
        
        # Filter for high-impact upcoming events
        now = datetime.now()
        high_impact_upcoming = []
        
        for event in events:
            impact = event.get('impact', '').lower()
            status = event.get('status', '').upper()
            
            if impact == 'high' and status in ['UPCOMING', 'IMMINENT']:
                # Parse event datetime
                try:
                    time_str = event.get('time', '')
                    date_str = event.get('date', '')
                    
                    if time_str and date_str:
                        datetime_str = f"{date_str} {time_str}"
                        event_datetime = datetime.strptime(datetime_str, "%a, %b %d %H:%M UTC")
                        event_datetime = event_datetime.replace(year=now.year)
                        
                        # Adjust year if needed
                        if (now.date() - event_datetime.date()).days > 30:
                            event_datetime = event_datetime.replace(year=now.year + 1)
                        
                        time_until_event = event_datetime - now
                        minutes_until_event = time_until_event.total_seconds() / 60
                        
                        # Check if within alert timing windows
                        if (8 <= minutes_until_event <= 10 or      # 10min before
                            55 <= minutes_until_event <= 60 or    # 1h before
                            115 <= minutes_until_event <= 120):   # 2h before
                            
                            high_impact_upcoming.append({
                                'event': event,
                                'minutes_until': minutes_until_event,
                                'datetime': event_datetime
                            })
                except Exception as e:
                    logger.debug(f"Error parsing event datetime: {e}")
                    continue
        
        print(f"🔥 Found {len(high_impact_upcoming)} high-impact upcoming events within alert windows")
        
        if high_impact_upcoming:
            print("\n📋 Events that should trigger alerts:")
            for i, item in enumerate(high_impact_upcoming[:5], 1):
                event = item['event']
                title = event.get('title', 'Unknown')[:60]
                minutes = item['minutes_until']
                event_dt = item['datetime']
                
                # Determine alert timing
                if 8 <= minutes <= 10:
                    timing = "10min_before"
                elif 55 <= minutes <= 60:
                    timing = "1h_before"
                elif 115 <= minutes <= 120:
                    timing = "2h_before"
                else:
                    timing = "unknown"
                
                print(f"   {i}. {title}...")
                print(f"      Time: {event_dt.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"      Minutes until: {minutes:.1f} ({timing})")
        
        # Check users
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        users = firebase.get_all_users_with_alerts()
        
        print(f"\n👥 Users with alerts enabled: {len(users) if users else 0}")
        
        if users:
            eligible_users = 0
            for user_data in users:
                user_settings = user_data.get('settings', {})
                
                # Check Telegram enabled
                telegram_enabled = (
                    user_settings.get('telegram_enabled', False) or
                    user_settings.get('telegram', False) or
                    user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)
                )
                
                # Check preNews enabled
                preferences = user_settings.get('preferences', {})
                alert_types = preferences.get('alertTypes', {})
                pre_news_enabled = alert_types.get('preNews', True)  # Default to True
                
                if telegram_enabled and pre_news_enabled:
                    eligible_users += 1
            
            print(f"   ✅ Eligible users (Telegram + preNews enabled): {eligible_users}")
        
        # Summary
        print("\n📊 ECONOMIC CALENDAR ALERTS SUMMARY:")
        if high_impact_upcoming and users:
            eligible_count = sum(1 for u in users if (
                (u.get('settings', {}).get('telegram_enabled', False) or
                 u.get('settings', {}).get('channels', {}).get('telegram', {}).get('enabled', False)) and
                u.get('settings', {}).get('preferences', {}).get('alertTypes', {}).get('preNews', True)
            ))
            expected_alerts = len(high_impact_upcoming) * eligible_count
            print(f"   Expected alerts to send: {expected_alerts} ({len(high_impact_upcoming)} events × {eligible_count} users)")
        else:
            print("   ⚠️  No alerts should be sent (no events in windows or no eligible users)")
    
    except Exception as e:
        print(f"❌ ERROR checking economic calendar alerts: {e}")
        import traceback
        traceback.print_exc()

def check_recent_alert_history():
    """Check recent alert history to see what was actually sent"""
    print("\n" + "="*80)
    print("4. RECENT ALERT HISTORY")
    print("="*80)
    
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Get recent alert history (last 24 hours)
        alert_history_path = "alerts/alert_history"
        history = firebase._make_request('GET', alert_history_path)
        
        if not history:
            print("⚠️  No alert history found")
            return
        
        # Count alerts by type
        news_alerts = 0
        calendar_alerts = 0
        recent_alerts = []
        
        now = datetime.now()
        for alert_id, alert_data in history.items():
            if isinstance(alert_data, dict):
                alert_type = alert_data.get('type', 'unknown')
                timestamp_str = alert_data.get('timestamp', '')
                
                if timestamp_str:
                    try:
                        alert_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        hours_ago = (now - alert_time.replace(tzinfo=None)).total_seconds() / 3600
                        
                        if hours_ago <= 24:  # Last 24 hours
                            if alert_type == 'liveNews':
                                news_alerts += 1
                            elif alert_type == 'calendar':
                                calendar_alerts += 1
                            
                            recent_alerts.append({
                                'type': alert_type,
                                'time': alert_time,
                                'hours_ago': hours_ago
                            })
                    except:
                        pass
        
        print(f"📊 Alerts sent in last 24 hours:")
        print(f"   News alerts: {news_alerts}")
        print(f"   Calendar alerts: {calendar_alerts}")
        print(f"   Total: {len(recent_alerts)}")
        
        if recent_alerts:
            print("\n📋 Recent alerts (last 5):")
            recent_alerts.sort(key=lambda x: x['time'], reverse=True)
            for i, alert in enumerate(recent_alerts[:5], 1):
                print(f"   {i}. {alert['type']} - {alert['hours_ago']:.1f} hours ago")
        else:
            print("   ⚠️  No alerts sent in last 24 hours")
    
    except Exception as e:
        print(f"❌ ERROR checking alert history: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run comprehensive diagnostic"""
    print("\n" + "="*80)
    print("COMPREHENSIVE ALERT SYSTEM DIAGNOSTIC v2")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check unified processor
    processor_running = check_unified_processor_status()
    
    # Check news alerts
    check_news_alerts()
    
    # Check economic calendar alerts
    check_economic_calendar_alerts()
    
    # Check recent alert history
    check_recent_alert_history()
    
    # Final summary
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)
    
    if not processor_running:
        print("\n⚠️  CRITICAL: Unified processor is not running!")
        print("   Alerts will not be sent. Check app startup logs.")
    else:
        print("\n✅ Unified processor is running")
        print("   Check the summaries above to see if alerts should be sent.")

if __name__ == '__main__':
    main()

