#!/usr/bin/env python3
"""
Test Live Analysis Endpoint
Test the optimized ChatGPT analysis system with real API calls
"""

import requests
import json
from datetime import datetime

def test_live_analysis():
    """Test the live analysis endpoint with different events"""
    
    print("🚀 Testing Live Optimized ChatGPT Analysis")
    print("=" * 60)
    
    # Test events with different impact levels
    test_events = [
        {
            'id': 'test_1',
            'title': 'US CPI Data Release',
            'currency': 'USD',
            'actual': '3.2%',
            'expected': '3.1%',
            'previous': '3.0%',
            'impact': 'High',
            'time': '13:30',
            'date': '2024-01-15'
        },
        {
            'id': 'test_2', 
            'title': 'UK Unemployment Rate',
            'currency': 'GBP',
            'actual': '4.7%',
            'expected': '4.7%',
            'previous': '4.7%',
            'impact': 'High',
            'time': '09:30',
            'date': '2024-01-15'
        },
        {
            'id': 'test_3',
            'title': 'ECB Interest Rate Decision',
            'currency': 'EUR',
            'actual': '4.50%',
            'expected': '4.50%',
            'previous': '4.25%',
            'impact': 'High',
            'time': '12:45',
            'date': '2024-01-15'
        }
    ]
    
    base_url = "http://localhost:5001"
    
    for i, event in enumerate(test_events, 1):
        print(f"\n🔍 Test {i}: {event['title']}")
        print(f"   Currency: {event['currency']}")
        print(f"   Data: Actual {event['actual']}, Expected {event['expected']}, Previous {event['previous']}")
        print(f"   Impact: {event['impact']}")
        
        try:
            # Call the enhanced analysis endpoint
            response = requests.post(
                f"{base_url}/api/enhanced-analysis/{event['id']}",
                json={'event': event},
                timeout=30
            )
            
            if response.status_code == 200:
                analysis = response.json()
                
                print(f"   ✅ Analysis completed successfully")
                print(f"   📊 Response time: {response.elapsed.total_seconds():.2f}s")
                
                # Display key analysis components
                if 'event_summary' in analysis:
                    summary = analysis['event_summary']
                    print(f"   📈 Bias: {summary.get('immediate_bias', 'N/A')}")
                    print(f"   🎯 Surprise: {summary.get('surprise_magnitude', 'N/A')}")
                
                if 'market_reaction' in analysis:
                    market = analysis['market_reaction']
                    print(f"   📊 Expected Movement: {market.get('expected_movement', 'N/A')}")
                    print(f"   📈 Volatility: {market.get('volatility_forecast', 'N/A')}")
                
                if 'trading_strategy' in analysis:
                    strategy = analysis['trading_strategy']
                    print(f"   🎯 Entry Zones: {strategy.get('entry_zones', 'N/A')}")
                    print(f"   🛑 Stop Loss: {strategy.get('stop_loss', 'N/A')}")
                
                if 'risk_assessment' in analysis:
                    risk = analysis['risk_assessment']
                    print(f"   ⚠️ Volatility Risk: {risk.get('volatility_risk', 'N/A')}/10")
                    print(f"   🏦 Policy Risk: {risk.get('policy_risk', 'N/A')}/10")
                    print(f"   📊 Confidence: {risk.get('confidence_level', 'N/A')}%")
                
                if 'metadata' in analysis:
                    metadata = analysis['metadata']
                    print(f"   🤖 Model: {metadata.get('model_used', 'N/A')}")
                    print(f"   💰 Cache Status: {metadata.get('cache_status', 'N/A')}")
                
                # Show a sample of the full response
                print(f"\n   📄 Sample Analysis:")
                print(f"   {json.dumps(analysis, indent=2)[:500]}...")
                
            else:
                print(f"   ❌ Request failed with status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection error - make sure server is running")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 Testing Cache Performance")
    print("-" * 40)
    
    # Test the same event again to see cache performance
    print(f"\n🔄 Testing Cache Hit (Same Event)")
    test_event = test_events[0]  # US CPI
    
    try:
        # First call
        print(f"   📞 First call for {test_event['title']}")
        start_time = datetime.now()
        response1 = requests.post(
            f"{base_url}/api/enhanced-analysis/{test_event['id']}",
            json={'event': test_event},
            timeout=30
        )
        time1 = (datetime.now() - start_time).total_seconds()
        
        if response1.status_code == 200:
            analysis1 = response1.json()
            metadata1 = analysis1.get('metadata', {})
            print(f"   📊 Cache Status: {metadata1.get('cache_status', 'N/A')}")
            print(f"   ⏱️ Response Time: {time1:.2f}s")
        
        # Second call (should be faster if cached)
        print(f"   📞 Second call for {test_event['title']}")
        start_time = datetime.now()
        response2 = requests.post(
            f"{base_url}/api/enhanced-analysis/{test_event['id']}",
            json={'event': test_event},
            timeout=30
        )
        time2 = (datetime.now() - start_time).total_seconds()
        
        if response2.status_code == 200:
            analysis2 = response2.json()
            metadata2 = analysis2.get('metadata', {})
            print(f"   📊 Cache Status: {metadata2.get('cache_status', 'N/A')}")
            print(f"   ⏱️ Response Time: {time2:.2f}s")
            
            if time2 < time1:
                print(f"   ✅ Cache working: Second call was {time1 - time2:.2f}s faster")
            else:
                print(f"   ⚠️ Cache may not be working as expected")
        
    except Exception as e:
        print(f"   ❌ Cache test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Analysis Quality Assessment")
    print("-" * 40)
    
    print("\n✅ What to Look For:")
    print("   📈 Professional language and tone")
    print("   🎯 Specific trading levels and strategies")
    print("   📊 Comprehensive risk assessment")
    print("   💰 Cost-effective API usage")
    print("   ⚡ Fast response times (especially on cache hits)")
    
    print("\n❌ Red Flags:")
    print("   🚫 Generic or repetitive language")
    print("   🚫 Missing specific trading levels")
    print("   🚫 No risk assessment")
    print("   🚫 Slow response times")
    print("   🚫 High API costs")

if __name__ == "__main__":
    test_live_analysis()
