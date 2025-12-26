#!/usr/bin/env python3
"""
Test if news items would pass frontend filtering
Specifically tests the WatcherGuru news item
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_forex_relevance():
    """Test if WatcherGuru news would pass isForexRelevant filter"""
    print("=" * 60)
    print("TESTING FOREX RELEVANCE FILTER")
    print("=" * 60)
    
    # Simulate the WatcherGuru news item
    watcher_guru_news = {
        'title': "🇺🇸 President Trump says 'anybody that disagrees with me will never be the Fed Chairman.'",
        'summary': "**JUST IN:** 🇺🇸 President Trump says 'anybody that disagrees with me will never be the Fed Chairman.'",
        'source': 'Telegram - WatcherGuru',
        'impact': 'high',
        'published_at': '2025-12-26T17:49:00',
        'added_to_feed_at': '2025-12-26T17:49:00'
    }
    
    # Simulate the frontend filter logic
    def isForexRelevant(item):
        title = (item.get('title', '') or '').lower()
        summary = (item.get('summary', '') or '').lower()
        text = f"{title} {summary}"
        
        # Core forex keywords
        coreForexKeywords = [
            'forex', 'currency', 'fx', 'foreign exchange',
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
            'fed', 'ecb', 'boj', 'boe', 'rba', 'boc', 'snb', 'rbnz',
            'cpi', 'inflation', 'interest rate', 'non-farm payrolls', 'gdp'
        ]
        
        # Economic and market terms
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
    
    # Test the news item
    print(f"\nTesting news item:")
    print(f"  Title: {watcher_guru_news['title']}")
    print(f"  Source: {watcher_guru_news['source']}")
    print(f"  Impact: {watcher_guru_news['impact']}")
    
    is_relevant = isForexRelevant(watcher_guru_news)
    print(f"\n✅ Would pass isForexRelevant filter: {is_relevant}")
    
    if is_relevant:
        print("   ✅ This news should be displayed!")
    else:
        print("   ❌ This news would be filtered out!")
    
    # Check which keywords matched
    title_lower = watcher_guru_news['title'].lower()
    summary_lower = watcher_guru_news.get('summary', '').lower()
    text = f"{title_lower} {summary_lower}"
    
    print(f"\nKeyword matches:")
    if 'fed' in text:
        print("   ✅ Contains 'fed' (core forex keyword)")
    if 'trump' in text:
        print("   ✅ Contains 'trump' (high impact keyword)")
    if 'president' in text:
        print("   ✅ Contains 'president'")
    
    return is_relevant

def check_news_structure():
    """Check if news items have the correct structure"""
    print("\n" + "=" * 60)
    print("NEWS STRUCTURE CHECK")
    print("=" * 60)
    
    required_fields = ['id', 'title', 'source', 'published_at', 'added_to_feed_at']
    
    # Simulate what Telegram news should look like
    telegram_news_example = {
        'id': '123456789',
        'title': "🇺🇸 President Trump says 'anybody that disagrees with me will never be the Fed Chairman.'",
        'summary': "**JUST IN:** 🇺🇸 President Trump says 'anybody that disagrees with me will never be the Fed Chairman.'",
        'source': 'Telegram - WatcherGuru',
        'url': 'https://t.me/watcherguru/123',
        'published_at': '2025-12-26T17:49:00',
        'added_to_feed_at': '2025-12-26T17:49:00',
        'impact': 'high',
        'currency_pairs': [],
        'type': 'TELEGRAM',
        'status': 'PUBLISHED'
    }
    
    print("\nRequired fields check:")
    missing = []
    for field in required_fields:
        if field in telegram_news_example:
            print(f"   ✅ {field}: {telegram_news_example[field]}")
        else:
            print(f"   ❌ {field}: MISSING")
            missing.append(field)
    
    if missing:
        print(f"\n⚠️  Missing fields: {missing}")
    else:
        print(f"\n✅ All required fields present")
    
    return len(missing) == 0

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("NEWS DISPLAY TEST")
    print("=" * 60)
    print()
    
    # Test forex relevance
    is_relevant = test_forex_relevance()
    
    # Check structure
    has_structure = check_news_structure()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if is_relevant:
        print("✅ News would pass frontend filter")
    else:
        print("❌ News would be filtered out by frontend")
    
    if has_structure:
        print("✅ News has correct structure")
    else:
        print("❌ News missing required fields")
    
    print("\n💡 If news is not displaying, check:")
    print("   1. Is Telegram news being fetched? (check logs)")
    print("   2. Is cache saving successfully? (check Firebase)")
    print("   3. Is frontend calling API with force_refresh? (check network tab)")
    print("   4. Are there any console errors? (check browser console)")

if __name__ == '__main__':
    main()

