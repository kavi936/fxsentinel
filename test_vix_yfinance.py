#!/usr/bin/env python3
"""
Test script to check if yfinance can fetch VIX data
"""

import sys
import traceback

print("=" * 60)
print("Testing VIX Data Fetch from yfinance")
print("=" * 60)

# Test 1: Check if yfinance is installed
print("\n1. Checking if yfinance is installed...")
try:
    import yfinance as yf
    print("✅ yfinance is installed")
    print(f"   Version: {yf.__version__ if hasattr(yf, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ yfinance is NOT installed: {e}")
    print("   Install with: pip install yfinance")
    sys.exit(1)

# Test 2: Try to create a VIX ticker
print("\n2. Creating VIX ticker (^VIX)...")
try:
    vix_ticker = yf.Ticker("^VIX")
    print("✅ VIX ticker created successfully")
except Exception as e:
    print(f"❌ Failed to create VIX ticker: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Try to fetch history
print("\n3. Fetching VIX history (2 days)...")
try:
    hist = vix_ticker.history(period="2d")
    print(f"✅ History fetched successfully")
    print(f"   Data shape: {hist.shape}")
    print(f"   Empty: {hist.empty}")
    print(f"   Columns: {list(hist.columns)}")
    
    if not hist.empty:
        print(f"\n   Latest data:")
        print(f"   {hist.tail()}")
        
        # Get current price
        current_price = float(hist['Close'].iloc[-1])
        print(f"\n   Current VIX: {current_price:.2f}")
        
        if len(hist) >= 2:
            previous_close = float(hist['Close'].iloc[-2])
            change = current_price - previous_close
            print(f"   Previous Close: {previous_close:.2f}")
            print(f"   Change: {change:+.2f}")
        else:
            print("   Only one day of data available")
    else:
        print("   ⚠️ History data is empty!")
        
except Exception as e:
    print(f"❌ Failed to fetch history: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Try to get info
print("\n4. Fetching VIX ticker info...")
try:
    info = vix_ticker.info
    if info:
        print("✅ Info fetched successfully")
        print(f"   Keys available: {len(info)} keys")
        if 'previousClose' in info:
            print(f"   Previous Close from info: {info.get('previousClose')}")
        if 'regularMarketPrice' in info:
            print(f"   Regular Market Price: {info.get('regularMarketPrice')}")
    else:
        print("   ⚠️ Info is empty")
except Exception as e:
    print(f"⚠️ Failed to fetch info (this is okay): {e}")

# Test 5: Try alternative period
print("\n5. Trying alternative fetch (1 day period)...")
try:
    hist_alt = vix_ticker.history(period="1d")
    if not hist_alt.empty:
        print(f"✅ Alternative fetch successful")
        print(f"   Data shape: {hist_alt.shape}")
        current_price_alt = float(hist_alt['Close'].iloc[-1])
        print(f"   Current VIX: {current_price_alt:.2f}")
    else:
        print("   ⚠️ Alternative fetch also returned empty data")
except Exception as e:
    print(f"⚠️ Alternative fetch failed: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)

