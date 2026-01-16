#!/usr/bin/env python3
"""Test the full prediction markets flow"""
import os, sys
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')

from services.prediction_markets_service import prediction_markets_service

print('Testing full prediction markets flow...')
result = prediction_markets_service.get_prediction_markets(force_refresh=True)

if result.get('status') == 'success':
    markets = result.get('markets', [])
    print(f'\n✅ Got {len(markets)} markets after filtering')
    
    if markets:
        print('\nSample markets:')
        for i, m in enumerate(markets[:5], 1):
            print(f'\n{i}. {m.get("question", "N/A")[:70]}')
            print(f'   Platform: {m.get("platform")}, Yes: {m.get("yes_price")}, No: {m.get("no_price")}')
            vol = m.get("volume", 0)
            if vol:
                print(f'   Volume: ${vol:,.2f}')
            else:
                print('   Volume: N/A')
            print(f'   URL: {m.get("url", "N/A")}')
    else:
        print('\n⚠️ No markets returned - may need to check filtering logic')
else:
    print(f'\n❌ Error: {result.get("error", "Unknown error")}')

