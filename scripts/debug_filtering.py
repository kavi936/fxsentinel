#!/usr/bin/env python3
"""
Debug script to see why markets are being filtered out
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')

from services.prediction_markets_service import prediction_markets_service

print("=== DEBUGGING PREDICTION MARKETS FILTERING ===\n")

# Get a sample of raw markets before filtering
print("Fetching raw markets...")
result = prediction_markets_service.get_prediction_markets(force_refresh=True)

# Check what we got
if result.get('status') == 'success':
    markets = result.get('data', {}).get('markets', [])
    print(f"\nMarkets returned: {len(markets)}")
    
    if len(markets) == 0:
        print("\n❌ PROBLEM: No markets returned after filtering")
        print("\nLet's check what's happening during filtering...")
        
        # We need to manually test the filtering logic
        # Let's fetch raw markets and see what they look like
        print("\n=== Testing Raw Market Fetch ===")
        
        # Access the internal refresh method to see raw data
        import importlib
        import services.prediction_markets_service
        importlib.reload(services.prediction_markets_service)
        from services.prediction_markets_service import prediction_markets_service
        
        # Force a refresh and check logs
        print("Check the logs above to see filtering stats")
        print("The issue is likely:")
        print("1. Too many markets are closed/resolved/archived")
        print("2. Remaining markets don't match economic keywords")
        print("3. Markets are being filtered out due to past resolution dates")
        
else:
    print(f"Error: {result.get('error')}")

