#!/usr/bin/env python3
"""
Check for missed alerts in the current news feed
"""

import requests
import json
from datetime import datetime, timedelta
import time

def check_current_news_feed():
    """Check the current news feed for high-impact forex news"""
    print("🔍 Checking Current News Feed for Missed Alerts")
    print("=" * 60)
    print(f"📅 Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Get current news from the worker
    worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
    
    try:
        print("📡 Fetching current news feed...")
        response = requests.get(f"{worker_url}/api/news-feed", timeout=30)
        
        if response.status_code == 200:
            news_data = response.json()
            print(f"✅ Successfully fetched news feed")
            print(f"📊 Total news items: {len(news_data.get('news', []))}")
            print()
            
            # Analyze news items
            news_items = news_data.get('news', [])
            high_impact_news = []
            
            print("🔍 Analyzing News Items:")
            print("=" * 30)
            
            for i, item in enumerate(news_items[:20]):  # Check last 20 items
                title = item.get('title', '')
                summary = item.get('summary', '')
                timestamp = item.get('timestamp', '')
                source = item.get('source', '')
                
                # Check if it's high-impact forex news
                is_forex_high_impact = check_if_forex_high_impact(title, summary)
                
                if is_forex_high_impact:
                    high_impact_news.append(item)
                    print(f"🚨 HIGH IMPACT: {title[:60]}...")
                    print(f"   📅 Time: {timestamp}")
                    print(f"   📰 Source: {source}")
                    print()
                else:
                    print(f"📰 Regular: {title[:60]}...")
            
            print(f"📊 Analysis Complete:")
            print(f"   🔍 Total items checked: {min(20, len(news_items))}")
            print(f"   🚨 High-impact forex news found: {len(high_impact_news)}")
            print()
            
            if high_impact_news:
                print("🚨 **HIGH-IMPACT FOREX NEWS THAT SHOULD TRIGGER ALERTS:**")
                print("=" * 60)
                
                for i, item in enumerate(high_impact_news, 1):
                    print(f"{i}. **{item.get('title', '')}**")
                    print(f"   📅 Time: {item.get('timestamp', '')}")
                    print(f"   📰 Source: {item.get('source', '')}")
                    print(f"   📝 Summary: {item.get('summary', '')[:100]}...")
                    print()
                
                # Test if these would trigger alerts
                print("🧪 Testing Alert Trigger for Latest High-Impact News:")
                print("=" * 50)
                
                latest_news = high_impact_news[0]
                test_alert_trigger(latest_news)
                
            else:
                print("✅ No high-impact forex news found in recent feed")
                print("   This could mean:")
                print("   - No significant forex news in the last few hours")
                print("   - All high-impact news has already been processed")
                print("   - News filtering is working correctly")
            
        else:
            print(f"❌ Failed to fetch news feed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error fetching news feed: {e}")

def check_if_forex_high_impact(title, summary):
    """Check if news item is high-impact forex news"""
    # High-impact keywords
    high_impact_keywords = [
        'interest rate', 'fed', 'federal reserve', 'ecb', 'european central bank',
        'boe', 'bank of england', 'boj', 'bank of japan', 'rba', 'reserve bank',
        'inflation', 'gdp', 'unemployment', 'non-farm payroll', 'nfp',
        'rate cut', 'rate hike', 'monetary policy', 'quantitative easing',
        'tapering', 'dovish', 'hawkish', 'fomc', 'policy decision',
        'breaking', 'urgent', 'alert', 'forex', 'currency', 'fx',
        'usd', 'eur', 'gbp', 'jpy', 'aud', 'cad', 'chf', 'nzd',
        'dollar', 'euro', 'pound', 'yen', 'australian dollar',
        'canadian dollar', 'swiss franc', 'new zealand dollar'
    ]
    
    # Combine title and summary
    text = f"{title} {summary}".lower()
    
    # Check for high-impact keywords
    keyword_matches = sum(1 for keyword in high_impact_keywords if keyword in text)
    
    # Check for breaking news indicators
    breaking_indicators = ['breaking', 'urgent', 'alert', 'flash', 'immediate']
    has_breaking = any(indicator in text for indicator in breaking_indicators)
    
    # Check for currency pairs
    currency_pairs = ['usd/eur', 'eur/usd', 'gbp/usd', 'usd/jpy', 'usd/cad', 'aud/usd']
    has_currency_pair = any(pair in text for pair in currency_pairs)
    
    # Determine if high impact
    is_high_impact = (
        keyword_matches >= 2 or  # Multiple forex-related keywords
        (keyword_matches >= 1 and has_breaking) or  # Forex keyword + breaking
        (keyword_matches >= 1 and has_currency_pair)  # Forex keyword + currency pair
    )
    
    return is_high_impact

def test_alert_trigger(news_item):
    """Test if the news item would trigger an alert"""
    try:
        worker_url = "https://fxsentinel-background-worker-v2-production.up.railway.app"
        
        # Create alert data
        alert_data = {
            'type': 'news',
            'data': news_item
        }
        
        print(f"🧪 Testing alert trigger for: {news_item.get('title', '')[:50]}...")
        
        response = requests.post(
            f"{worker_url}/api/trigger-alerts",
            json=alert_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Alert trigger test successful")
            print(f"   📊 News processed: {result.get('news_alerts_processed', False)}")
            print(f"   📊 Calendar processed: {result.get('calendar_alerts_processed', False)}")
            print(f"   📅 Timestamp: {result.get('timestamp', '')}")
        else:
            print(f"❌ Alert trigger test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing alert trigger: {e}")

if __name__ == "__main__":
    check_current_news_feed()
