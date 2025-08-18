#!/usr/bin/env python3
"""
Test script for Live News Analysis functionality
Tests the enhanced news caching, AI analysis, and history features
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"  # Adjust if your backend runs on different port

def test_news_endpoint():
    """Test the news endpoint"""
    print("🔍 Testing News Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/news", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News endpoint working - {len(data.get('news', []))} articles")
            print(f"   Cache status: {data.get('cache_status', 'unknown')}")
            print(f"   Sources: {data.get('sources', [])}")
            
            # Show first article details
            if data.get('news'):
                first_article = data['news'][0]
                print(f"   Sample article: {first_article.get('title', 'No title')[:50]}...")
                print(f"   Impact: {first_article.get('impact', 'Unknown')}")
                print(f"   Currency pairs: {first_article.get('currency_pairs', [])}")
            
            return data.get('news', [])
        else:
            print(f"❌ News endpoint failed - Status: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error testing news endpoint: {e}")
        return []

def test_news_history():
    """Test the news history endpoint"""
    print("\n🔍 Testing News History Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/news-history?hours=24", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News history working - {len(data.get('history', []))} items")
            print(f"   Total items in history: {data.get('status', {}).get('total_items', 0)}")
            
            return data.get('history', [])
        else:
            print(f"❌ News history failed - Status: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error testing news history: {e}")
        return []

def test_ai_analysis(news_items):
    """Test AI analysis for news items"""
    print("\n🔍 Testing AI Analysis...")
    
    if not news_items:
        print("❌ No news items to analyze")
        return
    
    # Test analysis on first news item
    first_item = news_items[0]
    news_id = first_item.get('id')
    
    if not news_id:
        print("❌ News item has no ID")
        return
    
    try:
        print(f"   Analyzing: {first_item.get('title', 'Unknown')[:50]}...")
        
        response = requests.get(f"{BASE_URL}/api/analysis/{news_id}", timeout=15)
        
        if response.status_code == 200:
            analysis = response.json()
            print(f"✅ AI Analysis working")
            print(f"   Summary: {analysis.get('summary', 'No summary')[:100]}...")
            print(f"   Confidence: {analysis.get('confidence', 'Unknown')}")
            print(f"   Sentiment: {analysis.get('sentiment', 'Unknown')}")
            print(f"   Analysis type: {analysis.get('analysis_type', 'Unknown')}")
            
            # Check for trading opportunities
            opportunities = analysis.get('trading_opportunities', [])
            if opportunities:
                print(f"   Trading opportunities: {len(opportunities)} found")
                for opp in opportunities[:2]:  # Show first 2
                    print(f"     - {opp.get('pair', 'Unknown')}: {opp.get('strategy', 'Unknown')}")
            
            # Check for currency pair analysis
            currency_pairs = analysis.get('currency_pairs', {})
            if currency_pairs:
                print(f"   Currency pairs analyzed: {len(currency_pairs)}")
                for pair, analysis_text in list(currency_pairs.items())[:2]:  # Show first 2
                    print(f"     - {pair}: {analysis_text[:50]}...")
            
            return analysis
        else:
            print(f"❌ AI Analysis failed - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ Error testing AI analysis: {e}")
        return None

def test_news_by_id(news_items):
    """Test getting news by ID"""
    print("\n🔍 Testing Get News by ID...")
    
    if not news_items:
        print("❌ No news items to test")
        return
    
    first_item = news_items[0]
    news_id = first_item.get('id')
    
    if not news_id:
        print("❌ News item has no ID")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/api/news/{news_id}", timeout=10)
        
        if response.status_code == 200:
            item = response.json()
            print(f"✅ Get news by ID working")
            print(f"   Retrieved: {item.get('title', 'Unknown')[:50]}...")
            print(f"   Source: {item.get('source', 'Unknown')}")
            print(f"   Impact: {item.get('impact', 'Unknown')}")
        else:
            print(f"❌ Get news by ID failed - Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing get news by ID: {e}")

def test_cache_status():
    """Test cache status endpoints"""
    print("\n🔍 Testing Cache Status...")
    
    try:
        # Test news endpoint to see cache status
        response = requests.get(f"{BASE_URL}/api/news", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            cache_status = data.get('cache_status', 'unknown')
            print(f"✅ Cache status: {cache_status}")
            
            if cache_status == 'cached':
                print("   Using cached data")
            elif cache_status == 'fresh':
                print("   Using fresh data")
            elif cache_status == 'fallback':
                print("   Using fallback data")
        else:
            print(f"❌ Could not check cache status - Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking cache status: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Live News Analysis Tests")
    print("=" * 50)
    
    # Test news endpoint
    news_items = test_news_endpoint()
    
    # Test news history
    history_items = test_news_history()
    
    # Test AI analysis
    if news_items:
        analysis_result = test_ai_analysis(news_items)
    
    # Test get news by ID
    test_news_by_id(news_items)
    
    # Test cache status
    test_cache_status()
    
    print("\n" + "=" * 50)
    print("🏁 Live News Analysis Tests Complete")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   News items: {len(news_items)}")
    print(f"   History items: {len(history_items)}")
    print(f"   AI analysis: {'✅ Working' if news_items and 'analysis_result' in locals() else '❌ Failed'}")
    
    if news_items:
        print(f"\n💡 Next Steps:")
        print(f"   1. Check the frontend to see the enhanced live news analysis card")
        print(f"   2. Try analyzing news items to see sentiment analysis")
        print(f"   3. Switch between Live and History tabs")
        print(f"   4. Test the filtering by impact level")

if __name__ == "__main__":
    main()
