#!/usr/bin/env python3
"""
Direct test of the analysis endpoint to see the exact data structure
"""

import requests
import json

def test_analysis_direct():
    """Test the analysis endpoint directly"""
    
    print("🧪 Testing Analysis Endpoint Directly...\n")
    
    # Test the analysis endpoint
    url = "http://localhost:5001/api/analysis/2301960550843964484"
    
    try:
        print(f"Making request to: {url}")
        response = requests.get(url)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            analysis = response.json()
            
            print("\n✅ Analysis received successfully!")
            print(f"Analysis type: {analysis.get('analysis_type')}")
            print(f"Confidence: {analysis.get('confidence')}")
            print(f"Immediate reaction: {analysis.get('immediate_reaction')}")
            print(f"Key pairs: {analysis.get('key_pairs')}")
            print(f"Volatility: {analysis.get('volatility')}")
            print(f"Timeframe: {analysis.get('timeframe')}")
            
            print(f"\n📰 News Impact ({len(analysis.get('news_impact', ''))} characters):")
            print(f"'{analysis.get('news_impact', 'NO DATA')}'")
            
            print(f"\n💼 Trading Implications ({len(analysis.get('trading_implications', ''))} characters):")
            print(f"'{analysis.get('trading_implications', 'NO DATA')}'")
            
            print(f"\n🔍 Risk Assessment:")
            print(json.dumps(analysis.get('risk_assessment', {}), indent=2))
            
            print(f"\n📊 Market Context:")
            print(json.dumps(analysis.get('market_context', {}), indent=2))
            
            print(f"\n📋 Full Response Structure:")
            print(json.dumps(analysis, indent=2))
            
            return analysis
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_with_different_id():
    """Test with a different news ID to see if we get GPT analysis"""
    
    print("\n" + "="*50)
    print("🧪 Testing with different news ID...\n")
    
    # Get current news items first
    try:
        news_response = requests.get("http://localhost:5001/api/news")
        if news_response.status_code == 200:
            news_data = news_response.json()
            news_items = news_data.get('news', [])
            
            print(f"Found {len(news_items)} news items")
            
            # Test with the first news item
            if news_items:
                first_news = news_items[0]
                news_id = first_news.get('id')
                title = first_news.get('title', 'No title')
                
                print(f"\nTesting with news item: {title[:50]}...")
                print(f"News ID: {news_id}")
                
                analysis_response = requests.get(f"http://localhost:5001/api/analysis/{news_id}")
                if analysis_response.status_code == 200:
                    analysis = analysis_response.json()
                    print(f"✅ Analysis type: {analysis.get('analysis_type')}")
                    print(f"✅ News impact length: {len(analysis.get('news_impact', ''))}")
                    print(f"✅ Trading implications length: {len(analysis.get('trading_implications', ''))}")
                    
                    if analysis.get('analysis_type') == 'gpt_enhanced':
                        print("🎉 SUCCESS: Got GPT analysis!")
                    else:
                        print("⚠️  Got fallback analysis")
                else:
                    print(f"❌ Analysis failed: {analysis_response.status_code}")
            else:
                print("❌ No news items found")
        else:
            print(f"❌ Failed to get news: {news_response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_analysis_direct()
    test_with_different_id()
