#!/usr/bin/env python3
"""
Direct test of enhanced trader analyzer
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.enhanced_trader_analysis import EnhancedTraderAnalyzer, MarketContext

def test_enhanced_analyzer():
    """Test the enhanced trader analyzer directly"""
    
    print("🧪 Testing Enhanced Trader Analyzer Directly")
    print("=" * 50)
    
    # Create analyzer instance
    analyzer = EnhancedTraderAnalyzer()
    print(f"✅ Analyzer created: {analyzer}")
    print(f"✅ Client available: {analyzer.client is not None}")
    print(f"✅ API key available: {analyzer.api_key is not None}")
    
    # Test event data
    test_event = {
        "id": "test_direct_001",
        "title": "US Consumer Price Index (CPI)",
        "currency": "USD",
        "date": "2024-01-15",
        "time": "13:30",
        "expected": "3.1%",
        "previous": "3.2%",
        "actual": "3.0%",
        "impact": "High"
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
            'EUR/USD': {'support': [1.0800, 1.0750, 1.0700], 'resistance': [1.0900, 1.0950, 1.1000]},
            'USD/JPY': {'support': [148.00, 147.50, 147.00], 'resistance': [149.00, 149.50, 150.00]},
            'GBP/USD': {'support': [1.2600, 1.2550, 1.2500], 'resistance': [1.2700, 1.2750, 1.2800]}
        },
        economic_calendar=[],
        bond_yields={'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8},
        equity_indices={'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000},
        commodity_prices={'GOLD': 2000, 'OIL': 75, 'SILVER': 25},
        retail_sentiment={
            'EUR/USD': 0.65,
            'USD/JPY': 0.35,
            'GBP/USD': 0.50,
            'USD/CHF': 0.70,
            'AUD/USD': 0.40,
            'USD/CAD': 0.55
        },
        futures_positioning={
            'EUR/USD': 15000,
            'USD/JPY': -8000,
            'GBP/USD': 5000,
            'USD/CHF': 12000,
            'AUD/USD': -3000,
            'USD/CAD': 2000
        },
        institutional_flow={
            'EUR/USD': 25.5,
            'USD/JPY': -15.2,
            'GBP/USD': 8.7,
            'USD/CHF': 18.3,
            'AUD/USD': -12.1,
            'USD/CAD': 5.4
        },
        time_to_event=3600,
        liquidity_level=2,
        scenario_probabilities={
            'higher': 0.30,
            'lower': 0.50,
            'inline': 0.20
        }
    )
    
    print(f"✅ Market context created")
    
    # Test analysis
    try:
        print("🔄 Running enhanced analysis...")
        result = analyzer.analyze_macro_event(test_event, market_context, "post_event")
        
        print("✅ Analysis completed!")
        print(f"   Model Used: {result.model_used}")
        print(f"   Headline: {result.headline}")
        print(f"   Key Takeaway: {result.key_takeaway}")
        print(f"   Confidence Score: {result.confidence_score}")
        
        if result.forward_scenarios:
            print("✅ Forward scenarios present:")
            for scenario, text in result.forward_scenarios.items():
                print(f"   {scenario}: {text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_analyzer()
