#!/usr/bin/env python3
"""
Test script for Risk Appetite calculation
Tests various scenarios to ensure the calculation works correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.market_sentiment_service import MarketSentimentService
import numpy as np

def test_risk_appetite_scenario(name, forex_data, expected_level, expected_percentage_range):
    """Test a specific risk appetite scenario"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    service = MarketSentimentService()
    result = service._calculate_risk_appetite(forex_data)
    
    print(f"Input Data:")
    for pair, data in forex_data.items():
        if pair in ['USDJPY', 'USDCHF', 'EURJPY', 'GBPJPY', 'EURCHF', 'GBPCHF']:
            change_pct = data.get('changePercent', 'N/A')
            print(f"  {pair}: {change_pct}%")
    
    print(f"\nResult:")
    print(f"  Level: {result['level']}")
    print(f"  Percentage: {result['percentage']}")
    print(f"  Safe Havens: {result['safe_havens']}")
    
    # Check if result matches expected
    level_match = result['level'] == expected_level
    percentage_match = expected_percentage_range[0] <= result['percentage'] <= expected_percentage_range[1]
    
    if level_match and percentage_match:
        print(f"\n✅ PASS: Level and percentage match expected values")
        return True
    else:
        print(f"\n❌ FAIL:")
        if not level_match:
            print(f"   Expected level: {expected_level}, Got: {result['level']}")
        if not percentage_match:
            print(f"   Expected percentage range: {expected_percentage_range}, Got: {result['percentage']}")
        return False

