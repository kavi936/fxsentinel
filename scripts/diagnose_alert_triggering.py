#!/usr/bin/env python3
"""
Diagnostic script to check why alerts aren't being triggered
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.news_aggregator import NewsAggregator
from services.news_alert_trigger import news_alert_trigger
from services.unified_alert_processor import get_unified_processor
from services.firebase_realtime_storage import FirebaseRealtimeStorage
from services.persistent_news_cache import get_persistent_news_cache

def main():
    print("=" * 80)
    print("ALERT TRIGGERING DIAGNOSTIC")
    print("=" * 80)
    
    # 1. Check if unified processor is running
    print("\n1. Checking Unified Alert Processor Status...")
    unified_processor = get_unified_processor()
    print(f"   Running: {unified_processor.running}")
    print(f"   Thread alive: {unified_processor.thread.is_alive() if unified_processor.thread else 'N/A'}")
    
    # 2. Check cached news
    print("\n2. Checking Cached News...")
    news_cache = get_persistent_news_cache()
    cached_news = news_cache.load_news()
    print(f"   Cached news count: {len(cached_news) if cached_news else 0}")
    
    if cached_news:
        print(f"   First 3 cached news items:")
        for i, item in enumerate(cached_news[:3], 1):
            title = item.get('title', 'No title')[:60]
            source = item.get('source', 'Unknown')
            impact = item.get('impact', 'unknown')
            is_high_impact = news_alert_trigger.is_forex_high_impact(item)
            print(f"     {i}. {title}...")
            print(f"        Source: {source}, Impact: {impact}, High-Impact: {is_high_impact}")
    
    # 3. Fetch fresh news
    print("\n3. Fetching Fresh News...")
    aggregator = NewsAggregator()
    try:
        fresh_news = aggregator.aggregate_news()
        print(f"   Fresh news count: {len(fresh_news) if fresh_news else 0}")
        
        if fresh_news:
            print(f"   First 5 fresh news items:")
            high_impact_count = 0
            for i, item in enumerate(fresh_news[:5], 1):
                title = item.get('title', 'No title')[:60]
                source = item.get('source', 'Unknown')
                impact = item.get('impact', 'unknown')
                is_high_impact = news_alert_trigger.is_forex_high_impact(item)
                if is_high_impact:
                    high_impact_count += 1
                print(f"     {i}. {title}...")
                print(f"        Source: {source}, Impact: {impact}, High-Impact: {is_high_impact}")
            
            print(f"\n   High-impact news count: {high_impact_count} out of {len(fresh_news)}")
            
            # 4. Check if alerts would be triggered
            print("\n4. Checking Alert Triggering Logic...")
            if high_impact_count > 0:
                print(f"   ✅ {high_impact_count} high-impact news items found - alerts should be triggered")
                
                # Check deduplication
                print("\n5. Checking Deduplication...")
                from services.persistent_alert_deduplication import get_persistent_deduplication
                dedup = get_persistent_deduplication()
                
                # Get user
                firebase = FirebaseRealtimeStorage()
                users = firebase.get_all_users_with_alerts()
                print(f"   Users with alerts enabled: {len(users) if users else 0}")
                
                if users:
                    user = users[0]
                    user_id = user.get('user_id')
                    print(f"   Testing with user: {user_id}")
                    
                    # Check first high-impact item
                    high_impact_items = [item for item in fresh_news if news_alert_trigger.is_forex_high_impact(item)]
                    if high_impact_items:
                        test_item = high_impact_items[0]
                        content_hash = dedup._get_news_content_hash(test_item)
                        print(f"   Test news item: {test_item.get('title', '')[:50]}...")
                        print(f"   Content hash: {content_hash}")
                        
                        # Check global deduplication
                        is_new_globally = dedup._check_global_content_hash(content_hash) if content_hash else True
                        print(f"   New globally: {is_new_globally}")
                        
                        # Check per-user deduplication
                        from services.persistent_alert_deduplication import should_send_news_alert
                        should_send = should_send_news_alert(test_item, user_id)
                        print(f"   Should send to user: {should_send}")
                        
                        if not should_send:
                            print(f"   ⚠️  Alert blocked by deduplication!")
                        else:
                            print(f"   ✅ Alert would be sent!")
            else:
                print(f"   ❌ No high-impact news found - alerts won't be triggered")
        else:
            print("   ❌ No fresh news fetched")
            
    except Exception as e:
        print(f"   ❌ Error fetching news: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Check cache TTL
    print("\n6. Checking Cache TTL...")
    should_fetch = news_cache.should_fetch_new_news()
    print(f"   Should fetch new news: {should_fetch}")
    if cached_news:
        cache_metadata = news_cache._load_cache_metadata()
        if cache_metadata:
            last_fetch = cache_metadata.get('last_fetch')
            print(f"   Last fetch: {last_fetch}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()

