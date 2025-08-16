#!/usr/bin/env python3
"""
Simple GPT AI integration test
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.gpt_ai_analysis import gpt_ai_analyzer, MarketContext

def test_gpt_analysis():
    """Test GPT analysis with a sample economic event"""
    
    # Sample economic event
    test_event = {
        "id": 1,
        "title": "US CPI Data Release",
        "currency": "USD",
        "impact": "high",
        "expected": "3.1%",
        "previous": "3.2%",
        "time": "13:30 UTC",
        "date": "2024-01-15",
        "type": "ECONOMIC RELEASE"
    }
    
    # Sample market context
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
    
    print("🧪 Testing GPT AI Analysis Integration")
    print("=" * 50)
    
    try:
        # Test pre-event analysis
        print("\n📊 Testing Pre-Event Analysis...")
        pre_event_analysis = gpt_ai_analyzer.analyze_macro_event(
            test_event, 
            market_context, 
            "pre_event"
        )
        
        print(f"✅ Pre-event analysis completed!")
        print(f"   Model used: {pre_event_analysis.model_used}")
        print(f"   Cost estimate: ${pre_event_analysis.cost_estimate:.4f}")
        print(f"   Confidence score: {pre_event_analysis.confidence_score}%")
        print(f"   Cache hit: {pre_event_analysis.cache_hit}")
        
        # Display analysis structure
        print(f"\n📋 Analysis Structure:")
        print(f"   Headline: {pre_event_analysis.headline}")
        print(f"   Key Takeaway: {pre_event_analysis.key_takeaway}")
        print(f"   Forward Scenarios: {len(pre_event_analysis.forward_scenarios)} scenarios")
        print(f"   Event Summary: {len(pre_event_analysis.event_summary)} fields")
        print(f"   Market Reaction: {len(pre_event_analysis.market_reaction)} fields")
        print(f"   Implications & Takeaways: {len(pre_event_analysis.implications_takeaways)} fields")
        print(f"   Trading Plan: {len(pre_event_analysis.trading_plan)} fields")
        print(f"   Big Picture: {len(pre_event_analysis.big_picture)} fields")
        print(f"   Positioning Context: {len(pre_event_analysis.positioning_context)} fields")
        print(f"   Next Catalysts: {len(pre_event_analysis.next_catalysts)} items")
        
        # Test usage stats
        print("\n📊 Testing Usage Statistics...")
        stats = gpt_ai_analyzer.get_usage_stats()
        print(f"   Total cost: ${stats['total_cost']:.4f}")
        print(f"   API calls this hour: {stats['api_calls_this_hour']}")
        print(f"   Max calls per hour: {stats['max_calls_per_hour']}")
        
        # Test caching (should be a cache hit now)
        print("\n🔄 Testing Cache Functionality...")
        cached_analysis = gpt_ai_analyzer.analyze_macro_event(
            test_event, 
            market_context, 
            "pre_event"
        )
        
        print(f"   Cache hit: {cached_analysis.cache_hit}")
        print(f"   Cost estimate: ${cached_analysis.cost_estimate:.4f}")
        
        print("\n🎉 All tests completed successfully!")
        
        # Save sample analysis to file for inspection
        sample_analysis = {
            "pre_event": {
                "headline": pre_event_analysis.headline,
                "key_takeaway": pre_event_analysis.key_takeaway,
                "forward_scenarios": pre_event_analysis.forward_scenarios,
                "event_summary": pre_event_analysis.event_summary,
                "market_reaction": pre_event_analysis.market_reaction,
                "implications_takeaways": pre_event_analysis.implications_takeaways,
                "trading_plan": pre_event_analysis.trading_plan,
                "big_picture": pre_event_analysis.big_picture,
                "positioning_context": pre_event_analysis.positioning_context,
                "next_catalysts": pre_event_analysis.next_catalysts,
                "confidence_score": pre_event_analysis.confidence_score,
                "model_used": pre_event_analysis.model_used,
                "cost_estimate": pre_event_analysis.cost_estimate
            }
        }
        
        with open('gpt_analysis_sample.json', 'w') as f:
            json.dump(sample_analysis, f, indent=2)
        
        print(f"\n💾 Sample analysis saved to 'gpt_analysis_sample.json'")
        
        # Show a preview of the analysis
        print(f"\n📖 Analysis Preview:")
        print(f"   Event: {test_event['title']}")
        print(f"   Headline: {pre_event_analysis.headline}")
        print(f"   Key Takeaway: {pre_event_analysis.key_takeaway[:100]}...")
        print(f"   Forward Scenarios: {len(pre_event_analysis.forward_scenarios)} scenarios")
        print(f"   Market Reaction: {pre_event_analysis.market_reaction.get('price_action', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key before running this test.")
        exit(1)
    
    test_gpt_analysis()
