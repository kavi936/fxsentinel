#!/usr/bin/env python3
"""
Test alert triggering for cached news
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.unified_alert_processor import get_unified_processor
from services.persistent_news_cache import get_persistent_news_cache
from services.news_alert_trigger import news_alert_trigger

def main():
    print("=" * 80)
    print("TESTING ALERT TRIGGERING")
    print("=" * 80)
    
    # 1. Check unified processor status
    print("\n1. Checking Unified Alert Processor...")
    unified_processor = get_unified_processor()
    print(f"   Running: {unified_processor.running}")
    print(f"   Thread alive: {unified_processor.thread.is_alive() if unified_processor.thread else 'N/A'}")
    
    if not unified_processor.running:
        print("   ⚠️  Processor not running - starting it...")
        unified_processor.start()
        print("   ✅ Processor started")
    
    # 2. Get cached news
    print("\n2. Getting Cached News...")
    news_cache = get_persistent_news_cache()
    cached_news = news_cache.load_news()
    print(f"   Cached news count: {len(cached_news) if cached_news else 0}")
    
    if not cached_news:
        print("   ❌ No cached news found")
        return
    
    # 3. Check for high-impact news
    print("\n3. Checking for High-Impact News...")
    high_impact = []
    for item in cached_news[:10]:  # Check top 10
        if news_alert_trigger.is_forex_high_impact(item):
            high_impact.append(item)
            print(f"   ✅ High-impact: {item.get('title', '')[:60]}...")
    
    print(f"\n   Found {len(high_impact)} high-impact news items in top 10")
    
    # 4. Trigger alerts manually
    if high_impact:
        print(f"\n4. Triggering Alerts for {len(high_impact)} High-Impact Items...")
        unified_processor.check_news_alerts_async(high_impact)
        print(f"   ✅ Alert check triggered (running in background thread)")
        print(f"   Check logs for 'Checking X news items for alerts...'")
    else:
        print("\n4. No high-impact news found - alerts won't be triggered")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check production logs for 'Checking X news items for alerts...'")
    print("2. Check for 'Found X high-impact forex news items'")
    print("3. Check for 'Processing alerts for X users'")
    print("4. Check for 'Alert sent successfully' messages")

if __name__ == '__main__':
    main()

