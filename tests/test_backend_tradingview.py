#!/usr/bin/env python3

import sys
import os
sys.path.append('backend')

# Import the function from the backend
from app import get_tradingview_prices

print("🚀 Testing backend's TradingView function...")
result = get_tradingview_prices()

if result:
    print(f"✅ Backend function successful! Got {len(result)} pairs")
    print("Sample data:")
    for pair, data in list(result.items())[:3]:
        print(f"  {pair}: {data}")
else:
    print("❌ Backend function failed - no data returned")
