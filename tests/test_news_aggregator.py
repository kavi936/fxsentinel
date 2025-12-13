#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.news_aggregator import news_aggregator

def test_news_aggregator():
    print("Testing News Aggregator...")
    print("=" * 50)
    
    try:
        # Test getting recent news
        print("Fetching recent news...")
        news = news_aggregator.get_recent_news(hours=24)
        
        print(f"Found {len(news)} articles")
        print("\nFirst few articles:")
        
        for i, article in enumerate(news[:3]):
            print(f"\n{i+1}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Impact: {article['impact']}")
            print(f"   Published: {article['published_at']}")
            if article['currency_pairs']:
                print(f"   Currency Pairs: {', '.join(article['currency_pairs'])}")
        
        return True
        
    except Exception as e:
        print(f"Error testing news aggregator: {e}")
        return False

if __name__ == "__main__":
    success = test_news_aggregator()
    if success:
        print("\n✅ News aggregator test completed successfully!")
    else:
        print("\n❌ News aggregator test failed!")
        sys.exit(1)
