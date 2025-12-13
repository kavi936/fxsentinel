#!/usr/bin/env python3
"""
Test script to show the difference between mock data and real AI analysis
"""

import requests
import json
from datetime import datetime

def test_ai_analysis_difference():
    """Test to show mock vs real AI analysis"""
    
    print("🤖 Testing AI Analysis: Mock vs Real")
    print("=" * 50)
    
    # Test 1: Check what happens with a real news ID
    print("\n1. Testing with Real News ID...")
    try:
        # Get some real news first
        response = requests.get(
            "http://localhost:5001/api/news",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            
            if news_items:
                # Use the first real news item
                real_news = news_items[0]
                real_news_id = str(real_news.get('id', ''))
                
                print(f"   Real news found: {real_news.get('title', '')[:50]}...")
                print(f"   News ID: {real_news_id}")
                
                # Try to get AI analysis for this real news
                analysis_response = requests.post(
                    f"http://localhost:5001/api/enhanced-analysis/{real_news_id}",
                    headers={"Content-Type": "application/json"},
                    json={"event": real_news},
                    timeout=30
                )
                
                if analysis_response.status_code == 200:
                    analysis_data = analysis_response.json()
                    print("   ✅ Real AI analysis successful!")
                    print(f"   Analysis type: {analysis_data.get('analysis_type', 'unknown')}")
                    print(f"   Model used: {analysis_data.get('model_used', 'unknown')}")
                    
                    # Show a sample of the analysis
                    if 'market_impact' in analysis_data:
                        print(f"   Market Impact: {analysis_data['market_impact'][:100]}...")
                    elif 'event_summary' in analysis_data:
                        print(f"   Event Summary: {analysis_data['event_summary'][:100]}...")
                    else:
                        print(f"   Analysis data: {str(analysis_data)[:200]}...")
                        
                else:
                    print(f"   ❌ Real AI analysis failed: {analysis_response.status_code}")
                    print(f"   Error: {analysis_response.text}")
            else:
                print("   ⚠️ No real news items found")
        else:
            print(f"   ❌ Failed to fetch news: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing real news: {e}")
    
    # Test 2: Show what the mock data looks like
    print("\n2. Mock Data Example...")
    mock_analysis = {
        "analysis": "This unprecedented political development targeting the Federal Reserve Chair has created extreme market uncertainty. The dollar is expected to face significant downward pressure as traders react to potential Fed leadership changes. USD pairs should see increased volatility with potential bearish moves across the board.",
        "market_impact": "High volatility expected in USD pairs",
        "trading_implications": "Consider short USD positions",
        "confidence": "High"
    }
    
    print("   Mock Analysis Structure:")
    for key, value in mock_analysis.items():
        print(f"   • {key}: {value[:50]}...")
    
    # Test 3: Check if AI analysis is actually being called
    print("\n3. Checking AI Analysis Integration...")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.news_alert_trigger import news_alert_trigger
        
        # Test with a sample news item that should trigger AI analysis
        sample_news = {
            'id': 'test_real_001',
            'title': 'Fed Announces Interest Rate Decision - Breaking News',
            'content': 'The Federal Reserve has announced a major interest rate decision that will impact EUR/USD and USD/JPY.',
            'source': 'Reuters',
            'url': 'https://example.com',
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if it should trigger AI analysis
        should_analyze = news_alert_trigger.should_analyze_with_ai(sample_news)
        print(f"   Should trigger AI analysis: {'✅ Yes' if should_analyze else '❌ No'}")
        
        if should_analyze:
            print("   ✅ AI analysis would be triggered for this news")
            print("   📊 This means real GPT analysis would be performed")
        else:
            print("   ❌ AI analysis would NOT be triggered")
            print("   📊 This means only mock data would be used")
            
    except Exception as e:
        print(f"   ❌ Error checking AI integration: {e}")
    
    print("\n" + "=" * 50)
    print("AI Analysis Test Summary:")
    print("\n📊 **What You're Getting:**")
    print("• Real AI Analysis: When news triggers AI analysis (Fed, ECB, etc.)")
    print("• Mock Data: When news doesn't meet AI analysis criteria")
    print("\n🎯 **The System:**")
    print("• Smart filtering determines when to use real AI")
    print("• Cost optimization prevents unnecessary AI calls")
    print("• Real GPT analysis for high-impact forex news")
    print("• Mock data for less important news")

if __name__ == "__main__":
    test_ai_analysis_difference()
