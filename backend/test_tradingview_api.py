#!/usr/bin/env python3
"""Test script to verify TradingView API is working"""

import requests
import json
from datetime import datetime

def test_tradingview_api():
    """Test TradingView API directly"""
    try:
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Test with just the 4 major pairs
        test_pairs = [
            "FX:EURUSD", "FX:GBPUSD", "FX:USDJPY", "FX:USDCHF"
        ]
        
        data = {
            "symbols": {
                "tickers": test_pairs
            },
            "columns": ["close", "change", "change_abs"]
        }
        
        print("🔍 Testing TradingView API...")
        print(f"   URL: {url}")
        print(f"   Pairs: {test_pairs}")
        print(f"   Request data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response text: {response.text}")
            return False
        
        result = response.json()
        print(f"\n📊 Response JSON keys: {list(result.keys())}")
        
        if 'data' in result and result['data']:
            print(f"✅ Successfully received data for {len(result['data'])} pairs")
            
            pair_mapping = {
                "FX:EURUSD": "EURUSD",
                "FX:GBPUSD": "GBPUSD", 
                "FX:USDJPY": "USDJPY",
                "FX:USDCHF": "USDCHF"
            }
            
            for item in result['data']:
                symbol = item['s']
                values = item['d']
                
                if len(values) >= 3:
                    price = values[0]
                    change_percent = values[1]
                    change_abs = values[2]
                    
                    if symbol in pair_mapping:
                        pair_key = pair_mapping[symbol]
                        print(f"\n✅ {pair_key}:")
                        print(f"   Price: {price}")
                        print(f"   Change %: {change_percent}")
                        print(f"   Change Abs: {change_abs}")
            
            return True
        else:
            print("❌ No data in response")
            print(f"   Full response: {json.dumps(result, indent=2)}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TradingView API Test")
    print("=" * 60)
    success = test_tradingview_api()
    print("\n" + "=" * 60)
    if success:
        print("✅ Test PASSED - TradingView API is working")
    else:
        print("❌ Test FAILED - TradingView API is not working")
    print("=" * 60)

