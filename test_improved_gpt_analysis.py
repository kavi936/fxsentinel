#!/usr/bin/env python3
"""
Test script for improved GPT analysis prompts
"""

import sys
import os
sys.path.append('backend')

from services.gpt_ai_analysis import GPTAIAnalyzer, MarketContext

def test_ppi_analysis():
    """Test PPI analysis with improved prompts"""
    
    # Create test event data
    event = {
        'id': 'test_ppi_001',
        'title': 'US PPI Data Release',
        'currency': 'USD',
        'impact': 'High',
        'expected': '0.3%',
        'previous': '0.2%',
        'actual': 'N/A',
        'time': '13:30 UTC',
        'date': '2024-01-15'
    }
    
    # Create market context
    market_context = MarketContext(
        current_prices={
            'EUR/USD': 1.0850,
            'USD/JPY': 148.50,
            'GBP/USD': 1.2650,
            'USD/CHF': 0.8650,
            'AUD/USD': 0.6650,
            'USD/CAD': 1.3550
        },
        recent_volatility={
            'EUR/USD': 0.008,
            'USD/JPY': 0.012,
            'GBP/USD': 0.010,
            'USD/CHF': 0.007,
            'AUD/USD': 0.009,
            'USD/CAD': 0.006
        },
        market_sentiment={
            'EUR/USD': 'neutral',
            'USD/JPY': 'bullish',
            'GBP/USD': 'bearish',
            'USD/CHF': 'neutral',
            'AUD/USD': 'neutral',
            'USD/CAD': 'neutral'
        },
        key_levels={
            'EUR/USD': {'support': 1.0800, 'resistance': 1.0900},
            'USD/JPY': {'support': 148.00, 'resistance': 149.00},
            'GBP/USD': {'support': 1.2600, 'resistance': 1.2700}
        },
        economic_calendar=[],
        bond_yields={'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8},
        equity_indices={'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000},
        commodity_prices={'GOLD': 2000, 'OIL': 75, 'SILVER': 25}
    )
    
    # Initialize analyzer
    analyzer = GPTAIAnalyzer()
    
    print("🔍 Testing PPI Analysis with Improved Prompts")
    print("=" * 60)
    
    # Test the economic indicator context
    context = analyzer._get_economic_indicator_context("US PPI Data Release")
    print(f"📊 Economic Context Generated:")
    print(context)
    print()
    
    # Test the prompt generation
    prompt = analyzer._build_pre_event_prompt(event, market_context)
    print(f"🤖 Generated Prompt Length: {len(prompt)} characters")
    print(f"🤖 Prompt contains PPI context: {'PPI' in prompt}")
    print(f"🤖 Prompt contains specific guidance: {'specific' in prompt}")
    print()
    
    # Test fallback analysis
    fallback = analyzer._get_fallback_analysis(event, "pre_event")
    print(f"🔄 Fallback Analysis:")
    print(f"   Event Explanation: {fallback.general_overview['event_explanation'][:100]}...")
    print(f"   Market Logic: {fallback.general_overview['market_logic'][:100]}...")
    print(f"   Contains PPI context: {'PPI' in fallback.general_overview['event_explanation']}")
    print()
    
    print("✅ Test completed successfully!")

def test_different_indicators():
    """Test different economic indicators"""
    
    indicators = [
        "US CPI Data Release",
        "US Non-Farm Payrolls",
        "US GDP Data Release",
        "US Retail Sales",
        "US Manufacturing PMI",
        "FOMC Interest Rate Decision",
        "US Unemployment Rate",
        "US Housing Starts",
        "US Trade Balance",
        "US Consumer Confidence",
        "US Industrial Production",
        "US Core PCE Inflation"
    ]
    
    analyzer = GPTAIAnalyzer()
    
    print("🔍 Testing Different Economic Indicators")
    print("=" * 60)
    
    for indicator in indicators:
        context = analyzer._get_economic_indicator_context(indicator)
        print(f"📊 {indicator}:")
        print(f"   Context Length: {len(context)} characters")
        print(f"   Contains specific info: {'measures' in context or 'indicator' in context or 'data' in context or 'drivers' in context}")
        print(f"   Sample: {context.strip()[:80]}...")
        print()

if __name__ == "__main__":
    test_ppi_analysis()
    print("\n" + "=" * 60 + "\n")
    test_different_indicators()
