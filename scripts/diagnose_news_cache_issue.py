#!/usr/bin/env python3
"""
Diagnostic script to identify why new news isn't being displayed
Checks cache TTL, cache age, and fetch behavior
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def check_cache_ttl():
    """Check the cache TTL configuration"""
    print("=" * 60)
    print("CACHE TTL ANALYSIS")
    print("=" * 60)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        cache = get_persistent_news_cache()
        
        print(f"Current Cache TTL: {cache.max_age_hours} hours")
        print(f"Old File Cache TTL: 0.25 hours (15 minutes)")
        print(f"\n⚠️  ISSUE IDENTIFIED:")
        print(f"   The persistent cache TTL is {cache.max_age_hours} hours")
        print(f"   This is {cache.max_age_hours / 0.25:.0f}x longer than the old cache!")
        print(f"   Once news is cached, it won't fetch fresh news for {cache.max_age_hours} hours")
        print(f"   unless force_refresh=true is used.")
        
        return cache.max_age_hours
        
    except Exception as e:
        print(f"❌ Error checking cache TTL: {e}")
        return None

def check_cache_status():
    """Check current cache status"""
    print("\n" + "=" * 60)
    print("CACHE STATUS ANALYSIS")
    print("=" * 60)
    
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        cache = get_persistent_news_cache()
        
        status = cache.get_cache_status()
        print(f"Cache Exists: {status.get('exists', False)}")
        print(f"Cache Valid: {status.get('is_valid', False)}")
        print(f"News Count: {status.get('news_count', 0)}")
        print(f"Cache Age: {status.get('age', 'N/A')}")
        
        if status.get('exists') and status.get('is_valid'):
            age_str = status.get('age', '')
            if age_str and ':' in age_str:
                # Parse age (format: "X:XX:XX")
                parts = age_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                total_minutes = hours * 60 + minutes
                
                print(f"\n📊 Cache Age Analysis:")
                print(f"   Cache is {total_minutes} minutes old")
                print(f"   Frontend refreshes every 2 minutes")
                print(f"   But cache won't expire for {cache.max_age_hours * 60 - total_minutes:.0f} more minutes")
                print(f"   So fresh news won't be fetched until cache expires!")
        
        return status
        
    except Exception as e:
        print(f"❌ Error checking cache status: {e}")
        return None

def check_fetch_behavior():
    """Check how the news endpoint behaves"""
    print("\n" + "=" * 60)
    print("FETCH BEHAVIOR ANALYSIS")
    print("=" * 60)
    
    print("Frontend Behavior:")
    print("  - Auto-refreshes every 2 minutes")
    print("  - Calls: GET /api/news (without force_refresh)")
    print("  - Only uses force_refresh=true on manual refresh")
    
    print("\nBackend Behavior:")
    print("  - Checks cache first (unless force_refresh=true)")
    print("  - If cache exists and is valid (< 24 hours old):")
    print("    → Returns cached news immediately")
    print("    → Does NOT fetch fresh news")
    print("  - Only fetches fresh news if:")
    print("    → force_refresh=true")
    print("    → Cache doesn't exist")
    print("    → Cache is older than 24 hours")
    
    print("\n⚠️  ROOT CAUSE:")
    print("   With 24-hour cache TTL:")
    print("   - News gets cached once")
    print("   - Frontend calls API every 2 minutes")
    print("   - Backend returns cached news (still valid)")
    print("   - Fresh news is NEVER fetched until cache expires!")
    print("   - Users see stale news for up to 24 hours!")

def recommend_solution():
    """Recommend a solution"""
    print("\n" + "=" * 60)
    print("RECOMMENDED SOLUTION")
    print("=" * 60)
    
    print("Option 1: Reduce Cache TTL (Recommended)")
    print("  - Change max_age_hours from 24.0 to 0.25 (15 minutes)")
    print("  - Matches old file cache behavior")
    print("  - Cache still persists across restarts (main benefit)")
    print("  - Fresh news fetched every 15 minutes")
    
    print("\nOption 2: Stale-While-Revalidate Pattern")
    print("  - Keep 24-hour TTL for persistence")
    print("  - But fetch fresh news in background if cache > 15 minutes old")
    print("  - Serve cached news immediately, update in background")
    print("  - More complex but better UX")
    
    print("\nOption 3: Hybrid Approach")
    print("  - Use 15-minute TTL (like old cache)")
    print("  - Cache persists across restarts (main benefit)")
    print("  - Simple and effective")
    
    print("\n✅ RECOMMENDATION: Option 1 or 3")
    print("   Reduce TTL to 15-30 minutes")
    print("   Cache still persists across restarts")
    print("   Fresh news fetched regularly")

def main():
    """Run all diagnostics"""
    print("\n" + "=" * 60)
    print("NEWS CACHE ISSUE DIAGNOSTIC")
    print("=" * 60)
    print("\nAnalyzing why new news isn't being displayed...\n")
    
    ttl = check_cache_ttl()
    status = check_cache_status()
    check_fetch_behavior()
    recommend_solution()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("Problem: Cache TTL is 24 hours (too long)")
    print("Impact: Fresh news not fetched for up to 24 hours")
    print("Solution: Reduce TTL to 15-30 minutes")
    print("Benefit: Cache still persists across restarts")

if __name__ == '__main__':
    main()

