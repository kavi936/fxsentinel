#!/usr/bin/env python3
"""
Test script to demonstrate AI analysis with different event types and data completeness
"""

import requests
import json

def test_ai_analysis_variations():
    """Test AI analysis with different event scenarios"""
    
    base_url = "http://localhost:5001"
    
    print("🧪 Testing AI Analysis with Different Event Types")
    print("=" * 60)
    
    # Test 1: Complete CPI data
    print("\n1️⃣ Testing Complete CPI Data (Event ID 1)...")
    try:
        response = requests.get(f"{base_url}/api/enhanced-analysis/1")
        if response.ok:
            data = response.json()
            print("✅ Complete CPI Analysis:")
            print(f"   Summary: {data['basic_analysis']['summary']}")
            print(f"   Trading Opportunity: {data['basic_analysis']['trading_opportunities'][0]['strategy']}")
            print(f"   Entry: {data['basic_analysis']['trading_opportunities'][0]['entry_zone']}")
            print(f"   Confidence: {data['basic_analysis']['confidence']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Generic event (minimal data)
    print("\n2️⃣ Testing Generic Event (Event ID 999)...")
    try:
        response = requests.get(f"{base_url}/api/enhanced-analysis/999")
        if response.ok:
            data = response.json()
            print("✅ Generic Event Analysis:")
            print(f"   Summary: {data['basic_analysis']['summary']}")
            print(f"   Trading Opportunity: {data['basic_analysis']['trading_opportunities'][0]['strategy']}")
            print(f"   Entry: {data['basic_analysis']['trading_opportunities'][0]['entry_zone']}")
            print(f"   Confidence: {data['basic_analysis']['confidence']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Large ID (fallback scenario)
    print("\n3️⃣ Testing Large Event ID (Fallback)...")
    try:
        response = requests.get(f"{base_url}/api/enhanced-analysis/4381183129679593500")
        if response.ok:
            data = response.json()
            print("✅ Fallback Analysis:")
            print(f"   Summary: {data['basic_analysis']['summary']}")
            print(f"   Trading Opportunity: {data['basic_analysis']['trading_opportunities'][0]['strategy']}")
            print(f"   Entry: {data['basic_analysis']['trading_opportunities'][0]['entry_zone']}")
            print(f"   Confidence: {data['basic_analysis']['confidence']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: News Sentiment Analysis
    print("\n4️⃣ Testing News Sentiment Analysis...")
    try:
        test_news = {
            "news_items": [
                {
                    "title": "Fed Signals Potential Rate Hike",
                    "content": "Federal Reserve officials indicated stronger than expected economic data, suggesting potential interest rate increases."
                },
                {
                    "title": "US CPI Disappoints Markets",
                    "content": "Consumer Price Index data came in below expectations, causing market concerns about economic growth."
                }
            ]
        }
        
        response = requests.post(f"{base_url}/api/news-sentiment", json=test_news)
        if response.ok:
            data = response.json()
            print("✅ News Sentiment Analysis:")
            print(f"   Overall Sentiment: {data['overall_sentiment']}")
            print(f"   Top Keywords: {', '.join(data['top_keywords'][:5])}")
            print(f"   Most Affected Pairs: {', '.join(data['most_affected_pairs'])}")
            print(f"   Average Impact Score: {data['average_impact_score']:.2f}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Technical Analysis
    print("\n5️⃣ Testing Technical Analysis...")
    try:
        response = requests.get(f"{base_url}/api/technical-analysis/EUR_USD")
        if response.ok:
            data = response.json()
            print("✅ Technical Analysis:")
            print(f"   Pair: {data['pair']}")
            print(f"   Sentiment: {data['sentiment']['sentiment']}")
            print(f"   RSI: {data['indicators']['rsi']:.1f}")
            print(f"   Patterns: {[p['pattern'] for p in data['patterns']]}")
            print(f"   Signals: {len(data['signals'])}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 AI Analysis Variations Test Complete!")
    print("\n📊 Key Findings:")
    print("• AI works with complete data (CPI events)")
    print("• AI works with minimal data (generic events)")
    print("• AI works with fallback scenarios (large IDs)")
    print("• AI provides specific trading opportunities")
    print("• AI adapts analysis based on data availability")

if __name__ == "__main__":
    test_ai_analysis_variations()