def main():
    print("="*60)
    print("RISK APPETITE CALCULATION TESTS")
    print("="*60)
    
    # Test 1: Strong Risk-Off (Safe Havens Strengthening Significantly)
    print("\n" + "="*60)
    print("Test 1: Strong Risk-Off Scenario")
    print("="*60)
    test_data_1 = {
        'USDJPY': {'price': 150.00, 'change': -0.60, 'changePercent': -0.40},  # JPY strengthening
        'USDCHF': {'price': 0.88, 'change': -0.003, 'changePercent': -0.34},   # CHF strengthening
        'EURJPY': {'price': 161.00, 'change': -0.80, 'changePercent': -0.50},  # JPY strengthening
        'GBPJPY': {'price': 187.00, 'change': -0.50, 'changePercent': -0.27},  # JPY strengthening
        'EURCHF': {'price': 0.96, 'change': -0.004, 'changePercent': -0.42},   # CHF strengthening
        'GBPCHF': {'price': 1.12, 'change': -0.003, 'changePercent': -0.27},   # CHF strengthening
        'EURUSD': {'price': 1.08, 'change': 0.001, 'changePercent': 0.09},     # Not used
        'GBPUSD': {'price': 1.27, 'change': 0.002, 'changePercent': 0.16},     # Not used
    }
    test_risk_appetite_scenario(
        "Strong Risk-Off (Safe Havens Strengthening)",
        test_data_1,
        'low',
        (20, 30)  # Should be 25%
    )
    
    # Test 2: Moderate Risk-Off
    print("\n" + "="*60)
    print("Test 2: Moderate Risk-Off Scenario")
    print("="*60)
    test_data_2 = {
        'USDJPY': {'price': 150.00, 'change': -0.30, 'changePercent': -0.20},  # JPY strengthening moderately
        'USDCHF': {'price': 0.88, 'change': -0.0015, 'changePercent': -0.17}, # CHF strengthening moderately
        'EURJPY': {'price': 161.00, 'change': -0.32, 'changePercent': -0.20}, # JPY strengthening moderately
        'GBPJPY': {'price': 187.00, 'change': -0.19, 'changePercent': -0.10}, # JPY strengthening slightly
        'EURCHF': {'price': 0.96, 'change': -0.001, 'changePercent': -0.10},  # CHF strengthening slightly
        'GBPCHF': {'price': 1.12, 'change': 0.001, 'changePercent': 0.09},    # GBP strengthening (ignored)
        'EURUSD': {'price': 1.08, 'change': 0.001, 'changePercent': 0.09},
        'GBPUSD': {'price': 1.27, 'change': 0.002, 'changePercent': 0.16},
    }
    test_risk_appetite_scenario(
        "Moderate Risk-Off",
        test_data_2,
        'medium',
        (45, 55)  # Should be 50%
    )
    
    # Test 3: Risk-On (Safe Havens Weakening)
    print("\n" + "="*60)
    print("Test 3: Risk-On Scenario")
    print("="*60)
    test_data_3 = {
        'USDJPY': {'price': 150.00, 'change': 0.30, 'changePercent': 0.20},   # USD strengthening (risk-on)
        'USDCHF': {'price': 0.88, 'change': 0.002, 'changePercent': 0.23},    # USD strengthening (risk-on)
        'EURJPY': {'price': 161.00, 'change': 0.16, 'changePercent': 0.10},  # EUR strengthening (risk-on)
        'GBPJPY': {'price': 187.00, 'change': 0.19, 'changePercent': 0.10},  # GBP strengthening (risk-on)
        'EURCHF': {'price': 0.96, 'change': 0.001, 'changePercent': 0.10},   # EUR strengthening (risk-on)
        'GBPCHF': {'price': 1.12, 'change': 0.002, 'changePercent': 0.18},   # GBP strengthening (risk-on)
        'EURUSD': {'price': 1.08, 'change': 0.001, 'changePercent': 0.09},
        'GBPUSD': {'price': 1.27, 'change': 0.002, 'changePercent': 0.16},
    }
    test_risk_appetite_scenario(
        "Risk-On (Safe Havens Weakening)",
        test_data_3,
        'high',
        (70, 80)  # Should be 75%
    )
    
    # Test 4: Mixed Scenario (Some Safe Havens Strengthening, Some Not)
    print("\n" + "="*60)
    print("Test 4: Mixed Scenario")
    print("="*60)
    test_data_4 = {
        'USDJPY': {'price': 150.00, 'change': -0.15, 'changePercent': -0.10}, # JPY strengthening slightly
        'USDCHF': {'price': 0.88, 'change': 0.001, 'changePercent': 0.11},   # USD strengthening (ignored)
        'EURJPY': {'price': 161.00, 'change': -0.16, 'changePercent': -0.10}, # JPY strengthening slightly
        'GBPJPY': {'price': 187.00, 'change': 0.09, 'changePercent': 0.05},   # GBP strengthening (ignored)
        'EURCHF': {'price': 0.96, 'change': -0.0005, 'changePercent': -0.05}, # CHF strengthening slightly
        'GBPCHF': {'price': 1.12, 'change': 0.001, 'changePercent': 0.09},    # GBP strengthening (ignored)
        'EURUSD': {'price': 1.08, 'change': 0.001, 'changePercent': 0.09},
        'GBPUSD': {'price': 1.27, 'change': 0.002, 'changePercent': 0.16},
    }
    test_risk_appetite_scenario(
        "Mixed Scenario",
        test_data_4,
        'high',
        (70, 80)  # Should be 75% (low average movement)
    )
    
    # Test 5: Edge Case - Missing changePercent (should calculate from change/price)
    print("\n" + "="*60)
    print("Test 5: Missing changePercent (Fallback Calculation)")
    print("="*60)
    test_data_5 = {
        'USDJPY': {'price': 150.00, 'change': -0.30},  # No changePercent, should calculate
        'USDCHF': {'price': 0.88, 'change': -0.002},   # No changePercent, should calculate
        'EURJPY': {'price': 161.00, 'change': -0.32},  # No changePercent, should calculate
        'GBPJPY': {'price': 187.00, 'change': -0.19},  # No changePercent, should calculate
        'EURCHF': {'price': 0.96, 'change': -0.001},   # No changePercent, should calculate
        'GBPCHF': {'price': 1.12, 'change': 0.001},    # No changePercent, should calculate
    }
    test_risk_appetite_scenario(
        "Missing changePercent (Fallback)",
        test_data_5,
        'medium',  # Should calculate correctly
        (45, 55)
    )
    
    # Test 6: Edge Case - No Safe Haven Data
    print("\n" + "="*60)
    print("Test 6: No Safe Haven Data")
    print("="*60)
    test_data_6 = {
        'EURUSD': {'price': 1.08, 'change': 0.001, 'changePercent': 0.09},
        'GBPUSD': {'price': 1.27, 'change': 0.002, 'changePercent': 0.16},
        'AUDUSD': {'price': 0.66, 'change': -0.001, 'changePercent': -0.15},
    }
    result = test_risk_appetite_scenario(
        "No Safe Haven Data",
        test_data_6,
        'medium',  # Should default to medium
        (45, 55)
    )
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("All tests completed. Check results above.")
    print("\nTo verify frontend integration:")
    print("1. Start the backend server")
    print("2. Navigate to the Overview page")
    print("3. Check the 'Risk Appetite' condition in Market Conditions")
    print("4. Verify it shows the correct level and safe havens")

if __name__ == "__main__":
    main()

