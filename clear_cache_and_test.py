#!/usr/bin/env python3
"""
Clear Cache and Test
Clear the cache and force a fresh ChatGPT analysis
"""

import requests
import json

def clear_cache_and_test():
    """Clear cache and test fresh ChatGPT analysis"""
    
    print("🧹 CLEARING CACHE AND TESTING FRESH ANALYSIS")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    # The exact event the user mentioned
    test_event = {
        'title': 'Unemployment Rate',
        'currency': 'GBP',
        'actual': '4.7%',
        'expected': '4.7%',
        'previous': '4.7%',
        'impact': 'High',
        'date': 'Tue, Aug 12',
        'time': '10:00 GST',
        'id': '8673173089515658000_clear_cache'  # Different ID to force fresh analysis
    }
    
    try:
        print("🚀 Calling enhanced-analysis endpoint with new ID to force fresh analysis...")
        response = requests.post(
            f"{base_url}/api/enhanced-analysis/{test_event['id']}",
            json={'event': test_event},
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            analysis = response.json()
            print("✅ Fresh analysis received successfully!")
            print()
            
            # Check if this is fresh
            metadata = analysis.get('metadata', {})
            model_used = metadata.get('model_used', 'unknown')
            cache_status = metadata.get('cache_status', 'unknown')
            
            print(f"🤖 Model Used: {model_used}")
            print(f"💰 Cache Status: {cache_status}")
            print()
            
            # Show the detailed content that should now be displayed
            print("📊 DETAILED CONTENT PREVIEW:")
            print("-" * 40)
            
            event_summary = analysis.get('event_summary', {})
            print(f"📋 Event Summary:")
            print(f"   Release: {event_summary.get('release', 'MISSING')}")
            print(f"   Currency: {event_summary.get('currency', 'MISSING')}")
            print(f"   Actual: {event_summary.get('actual', 'MISSING')}")
            print(f"   Expected: {event_summary.get('expected', 'MISSING')}")
            print(f"   Previous: {event_summary.get('previous', 'MISSING')}")
            print(f"   Bias: {event_summary.get('immediate_bias', 'MISSING')}")
            print(f"   Surprise: {event_summary.get('surprise_magnitude', 'MISSING')}")
            print()
            
            market_reaction = analysis.get('market_reaction', {})
            print(f"📈 Market Reaction:")
            print(f"   Expected Movement: {market_reaction.get('expected_movement', 'MISSING')}")
            print(f"   Volatility: {market_reaction.get('volatility_forecast', 'MISSING')}")
            print(f"   Duration: {market_reaction.get('duration', 'MISSING')}")
            print()
            
            economic_significance = analysis.get('economic_significance', {})
            print(f"🌍 Economic Significance:")
            print(f"   What it measures: {economic_significance.get('what_it_measures', 'MISSING')}")
            print(f"   Economic implications: {economic_significance.get('economic_implications', 'MISSING')}")
            print(f"   Policy relevance: {economic_significance.get('policy_relevance', 'MISSING')}")
            print()
            
            policy_implications = analysis.get('policy_implications', {})
            print(f"🏦 Policy Implications:")
            print(f"   Central Bank Impact: {policy_implications.get('central_bank_impact', 'MISSING')}")
            print(f"   Rate Expectations: {policy_implications.get('rate_expectations', 'MISSING')}")
            print(f"   Forward Guidance: {policy_implications.get('forward_guidance', 'MISSING')}")
            print()
            
            trading_strategy = analysis.get('trading_strategy', {})
            print(f"🎯 Trading Strategy:")
            print(f"   Entry Zones: {trading_strategy.get('entry_zones', 'MISSING')}")
            print(f"   Stop Loss: {trading_strategy.get('stop_loss', 'MISSING')}")
            print(f"   Take Profit: {trading_strategy.get('take_profit', 'MISSING')}")
            print(f"   Position Sizing: {trading_strategy.get('position_sizing', 'MISSING')}")
            print(f"   Time Horizon: {trading_strategy.get('time_horizon', 'MISSING')}")
            print()
            
            risk_assessment = analysis.get('risk_assessment', {})
            print(f"⚠️ Risk Assessment:")
            print(f"   Volatility Risk: {risk_assessment.get('volatility_risk', 'MISSING')}/10")
            print(f"   Policy Risk: {risk_assessment.get('policy_risk', 'MISSING')}/10")
            print(f"   Liquidity Risk: {risk_assessment.get('liquidity_risk', 'MISSING')}/10")
            print(f"   Confidence: {risk_assessment.get('confidence_level', 'MISSING')}")
            print(f"   Key Risks: {risk_assessment.get('key_risks', 'MISSING')}")
            print()
            
            # Check if this is fresh ChatGPT analysis
            if cache_status == 'fresh' and model_used in ['gpt-4-turbo-preview', 'gpt-3.5-turbo']:
                print("✅ This is FRESH CHATGPT ANALYSIS!")
                print("   - Should have detailed content")
                print("   - Not cached")
                print("   - Professional quality")
                
                # Check if we have detailed content
                expected_movement = market_reaction.get('expected_movement', '')
                economic_implications = economic_significance.get('economic_implications', '')
                
                if 'Expected price movements will depend on the actual data versus expectations' in expected_movement:
                    print("❌ Still showing generic content in market reaction!")
                else:
                    print("✅ Showing detailed content in market reaction!")
                
                if 'Economic context analysis based on the indicator type and current conditions' in economic_implications:
                    print("❌ Still showing generic content in economic implications!")
                else:
                    print("✅ Showing detailed content in economic implications!")
                    
            else:
                print(f"⚠️ This may not be fresh analysis: {cache_status}, {model_used}")
            
        else:
            print(f"❌ Analysis Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clear_cache_and_test()
