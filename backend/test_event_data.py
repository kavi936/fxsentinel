#!/usr/bin/env python3
"""
Test script to check event data structure
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append('.')

from services.gpt_ai_analysis import gpt_ai_analyzer, MarketContext

def test_event_data():
    """Test with different event data structures"""
    
    print("🧪 Testing Event Data Structure")
    print("=" * 50)
    
    # Test 1: Event data from economic calendar (what the web app uses)
    print("📊 Test 1: Economic Calendar Event Data")
    calendar_event = {
        "id": 1,
        "title": "US CPI Data Release",
        "currency": "USD",
        "impact": "High",
        "expected": "3.1%",
        "previous": "3.0%",
        "actual": "N/A",
        "time": "14:30 UTC",
        "date": "Tue, Aug 12"
    }
    
    print(f"   Event: {calendar_event}")
    
    # Test 2: Event data that works (from our test)
    print("\n📊 Test 2: Working Event Data")
    working_event = {
        "id": 1,
        "title": "US CPI Data Release",
        "currency": "USD",
        "impact": "High",
        "expected": "3.1%",
        "previous": "3.0%",
        "actual": "N/A",
        "time": "14:30 UTC",
        "date": "Tue, Aug 12"
    }
    
    print(f"   Event: {working_event}")
    
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
    
    # Test both event structures
    for i, event in enumerate([calendar_event, working_event], 1):
        print(f"\n🚀 Test {i}: Testing with event data")
        try:
            analysis = gpt_ai_analyzer.analyze_macro_event(
                event, 
                market_context, 
                "pre_event"
            )
            
            print(f"✅ Test {i} completed!")
            print(f"   Model Used: {analysis.model_used}")
            print(f"   Event Explanation Length: {len(analysis.general_overview.get('event_explanation', ''))}")
            print(f"   Market Logic Length: {len(analysis.general_overview.get('market_logic', ''))}")
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
    
    print(f"\n🎉 Event data testing completed!")

if __name__ == "__main__":
    test_event_data()
