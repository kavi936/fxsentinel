#!/usr/bin/env python3

import requests
from datetime import datetime
import json

def get_tradingview_prices():
    """Get real-time forex prices from TradingView API for all supported pairs"""
    try:
        print("🔍 Testing TradingView API...")
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {
            "Content-Type": "application/json"
        }
        
        # All 15 forex pairs we support - using pairs that are actually available on TradingView
        all_pairs = [
            "FX:EURUSD", "FX:GBPUSD", "FX:USDJPY", "FX:USDCHF", "FX:AUDUSD",
            "FX:USDCAD", "FX:NZDUSD", "FX:EURGBP", "FX:EURJPY", "FX:GBPJPY",
            "FX:USDSEK", "FX:USDNOK", "FX:USDHKD", "FX:EURCHF", "FX:GBPCHF"
        ]
        
        data = {
            "symbols": {
                "tickers": all_pairs
            },
            "columns": ["close", "change", "change_abs"]
        }
        
        print(f"📡 Making request to: {url}")
        print(f"📊 Request data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"📈 Response status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        print(f"📋 Response data: {json.dumps(result, indent=2)}")
        
        if 'data' in result and result['data']:
            prices = {}
            
            for item in result['data']:
                symbol = item['s']
                values = item['d']
                
                print(f"🔍 Processing symbol: {symbol}, values: {values}")
                
                if len(values) >= 3:
                    price = values[0]  # close price
                    change_percent = values[1]  # change percentage
                    change_abs = values[2]  # absolute change
                    
                    # Map TradingView symbols to our internal format
                    pair_mapping = {
                        "FX:EURUSD": "EURUSD",
                        "FX:GBPUSD": "GBPUSD", 
                        "FX:USDJPY": "USDJPY",
                        "FX:USDCHF": "USDCHF",
                        "FX:AUDUSD": "AUDUSD",
                        "FX:USDCAD": "USDCAD",
                        "FX:NZDUSD": "NZDUSD",
                        "FX:EURGBP": "EURGBP",
                        "FX:EURJPY": "EURJPY",
                        "FX:GBPJPY": "GBPJPY",
                        "FX:USDSEK": "USDSEK",
                        "FX:USDNOK": "USDNOK",
                        "FX:USDHKD": "USDHKD",  # Replaced USDDKK with USDHKD
                        "FX:EURCHF": "EURCHF",
                        "FX:GBPCHF": "GBPCHF"
                    }
                    
                    if symbol in pair_mapping:
                        pair_key = pair_mapping[symbol]
                        prices[pair_key] = {
                            'price': price,
                            'change': change_abs,
                            'changePercent': change_percent,
                            'lastUpdate': datetime.now().isoformat(),
                            'source': 'TradingView'
                        }
                        print(f"✅ Added {pair_key}: {price}")
            
            if prices:
                print(f"✅ Successfully fetched data from TradingView")
                print(f"   Fetched {len(prices)} pairs: {list(prices.keys())}")
                
                # Check if we got all expected pairs
                expected_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", 
                                "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
                                "USDSEK", "USDNOK", "USDHKD", "EURCHF", "GBPCHF"]
                missing_pairs = [pair for pair in expected_pairs if pair not in prices]
                if missing_pairs:
                    print(f"⚠️ TradingView missing pairs: {missing_pairs}")
                
                return prices
            else:
                print("❌ No prices found in response")
                
    except Exception as e:
        print(f"❌ Error fetching from TradingView: {e}")
        import traceback
        traceback.print_exc()
    
    return None

if __name__ == "__main__":
    print("🚀 Starting TradingView API test...")
    result = get_tradingview_prices()
    
    if result:
        print(f"✅ Test successful! Got {len(result)} pairs")
        print("Sample data:")
        for pair, data in list(result.items())[:3]:
            print(f"  {pair}: {data}")
    else:
        print("❌ Test failed - no data returned")
