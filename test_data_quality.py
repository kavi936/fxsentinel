#!/usr/bin/env python3
"""
Test script to verify data quality improvements
Shows the difference between old and new analysis systems
"""

import requests
import json
from datetime import datetime

def test_data_quality_improvements():
    """Test the new data quality improvements"""
    print("🧪 Testing Data Quality Improvements")
    print("=" * 50)
    
    # Test 1: Valid Event Data
    print("\n1️⃣ Testing Valid Event Data:")
    valid_event = {
        "id": "test_123",
        "title": "US Non-Farm Payrolls 2025",
        "currency": "USD",
        "impact": "high",
        "expected": "180K",
        "previous": "175K",
        "actual": "N/A",
        "date": "Fri, Jan 10",
        "time": "13:30 UTC"
    }
    
    print(f"   Event: {valid_event['title']}")
    print(f"   Currency: {valid_event['currency']}")
    print(f"   Expected: {valid_event['expected']}")
    print(f"   Previous: {valid_event['previous']}")
    
    # Test 2: Invalid Event Data (Mock Data)
    print("\n2️⃣ Testing Invalid Event Data (Mock):")
    invalid_event = {
        "id": "test_456",
        "title": "US Unemployment Rate",  # Common mock title
        "currency": "USD",
        "impact": "high",
        "expected": "3.8%",
        "previous": "3.9%",
        "actual": "--",
        "date": "Fri, Aug 15",
        "time": "13:30 UTC",
        "source": "fallback_data"  # Mock data indicator
    }
    
    print(f"   Event: {invalid_event['title']}")
    print(f"   Source: {invalid_event.get('source', 'unknown')}")
    print(f"   Expected: {invalid_event['expected']}")
    
    # Test 3: Event with Unrealistic Values
    print("\n3️⃣ Testing Event with Unrealistic Values:")
    unrealistic_event = {
        "id": "test_789",
        "title": "US Non-Farm Payrolls",
        "currency": "USD",
        "impact": "high",
        "expected": "50",  # Unrealistic - too small for NFP
        "previous": "1000%",  # Unrealistic percentage
        "actual": "N/A",
        "date": "Fri, Jan 10",
        "time": "13:30 UTC"
    }
    
    print(f"   Event: {unrealistic_event['title']}")
    print(f"   Expected: {unrealistic_event['expected']} (unrealistic)")
    print(f"   Previous: {unrealistic_event['previous']} (unrealistic)")
    
    # Test 4: Live Market Data
    print("\n4️⃣ Testing Live Market Data Integration:")
    try:
        response = requests.get("http://localhost:5001/api/forex-prices")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Live market data available")
            print(f"   Source: {data.get('dataSource', 'unknown')}")
            print(f"   Pairs: {len(data.get('prices', {}))}")
            print(f"   Sample prices:")
            prices = data.get('prices', {})
            for pair in list(prices.keys())[:3]:
                price_data = prices[pair]
                print(f"     {pair}: {price_data.get('price', 'N/A')}")
        else:
            print(f"   ❌ Live market data unavailable: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error fetching live market data: {e}")
    
    # Test 5: Enhanced Analysis Endpoint
    print("\n5️⃣ Testing Enhanced Analysis Endpoint:")
    try:
        # Test with valid event
        response = requests.post(
            "http://localhost:5001/api/enhanced-analysis/test_123",
            json={
                "event": valid_event,
                "analysisType": "pre-event"
            }
        )
        
        if response.status_code == 200:
            analysis = response.json()
            print(f"   ✅ Enhanced analysis successful")
            print(f"   Data Quality: {analysis.get('data_quality', 'unknown')}")
            print(f"   Validation Status: {analysis.get('validation_status', 'unknown')}")
            print(f"   Market Data Source: {analysis.get('market_data_source', 'unknown')}")
            print(f"   Headline: {analysis.get('headline', 'N/A')}")
            print(f"   Key Takeaway: {analysis.get('key_takeaway', 'N/A')}")
        elif response.status_code == 400:
            error_data = response.json()
            print(f"   ❌ Analysis rejected due to data quality issues")
            print(f"   Validation Errors: {error_data.get('validation_errors', [])}")
            print(f"   Recommendation: {error_data.get('recommendation', 'N/A')}")
        else:
            print(f"   ❌ Analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing enhanced analysis: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Data Quality Test Complete")

def compare_old_vs_new_analysis():
    """Compare old vs new analysis quality"""
    print("\n🔄 Comparing Old vs New Analysis Quality")
    print("=" * 50)
    
    # Example of old analysis output (what you showed)
    old_analysis = {
        "headline": "📊 Non Farm Payrolls Analysis - Significant Deviation from Expectations",
        "market_confidence": "85%",
        "non_impact": "Weak",
        "volatility": "Medium",
        "risk_level": "Low",
        "market_sentiment": "Neutral",
        "forward_scenarios": {
            "bullish": "✅ If actual figures exceed expectations, USD could test resistance at EUR/USD 1.09 and USD/JPY 149.0",
            "bearish": "❌ If figures fall short, USD might see support levels at EUR/USD 1.08 and USD/JPY 148.0",
            "neutral": "➡️ With data pending, USD might fluctuate within a tight range around current levels"
        },
        "event_summary": {
            "event": "Non Farm Payrolls report for September 2023",  # Wrong year!
            "outcome": "The Non Farm Payrolls report showed a significant deviation from expectations, with actual figures yet to be released."
        }
    }
    
    # Example of new analysis output (what we expect)
    new_analysis = {
        "headline": "📊 US Non-Farm Payrolls Analysis - Employment Data Expected",
        "key_takeaway": "NFP data expected to show employment trends with moderate USD impact based on current market conditions.",
        "data_quality": "validated",
        "validation_status": "passed",
        "market_data_source": "TradingView",
        "forward_scenarios": {
            "bullish": "✅ Strong NFP above 180K: USD strengthens, EUR/USD targets 1.0800, USD/JPY tests 149.00",
            "bearish": "❌ Weak NFP below 180K: USD weakens, EUR/USD targets 1.0900, USD/JPY tests 148.00",
            "neutral": "➡️ NFP in line with 180K: Range trading likely, EUR/USD 1.0800-1.0900, USD/JPY 148.00-149.00"
        },
        "event_summary": {
            "release": "US Non-Farm Payrolls 2025",
            "outcome": "NFP expected to show employment trends with moderate market impact.",
            "previous": "175K",
            "expected": "180K",
            "actual": "Data pending"
        }
    }
    
    print("\n📊 OLD ANALYSIS (Problems):")
    print(f"   ❌ Wrong year: {old_analysis['event_summary']['event']}")
    print(f"   ❌ Generic metrics: {old_analysis['market_confidence']}")
    print(f"   ❌ Contradictory: {old_analysis['non_impact']}")
    print(f"   ❌ Vague scenarios: {old_analysis['forward_scenarios']['neutral']}")
    
    print("\n📊 NEW ANALYSIS (Improvements):")
    print(f"   ✅ Correct year: {new_analysis['event_summary']['release']}")
    print(f"   ✅ Data quality: {new_analysis['data_quality']}")
    print(f"   ✅ Validation: {new_analysis['validation_status']}")
    print(f"   ✅ Market source: {new_analysis['market_data_source']}")
    print(f"   ✅ Specific scenarios: {new_analysis['forward_scenarios']['neutral']}")
    print(f"   ✅ Real data: {new_analysis['event_summary']['expected']} vs {new_analysis['event_summary']['previous']}")

if __name__ == "__main__":
    test_data_quality_improvements()
    compare_old_vs_new_analysis()
