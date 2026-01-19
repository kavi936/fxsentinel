#!/usr/bin/env python3
"""
Comprehensive diagnostic script to identify why prediction markets aren't displaying
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')

from services.prediction_markets_service import prediction_markets_service
from datetime import datetime, timezone

print("="*80)
print("PREDICTION MARKETS DIAGNOSTIC TOOL")
print("="*80)

# Step 1: Check API configuration
print("\n1. CHECKING API CONFIGURATION")
print("-" * 80)
use_direct_clob = os.getenv('USE_DIRECT_CLOB', 'true').lower() == 'true'
dome_api_key = os.getenv('DOME_API_KEY')
clob_max_pages = int(os.getenv('CLOB_MAX_PAGES', '3'))

print(f"USE_DIRECT_CLOB: {use_direct_clob}")
print(f"DOME_API_KEY: {'SET' if dome_api_key else 'NOT SET'}")
print(f"CLOB_MAX_PAGES: {clob_max_pages}")
print(f"API Tier: {os.getenv('DOME_API_TIER', 'free')}")

# Step 2: Try to fetch raw markets
print("\n2. FETCHING RAW MARKETS FROM API")
print("-" * 80)

try:
    print("Attempting to fetch from Polymarket CLOB API...")
    raw_polymarket = prediction_markets_service._fetch_polymarket_clob_direct(early_stop_threshold=100)
    print(f"✅ Fetched {len(raw_polymarket)} Polymarket markets")
    
    if len(raw_polymarket) > 0:
        print("\nSample Polymarket market:")
        sample = raw_polymarket[0]
        print(f"  Question: {sample.get('question', 'N/A')[:100]}")
        print(f"  Active: {sample.get('active')}")
        print(f"  Closed: {sample.get('closed')}")
        print(f"  Accepting Orders: {sample.get('accepting_orders')}")
        print(f"  Keys: {list(sample.keys())[:15]}")
        
        # Count active vs closed
        active_count = sum(1 for m in raw_polymarket if m.get('active') and not m.get('closed'))
        closed_count = sum(1 for m in raw_polymarket if m.get('closed'))
        print(f"\n  Active markets: {active_count}")
        print(f"  Closed markets: {closed_count}")
    else:
        print("❌ No markets fetched from Polymarket CLOB API")
        
except Exception as e:
    print(f"❌ Error fetching Polymarket markets: {e}")
    import traceback
    traceback.print_exc()
    raw_polymarket = []

# Step 3: Test filtering logic
print("\n3. TESTING FILTERING LOGIC")
print("-" * 80)

if raw_polymarket:
    print(f"Testing with {len(raw_polymarket)} raw markets...")
    
    # Check how many pass each filter stage
    total = len(raw_polymarket)
    active_not_closed = sum(1 for m in raw_polymarket if m.get('active') and not m.get('closed'))
    has_valid_id = sum(1 for m in raw_polymarket if m.get('condition_id') or m.get('id'))
    has_question = sum(1 for m in raw_polymarket if m.get('question'))
    
    print(f"  Total markets: {total}")
    print(f"  Active & not closed: {active_not_closed}")
    print(f"  Has valid ID: {has_valid_id}")
    print(f"  Has question/title: {has_question}")
    
    # Test actual filtering
    try:
        filtered = prediction_markets_service._filter_economic_markets(raw_polymarket[:500])  # Limit for speed
        print(f"\n  ✅ After filtering: {len(filtered)} markets")
        
        if len(filtered) == 0:
            print("\n  ❌ PROBLEM: All markets filtered out!")
            print("\n  Let's see why...")
            
            # Check a few markets manually
            print("\n  Analyzing first 10 markets:")
            for i, market in enumerate(raw_polymarket[:10], 1):
                question = market.get('question', '')[:80]
                active = market.get('active')
                closed = market.get('closed')
                accepting = market.get('accepting_orders')
                
                # Check for keywords
                text = question.lower()
                economic_keywords = ['fed', 'fomc', 'inflation', 'cpi', 'gdp', 'employment', 'ecb', 'boe', 'boj', 'interest rate']
                has_keyword = any(kw in text for kw in economic_keywords)
                
                print(f"    {i}. {question}")
                print(f"       Active: {active}, Closed: {closed}, Accepting: {accepting}, Has keyword: {has_keyword}")
        
    except Exception as e:
        print(f"  ❌ Error in filtering: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⚠️ Cannot test filtering - no raw markets available")

# Step 4: Test full service call
print("\n4. TESTING FULL SERVICE CALL")
print("-" * 80)

try:
    result = prediction_markets_service.get_prediction_markets(force_refresh=True)
    
    print(f"Status: {result.get('status')}")
    print(f"Markets returned: {len(result.get('markets', []))}")
    print(f"Cached: {result.get('cached', False)}")
    
    if result.get('error'):
        print(f"Error: {result.get('error')}")
    
    markets = result.get('markets', [])
    if len(markets) > 0:
        print(f"\n✅ Success! {len(markets)} markets returned")
        print("\nFirst market:")
        m = markets[0]
        print(f"  Question: {m.get('question', 'N/A')[:80]}")
        print(f"  Platform: {m.get('platform')}")
        print(f"  Yes price: {m.get('yes_price')}")
        print(f"  No price: {m.get('no_price')}")
        print(f"  Closed: {m.get('closed')}")
        print(f"  Is resolved: {m.get('is_resolved')}")
        print(f"  Recently resolved: {m.get('is_recently_resolved')}")
    else:
        print("\n❌ No markets returned")
        
except Exception as e:
    print(f"❌ Error in service call: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Check cache
print("\n5. CHECKING CACHE")
print("-" * 80)

try:
    if prediction_markets_service.use_persistent_cache:
        cache_result = prediction_markets_service.persistent_cache.load_markets(allow_stale=True)
        if cache_result:
            print(f"✅ Cache has {len(cache_result)} markets")
        else:
            print("⚠️ Cache is empty")
    else:
        if prediction_markets_service.cached_markets:
            print(f"✅ File cache has {len(prediction_markets_service.cached_markets)} markets")
        else:
            print("⚠️ File cache is empty")
except Exception as e:
    print(f"❌ Error checking cache: {e}")

# Step 6: Recommendations
print("\n6. DIAGNOSTIC SUMMARY & RECOMMENDATIONS")
print("="*80)

issues_found = []

if len(raw_polymarket) == 0:
    issues_found.append("No markets fetched from API - check API endpoints or network")

if raw_polymarket:
    active_count = sum(1 for m in raw_polymarket if m.get('active') and not m.get('closed'))
    if active_count == 0:
        issues_found.append("All fetched markets are closed/inactive - may need to adjust filtering")

try:
    result = prediction_markets_service.get_prediction_markets(force_refresh=True)
    if len(result.get('markets', [])) == 0:
        issues_found.append("Filtering is removing all markets - keywords may be too restrictive")
except:
    pass

if issues_found:
    print("\n⚠️ ISSUES IDENTIFIED:")
    for i, issue in enumerate(issues_found, 1):
        print(f"  {i}. {issue}")
    
    print("\n💡 RECOMMENDATIONS:")
    print("  1. Check if Polymarket API endpoints are accessible")
    print("  2. Consider relaxing filtering criteria temporarily to test")
    print("  3. Check logs for detailed filtering statistics")
    print("  4. Verify keywords match current market questions")
    print("  5. Consider showing recently resolved markets if no active markets available")
else:
    print("\n✅ No obvious issues found - markets should be displaying")
    print("   Check frontend console for errors or API endpoint issues")

print("\n" + "="*80)

