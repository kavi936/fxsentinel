#!/usr/bin/env python3
"""
Test script for Force Refresh News functionality
"""
import requests
import json
import time
from datetime import datetime

def test_force_refresh_news():
    """Test the force refresh news endpoint"""
    print("🔄 Testing Force Refresh News Functionality")
    print("=" * 50)
    
    # Test the force refresh endpoint
    try:
        print("1. Testing force refresh endpoint...")
        response = requests.post('http://localhost:5001/api/force-refresh-news')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh successful!")
            print(f"   Message: {data.get('message')}")
            print(f"   Articles count: {data.get('articles_count')}")
            print(f"   Alert results: {data.get('alert_results')}")
            
            # Test regular news endpoint to see updated data
            print("\n2. Testing regular news endpoint after force refresh...")
            news_response = requests.get('http://localhost:5001/api/news')
            
            if news_response.status_code == 200:
                news_data = news_response.json()
                print(f"✅ News endpoint working!")
                print(f"   Total articles: {news_data.get('total_articles')}")
                print(f"   Cache status: {news_data.get('cache_status')}")
                print(f"   Last updated: {news_data.get('last_updated')}")
                
                # Show first few articles
                news_items = news_data.get('news', [])
                if news_items:
                    print(f"\n3. Latest news articles:")
                    for i, item in enumerate(news_items[:3]):
                        print(f"   {i+1}. {item.get('title', 'No title')[:60]}...")
                        print(f"      Source: {item.get('source')}")
                        print(f"      Time: {item.get('published_at')}")
                        print()
                else:
                    print("   ⚠️ No news articles found")
            else:
                print(f"❌ News endpoint failed: {news_response.status_code}")
                
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing force refresh: {e}")

def test_alert_triggering():
    """Test if alerts are triggered with fresh news"""
    print("\n🎯 Testing Alert Triggering")
    print("=" * 30)
    
    try:
        # First, force refresh to get fresh news
        print("1. Force refreshing news...")
        refresh_response = requests.post('http://localhost:5001/api/force-refresh-news')
        
        if refresh_response.status_code == 200:
            refresh_data = refresh_response.json()
            alert_results = refresh_data.get('alert_results')
            
            if alert_results:
                print("✅ Alert triggering results:")
                print(f"   Alerts sent: {alert_results.get('alerts_sent', 0)}")
                print(f"   High-impact news found: {alert_results.get('high_impact_news', 0)}")
                print(f"   AI analyses triggered: {alert_results.get('ai_analyses_triggered', 0)}")
                print(f"   Errors: {len(alert_results.get('errors', []))}")
                
                if alert_results.get('errors'):
                    print("   Error details:")
                    for error in alert_results['errors']:
                        print(f"     - {error}")
            else:
                print("⚠️ No alert results returned")
        else:
            print(f"❌ Force refresh failed: {refresh_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing alert triggering: {e}")

def test_cache_behavior():
    """Test cache behavior with force refresh"""
    print("\n💾 Testing Cache Behavior")
    print("=" * 25)
    
    try:
        # Test regular news endpoint (should use cache)
        print("1. Testing regular news endpoint (should use cache)...")
        response1 = requests.get('http://localhost:5001/api/news')
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"   Cache status: {data1.get('cache_status')}")
            print(f"   Articles: {data1.get('total_articles')}")
            
            # Force refresh
            print("\n2. Force refreshing...")
            refresh_response = requests.post('http://localhost:5001/api/force-refresh-news')
            
            if refresh_response.status_code == 200:
                # Test regular endpoint again
                print("\n3. Testing regular news endpoint after force refresh...")
                response2 = requests.get('http://localhost:5001/api/news')
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"   Cache status: {data2.get('cache_status')}")
                    print(f"   Articles: {data2.get('total_articles')}")
                    
                    # Compare timestamps
                    time1 = data1.get('last_updated')
                    time2 = data2.get('last_updated')
                    print(f"   Time difference: {time1} vs {time2}")
                    
                else:
                    print(f"❌ Second request failed: {response2.status_code}")
            else:
                print(f"❌ Force refresh failed: {refresh_response.status_code}")
        else:
            print(f"❌ First request failed: {response1.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing cache behavior: {e}")

if __name__ == "__main__":
    print(f"🚀 Starting Force Refresh News Tests at {datetime.now()}")
    print()
    
    test_force_refresh_news()
    test_alert_triggering()
    test_cache_behavior()
    
    print(f"\n✅ All tests completed at {datetime.now()}")
