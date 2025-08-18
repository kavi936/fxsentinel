#!/usr/bin/env python3

import requests
from datetime import datetime
import json

def test_tradingview_simple():
    """Simple test of TradingView API without Flask overhead"""
    try:
        print("🔍 Testing TradingView API directly...")
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"Content-Type": "application/json"}
        
        data = {
            "symbols": {"tickers": ["FX:EURUSD", "FX:GBPUSD", "FX:USDJPY"]},
            "columns": ["close", "change", "change_abs"]
        }
        
        print(f"📡 Making request to: {url}")
        print(f"📊 Request data: {json.dumps(data, indent=2)}")
        
        # Test with shorter timeout
        response = requests.post(url, headers=headers, json=data, timeout=3)
        print(f"📈 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Got response in {response.elapsed.total_seconds():.2f} seconds")
            print(f"📋 Response data: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 3 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting simple TradingView test...")
    success = test_tradingview_simple()
    if success:
        print("✅ TradingView API is working")
    else:
        print("❌ TradingView API is not working")
