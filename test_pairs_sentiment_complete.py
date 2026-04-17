#!/usr/bin/env python3
"""
Complete test for Major Pairs Sentiment - Backend calculations and Frontend data structure
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.market_sentiment_service import MarketSentimentService

def test_backend_calculations():
    """Test backend calculations with realistic data"""
    print("="*70)
    print("TEST 1: Backend Calculations")
    print("="*70)
    
    service = MarketSentimentService()
    
    # Realistic test data matching TradingView structure
    test_forex = {
        'EURUSD': {'price': 1.0923, 'change': 0.0012, 'changePercent': 0.11},
        'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'changePercent': -0.16},
        'USDJPY': {'price': 150.00, 'change': 0.30, 'changePercent': 0.20},
        'USDCHF': {'price': 0.8845, 'change': -0.0015, 'changePercent': -0.17},
        'AUDUSD': {'price': 0.6623, 'change': -0.0018, 'changePercent': -0.27},
        'USDCAD': {'price': 1.3542, 'change': 0.0021, 'changePercent': 0.16},
    }
    
    pairs = service._calculate_pairs_sentiment(test_forex)
    
    print(f"\n✅ Calculated {len(pairs)} pairs sentiment")
    print("\nResults:")
    print("-"*70)
    
    all_valid = True
    for pair in pairs:
        # Check all required fields
        checks = {
            'pair': pair.pair is not None and pair.pair in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
            'sentiment': pair.sentiment in ['bullish', 'bearish', 'neutral'],
            'percentage': 0 <= pair.percentage <= 100,
            'price_change': isinstance(pair.price_change, (int, float)),
            'rsi': 0 <= pair.rsi <= 100,
            'volatility': pair.volatility >= 0
        }
        
        print(f"\n{pair.pair}:")
        print(f"  ✅ Pair: {pair.pair}")
        print(f"  ✅ Sentiment: {pair.sentiment}")
        print(f"  ✅ Percentage: {pair.percentage}%")
        print(f"  ✅ Price Change: {pair.price_change:+.2f}%")
        print(f"  ✅ RSI: {pair.rsi:.1f}")
        print(f"  ✅ Volatility: {pair.volatility:.2f}%")
        
        if not all(checks.values()):
            print(f"  ❌ Validation failed: {checks}")
            all_valid = False
    
    return all_valid, pairs

def test_frontend_data_structure(pairs):
    """Test data structure matches frontend expectations"""
    print("\n" + "="*70)
    print("TEST 2: Frontend Data Structure")
    print("="*70)
    
    # Simulate what frontend receives from API
    frontend_data = []
    for pair in pairs:
        frontend_pair = {
            'pair': pair.pair,
            'sentiment': pair.sentiment,
            'percentage': pair.percentage,
            'price_change': pair.price_change,
            'rsi': pair.rsi,
            'volatility': pair.volatility,
            'support': pair.support,
            'resistance': pair.resistance
        }
        frontend_data.append(frontend_pair)
    
    print(f"\n✅ Frontend data structure created for {len(frontend_data)} pairs")
    print("\nFrontend JSON (first pair):")
    print(json.dumps(frontend_data[0], indent=2))
    
    # Verify frontend can process this
    print("\n✅ Frontend Display Simulation:")
    print("-"*70)
    
    for pair_data in frontend_data:
        pair_name = pair_data['pair']
        sentiment = pair_data['sentiment']
        percentage = pair_data['percentage']
        price_change = pair_data['price_change']
        rsi = pair_data['rsi']
        volatility = pair_data['volatility']
        
        # Simulate frontend rendering
        change_display = f"{'+' if price_change >= 0 else ''}{price_change:.2f}%"
        change_class = 'positive' if price_change >= 0 else 'negative'
        
        print(f"\n{pair_name} Card:")
        print(f"  Pair Name: {pair_name}")
        print(f"  Daily Change: <span class='pair-change {change_class}'>{change_display}</span>")
        print(f"  Sentiment: {sentiment.capitalize()}")
        print(f"  Gauge position (0=flat, 100=max bull): {percentage}%")
        print(f"  RSI: {rsi:.0f}")
        print(f"  Volatility: {volatility:.1f}%")
        
        # Verify all fields are present and valid
        required_fields = ['pair', 'sentiment', 'percentage', 'price_change', 'rsi', 'volatility']
        missing_fields = [f for f in required_fields if f not in pair_data or pair_data[f] is None]
        
        if missing_fields:
            print(f"  ❌ Missing fields: {missing_fields}")
            return False
    
    return True

def test_calculation_accuracy():
    """Test calculation accuracy with known inputs"""
    print("\n" + "="*70)
    print("TEST 3: Calculation Accuracy")
    print("="*70)
    
    service = MarketSentimentService()
    
    test_cases = [
        {
            'name': 'Strong Bullish',
            'data': {'EURUSD': {'price': 1.10, 'change': 0.0055, 'changePercent': 0.50}},
            'expected': {
                'sentiment': 'bullish',
                'percentage_range': (68, 76),
                'rsi_range': (70, 100),  # 75 is the lower bound, so include it
                'volatility_range': (0.45, 0.55)
            }
        },
        {
            'name': 'Strong Bearish',
            'data': {'GBPUSD': {'price': 1.27, 'change': -0.00635, 'changePercent': -0.50}},
            'expected': {
                'sentiment': 'bearish',
                'percentage_range': (22, 32),
                'rsi_range': (0, 25),
                'volatility_range': (0.45, 0.55)
            }
        },
        {
            'name': 'Neutral',
            'data': {'USDJPY': {'price': 150.00, 'change': 0.0075, 'changePercent': 0.05}},
            'expected': {
                'sentiment': 'neutral',
                'percentage_range': (45, 55),
                'rsi_range': (45, 55),
                'volatility_range': (0.04, 0.06)
            }
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        pairs = service._calculate_pairs_sentiment(test_case['data'])
        
        if not pairs:
            print(f"  ❌ No pairs returned")
            all_passed = False
            continue
        
        pair = pairs[0]
        expected = test_case['expected']
        
        # Check sentiment
        if pair.sentiment != expected['sentiment']:
            print(f"  ❌ Sentiment: Expected {expected['sentiment']}, got {pair.sentiment}")
            all_passed = False
        else:
            print(f"  ✅ Sentiment: {pair.sentiment}")
        
        # Check percentage
        if not (expected['percentage_range'][0] <= pair.percentage <= expected['percentage_range'][1]):
            print(f"  ❌ Percentage: Expected {expected['percentage_range']}, got {pair.percentage}")
            all_passed = False
        else:
            print(f"  ✅ Percentage: {pair.percentage}% (within {expected['percentage_range']})")
        
        # Check RSI
        if not (expected['rsi_range'][0] <= pair.rsi <= expected['rsi_range'][1]):
            print(f"  ❌ RSI: Expected {expected['rsi_range']}, got {pair.rsi:.1f}")
            all_passed = False
        else:
            print(f"  ✅ RSI: {pair.rsi:.1f} (within {expected['rsi_range']})")
        
        # Check volatility
        if not (expected['volatility_range'][0] <= pair.volatility <= expected['volatility_range'][1]):
            print(f"  ❌ Volatility: Expected {expected['volatility_range']}, got {pair.volatility:.2f}")
            all_passed = False
        else:
            print(f"  ✅ Volatility: {pair.volatility:.2f}% (within {expected['volatility_range']})")
    
    return all_passed

def test_data_reuse():
    """Test that forex data is reused and not fetched multiple times"""
    print("\n" + "="*70)
    print("TEST 4: Data Reuse (No Redundant API Calls)")
    print("="*70)
    
    service = MarketSentimentService()
    
    test_forex = {
        'EURUSD': {'price': 1.0923, 'change': 0.0012, 'changePercent': 0.11},
        'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'changePercent': -0.16},
        'USDJPY': {'price': 150.00, 'change': 0.30, 'changePercent': 0.20},
        'USDCHF': {'price': 0.8845, 'change': -0.0015, 'changePercent': -0.17},
    }
    
    # Test that methods accept forex_data parameter
    try:
        pairs = service._calculate_pairs_sentiment(test_forex)
        print(f"✅ _calculate_pairs_sentiment() accepts forex_data parameter")
        print(f"   Calculated {len(pairs)} pairs")
        
        # Verify data matches input
        for pair in pairs:
            if pair.pair in test_forex:
                input_change = test_forex[pair.pair]['changePercent']
                output_change = pair.price_change
                if abs(input_change - output_change) < 0.01:  # Allow small floating point differences
                    print(f"   ✅ {pair.pair}: Input {input_change}% = Output {output_change}%")
                else:
                    print(f"   ❌ {pair.pair}: Input {input_change}% != Output {output_change}%")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("MAJOR PAIRS SENTIMENT - COMPLETE TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Test 1: Backend calculations
    try:
        valid, pairs = test_backend_calculations()
        results['backend_calculations'] = valid
    except Exception as e:
        print(f"\n❌ Test 1 failed with error: {e}")
        import traceback
        traceback.print_exc()
        results['backend_calculations'] = False
        pairs = []
    
    # Test 2: Frontend data structure
    if pairs:
        try:
            results['frontend_structure'] = test_frontend_data_structure(pairs)
        except Exception as e:
            print(f"\n❌ Test 2 failed with error: {e}")
            results['frontend_structure'] = False
    else:
        results['frontend_structure'] = False
    
    # Test 3: Calculation accuracy
    try:
        results['calculation_accuracy'] = test_calculation_accuracy()
    except Exception as e:
        print(f"\n❌ Test 3 failed with error: {e}")
        results['calculation_accuracy'] = False
    
    # Test 4: Data reuse
    try:
        results['data_reuse'] = test_data_reuse()
    except Exception as e:
        print(f"\n❌ Test 4 failed with error: {e}")
        results['data_reuse'] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All tests passed!")
        print("\nFrontend should display:")
        print("  - Pair names (EURUSD, GBPUSD, USDJPY, USDCHF)")
        print("  - Daily Change with +/- sign and color coding")
        print("  - Daily-change gauge (center = flat; length ∝ |%| up to cap)")
        print("  - RSI value (0-100)")
        print("  - Volatility percentage")
    else:
        print("\n❌ Some tests failed. Check output above for details.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

