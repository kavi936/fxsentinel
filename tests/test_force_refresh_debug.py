#!/usr/bin/env python3
"""
Test Force Refresh Debug
Directly test the force refresh function to see debugging output
"""

import sys
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

def test_force_refresh():
    """Test the force refresh function directly"""
    print("🔍 Testing Force Refresh Function")
    print("=" * 50)
    
    # Test 1: Check if backend is running
    print("\n1️⃣ Checking if backend is running...")
    try:
        response = requests.get("http://localhost:5001/api/hello", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False
    
    # Test 2: Call force refresh
    print("\n2️⃣ Calling force refresh...")
    try:
        response = requests.post(
            "http://localhost:5001/api/force-refresh-news",
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh successful: {data.get('articles_count', 0)} articles")
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Sources: {data.get('sources', [])}")
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in force refresh: {e}")
        return False
    
    # Test 3: Check news endpoint
    print("\n3️⃣ Checking news endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/news?force_refresh=true", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News endpoint: {data.get('total_articles', 0)} articles")
            print(f"   Cache status: {data.get('cache_status', 'unknown')}")
            print(f"   Sources used: {data.get('sources', [])}")
            
            # Check for Telegram news
            news_items = data.get('news', [])
            telegram_news = [item for item in news_items if 'Telegram' in item.get('source', '')]
            
            print(f"   Telegram news count: {len(telegram_news)}")
            
            if telegram_news:
                print("📰 Telegram news found:")
                for i, news in enumerate(telegram_news[:3], 1):
                    print(f"  {i}. {news.get('title', 'No title')}")
                    print(f"     Source: {news.get('source', 'No source')}")
                    print()
            else:
                print("❌ No Telegram news found")
                
                # Show all sources
                sources = {}
                for item in news_items:
                    source = item.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                print("📊 All sources in response:")
                for source, count in sorted(sources.items()):
                    print(f"  {source}: {count} articles")
                    
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in news endpoint: {e}")
        return False
    
    print("\n🎯 Test completed!")
    return True

if __name__ == "__main__":
    success = test_force_refresh()
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
