#!/usr/bin/env python3

import requests
import time
from datetime import datetime

def test_tradingview_direct():
    """Test TradingView API directly"""
    print("🔍 Testing TradingView API directly...")
    start_time = time.time()
    
    try:
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"Content-Type": "application/json"}
        
        data = {
            "symbols": {"tickers": ["FX:EURUSD", "FX:GBPUSD", "FX:USDJPY"]},
            "columns": ["close", "change", "change_abs"]
        }
        
        print(f"📡 Making request to TradingView...")
        response = requests.post(url, headers=headers, json=data, timeout=5)
        print(f"📈 Response received in {time.time() - start_time:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Got {len(result.get('data', []))} pairs")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout after {time.time() - start_time:.2f} seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting TradingView API test...")
    success = test_tradingview_direct()
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
