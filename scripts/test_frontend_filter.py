#!/usr/bin/env python3
"""
Test if news items from API would pass frontend isForexRelevant filter
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def isForexRelevant(item):
    """Replicate frontend filter logic"""
    title = (item.get('title', '') or '').lower()
    summary = (item.get('summary', '') or '').lower()
    text = f"{title} {summary}"
    
    # Core forex keywords that indicate relevance
    coreForexKeywords = [
        'forex', 'currency', 'fx', 'foreign exchange',
        'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
        'fed', 'ecb', 'boj', 'boe', 'rba', 'boc', 'snb', 'rbnz',
        'cpi', 'inflation', 'interest rate', 'non-farm payrolls', 'gdp'
    ]
    
    # Economic and market terms that are forex-relevant
    forexRelevantTerms = [
        'commodity', 'oil', 'crude', 'gold', 'silver', 'copper', 'natural gas',
        'economic', 'economy', 'economic data', 'economic indicator',
        'trade', 'tariff', 'trade war', 'trade deal', 'trade agreement',
        'geopolitical', 'geopolitics', 'diplomatic', 'sanctions',
        'market sentiment', 'risk-off', 'risk-on', 'safe haven'
    ]
    
    hasCoreForex = any(keyword in text for keyword in coreForexKeywords)
    hasForexRelevant = any(term in text for term in forexRelevantTerms)
    
    return hasCoreForex or hasForexRelevant

def main():
    print("=" * 60)
    print("FRONTEND FILTER TEST")
    print("=" * 60)
    print()
    
    try:
        import requests
        response = requests.get('http://localhost:5001/api/news', timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API returned {response.status_code}")
            return
        
        data = response.json()
        news_items = data.get('news', [])
        
        print(f"📊 API returned {len(news_items)} news items")
        print()
        
        # Test each item
        passed = []
        failed = []
        
        for item in news_items:
            title = item.get('title', 'No title')
            source = item.get('source', 'Unknown')
            impact = item.get('impact', 'Unknown')
            
            if isForexRelevant(item):
                passed.append(item)
                print(f"✅ PASS: {title[:60]}...")
                print(f"   Source: {source}, Impact: {impact}")
            else:
                failed.append(item)
                print(f"❌ FAIL: {title[:60]}...")
                print(f"   Source: {source}, Impact: {impact}")
                print(f"   Title: {title}")
                if item.get('summary'):
                    print(f"   Summary: {item.get('summary')[:80]}...")
        
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Passed filter: {len(passed)} items")
        print(f"❌ Failed filter: {len(failed)} items")
        print(f"📊 Total: {len(news_items)} items")
        print()
        
        if len(failed) > 0:
            print("⚠️  Items that will NOT be displayed:")
            for item in failed[:5]:  # Show first 5
                print(f"   - {item.get('title', 'No title')[:60]}...")
                print(f"     Source: {item.get('source', 'Unknown')}")
        
        # Check for Telegram news specifically
        telegram_items = [item for item in news_items if 'telegram' in item.get('source', '').lower()]
        print()
        print(f"📱 Telegram items in response: {len(telegram_items)}")
        if telegram_items:
            telegram_passed = [item for item in telegram_items if isForexRelevant(item)]
            telegram_failed = [item for item in telegram_items if not isForexRelevant(item)]
            print(f"   ✅ Passed filter: {len(telegram_passed)}")
            print(f"   ❌ Failed filter: {len(telegram_failed)}")
            
            if telegram_failed:
                print()
                print("⚠️  Telegram items that failed filter:")
                for item in telegram_failed:
                    print(f"   - {item.get('title', 'No title')[:80]}...")
                    print(f"     Text checked: {(item.get('title', '') + ' ' + item.get('summary', '')).lower()[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

