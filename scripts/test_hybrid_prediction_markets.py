#!/usr/bin/env python3
"""
Test script for hybrid prediction markets implementation
Tests both CLOB direct API and DOME API integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.prediction_markets_service import PredictionMarketsService
import json
from datetime import datetime

def test_hybrid_implementation():
    """Test the hybrid prediction markets implementation"""
    print("\n" + "="*80)
    print("TESTING HYBRID PREDICTION MARKETS IMPLEMENTATION")
    print("="*80)
    print(f"Test started: {datetime.now().isoformat()}\n")
    
    # Initialize service
    print("Initializing PredictionMarketsService...")
    service = PredictionMarketsService()
    
    print(f"Configuration:")
    print(f"  - Use Direct CLOB: {service.use_direct_clob}")
    print(f"  - CLOB Max Pages: {service.clob_max_pages}")
    print(f"  - CLOB Request Delay: {service.clob_request_delay}s")
    print(f"  - DOME API Available: {service.api_available}")
    print()
    
    # Test fetching markets
    print("Fetching prediction markets...")
    result = service.get_prediction_markets(force_refresh=True)
    
    if result.get('status') == 'success':
        markets = result.get('markets', [])
        summary = result.get('summary', {})
        
        print(f"\n✅ Success!")
        print(f"  Total Markets: {len(markets)}")
        print(f"  Cached: {result.get('cached', False)}")
        print(f"  Timestamp: {result.get('timestamp', 'N/A')}")
        
        # Analyze markets
        if markets:
            print(f"\nMarket Analysis:")
            
            # Count by source
            clob_markets = [m for m in markets if m.get('platform') == 'polymarket' and '_source' not in m or m.get('_source') == 'clob_direct']
            dome_markets = [m for m in markets if m.get('_source') == 'dome']
            kalshi_markets = [m for m in markets if m.get('platform') == 'kalshi']
            
            print(f"  Polymarket (CLOB): {len(clob_markets)}")
            print(f"  Polymarket (DOME): {len(dome_markets)}")
            print(f"  Kalshi (DOME): {len(kalshi_markets)}")
            
            # Count forex-relevant
            forex_keywords = ["fed", "federal reserve", "fomc", "interest rate", "inflation", "cpi", 
                             "gdp", "employment", "nfp", "ecb", "boe", "boj", "eur/usd", "gbp/usd", "usd/jpy"]
            forex_relevant = 0
            for market in markets:
                question = str(market.get('question', '')).lower()
                if any(keyword in question for keyword in forex_keywords):
                    forex_relevant += 1
            
            print(f"  Forex-Relevant: {forex_relevant}")
            
            # Show sample markets
            print(f"\nSample Markets (first 5):")
            for i, market in enumerate(markets[:5], 1):
                print(f"\n  {i}. {market.get('question', 'N/A')[:80]}")
                print(f"     Platform: {market.get('platform')}")
                print(f"     Source: {market.get('_source', 'dome')}")
                print(f"     Volume: ${(market.get('volume', 0) / 1000):.0f}k" if market.get('volume') else "     Volume: N/A")
                print(f"     Yes: {market.get('yes_price', 0)*100:.0f}% | No: {market.get('no_price', 0)*100:.0f}%")
                if market.get('affected_currency_pairs'):
                    print(f"     Pairs: {', '.join(market.get('affected_currency_pairs', [])[:3])}")
        else:
            print("  ⚠️  No markets returned")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_hybrid_implementation()

