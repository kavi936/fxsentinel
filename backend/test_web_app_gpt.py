#!/usr/bin/env python3
"""
Test script to simulate the web app GPT call
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append('.')

from services.gpt_ai_analysis import gpt_ai_analyzer, MarketContext

def test_web_app_gpt_call():
    """Test the exact same GPT call that the web app would make"""
    
    print("🧪 Testing Web App GPT Call")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"🔍 Environment Check:")
    print(f"   OPENAI_API_KEY: {'SET' if api_key else 'NOT SET'}")
    if api_key:
        print(f"   API Key Preview: {api_key[:10]}...{api_key[-4:]}")
    
    # Create the same event data that the web app would use
    event = {
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
    
    # Create the same market context that the web app would use
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
    
    # Determine analysis type (same logic as web app)
    has_actual_data = event.get('actual') and event.get('actual') not in ['N/A', '', None]
    analysis_type = "post_event" if has_actual_data else "pre_event"
    
    print(f"📊 Analysis Parameters:")
    print(f"   Event: {event['title']}")
    print(f"   Analysis Type: {analysis_type}")
    print(f"   Has Actual Data: {has_actual_data}")
    
    try:
        # Make the exact same call that the web app would make
        print(f"\n🚀 Making GPT API call...")
        gpt_analysis = gpt_ai_analyzer.analyze_macro_event(
            event, 
            market_context, 
            analysis_type
        )
        
        print(f"✅ GPT Analysis completed!")
        print(f"   Model Used: {gpt_analysis.model_used}")
        print(f"   Cache Hit: {gpt_analysis.cache_hit}")
        print(f"   Cost Estimate: ${gpt_analysis.cost_estimate:.4f}")
        
        # Check the content lengths
        print(f"\n📊 Content Analysis:")
        print(f"   Event Explanation Length: {len(gpt_analysis.general_overview.get('event_explanation', ''))}")
        print(f"   Market Logic Length: {len(gpt_analysis.general_overview.get('market_logic', ''))}")
        print(f"   Detailed Analysis Length: {len(gpt_analysis.immediate_impact.get('detailed_analysis', ''))}")
        print(f"   Historical Context Length: {len(gpt_analysis.context_expectations.get('historical_context', ''))}")
        
        # Show sample content
        print(f"\n📖 Sample Content:")
        event_explanation = gpt_analysis.general_overview.get('event_explanation', '')
        print(f"   Event Explanation: {event_explanation[:100]}...")
        
        market_logic = gpt_analysis.general_overview.get('market_logic', '')
        print(f"   Market Logic: {market_logic[:100]}...")
        
        detailed_analysis = gpt_analysis.immediate_impact.get('detailed_analysis', '')
        print(f"   Detailed Analysis: {detailed_analysis[:100]}...")
        
        # Check if this is fallback content
        if gpt_analysis.model_used == "fallback":
            print(f"\n⚠️ WARNING: Using fallback analysis!")
            print(f"   This means the GPT API call failed.")
        else:
            print(f"\n✅ SUCCESS: Using real GPT analysis!")
            print(f"   Detailed paragraphs should be displayed.")
        
        return gpt_analysis
        
    except Exception as e:
        print(f"❌ Error in GPT analysis: {e}")
        print(f"   Error Type: {type(e).__name__}")
        return None

if __name__ == "__main__":
    result = test_web_app_gpt_call()
    if result:
        print(f"\n🎉 Test completed successfully!")
    else:
        print(f"\n💥 Test failed!")
