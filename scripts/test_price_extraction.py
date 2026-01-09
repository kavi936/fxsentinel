#!/usr/bin/env python3
"""Test price extraction from markets"""

import sys
sys.path.append('backend')

from services.prediction_markets_service import prediction_markets_service

# Get some markets
result = prediction_markets_service.get_prediction_markets(force_refresh=True)
markets = result.get('markets', [])

print(f"Found {len(markets)} markets\n")

if markets:
    for i, market in enumerate(markets[:5], 1):
        print(f"Market {i}:")
        print(f"  Question: {market.get('question', 'N/A')[:80]}")
        print(f"  Yes Price: {market.get('yes_price')}")
        print(f"  No Price: {market.get('no_price')}")
        print(f"  Active: {market.get('active')}")
        print(f"  Closed: {market.get('closed')}")
        print()

