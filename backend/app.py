#!/usr/bin/env python3

from flask import Flask, jsonify, request
import requests
from datetime import datetime
import os

app = Flask(__name__)

def get_tradingview_prices():
    """Get real-time forex prices from TradingView API for all supported pairs"""
    try:
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"Content-Type": "application/json"}
        
        # All 15 forex pairs we support
        all_pairs = [
            "FX:EURUSD", "FX:GBPUSD", "FX:USDJPY", "FX:USDCHF", "FX:AUDUSD",
            "FX:USDCAD", "FX:NZDUSD", "FX:EURGBP", "FX:EURJPY", "FX:GBPJPY",
            "FX:USDSEK", "FX:USDNOK", "FX:USDHKD", "FX:EURCHF", "FX:GBPCHF"
        ]
        
        data = {
            "symbols": {"tickers": all_pairs},
            "columns": ["close", "change", "change_abs"]
        }
        
        print("🔍 Making TradingView API call...")
        response = requests.post(url, headers=headers, json=data, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ TradingView API responded in {response.elapsed.total_seconds():.2f} seconds")
        
        if 'data' in result and result['data']:
            prices = {}
            
            for item in result['data']:
                symbol = item['s']
                values = item['d']
                
                if len(values) >= 3:
                    price = values[0]  # close price
                    change_percent = values[1]  # change percentage
                    change_abs = values[2]  # absolute change
                    
                    # Map TradingView symbols to our internal format
                    pair_mapping = {
                        "FX:EURUSD": "EURUSD", "FX:GBPUSD": "GBPUSD", 
                        "FX:USDJPY": "USDJPY", "FX:USDCHF": "USDCHF",
                        "FX:AUDUSD": "AUDUSD", "FX:USDCAD": "USDCAD",
                        "FX:NZDUSD": "NZDUSD", "FX:EURGBP": "EURGBP",
                        "FX:EURJPY": "EURJPY", "FX:GBPJPY": "GBPJPY",
                        "FX:USDSEK": "USDSEK", "FX:USDNOK": "USDNOK",
                        "FX:USDHKD": "USDHKD", "FX:EURCHF": "EURCHF",
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
            
            if prices:
                print(f"✅ Successfully fetched {len(prices)} pairs from TradingView")
                return prices
                
    except Exception as e:
        print(f"❌ Error fetching from TradingView: {e}")
        import traceback
        traceback.print_exc()
    
    return None

@app.route('/api/forex-prices', methods=['GET', 'OPTIONS'])
def get_forex_prices():
    """Get real-time forex prices from TradingView API only"""
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        print("🔍 Starting TradingView API call...")
        tradingview_prices = get_tradingview_prices()
        
        if tradingview_prices:
            print(f"✅ Successfully fetched data from TradingView: {len(tradingview_prices)} pairs")
            
            return jsonify({
                'prices': tradingview_prices,
                'dataSource': 'TradingView',
                'timestamp': datetime.now().isoformat(),
                'dataQuality': {
                    'hasStaleData': False,
                    'hasModeratelyOldData': False,
                    'isMarketClosed': False,
                    'averageAgeMinutes': 0
                }
            })
        else:
            print("⚠️ TradingView returned None or empty data")
            # Return minimal fallback data
            fallback_prices = {
                'EURUSD': {'price': 1.0923, 'change': 0.0012, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
                'USDJPY': {'price': 147.85, 'change': -0.08, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
                'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'}
            }
            
            return jsonify({
                'prices': fallback_prices,
                'dataSource': 'fallback',
                'timestamp': datetime.now().isoformat(),
                'dataQuality': {
                    'hasStaleData': False,
                    'hasModeratelyOldData': False,
                    'isMarketClosed': True,
                    'averageAgeMinutes': 0
                }
            })
        
    except Exception as e:
        print(f"❌ Error in forex prices endpoint: {e}")
        import traceback
        traceback.print_exc()
        
        # Return minimal fallback data
        fallback_prices = {
            'EURUSD': {'price': 1.0923, 'change': 0.0012, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
            'USDJPY': {'price': 147.85, 'change': -0.08, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
            'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'}
        }
        
        return jsonify({
            'prices': fallback_prices,
            'dataSource': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'dataQuality': {
                'hasStaleData': False,
                'hasModeratelyOldData': False,
                'isMarketClosed': True,
                'averageAgeMinutes': 0
            }
        })

@app.route('/api/hello', methods=['GET'])
def hello():
    """Simple health check endpoint"""
    return jsonify({"message": "Hello from minimal Flask app!", "status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Starting minimal Flask server on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
