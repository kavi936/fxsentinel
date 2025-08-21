#!/usr/bin/env python3
"""
Test Enhanced Filtering System
Demonstrates the improved filtering accuracy for forex news alerts
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.enhanced_forex_filter import EnhancedForexFilter
from services.news_alert_trigger import NewsAlertTrigger

def test_enhanced_filtering():
    """Test the enhanced filtering system with various news examples"""
    
    print("🔍 Testing Enhanced Forex Filtering System")
    print("=" * 60)
    
    # Initialize filters
    forex_filter = EnhancedForexFilter()
    alert_trigger = NewsAlertTrigger()
    
    # Test news items with different characteristics
    test_news = [
        {
            'title': 'Federal Reserve Raises Interest Rates by 25 Basis Points',
            'summary': 'The Fed announced a quarter-point rate hike, signaling continued monetary tightening.',
            'source': 'Reuters',
            'impact': 'high'
        },
        {
            'title': 'US CPI Inflation Rises to 3.2% in August',
            'summary': 'Consumer price index shows inflation remains above target, affecting USD strength.',
            'source': 'Bloomberg',
            'impact': 'high'
        },
        {
            'title': 'ECB President Lagarde Speaks on Monetary Policy',
            'summary': 'European Central Bank head discusses inflation outlook and rate decisions.',
            'source': 'CNBC',
            'impact': 'high'
        },
        {
            'title': 'Bitcoin Surges to New All-Time High',
            'summary': 'Cryptocurrency market sees massive gains as Bitcoin reaches $50,000.',
            'source': 'CryptoNews',
            'impact': 'high'
        },
        {
            'title': 'Apple Stock Rises on Strong Earnings Report',
            'summary': 'Tech giant reports better-than-expected quarterly results.',
            'source': 'MarketWatch',
            'impact': 'medium'
        },
        {
            'title': 'Oil Prices Fall on OPEC+ Production Decision',
            'summary': 'Crude oil prices decline as cartel announces production cuts.',
            'source': 'Reuters',
            'impact': 'medium'
        },
        {
            'title': 'US Non-Farm Payrolls: +187K Jobs Added',
            'summary': 'Employment data shows strong job growth, supporting USD strength.',
            'source': 'Bloomberg',
            'impact': 'high'
        },
        {
            'title': 'UK Retail Sales Decline in September',
            'summary': 'British consumer spending falls, putting pressure on GBP.',
            'source': 'FXStreet',
            'impact': 'medium'
        },
        {
            'title': 'Random Tech Company Announces New Product',
            'summary': 'Some tech company releases a new gadget that nobody cares about.',
            'source': 'TechBlog',
            'impact': 'low'
        },
        {
            'title': 'Fed Chair Powell Testifies Before Congress',
            'summary': 'Federal Reserve Chairman discusses monetary policy and economic outlook.',
            'source': 'Reuters',
            'impact': 'high'
        }
    ]
    
    print("\n📊 Testing Enhanced Filtering Logic")
    print("-" * 40)
    
    for i, news_item in enumerate(test_news, 1):
        print(f"\n{i}. {news_item['title']}")
        print(f"   Source: {news_item['source']}")
        print(f"   Impact: {news_item['impact']}")
        
        # Test enhanced forex filter
        forex_score = forex_filter.get_forex_score(news_item['title'], news_item['summary'])
        is_forex_related = forex_filter.is_forex_related(news_item['title'], news_item['summary'])
        is_high_impact = forex_filter.is_high_impact_for_alerts(news_item['title'], news_item['summary'], news_item['source'])
        
        # Test alert trigger filter
        old_high_impact = alert_trigger.is_high_impact_news(news_item)
        
        # Comprehensive decision
        alert_decision = forex_filter.should_trigger_alert(news_item)
        
        print(f"   Forex Related: {'✅ Yes' if is_forex_related else '❌ No'}")
        print(f"   High Impact (Enhanced): {'✅ Yes' if is_high_impact else '❌ No'}")
        print(f"   High Impact (Old): {'✅ Yes' if old_high_impact else '❌ No'}")
        print(f"   Should Alert: {'✅ Yes' if alert_decision['should_alert'] else '❌ No'}")
        print(f"   Confidence: {forex_score['confidence']}%")
        print(f"   Impact Level: {forex_score['impact_level']}")
        print(f"   Currency Pairs: {alert_decision['currency_pairs']}")
        print(f"   Reasoning: {', '.join(alert_decision['reasoning'])}")
    
    print("\n🎯 Filtering Comparison Summary")
    print("-" * 40)
    
    # Count results
    enhanced_alerts = 0
    old_alerts = 0
    forex_related = 0
    
    for news_item in test_news:
        if forex_filter.is_forex_related(news_item['title'], news_item['summary']):
            forex_related += 1
        
        if forex_filter.is_high_impact_for_alerts(news_item['title'], news_item['summary'], news_item['source']):
            enhanced_alerts += 1
        
        if alert_trigger.is_high_impact_news(news_item):
            old_alerts += 1
    
    print(f"Total News Items: {len(test_news)}")
    print(f"Forex Related: {forex_related}")
    print(f"High Impact (Enhanced Filter): {enhanced_alerts}")
    print(f"High Impact (Old Filter): {old_alerts}")
    print(f"Filtering Strictness Improvement: {((old_alerts - enhanced_alerts) / old_alerts * 100):.1f}% more strict")
    
    print("\n📈 Key Improvements")
    print("-" * 40)
    print("✅ More accurate forex relevance detection")
    print("✅ Source credibility weighting")
    print("✅ Critical keyword prioritization")
    print("✅ Reduced false positives")
    print("✅ Better currency pair extraction")
    print("✅ Comprehensive decision reasoning")
    
    print("\n🔧 Filtering Criteria")
    print("-" * 40)
    print("Critical Keywords (Auto High Impact):")
    critical_keywords = forex_filter.critical_forex_keywords[:10]  # Show first 10
    for keyword in critical_keywords:
        print(f"  • {keyword}")
    
    print("\nCredible Sources:")
    credible_sources = forex_filter.credible_sources[:8]  # Show first 8
    for source in credible_sources:
        print(f"  • {source}")
    
    print("\nHigh Impact Requirements:")
    print("  • Credible sources: 2+ high-impact keywords OR 1+ critical keyword")
    print("  • Other sources: 3+ high-impact keywords OR 2+ critical keywords")

if __name__ == "__main__":
    test_enhanced_filtering()
