#!/usr/bin/env python3
"""
Test script to verify the complete AI analysis flow
"""

import requests
import json
from datetime import datetime

def test_ai_analysis_flow():
    """Test the complete AI analysis flow"""
    
    base_url = "http://localhost:5001"  # Backend runs on port 5001
    
    print("🧪 Testing AI Analysis Flow")
    print("=" * 50)
    
    # Test 1: Basic AI Analysis
    print("\n1️⃣ Testing Basic AI Analysis...")
    try:
        response = requests.get(f"{base_url}/api/analysis/1")
        if response.status_code == 200:
            analysis = response.json()
            print("✅ Basic analysis working!")
            print(f"   Summary: {analysis.get('summary', 'N/A')[:100]}...")
            print(f"   Confidence: {analysis.get('confidence', 'N/A')}")
        else:
            print(f"❌ Basic analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic analysis error: {e}")
    
    # Test 2: News Sentiment Analysis
    print("\n2️⃣ Testing News Sentiment Analysis...")
    try:
        test_news = {
            "news_items": [
                {
                    "title": "US CPI Data Better Than Expected",
                    "content": "Consumer Price Index rose 0.3% in December, beating expectations of 0.2%. This suggests inflation is cooling faster than anticipated."
                }
            ]
        }
        
        response = requests.post(f"{base_url}/api/news-sentiment", json=test_news)
        if response.status_code == 200:
            sentiment = response.json()
            print("✅ Sentiment analysis working!")
            print(f"   Overall sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
            print(f"   Top keywords: {sentiment.get('top_keywords', [])[:3]}")
        else:
            print(f"❌ Sentiment analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Sentiment analysis error: {e}")
    
    # Test 3: Technical Analysis
    print("\n3️⃣ Testing Technical Analysis...")
    try:
        response = requests.get(f"{base_url}/api/technical-analysis/EUR_USD")
        if response.status_code == 200:
            technical = response.json()
            print("✅ Technical analysis working!")
            print(f"   Pair: {technical.get('pair', 'N/A')}")
            print(f"   Sentiment: {technical.get('sentiment', {}).get('sentiment', 'N/A')}")
            print(f"   Signals: {len(technical.get('signals', []))}")
        else:
            print(f"❌ Technical analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Technical analysis error: {e}")
    
    # Test 4: Enhanced Analysis
    print("\n4️⃣ Testing Enhanced Analysis...")
    try:
        response = requests.get(f"{base_url}/api/enhanced-analysis/1")
        if response.status_code == 200:
            enhanced = response.json()
            print("✅ Enhanced analysis working!")
            print(f"   Analysis type: {enhanced.get('analysis_type', 'N/A')}")
            print(f"   Sentiment: {enhanced.get('sentiment_analysis', {}).get('sentiment', 'N/A')}")
            print(f"   Technical pairs: {len(enhanced.get('technical_analyses', {}))}")
        else:
            print(f"❌ Enhanced analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Enhanced analysis error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 AI Analysis Flow Test Complete!")

if __name__ == "__main__":
    test_ai_analysis_flow()
