#!/usr/bin/env python3
"""
Evaluate Alert System - Check why no alerts are being sent
Focuses on: worker status, news availability, deduplication, user settings
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_news_availability():
    """Check if there's new news available"""
    print_section("1. NEWS AVAILABILITY CHECK")
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        news_cache = get_persistent_news_cache()
        
        # Get cached news
        cached_news = news_cache.get_cached_news()
        
        print(f"Total cached news items: {len(cached_news)}")
        
        if cached_news:
            # Check most recent
            most_recent = cached_news[0]
            title = most_recent.get('title', 'Unknown')
            added_at = most_recent.get('added_to_feed_at') or most_recent.get('timestamp', '')
            
            print(f"\nMost recent news:")
            print(f"  Title: {title[:70]}")
            print(f"  Added at: {added_at}")
            
            # Check age
            try:
                if added_at:
                    if 'T' in str(added_at):
                        news_time = datetime.fromisoformat(str(added_at).replace('Z', '+00:00'))
                    else:
                        news_time = datetime.fromisoformat(str(added_at))
                    now = datetime.now(news_time.tzinfo) if news_time.tzinfo else datetime.now()
                    age = now - news_time
                    hours = age.total_seconds() / 3600
                    
                    print(f"  Age: {hours:.1f} hours")
                    
                    if hours < 1:
                        print("  ✅ News is recent (less than 1 hour old)")
                    elif hours < 12:
                        print(f"  ⚠️  News is {hours:.1f} hours old")
                    else:
                        print(f"  ❌ News is stale ({hours:.1f} hours old)")
            except Exception as e:
                print(f"  ⚠️  Could not parse timestamp: {e}")
            
            # Check if should fetch new news
            should_fetch = news_cache.should_fetch_new_news()
            print(f"\nShould fetch new news: {should_fetch}")
            
            if not should_fetch:
                last_fetch = news_cache.get_last_fetch_time()
                print(f"Last fetch time: {last_fetch}")
        else:
            print("❌ No news in cache")
        
        return cached_news
        
    except Exception as e:
        print(f"❌ Error checking news: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_deduplication():
    """Check deduplication state"""
    print_section("2. DEDUPLICATION CHECK")
    try:
        from services.persistent_alert_deduplication import get_persistent_deduplication
        dedup = get_persistent_deduplication()
        
        # Check recent deduplication entries
        print("Checking deduplication service...")
        
        # Try to get some stats (if available)
        print("✅ Deduplication service accessible")
        print("   (Detailed stats require Firebase access)")
        
        return True
    except Exception as e:
        print(f"❌ Error checking deduplication: {e}")
        return False

def check_user_settings():
    """Check user alert settings"""
    print_section("3. USER SETTINGS CHECK")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        users = firebase.get_all_users_with_alerts()
        
        if not users:
            print("❌ No users found with alerts enabled")
            return []
        
        print(f"✅ Found {len(users)} users with alerts enabled")
        
        # Check first user's settings
        if len(users) > 0:
            user = users[0]
            user_id = user.get('user_id', 'Unknown')
            settings = user.get('settings', {})
            
            print(f"\nSample user (ID: {user_id[:12]}...):")
            
            # Telegram settings
            channels = settings.get('channels', {})
            telegram = channels.get('telegram', {})
            if telegram.get('enabled'):
                print(f"  ✅ Telegram enabled")
                print(f"  Chat ID: {telegram.get('chatId', 'Not set')}")
            else:
                print(f"  ❌ Telegram disabled")
            
            # Alert types
            preferences = settings.get('preferences', {})
            alert_types = preferences.get('alertTypes', {})
            print(f"\n  Alert Types:")
            print(f"    Live News: {alert_types.get('liveNews', False)}")
            print(f"    Pre-News: {alert_types.get('preNews', False)}")
            print(f"    Post-News: {alert_types.get('postNews', False)}")
            
            # Impact levels
            impact_levels = preferences.get('impactLevels', {})
            print(f"\n  Impact Levels:")
            for level, enabled in impact_levels.items():
                print(f"    {level}: {enabled}")
        
        return users
        
    except Exception as e:
        print(f"❌ Error checking user settings: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_worker_logic():
    """Check the worker's alert checking logic"""
    print_section("4. WORKER LOGIC CHECK")
    try:
        from services.background_alert_worker import BackgroundAlertWorker
        from services.news_alert_trigger import news_alert_trigger
        
        print("Checking worker initialization...")
        worker = BackgroundAlertWorker(check_interval=60)
        
        print(f"✅ Worker initialized")
        print(f"  Check interval: {worker.check_interval} seconds")
        print(f"  API base URL: {worker.api_base_url}")
        print(f"  Running: {worker.running}")
        
        # Check news alert trigger
        print(f"\nNews Alert Trigger:")
        print(f"  API base URL: {news_alert_trigger.api_base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking worker logic: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_news_filtering():
    """Check if news is being filtered correctly"""
    print_section("5. NEWS FILTERING CHECK")
    try:
        from services.news_alert_trigger import news_alert_trigger
        
        # Get cached news
        from services.persistent_news_cache import get_persistent_news_cache
        news_cache = get_persistent_news_cache()
        cached_news = news_cache.get_cached_news()
        
        if not cached_news:
            print("No news to check filtering")
            return
        
        print(f"Checking filtering for {len(cached_news)} news items...")
        
        # Check if news items would trigger alerts
        high_impact_count = 0
        for news_item in cached_news[:10]:  # Check first 10
            impact = news_item.get('impact', 'low')
            if impact == 'high':
                high_impact_count += 1
        
        print(f"High impact news items (first 10): {high_impact_count}")
        
        # Check currency pairs
        pairs_found = set()
        for news_item in cached_news[:10]:
            pairs = news_alert_trigger.get_affected_currency_pairs(news_item)
            pairs_found.update(pairs)
        
        print(f"Currency pairs found: {', '.join(list(pairs_found)[:10])}")
        
    except Exception as e:
        print(f"❌ Error checking filtering: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("\n" + "=" * 70)
    print("  ALERT SYSTEM EVALUATION")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Checking why no alerts since yesterday 8:46pm")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Check news availability
    news_items = check_news_availability()
    
    # Check deduplication
    dedup_ok = check_deduplication()
    
    # Check user settings
    users = check_user_settings()
    
    # Check worker logic
    worker_ok = check_worker_logic()
    
    # Check news filtering
    check_news_filtering()
    
    # Summary
    print_section("EVALUATION SUMMARY")
    
    issues = []
    recommendations = []
    
    if not news_items:
        issues.append("No news items in cache")
        recommendations.append("Check if news sources are providing updates")
    
    if news_items:
        # Check if news is stale
        most_recent = news_items[0] if news_items else None
        if most_recent:
            added_at = most_recent.get('added_to_feed_at') or most_recent.get('timestamp', '')
            try:
                if added_at:
                    if 'T' in str(added_at):
                        news_time = datetime.fromisoformat(str(added_at).replace('Z', '+00:00'))
                    else:
                        news_time = datetime.fromisoformat(str(added_at))
                    now = datetime.now(news_time.tzinfo) if news_time.tzinfo else datetime.now()
                    age_hours = (now - news_time).total_seconds() / 3600
                    
                    if age_hours > 12:
                        issues.append(f"Most recent news is {age_hours:.1f} hours old")
                        recommendations.append("Check if news fetching is working")
            except:
                pass
    
    if not users:
        issues.append("No users with alerts enabled")
        recommendations.append("Verify user settings in Firebase")
    
    if not worker_ok:
        issues.append("Worker logic check failed")
        recommendations.append("Check worker initialization")
    
    if issues:
        print("⚠️  Potential Issues:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("✅ No obvious code issues found")
    
    print("\n📋 Recommendations:")
    print("1. Check Railway dashboard for background worker status")
    print("2. Check Railway logs for worker errors or exceptions")
    print("3. Verify background worker is running (separate Railway service)")
    print("4. Check if news sources (WatcherGuru Telegram) are providing updates")
    print("5. Check deduplication - alerts may have already been sent")
    print("6. Manually trigger alerts: POST to /api/trigger-alerts endpoint")
    
    if recommendations:
        print("\nSpecific recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")

if __name__ == "__main__":
    main()

