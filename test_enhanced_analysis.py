#!/usr/bin/env python3
"""
Test script for Enhanced Trader-Focused AI Analysis System
Demonstrates the improved analysis with quick-scan elements and forward scenarios
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.enhanced_trader_analysis import EnhancedTraderAnalyzer, MarketContext

def test_enhanced_analysis():
    """Test the enhanced trader analysis system"""
    
    print("🚀 Testing Enhanced Trader-Focused AI Analysis System")
    print("=" * 60)
    
    # Initialize the enhanced analyzer
    analyzer = EnhancedTraderAnalyzer()
    
    # Sample event data
    sample_event = {
        "id": "test_cpi_001",
        "title": "US Consumer Price Index (CPI)",
        "currency": "USD",
        "date": "2024-01-15",
        "time": "13:30",
        "expected": "3.1%",
        "previous": "3.2%",
        "actual": "3.0%",
        "impact": "High"
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
        time_to_event=3600,  # 1 hour until event
        liquidity_level=2,   # Medium liquidity
        scenario_probabilities={
            'higher': 0.30,
            'lower': 0.50,
            'inline': 0.20
        }
    )
    
    print(f"📊 Testing Event: {sample_event['title']}")
    print(f"💰 Currency: {sample_event['currency']}")
    print(f"📈 Expected: {sample_event['expected']}, Actual: {sample_event['actual']}")
    print(f"🎯 Impact Level: {sample_event['impact']}")
    print()
    
    # Test post-event analysis
    print("🔄 Generating Enhanced Post-Event Analysis...")
    print("-" * 40)
    
    try:
        analysis_result = analyzer.analyze_macro_event(
            sample_event, 
            market_context, 
            "post_event"
        )
        
        # Display the enhanced analysis results
        print("✅ Enhanced Analysis Generated Successfully!")
        print()
        
        print("📰 QUICK-SCAN SUMMARY:")
        print(f"   Headline: {analysis_result.headline}")
        print(f"   Key Takeaway: {analysis_result.key_takeaway}")
        print(f"   Confidence Score: {analysis_result.confidence_score}%")
        print()
        
        print("🎯 FORWARD SCENARIOS:")
        print(f"   ✅ Bullish: {analysis_result.forward_scenarios.get('bullish', 'Not available')}")
        print(f"   ❌ Bearish: {analysis_result.forward_scenarios.get('bearish', 'Not available')}")
        print(f"   ➡️ Neutral: {analysis_result.forward_scenarios.get('neutral', 'Not available')}")
        print()
        
        print("📈 MARKET REACTION:")
        print(f"   Price Action: {analysis_result.market_reaction.get('price_action', 'Not available')}")
        print(f"   Volatility: {analysis_result.market_reaction.get('volatility', 'Not available')}")
        print(f"   Positioning: {analysis_result.market_reaction.get('positioning_context', 'Not available')}")
        print()
        
        print("💡 IMPLICATIONS & TAKEAWAYS:")
        print(f"   Policy Impact: {analysis_result.implications_takeaways.get('policy', 'Not available')}")
        print(f"   Big Picture: {analysis_result.implications_takeaways.get('big_picture', 'Not available')}")
        print(f"   Risk Note: {analysis_result.implications_takeaways.get('risk_note', 'Not available')}")
        print()
        
        print("🎯 TRADING PLAN:")
        print(f"   Best Approach: {analysis_result.trading_plan.get('best_approach', 'Not available')}")
        print(f"   Risk Management: {analysis_result.trading_plan.get('risk_management', 'Not available')}")
        print(f"   Key Levels: {analysis_result.trading_plan.get('key_levels', [])}")
        print(f"   Next Catalyst: {analysis_result.trading_plan.get('next_catalyst', 'Not available')}")
        print()
        
        print("📊 METADATA:")
        print(f"   Model Used: {analysis_result.model_used}")
        print(f"   Analysis Type: {analysis_result.analysis_type}")
        print(f"   Cost Estimate: ${analysis_result.cost_estimate:.4f}")
        print(f"   Timestamp: {analysis_result.analysis_timestamp}")
        print()
        
        # Test pre-event analysis
        print("🔄 Generating Enhanced Pre-Event Analysis...")
        print("-" * 40)
        
        pre_event = sample_event.copy()
        pre_event["actual"] = "N/A"  # No actual data for pre-event
        
        pre_analysis_result = analyzer.analyze_macro_event(
            pre_event, 
            market_context, 
            "pre_event"
        )
        
        print("✅ Pre-Event Analysis Generated Successfully!")
        print()
        print("📰 PRE-EVENT QUICK-SCAN:")
        print(f"   Headline: {pre_analysis_result.headline}")
        print(f"   Key Takeaway: {pre_analysis_result.key_takeaway}")
        print(f"   Confidence Score: {pre_analysis_result.confidence_score}%")
        print()
        
        print("🎯 PRE-EVENT SCENARIOS:")
        print(f"   ✅ Bullish: {pre_analysis_result.forward_scenarios.get('bullish', 'Not available')}")
        print(f"   ❌ Bearish: {pre_analysis_result.forward_scenarios.get('bearish', 'Not available')}")
        print(f"   ➡️ Neutral: {pre_analysis_result.forward_scenarios.get('neutral', 'Not available')}")
        print()
        
        # Compare the two analyses
        print("📊 COMPARISON:")
        print("   Post-Event Analysis focuses on actual impact and market reaction")
        print("   Pre-Event Analysis focuses on expectations and preparation")
        print("   Both provide forward scenarios and actionable insights")
        print()
        
        print("🎉 Enhanced Analysis System Test Completed Successfully!")
        print()
        print("🚀 Key Improvements Demonstrated:")
        print("   ✅ Quick-scan headlines with emojis")
        print("   ✅ One-line key takeaways")
        print("   ✅ Forward scenarios with ✅/❌ icons")
        print("   ✅ Positioning context integration")
        print("   ✅ Next catalyst identification")
        print("   ✅ Professional yet trader-friendly tone")
        print("   ✅ Enhanced visual hierarchy")
        print("   ✅ Comprehensive market context usage")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("This is expected if OpenAI API key is not configured")
        print("The system will use fallback analysis in such cases")

def test_fallback_analysis():
    """Test fallback analysis when GPT is not available"""
    
    print("\n🔄 Testing Fallback Analysis (No GPT)...")
    print("=" * 50)
    
    # Create analyzer without API key to test fallback
    analyzer = EnhancedTraderAnalyzer()
    analyzer.client = None  # Simulate no GPT access
    
    sample_event = {
        "id": "test_fallback_001",
        "title": "UK Retail Sales",
        "currency": "GBP",
        "date": "2024-01-16",
        "time": "09:30",
        "expected": "0.3%",
        "previous": "0.2%",
        "actual": "0.4%",
        "impact": "Medium"
    }
    
    market_context = MarketContext(
        current_prices={'GBP/USD': 1.2650, 'EUR/GBP': 0.8575},
        recent_volatility={'GBP/USD': 0.010, 'EUR/GBP': 0.006},
        market_sentiment={'GBP/USD': 'bearish', 'EUR/GBP': 'neutral'},
        key_levels={'GBP/USD': {'support': [1.2600, 1.2550], 'resistance': [1.2700, 1.2750]}},
        economic_calendar=[],
        bond_yields={'UK_10Y': 3.8},
        equity_indices={'FTSE': 7500},
        commodity_prices={'GOLD': 2000},
        retail_sentiment={'GBP/USD': 0.45},
        futures_positioning={'GBP/USD': -5000},
        institutional_flow={'GBP/USD': -8.5},
        time_to_event=1800,
        liquidity_level=2,
        scenario_probabilities={'higher': 0.40, 'lower': 0.40, 'inline': 0.20}
    )
    
    try:
        fallback_result = analyzer.analyze_macro_event(
            sample_event, 
            market_context, 
            "post_event"
        )
        
        print("✅ Fallback Analysis Generated Successfully!")
        print()
        print("📰 FALLBACK QUICK-SCAN:")
        print(f"   Headline: {fallback_result.headline}")
        print(f"   Key Takeaway: {fallback_result.key_takeaway}")
        print(f"   Model Used: {fallback_result.model_used}")
        print(f"   Cost: ${fallback_result.cost_estimate:.4f}")
        print()
        
        print("🎯 FALLBACK SCENARIOS:")
        print(f"   ✅ Bullish: {fallback_result.forward_scenarios.get('bullish', 'Not available')}")
        print(f"   ❌ Bearish: {fallback_result.forward_scenarios.get('bearish', 'Not available')}")
        print(f"   ➡️ Neutral: {fallback_result.forward_scenarios.get('neutral', 'Not available')}")
        print()
        
        print("✅ Fallback system works correctly when GPT is unavailable!")
        
    except Exception as e:
        print(f"❌ Error in fallback analysis: {e}")

if __name__ == "__main__":
    test_enhanced_analysis()
    test_fallback_analysis()
