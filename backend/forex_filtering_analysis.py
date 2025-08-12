#!/usr/bin/env python3
"""
Forex Filtering Analysis - Test and improve forex news filtering
"""

import requests
import feedparser
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any

def analyze_current_filtering():
    """Analyze current forex filtering system"""
    
    print("🔍 FOREX FILTERING ANALYSIS")
    print("=" * 60)
    
    # Current keywords from both systems
    rss_keywords = [
        'forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'franc', 'australian dollar', 'canadian dollar',
        'cpi', 'inflation', 'interest rate', 'fed', 'ecb', 'boj', 'boe', 'rba', 'boc', 'snb',
        'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
        'non-farm payrolls', 'gdp', 'retail sales', 'manufacturing', 'services pmi',
        'unemployment', 'employment', 'wages', 'trade balance', 'current account'
    ]
    
    telegram_keywords = [
        'forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'franc',
        'cpi', 'inflation', 'interest rate', 'fed', 'ecb', 'boj', 'boe',
        'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad',
        'non-farm payrolls', 'gdp', 'retail sales', 'manufacturing',
        'unemployment', 'employment', 'wages', 'trade balance'
    ]
    
    print("📊 CURRENT KEYWORDS:")
    print(f"RSS Keywords: {len(rss_keywords)}")
    print(f"Telegram Keywords: {len(telegram_keywords)}")
    print()
    
    # Test with real news examples
    test_articles = [
        {
            "title": "US CPI Data Shows Inflation Cooling",
            "summary": "Consumer price index fell to 3.1% in December, below expectations",
            "expected_forex": True
        },
        {
            "title": "Fed Signals Potential Rate Cuts",
            "summary": "Federal Reserve officials suggest interest rates may be lowered in 2024",
            "expected_forex": True
        },
        {
            "title": "EUR/USD Hits 1.0950 Resistance",
            "summary": "Euro dollar pair reaches key technical level amid ECB policy uncertainty",
            "expected_forex": True
        },
        {
            "title": "Bitcoin Surges to $120,000",
            "summary": "Cryptocurrency reaches new all-time high as institutional adoption grows",
            "expected_forex": False
        },
        {
            "title": "Apple Reports Strong Q4 Earnings",
            "summary": "Tech giant beats analyst expectations with record iPhone sales",
            "expected_forex": False
        },
        {
            "title": "ECB Maintains Interest Rates at 4.5%",
            "summary": "European Central Bank holds rates steady as inflation concerns persist",
            "expected_forex": True
        },
        {
            "title": "Non-Farm Payrolls Beat Expectations",
            "summary": "US economy adds 216,000 jobs in December, unemployment rate at 3.7%",
            "expected_forex": True
        },
        {
            "title": "Oil Prices Fall on OPEC+ Decision",
            "summary": "Crude oil drops 3% as cartel announces production cuts",
            "expected_forex": False
        }
    ]
    
    print("🧪 TESTING CURRENT FILTERING:")
    print("-" * 60)
    
    correct_matches = 0
    total_tests = len(test_articles)
    
    for i, article in enumerate(test_articles, 1):
        text = f"{article['title']} {article['summary']}".lower()
        
        # Check if any keyword matches
        is_forex = any(keyword.lower() in text for keyword in rss_keywords)
        
        status = "✅" if is_forex == article['expected_forex'] else "❌"
        result = "FOREX" if is_forex else "NOT FOREX"
        expected = "FOREX" if article['expected_forex'] else "NOT FOREX"
        
        if is_forex == article['expected_forex']:
            correct_matches += 1
        
        print(f"{i}. {status} {article['title'][:40]}...")
        print(f"   Result: {result} | Expected: {expected}")
        print(f"   Keywords found: {[k for k in rss_keywords if k.lower() in text]}")
        print()
    
    accuracy = (correct_matches / total_tests) * 100
    print(f"📈 FILTERING ACCURACY: {accuracy:.1f}% ({correct_matches}/{total_tests})")
    print()

