#!/usr/bin/env python3
"""
Test script for MVP News Analyzer
"""

import sys
import os
sys.path.append('backend')

from services.mvp_news_analyzer import mvp_news_analyzer

def test_mvp_analyzer():
    """Test the MVP news analyzer with sample news items"""
    
    # Test news items
    test_news_items = [
        {
            "id": 123456789,
            "title": "Trump Says Dollar 'Too Strong', Threatens Currency Intervention",
            "summary": "Former President Trump criticized the strength of the US dollar in a campaign speech, suggesting he would take action to weaken the currency if re-elected. 'The dollar is killing our exports,' Trump said, 'we need to do something about it.'",
            "source": "Reuters",
            "currency_pairs": ["EUR/USD", "USD/JPY", "USD/CNY"],
            "impact": "High"
        },
        {
            "id": 123456790,
            "title": "Fed Chair Powell Signals Potential Rate Cuts in 2024",
            "summary": "Federal Reserve Chair Jerome Powell indicated that the central bank may consider interest rate cuts in 2024 if inflation continues to moderate. The dovish comments suggest a more accommodative monetary policy stance.",
            "source": "Bloomberg",
            "currency_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
            "impact": "High"
        },
        {
            "id": 123456791,
            "title": "European Manufacturing PMI Shows Slight Improvement",
            "summary": "The European manufacturing Purchasing Managers' Index (PMI) showed a slight improvement in December, rising to 47.8 from 47.6 in November. While still below the 50.0 threshold indicating expansion, the data suggests stabilization in the sector.",
            "source": "MarketWatch",
            "currency_pairs": ["EUR/USD", "EUR/GBP"],
            "impact": "Medium"
        }
    ]
    
    print("🧪 Testing MVP News Analyzer")
    print("=" * 50)
    
    for i, news_item in enumerate(test_news_items, 1):
        print(f"\n📰 Test {i}: {news_item['title']}")
        print("-" * 40)
        
        # Test if news deserves GPT analysis
        should_use_gpt = mvp_news_analyzer.should_use_gpt_analysis(news_item)
        print(f"Should use GPT: {should_use_gpt}")
        
        # Analyze news
        result = mvp_news_analyzer.analyze_news(news_item)
        
        print(f"Analysis Type: {result.analysis_type}")
        print(f"Immediate Reaction: {result.immediate_reaction}")
        print(f"Confidence: {result.confidence}%")
        print(f"Volatility: {result.volatility}")
        print(f"Timeframe: {result.timeframe}")
        print(f"Cost: ${result.cost}")
        
        print(f"\n📊 News Impact:")
        print(result.news_impact)
        
        print(f"\n💼 Trading Implications:")
        print(result.trading_implications)
        
        print(f"\n🎯 Key Pairs: {', '.join(result.key_pairs)}")
        print(f"🔑 Key Levels: {', '.join(result.key_levels)}")
        
        print(f"\n📈 Trading Strategies:")
        for strategy in result.trading_strategies:
            print(f"  - {strategy['name']}: {strategy['direction']} on {strategy['pair']}")
            print(f"    Risk Level: {strategy['risk_level']}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    test_mvp_analyzer()
