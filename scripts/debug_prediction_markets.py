#!/usr/bin/env python3
"""
Debug script to see what markets are being fetched and why they're filtered out
"""

import sys
sys.path.append('backend')

from services.prediction_markets_service import prediction_markets_service
import json

print("="*80)
print("DEBUGGING PREDICTION MARKETS FILTERING")
print("="*80)

# Fetch markets
print("\n1. Fetching markets from Polymarket...")
all_markets = prediction_markets_service._fetch_polymarket_markets()
print(f"   Total markets fetched: {len(all_markets)}")

if len(all_markets) > 0:
    print(f"\n2. Sample market structure:")
    sample = all_markets[0]
    print(f"   Question: {sample.get('question', 'N/A')[:100]}")
    print(f"   Active: {sample.get('active')}")
    print(f"   Closed: {sample.get('closed')}")
    print(f"   Keys: {list(sample.keys())[:10]}...")
    
    # Check how many are active
    active_markets = [m for m in all_markets if m.get('active') and not m.get('closed')]
    print(f"\n3. Active markets (not closed): {len(active_markets)}")
    
    # Test filtering
    print(f"\n4. Testing filtering logic...")
    filtered = prediction_markets_service._filter_economic_markets(all_markets)
    print(f"   Markets after filtering: {len(filtered)}")
    
    if len(filtered) == 0:
        print(f"\n5. No markets matched. Checking why...")
        
        # Check first 20 active markets for keywords
        print(f"\n   Checking first 20 active markets for economic keywords:")
        for i, market in enumerate(active_markets[:20], 1):
            question = market.get("question", "").lower()
            description = market.get("description", "").lower()
            text = f"{question} {description}"
            
            # Check for exclude keywords
            has_exclude = any(exclude in text for exclude in prediction_markets_service.exclude_keywords)
            
            # Check for economic keywords
            matched = [kw for kw in prediction_markets_service.economic_keywords if kw.lower() in text]
            
            print(f"\n   Market {i}:")
            print(f"      Question: {question[:80]}...")
            print(f"      Active: {market.get('active')}, Closed: {market.get('closed')}")
            print(f"      Has exclude keywords: {has_exclude}")
            print(f"      Matched economic keywords: {matched[:3] if matched else 'None'}")
            
            if matched and not has_exclude:
                print(f"      ✅ Should be included!")
                break
    else:
        print(f"\n5. Found {len(filtered)} markets. Sample:")
        for i, market in enumerate(filtered[:3], 1):
            print(f"\n   Market {i}:")
            print(f"      Question: {market.get('question', 'N/A')[:80]}")
            print(f"      Relevance: {market.get('relevance')}")
            print(f"      Related event: {market.get('related_event')}")
            print(f"      Matched keywords: {market.get('matched_keywords', [])[:3]}")

# Test the full service
print(f"\n6. Testing full service call...")
result = prediction_markets_service.get_prediction_markets(force_refresh=True)
print(f"   Status: {result.get('status')}")
print(f"   Markets returned: {len(result.get('markets', []))}")
if result.get('markets'):
    print(f"   Sample market: {result['markets'][0].get('question', 'N/A')[:80]}")

