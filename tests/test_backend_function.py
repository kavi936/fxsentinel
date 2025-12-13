#!/usr/bin/env python3

import sys
import os
sys.path.append('backend')

# Import the function from the backend
from app import get_tradingview_prices
import time

print("🚀 Testing backend's TradingView function...")
start_time = time.time()

try:
    result = get_tradingview_prices()
    elapsed = time.time() - start_time
    print(f"⏱️ Function completed in {elapsed:.2f} seconds")
    
    if result:
        print(f"✅ Backend function successful! Got {len(result)} pairs")
        print("Sample data:")
        for pair, data in list(result.items())[:3]:
            print(f"  {pair}: {data}")
    else:
        print("❌ Backend function failed - no data returned")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ Backend function failed after {elapsed:.2f} seconds: {e}")
    import traceback
    traceback.print_exc()
