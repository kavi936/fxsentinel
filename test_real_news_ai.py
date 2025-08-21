#!/usr/bin/env python3
"""
Test script to verify real news AI analysis
"""

import requests
import json
from datetime import datetime

def test_real_news_ai_analysis():
    """Test AI analysis with real news format"""
    
    print("🧪 Testing Real News AI Analysis")
    print("=" * 50)
    
    # Test news item (similar to what comes from Telegram)
    test_news = {
        'id': 'test_real_news_123',
        'title': 'Fed Chair Powell Signals Potential Rate Cut in September',
        'summary': 'Federal Reserve Chair Jerome Powell indicated in his Jackson Hole speech that the central bank may consider a rate cut at the September meeting if inflation continues to moderate.',
        'source': 'Reuters',
        'timestamp': datetime.now().isoformat(),
        'impact': 'high',
        'url': 'https://www.reuters.com/markets/us/fed-powell-signals-potential-rate-cut-september-2024-08-21/'
    }
    
    print(f"📰 Test News: {test_news['title']}")
    print(f"📊 Impact: {test_news['impact']}")
    print(f"📅 Time: {test_news['timestamp']}")
    
    # Test AI analysis endpoint
    try:
        event_data = {
            'event': {
                'title': test_news['title'],
                'currency': 'USD',
                'impact': test_news['impact'],
                'description': test_news['summary'],
                'time': test_news['timestamp'],
                'source': test_news['source']
            },
            'analysisType': 'news_analysis'
        }
        
        print("\n🤖 Testing AI Analysis...")
        response = requests.post(
            'http://localhost:5001/api/enhanced-analysis/test_real_news_123',
            json=event_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            analysis = response.json()
            print("✅ AI Analysis Successful!")
            print(f"📊 Confidence Score: {analysis.get('confidence_score', 'N/A')}")
            print(f"🎯 Key Takeaway: {analysis.get('key_takeaway', 'N/A')}")
            print(f"📈 Headline: {analysis.get('headline', 'N/A')}")
            
            # Test alert message creation
            print("\n📱 Testing Alert Message Creation...")
            from backend.services.news_alert_trigger import news_alert_trigger
            
            alert_message = news_alert_trigger._create_alert_message(test_news, analysis)
            print("✅ Alert Message Created:")
            print("-" * 30)
            print(alert_message)
            print("-" * 30)
            
            return True
            
        else:
            print(f"❌ AI Analysis Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI analysis: {e}")
        return False

if __name__ == "__main__":
    test_real_news_ai_analysis()
