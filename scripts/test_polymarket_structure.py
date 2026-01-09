#!/usr/bin/env python3
"""
Quick test to understand Polymarket API structure
This helps us build the frontend with accurate mock data
"""

import requests
import json
from datetime import datetime

print("="*80)
print("POLYMARKET API STRUCTURE TEST")
print("="*80)

# Fetch markets from CLOB API
url = "https://clob.polymarket.com/markets"
params = {"limit": 5}

try:
    print(f"\nFetching from: {url}")
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ Success! Response structure:")
        print(f"   Top-level keys: {list(data.keys())}")
        
        if "data" in data and len(data["data"]) > 0:
            market = data["data"][0]
            
            print(f"\n{'='*80}")
            print("SAMPLE MARKET STRUCTURE:")
            print(f"{'='*80}")
            print(json.dumps(market, indent=2))
            
            print(f"\n{'='*80}")
            print("KEY FIELDS ANALYSIS:")
            print(f"{'='*80}")
            print(f"Question: {market.get('question', 'N/A')[:80]}...")
            print(f"Active: {market.get('active')}")
            print(f"Closed: {market.get('closed')}")
            print(f"All available keys: {list(market.keys())}")
            
            # Check for price/outcome related fields
            price_fields = [k for k in market.keys() if 'price' in k.lower() or 'outcome' in k.lower() or 'yes' in k.lower() or 'no' in k.lower()]
            if price_fields:
                print(f"\nPrice/Outcome related fields: {price_fields}")
            
            # Check for date fields
            date_fields = [k for k in market.keys() if 'date' in k.lower() or 'time' in k.lower() or 'end' in k.lower()]
            if date_fields:
                print(f"Date/Time related fields: {date_fields}")
            
            # Check for volume/liquidity fields
            volume_fields = [k for k in market.keys() if 'volume' in k.lower() or 'liquidity' in k.lower()]
            if volume_fields:
                print(f"Volume/Liquidity fields: {volume_fields}")
            
            # Save sample to file for reference
            with open("data/polymarket_sample_response.json", "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "sample_market": market,
                    "all_fields": list(market.keys())
                }, f, indent=2)
            
            print(f"\n✅ Sample saved to: data/polymarket_sample_response.json")
            
        else:
            print("\n⚠️ No markets in response")
            print(f"Full response: {json.dumps(data, indent=2)[:500]}")
    
    else:
        print(f"\n❌ Error: HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("TEST COMPLETE")
print(f"{'='*80}")

