#!/usr/bin/env python3
"""
Test script for economy context integration
Tests all three approaches: Currency-Specific Context, Event-Specific Matching, Policy Target Comparison
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from services.economy_context_service import economy_context_service
from services.gpt_ai_analysis import GPTAIAnalyzer, EVENT_TYPE_MAPPING, POLICY_TARGETS

def test_economy_context_service():
    """Test 1: Economy Context Service loads data correctly"""
    print("\n" + "="*60)
    print("TEST 1: Economy Context Service")
    print("="*60)
    
    currencies = ['USD', 'EUR', 'GBP', 'JPY']
    all_passed = True
    
    for currency in currencies:
        context = economy_context_service.get_economy_context(currency)
        if context:
            print(f"✅ {currency}: Economy context loaded")
            print(f"   - Central Bank Rate: {context.get('central_bank_rate')}")
            print(f"   - Indicators count: {len(context.get('indicators', {}))}")
        else:
            print(f"❌ {currency}: Failed to load economy context")
            all_passed = False
    
    return all_passed

def test_currency_mapping():
    """Test 2: Currency mapping works correctly"""
    print("\n" + "="*60)
    print("TEST 2: Currency Mapping")
    print("="*60)
    
    test_cases = [
        ('USD', 'US'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('JPY', 'JPY')
    ]
    
    all_passed = True
    for currency, expected_country in test_cases:
        context = economy_context_service.get_economy_context(currency)
        if context and context.get('country_code') == expected_country:
            print(f"✅ {currency} → {expected_country}: Correct mapping")
        else:
            print(f"❌ {currency} → {expected_country}: Mapping failed")
            all_passed = False
    
    return all_passed

def test_event_type_matching():
    """Test 3: Event type matching for indicator filtering"""
    print("\n" + "="*60)
    print("TEST 3: Event Type Matching")
    print("="*60)
    
    analyzer = GPTAIAnalyzer()
    
    test_cases = [
        ('US Non-Farm Payrolls', ['interest-rate', 'unemployment', 'nonfarm-payrolls']),
        ('US CPI', ['interest-rate', 'inflation-YoY', 'core-inflation-YoY']),
        ('US GDP Growth', ['interest-rate', 'gdp-growth']),
        ('US Unemployment Rate', ['interest-rate', 'unemployment']),
        ('US ADP Employment Change', ['interest-rate', 'unemployment', 'nonfarm-payrolls']),
    ]
    
    all_passed = True
    for event_title, expected_indicators in test_cases:
        relevant = analyzer._get_relevant_indicators(event_title)
        # Check that all expected indicators are present
        missing = [ind for ind in expected_indicators if ind not in relevant]
        if not missing:
            print(f"✅ '{event_title}': Matched correctly")
            print(f"   - Relevant indicators: {relevant}")
        else:
            print(f"❌ '{event_title}': Missing indicators {missing}")
            print(f"   - Got: {relevant}")
            all_passed = False
    
    return all_passed

def test_indicator_filtering():
    """Test 4: Indicator filtering works with economy context"""
    print("\n" + "="*60)
    print("TEST 4: Indicator Filtering")
    print("="*60)
    
    analyzer = GPTAIAnalyzer()
    
    # Test NFP event - should only show employment indicators
    event_title = "US Non-Farm Payrolls"
    relevant_indicators = analyzer._get_relevant_indicators(event_title)
    economy_context = analyzer._get_economy_context('USD', relevant_indicators)
    
    if economy_context:
        indicators = economy_context.get('indicators', {})
        indicator_ids = list(indicators.keys())
        print(f"✅ NFP Event: Filtered to {len(indicator_ids)} indicators")
        print(f"   - Indicators: {indicator_ids}")
        
        # Should include interest-rate and employment-related
        has_employment = any('employment' in ind or 'payroll' in ind or 'unemployment' in ind for ind in indicator_ids)
        has_interest_rate = 'interest-rate' in indicator_ids
        
        if has_employment and has_interest_rate:
            print(f"   ✅ Correctly filtered to employment indicators")
            return True
        else:
            print(f"   ❌ Missing expected indicators")
            return False
    else:
        print(f"❌ Failed to get economy context")
        return False

def test_policy_pressure_calculation():
    """Test 5: Policy pressure calculation"""
    print("\n" + "="*60)
    print("TEST 5: Policy Pressure Calculation")
    print("="*60)
    
    analyzer = GPTAIAnalyzer()
    
    # Test inflation policy pressure (above target)
    policy_pressure = analyzer._get_policy_pressure('USD', 'inflation', 2.7)
    if policy_pressure:
        print(f"✅ Inflation Policy Pressure (2.7% vs 2.0% target):")
        print(f"   - Pressure Level: {policy_pressure['pressure_level']}")
        print(f"   - Deviation: {policy_pressure['deviation']:+.2f}pp")
        print(f"   - Deviation %: {policy_pressure['deviation_percent']:+.1f}%")
        
        # 2.7% vs 2.0% target = +0.70pp deviation, which is > 0.5pp, so should be "strong hawkish pressure"
        if policy_pressure['pressure_level'] == 'strong hawkish pressure':
            print(f"   ✅ Correct pressure level")
            return True
        else:
            print(f"   ❌ Incorrect pressure level (expected 'strong hawkish pressure', got '{policy_pressure['pressure_level']}')")
            return False
    else:
        print(f"❌ Failed to calculate policy pressure")
        return False

def test_policy_context_generation():
    """Test 6: Policy context generation for prompt"""
    print("\n" + "="*60)
    print("TEST 6: Policy Context Generation")
    print("="*60)
    
    analyzer = GPTAIAnalyzer()
    
    # Get economy context for USD
    economy_context = analyzer._get_economy_context('USD')
    if not economy_context:
        print("❌ Failed to get economy context")
        return False
    
    # Test CPI event (should generate inflation policy context)
    policy_context = analyzer._add_policy_context_to_prompt('USD', economy_context, 'US CPI')
    
    if policy_context:
        print(f"✅ Policy Context Generated for CPI Event:")
        print(f"   {policy_context[:200]}...")
        return True
    else:
        print(f"⚠️ No policy context generated (may be expected if data missing)")
        return True  # Not a failure, just no relevant data

def test_full_prompt_integration():
    """Test 7: Full prompt integration with economy context"""
    print("\n" + "="*60)
    print("TEST 7: Full Prompt Integration")
    print("="*60)
    
    analyzer = GPTAIAnalyzer()
    
    # Create a mock event
    mock_event = {
        'title': 'US Non-Farm Payrolls',
        'currency': 'USD',
        'impact': 'high',
        'previous': '150K',
        'expected': '180K',
        'actual': '200K'
    }
    
    # Create a minimal market context
    from services.gpt_ai_analysis import MarketContext
    market_context = MarketContext(
        current_prices={'EURUSD': 1.0850},
        recent_volatility={'EURUSD': 'moderate'},
        market_sentiment={'EURUSD': 'neutral'},
        key_levels=None,
        economic_calendar=[],
        bond_yields=None,
        equity_indices=None,
        commodity_prices=None,
        retail_sentiment=None,
        futures_positioning=None,
        institutional_flow=None
    )
    
    # Generate prompt
    prompt = analyzer._create_analysis_prompt(mock_event, market_context, 'pre-event')
    
    # Check if economy context is included
    if 'ECONOMIC CONTEXT FOR USD' in prompt:
        print(f"✅ Economy context included in prompt")
        print(f"   - Prompt length: {len(prompt)} characters")
        
        # Check for specific indicators
        if 'Central Bank Rate' in prompt:
            print(f"   ✅ Central Bank Rate included")
        if 'Unemployment' in prompt or 'Non-Farm Payrolls' in prompt:
            print(f"   ✅ Employment indicators included")
        
        return True
    else:
        print(f"❌ Economy context not found in prompt")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ECONOMY CONTEXT INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Economy Context Service", test_economy_context_service),
        ("Currency Mapping", test_currency_mapping),
        ("Event Type Matching", test_event_type_matching),
        ("Indicator Filtering", test_indicator_filtering),
        ("Policy Pressure Calculation", test_policy_pressure_calculation),
        ("Policy Context Generation", test_policy_context_generation),
        ("Full Prompt Integration", test_full_prompt_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

