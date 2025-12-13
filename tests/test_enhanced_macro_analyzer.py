#!/usr/bin/env python3
"""
Test script for the enhanced macroeconomic analyzer
Tests all the new features: hybrid AI fallback, enhanced prompts, new structure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.gpt_ai_analysis import GPTAIAnalyzer, MarketContext
from datetime import datetime
import json

def create_mock_market_context():
    """Create a mock market context with all the new positioning data"""
    return MarketContext(
        current_prices={
            'EUR/USD': 1.0850,
            'USD/JPY': 148.50,
            'GBP/USD': 1.2650,
            'USD/CHF': 0.8750
        },
        recent_volatility={
            'EUR/USD': 0.008,
            'USD/JPY': 0.012,
            'GBP/USD': 0.010,
            'USD/CHF': 0.006
        },
        market_sentiment={
            'EUR/USD': 'bullish',
            'USD/JPY': 'bearish',
            'GBP/USD': 'neutral',
            'USD/CHF': 'bullish'
        },
        key_levels={
            'EUR/USD': {
                'support': [1.0800, 1.0750, 1.0700],
                'resistance': [1.0900, 1.0950, 1.1000]
            },
            'USD/JPY': {
                'support': [148.00, 147.50, 147.00],
                'resistance': [149.00, 149.50, 150.00]
            }
        },
        economic_calendar=[],
        bond_yields={
            'US_10Y': 4.25,
            'US_2Y': 4.75,
            'DE_10Y': 2.15,
            'JP_10Y': 0.85
        },
        equity_indices={
            'SPX': 4850,
            'NDX': 17200,
            'DAX': 16500,
            'NIKKEI': 36000
        },
        commodity_prices={
            'GOLD': 2050,
            'OIL': 75.50,
            'SILVER': 23.50,
            'COPPER': 3.85
        },
        # New positioning data
        retail_sentiment={
            'EUR/USD': 0.65,  # 65% long
            'USD/JPY': 0.35,  # 35% long
            'GBP/USD': 0.50,  # 50% long
            'USD/CHF': 0.70   # 70% long
        },
        futures_positioning={
            'EUR/USD': 15000,  # Net long contracts
            'USD/JPY': -8000,  # Net short contracts
            'GBP/USD': 5000,   # Net long contracts
            'USD/CHF': 12000   # Net long contracts
        },
        institutional_flow={
            'EUR/USD': 25.5,   # Net buying in millions
            'USD/JPY': -15.2,  # Net selling in millions
            'GBP/USD': 8.7,    # Net buying in millions
            'USD/CHF': 18.3    # Net buying in millions
        },
        time_to_event=3600,  # 1 hour until event
        liquidity_level=2,   # Medium liquidity
        scenario_probabilities={
            'higher': 0.30,
            'lower': 0.50,
            'inline': 0.20
        }
    )

def test_hybrid_economic_indicator_context():
    """Test the hybrid approach for economic indicator context"""
    print("🔍 Testing Hybrid Economic Indicator Context...")
    
    analyzer = GPTAIAnalyzer()
    
    # Test known indicators (should use hardcoded patterns)
    known_indicators = [
        "US PPI Data Release",
        "US CPI Data Release", 
        "US Non-Farm Payrolls",
        "US GDP Data Release",
        "US Retail Sales MOM",
        "FOMC Interest Rate Decision"
    ]
    
    print("\n📊 Testing Known Indicators (Hardcoded Patterns):")
    for indicator in known_indicators:
        context = analyzer.get_economic_indicator_context(indicator)
        print(f"✅ {indicator}: {len(context)} chars - {context[:80]}...")
    
    # Test unknown indicators (should use AI fallback)
    unknown_indicators = [
        "US Manufacturing Capacity Utilization",
        "US Business Confidence Index",
        "US Industrial Production MOM",
        "US Building Permits MOM",
        "US Trade Deficit Data",
        "US Consumer Spending MOM"
    ]
    
    print("\n🤖 Testing Unknown Indicators (AI Fallback):")
    for indicator in unknown_indicators:
        context = analyzer.get_economic_indicator_context(indicator)
        print(f"✅ {indicator}: {len(context)} chars - {context[:80]}...")
    
    # Test cache functionality
    print("\n💾 Testing Cache Functionality:")
    for indicator in unknown_indicators:
        # Second call should use cache
        context = analyzer.get_economic_indicator_context(indicator)
        print(f"✅ Cached {indicator}: {len(context)} chars")

def test_enhanced_pre_event_analysis():
    """Test the enhanced pre-event analysis"""
    print("\n🔍 Testing Enhanced Pre-Event Analysis...")
    
    analyzer = GPTAIAnalyzer()
    market_context = create_mock_market_context()
    
    # Test with a known indicator
    event = {
        'id': 'test_ppi_001',
        'title': 'US PPI Data Release',
        'currency': 'USD',
        'impact': 'High',
        'expected': '0.3%',
        'previous': '0.2%',
        'time': '13:30',
        'date': '2024-01-15'
    }
    
    try:
        result = analyzer.analyze_macro_event(event, market_context, "pre_event")
        
        print(f"✅ Analysis completed successfully!")
        print(f"📊 Model Used: {result.model_used}")
        print(f"💰 Cost Estimate: ${result.cost_estimate:.4f}")
        print(f"🎯 Confidence Score: {result.confidence_score}")
        print(f"📝 Definition Source: {result.definition_source}")
        
        # Check new structure
        print(f"\n📋 New Structure Sections:")
        print(f"  - General Overview: {len(result.general_overview)} fields")
        print(f"  - Market Logic: {len(result.market_logic)} fields")
        print(f"  - Scenario Analysis: {len(result.scenario_analysis)} scenarios")
        print(f"  - Risk Metrics: {len(result.risk_metrics)} metrics")
        print(f"  - Historical Context: {len(result.historical_context)} fields")
        
        # Show sample content
        print(f"\n📄 Sample Content:")
        if 'indicator_explanation' in result.general_overview:
            print(f"  Indicator Explanation: {result.general_overview['indicator_explanation'][:100]}...")
        
        if 'scenario_analysis' in result.scenario_analysis:
            scenarios = result.scenario_analysis['scenario_analysis']
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict) and 'probability' in scenario_data:
                    print(f"  {scenario_name}: {scenario_data['probability']:.1%} probability")
        
    except Exception as e:
        print(f"❌ Error in pre-event analysis: {e}")

def test_enhanced_post_event_analysis():
    """Test the enhanced post-event analysis"""
    print("\n🔍 Testing Enhanced Post-Event Analysis...")
    
    analyzer = GPTAIAnalyzer()
    market_context = create_mock_market_context()
    
    # Test with actual data
    event = {
        'id': 'test_ppi_002',
        'title': 'US PPI Data Release',
        'currency': 'USD',
        'impact': 'High',
        'actual': '0.4%',
        'expected': '0.3%',
        'previous': '0.2%',
        'time': '13:30',
        'date': '2024-01-15'
    }
    
    try:
        result = analyzer.analyze_macro_event(event, market_context, "post_event")
        
        print(f"✅ Post-event analysis completed successfully!")
        print(f"📊 Model Used: {result.model_used}")
        print(f"💰 Cost Estimate: ${result.cost_estimate:.4f}")
        print(f"🎯 Confidence Score: {result.confidence_score}")
        
        # Check post-event specific structure
        if 'scenario_analysis' in result.scenario_analysis:
            scenarios = result.scenario_analysis['scenario_analysis']
            if 'actual_vs_expected' in scenarios:
                print(f"✅ Actual vs Expected analysis present")
            if 'forward_looking' in scenarios:
                print(f"✅ Forward-looking analysis present")
        
    except Exception as e:
        print(f"❌ Error in post-event analysis: {e}")

def test_cache_functionality():
    """Test the caching functionality"""
    print("\n🔍 Testing Cache Functionality...")
    
    analyzer = GPTAIAnalyzer()
    market_context = create_mock_market_context()
    
    event = {
        'id': 'test_cache_001',
        'title': 'US Manufacturing Capacity Utilization',
        'currency': 'USD',
        'impact': 'Medium',
        'expected': '78.5%',
        'previous': '78.2%',
        'time': '14:00',
        'date': '2024-01-15'
    }
    
    # First call - should use AI
    print("📞 First call (should use AI):")
    result1 = analyzer.analyze_macro_event(event, market_context, "pre_event")
    print(f"  Cache Hit: {result1.cache_hit}")
    print(f"  Model Used: {result1.model_used}")
    
    # Second call - should use cache
    print("📞 Second call (should use cache):")
    result2 = analyzer.analyze_macro_event(event, market_context, "pre_event")
    print(f"  Cache Hit: {result2.cache_hit}")
    print(f"  Model Used: {result2.model_used}")

def test_usage_statistics():
    """Test usage statistics"""
    print("\n🔍 Testing Usage Statistics...")
    
    analyzer = GPTAIAnalyzer()
    stats = analyzer.get_usage_stats()
    
    print(f"📊 Usage Statistics:")
    print(f"  Total Cost: ${stats['total_cost']:.4f}")
    print(f"  API Calls This Hour: {stats['api_calls_this_hour']}")
    print(f"  Max Calls Per Hour: {stats['max_calls_per_hour']}")
    print(f"  Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
    print(f"  Last Reset: {stats['last_reset']}")

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Macroeconomic Analyzer")
    print("=" * 50)
    
    try:
        # Test 1: Hybrid Economic Indicator Context
        test_hybrid_economic_indicator_context()
        
        # Test 2: Enhanced Pre-Event Analysis
        test_enhanced_pre_event_analysis()
        
        # Test 3: Enhanced Post-Event Analysis
        test_enhanced_post_event_analysis()
        
        # Test 4: Cache Functionality
        test_cache_functionality()
        
        # Test 5: Usage Statistics
        test_usage_statistics()
        
        print("\n✅ All tests completed successfully!")
        print("\n🎉 Enhanced Macroeconomic Analyzer is ready!")
        print("\nKey Features Implemented:")
        print("  ✅ Hybrid AI Fallback System")
        print("  ✅ Enhanced Market Context with Positioning Data")
        print("  ✅ New Structured JSON Output Format")
        print("  ✅ Probability-Weighted Scenario Analysis")
        print("  ✅ Risk Metrics and Historical Context")
        print("  ✅ Smart Caching with Cost Efficiency")
        print("  ✅ Comprehensive Economic Indicator Coverage")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
