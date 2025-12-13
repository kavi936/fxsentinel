#!/usr/bin/env python3
"""
Test script to debug the analysis endpoint
"""

import requests
import json

def test_analysis_endpoint():
    """Test the analysis endpoint to see what's happening"""
    
    # Test news endpoint first
    print("🔍 Testing news endpoint...")
    try:
        news_response = requests.get('http://localhost:5001/api/news')
        print(f"News response status: {news_response.status_code}")
        
        if news_response.status_code == 200:
            news_data = news_response.json()
            news_items = news_data.get('news', [])
            print(f"Found {len(news_items)} news items")
            
            if news_items:
                # Test analysis on first news item
                test_news = news_items[0]
                news_id = test_news['id']
                print(f"\n🔍 Testing analysis for news ID: {news_id}")
                print(f"News title: {test_news.get('title', 'No title')}")
                print(f"News source: {test_news.get('source', 'No source')}")
                
                # Test analysis endpoint
                analysis_url = f'http://localhost:5001/api/analysis/{news_id}'
                print(f"Analysis URL: {analysis_url}")
                
                analysis_response = requests.get(analysis_url)
                print(f"Analysis response status: {analysis_response.status_code}")
                print(f"Analysis response headers: {dict(analysis_response.headers)}")
                
                if analysis_response.status_code == 200:
                    analysis_data = analysis_response.json()
                    print(f"\n✅ Analysis successful!")
                    print(f"Analysis type: {analysis_data.get('analysis_type', 'unknown')}")
                    print(f"Confidence: {analysis_data.get('confidence', 'unknown')}")
                    print(f"Immediate reaction: {analysis_data.get('immediate_reaction', 'unknown')}")
                    print(f"News impact length: {len(analysis_data.get('news_impact', ''))}")
                    print(f"Trading implications length: {len(analysis_data.get('trading_implications', ''))}")
                    print(f"Key pairs: {analysis_data.get('key_pairs', [])}")
                    print(f"Volatility: {analysis_data.get('volatility', 'unknown')}")
                    print(f"Timeframe: {analysis_data.get('timeframe', 'unknown')}")
                    
                    # Check if the data looks valid
                    if analysis_data.get('news_impact') and analysis_data.get('trading_implications'):
                        print(f"\n✅ Analysis data looks valid - should display in frontend")
                        print(f"News impact preview: {analysis_data['news_impact'][:100]}...")
                        print(f"Trading implications preview: {analysis_data['trading_implications'][:100]}...")
                    else:
                        print(f"\n❌ Analysis data appears empty or invalid")
                        print(f"Full analysis data: {json.dumps(analysis_data, indent=2)}")
                else:
                    print(f"❌ Analysis failed with status {analysis_response.status_code}")
                    try:
                        error_data = analysis_response.json()
                        print(f"Error response: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"Error text: {analysis_response.text}")
            else:
                print("❌ No news items available for testing")
        else:
            print(f"❌ News endpoint failed with status {news_response.status_code}")
            print(f"Response: {news_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - backend server may not be running")
        print("Please start the backend server with: cd backend && python3 app.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_analysis_endpoint()