def suggest_improvements():
    """Suggest improvements to forex filtering"""
    
    print("🚀 SUGGESTED IMPROVEMENTS:")
    print("=" * 60)
    
    # Enhanced keywords
    enhanced_keywords = [
        # Currency names
        'forex', 'currency', 'fx', 'foreign exchange',
        'dollar', 'euro', 'yen', 'pound', 'franc', 'australian dollar', 'canadian dollar', 'kiwi',
        'usd', 'eur', 'jpy', 'gbp', 'chf', 'aud', 'cad', 'nzd',
        
        # Central banks
        'fed', 'federal reserve', 'ecb', 'european central bank', 'boj', 'bank of japan', 
        'boe', 'bank of england', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
        'snb', 'swiss national bank', 'rbnz', 'reserve bank of new zealand',
        
        # Economic indicators
        'cpi', 'consumer price index', 'inflation', 'deflation', 'interest rate', 'monetary policy',
        'non-farm payrolls', 'nfp', 'gdp', 'gross domestic product', 'retail sales', 'manufacturing',
        'services pmi', 'unemployment', 'employment', 'wages', 'trade balance', 'current account',
        'balance of payments', 'budget deficit', 'fiscal policy',
        
        # Currency pairs
        'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
        'eur/gbp', 'eur/jpy', 'gbp/jpy', 'eur/chf', 'gbp/chf', 'aud/jpy', 'cad/jpy',
        
        # Market terms
        'pip', 'spread', 'leverage', 'margin', 'liquidity', 'volatility', 'correlation',
        'support', 'resistance', 'breakout', 'consolidation', 'trend', 'momentum',
        
        # Economic events
        'rate decision', 'policy meeting', 'minutes', 'speech', 'testimony', 'hearing',
        'economic calendar', 'market hours', 'session', 'asian session', 'london session', 'ny session'
    ]
    
    # Negative keywords (to exclude)
    negative_keywords = [
        'cryptocurrency', 'bitcoin', 'ethereum', 'crypto', 'blockchain', 'defi',
        'stock', 'equity', 'shares', 'dividend', 'earnings', 'revenue',
        'commodity', 'oil', 'gold', 'silver', 'copper', 'natural gas',
        'real estate', 'property', 'mortgage', 'housing'
    ]
    
    print("✅ ENHANCED KEYWORDS:")
    print(f"   Total: {len(enhanced_keywords)} keywords")
    print(f"   Categories: Currency, Central Banks, Economic Indicators, Pairs, Market Terms")
    print()
    
    print("❌ NEGATIVE KEYWORDS (to exclude):")
    print(f"   Total: {len(negative_keywords)} keywords")
    print(f"   Categories: Crypto, Stocks, Commodities, Real Estate")
    print()
    
    print("🎯 IMPROVED FILTERING LOGIC:")
    print("1. Check for positive forex keywords")
    print("2. Exclude if negative keywords present")
    print("3. Use weighted scoring system")
    print("4. Consider source credibility")
    print("5. Add machine learning classification")
    print()

def test_enhanced_filtering():
    """Test enhanced filtering system"""
    
    print("🧪 TESTING ENHANCED FILTERING:")
    print("=" * 60)
    
    # Enhanced keywords
    positive_keywords = [
        'forex', 'currency', 'fx', 'dollar', 'euro', 'yen', 'pound', 'fed', 'ecb', 'boj', 'boe',
        'cpi', 'inflation', 'interest rate', 'non-farm payrolls', 'gdp', 'eur/usd', 'usd/jpy'
    ]
    
    negative_keywords = [
        'cryptocurrency', 'bitcoin', 'ethereum', 'crypto', 'stock', 'equity', 'earnings',
        'commodity', 'oil', 'gold', 'real estate', 'property'
    ]
    
    test_cases = [
        {
            "title": "Fed Chair Powell Testifies on Monetary Policy",
            "summary": "Federal Reserve Chairman Jerome Powell addresses Congress on interest rate outlook",
            "expected": True
        },
        {
            "title": "Bitcoin Reaches New High as Institutional Adoption Grows",
            "summary": "Cryptocurrency market sees increased institutional investment",
            "expected": False
        },
        {
            "title": "EUR/USD Breaks Key Resistance Level",
            "summary": "Euro dollar pair reaches 1.1000 as ECB policy uncertainty continues",
            "expected": True
        },
        {
            "title": "Apple Stock Surges on Strong Earnings Report",
            "summary": "Tech giant beats analyst expectations with record iPhone sales",
            "expected": False
        },
        {
            "title": "Oil Prices Impact Currency Markets",
            "summary": "Crude oil volatility affects USD/CAD and other commodity currencies",
            "expected": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        text = f"{case['title']} {case['summary']}".lower()
        
        # Enhanced filtering logic
        positive_score = sum(1 for keyword in positive_keywords if keyword.lower() in text)
        negative_score = sum(1 for keyword in negative_keywords if keyword.lower() in text)
        
        # Decision logic
        is_forex = positive_score > 0 and negative_score == 0
        
        status = "✅" if is_forex == case['expected'] else "❌"
        result = "FOREX" if is_forex else "NOT FOREX"
        
        print(f"{i}. {status} {case['title']}")
        print(f"   Result: {result} | Positive: {positive_score} | Negative: {negative_score}")
        print()

if __name__ == "__main__":
    analyze_current_filtering()
    suggest_improvements()
    test_enhanced_filtering()
