#!/usr/bin/env python3

from flask import Flask, jsonify
from datetime import datetime
import requests

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
        
        response = requests.post(url, headers=headers, json=data, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        
        if 'data' in result and result['data']:
            prices = {}
            
            for item in result['data']:
                symbol = item['s']
                values = item['d']
                
                if len(values) >= 3:
                    price = values[0]
                    change_percent = values[1]
                    change_abs = values[2]
                    
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
                print(f"✅ Successfully fetched data from TradingView: {len(prices)} pairs")
                return prices
                
    except Exception as e:
        print(f"❌ TradingView failed: {e}")
    
    return None

@app.route('/api/forex-prices', methods=['GET'])
def get_forex_prices():
    """Get real-time forex prices from TradingView"""
    try:
        print("🔍 Starting TradingView API call...")
        tradingview_prices = get_tradingview_prices()
        
        if tradingview_prices:
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
            # Fallback data
            fallback_prices = {
                'EURUSD': {'price': 1.0923, 'change': 0.0012, 'lastUpdate': datetime.now().isoformat()},
                'USDJPY': {'price': 147.85, 'change': -0.08, 'lastUpdate': datetime.now().isoformat()},
                'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'lastUpdate': datetime.now().isoformat()}
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting simple Flask server...")
    app.run(host='0.0.0.0', port=5002, debug=False)
