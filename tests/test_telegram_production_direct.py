#!/usr/bin/env python3
"""
Direct test of Telegram functionality on production server
"""

import requests
import json
import time

def test_telegram_direct():
    """Test Telegram functionality directly on production"""
    
    print("🔍 Direct Telegram Production Test")
    print("=" * 50)
    
    # Step 1: Clear cache and force fresh fetch
    print("\n1️⃣ Clearing cache and forcing fresh fetch...")
    try:
        # First, try to clear any existing cache
        response = requests.post("https://fxsentinel-production.up.railway.app/api/force-refresh-news", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force refresh completed: {data.get('articles_count', 0)} articles")
            print(f"📊 Sources: {data.get('alert_results', {})}")
        else:
            print(f"❌ Force refresh failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Force refresh error: {e}")
        return
    
    # Step 2: Wait a moment and check the news endpoint
    print("\n2️⃣ Checking news endpoint after force refresh...")
    time.sleep(5)  # Wait for processing
    
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news", timeout=30)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            telegram_news = [n for n in news_items if 'Telegram' in n.get('source', '')]
            
            print(f"✅ News endpoint: {len(news_items)} total articles")
            print(f"📱 Telegram articles: {len(telegram_news)}")
            print(f"📊 Cache status: {data.get('cache_status', 'unknown')}")
            print(f"📋 Sources used: {data.get('sources', [])}")
            
            if telegram_news:
                print("📰 Telegram articles found:")
                for i, news in enumerate(telegram_news[:3]):
                    print(f"   {i+1}. {news.get('title', 'No title')}")
                    print(f"      Source: {news.get('source', 'Unknown')}")
                    print(f"      Impact: {news.get('impact', 'Unknown')}")
            else:
                print("❌ No Telegram articles found")
                
                # Check if Telegram is in the sources list
                sources = data.get('sources', [])
                if 'Telegram' in sources:
                    print("⚠️ Telegram is listed in sources but no articles found")
                    print("   This suggests the Telegram service is running but not finding forex-related messages")
                else:
                    print("⚠️ Telegram is not in the sources list")
                    print("   This suggests the Telegram service is not being called")
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ News endpoint error: {e}")
    
    # Step 3: Check if there are any recent messages that should be forex-related
    print("\n3️⃣ Analyzing recent news for forex content...")
    try:
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news", timeout=30)
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('news', [])
            
            # Look for news that might be forex-related but not from Telegram
            forex_keywords = ['fed', 'federal reserve', 'ecb', 'boe', 'boj', 'interest rate', 'cpi', 'inflation', 'forex', 'currency', 'dollar', 'euro', 'yen', 'pound']
            potential_forex_news = []
            
            for news in news_items[:10]:  # Check first 10 articles
                title = news.get('title', '').lower()
                summary = news.get('summary', '').lower()
                source = news.get('source', '')
                
                if any(keyword in title or keyword in summary for keyword in forex_keywords):
                    potential_forex_news.append({
                        'title': news.get('title', ''),
                        'source': source,
                        'impact': news.get('impact', 'unknown')
                    })
            
            print(f"📊 Found {len(potential_forex_news)} potential forex-related articles:")
            for i, news in enumerate(potential_forex_news[:5]):
                print(f"   {i+1}. {news['title']}")
                print(f"      Source: {news['source']} | Impact: {news['impact']}")
            
            if potential_forex_news:
                print("\n💡 These articles should have been detected by Telegram service")
                print("   The issue might be with the forex filtering logic")
            else:
                print("\n💡 No obvious forex-related news found")
                print("   This might explain why Telegram service isn't finding forex content")
                
    except Exception as e:
        print(f"❌ Analysis error: {e}")

if __name__ == "__main__":
    test_telegram_direct()
