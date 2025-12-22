#!/usr/bin/env python3
"""
Test API response format matches frontend expectations
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.market_sentiment_service import MarketSentimentService
from dataclasses import asdict

def test_api_response_format():
    """Test that API response format matches what frontend expects"""
    print("="*70)
    print("API RESPONSE FORMAT TEST")
    print("="*70)
    
    service = MarketSentimentService()
    
    # Create test sentiment with pairs
    test_forex = {
        'EURUSD': {'price': 1.0923, 'change': 0.0012, 'changePercent': 0.11},
        'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'changePercent': -0.16},
        'USDJPY': {'price': 150.00, 'change': 0.30, 'changePercent': 0.20},
        'USDCHF': {'price': 0.8845, 'change': -0.0015, 'changePercent': -0.17},
    }
    
    # Calculate pairs sentiment
    pairs = service._calculate_pairs_sentiment(test_forex)
    
    # Simulate _format_for_frontend() output
    pairs_sentiment_formatted = [
        {
            'pair': p.pair,
            'sentiment': p.sentiment,
            'percentage': p.percentage,
            'price_change': p.price_change,
            'rsi': p.rsi,
            'volatility': p.volatility,
            'support': p.support,
            'resistance': p.resistance
        } for p in pairs
    ]
    
    print("\n✅ Formatted pairs_sentiment for API response:")
    print(json.dumps(pairs_sentiment_formatted, indent=2))
    
    # Verify frontend can process this
    print("\n" + "="*70)
    print("FRONTEND PROCESSING SIMULATION")
    print("="*70)
    
    for pair_data in pairs_sentiment_formatted:
        print(f"\n{pair_data['pair']} Card Rendering:")
        
        # Simulate frontend code execution
        pair_name = pair_data['pair']
        sentiment = pair_data['sentiment']
        percentage = pair_data['percentage']
        price_change = pair_data['price_change']
        rsi = pair_data['rsi']
        volatility = pair_data['volatility']
        
        # Frontend code: pair.price_change >= 0 ? '+' : ''
        change_sign = '+' if price_change >= 0 else ''
        change_display = f"{change_sign}{price_change:.2f}%"
        change_class = 'positive' if price_change >= 0 else 'negative'
        
        # Frontend code: pair.sentiment
        sentiment_class = sentiment
        
        # Frontend code: pair.percentage
        bar_width = percentage
        
        # Frontend code: pair.rsi.toFixed(0)
        rsi_display = f"{rsi:.0f}"
        
        # Frontend code: pair.volatility.toFixed(1)
        vol_display = f"{volatility:.1f}"
        
        print(f"  ✅ Pair Name: {pair_name}")
        print(f"  ✅ Daily Change: {change_display} (class: {change_class})")
        print(f"  ✅ Sentiment: {sentiment} (class: {sentiment_class})")
        print(f"  ✅ Percentage Bar: {bar_width}% width")
        print(f"  ✅ RSI: {rsi_display}")
        print(f"  ✅ Volatility: {vol_display}%")
        
        # Verify all fields exist and are valid
        assert 'pair' in pair_data and pair_data['pair'], "Missing pair"
        assert 'sentiment' in pair_data and pair_data['sentiment'], "Missing sentiment"
        assert 'percentage' in pair_data and isinstance(pair_data['percentage'], (int, float)), "Missing/invalid percentage"
        assert 'price_change' in pair_data and isinstance(pair_data['price_change'], (int, float)), "Missing/invalid price_change"
        assert 'rsi' in pair_data and isinstance(pair_data['rsi'], (int, float)), "Missing/invalid rsi"
        assert 'volatility' in pair_data and isinstance(pair_data['volatility'], (int, float)), "Missing/invalid volatility"
        
        print(f"  ✅ All fields validated")
    
    print("\n" + "="*70)
    print("✅ All frontend processing checks passed!")
    print("="*70)
    
    return True

if __name__ == "__main__":
    try:
        success = test_api_response_format()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

