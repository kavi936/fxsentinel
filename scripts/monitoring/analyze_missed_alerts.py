#!/usr/bin/env python3
"""
Analyze missed alerts - check live news feed for high-impact news that should have been sent
"""

import sys
import os
sys.path.append('backend')

import requests
import json
from datetime import datetime, timedelta
from backend.services.enhanced_forex_filter import EnhancedForexFilter
from backend.services.news_alert_trigger import news_alert_trigger

def analyze_missed_alerts():
    """Analyze the live news feed for missed high-impact alerts"""
    print("🔍 Analyzing Missed Alerts")
    print("=" * 60)
    
    try:
        # Get current news from the main app
        print("📰 Fetching current news feed...")
        response = requests.get("https://fxsentinel-production.up.railway.app/api/news", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to get news: {response.status_code}")
            return False
        
        news_data = response.json()
        news_items = news_data.get('news', [])
        
        print(f"📊 Found {len(news_items)} total news items")
        
        # Initialize filters
        forex_filter = EnhancedForexFilter()
        
        # Analyze each news item
        high_impact_news = []
        missed_alerts = []
        
        print(f"\n🔍 Analyzing news items for high-impact forex relevance...")
        
        for i, news_item in enumerate(news_items):
            title = news_item.get('title', '')
            summary = news_item.get('summary', '')
            source = news_item.get('source', '')
            impact = news_item.get('impact', '')
            published_at = news_item.get('published_at', '')
            
            print(f"\n📰 News {i+1}: {title[:60]}...")
            print(f"   📅 Published: {published_at}")
            print(f"   🏷️  Impact: {impact}")
            print(f"   📡 Source: {source}")
            
            # Check if it's high impact according to our system
            is_high_impact = news_item.get('impact') == 'high'
            
            # Check if it's forex relevant using enhanced filter
            is_forex_related = forex_filter.is_forex_related(title, summary, source)
            is_high_impact_for_alerts = forex_filter.is_high_impact_for_alerts(title, summary, source)
            
            # Check if it should have been sent as alert
            should_send_alert = news_alert_trigger.is_forex_high_impact(news_item)
            
            print(f"   🎯 System Impact: {is_high_impact}")
            print(f"   💱 Forex Related: {is_forex_related}")
            print(f"   🚨 High Impact for Alerts: {is_high_impact_for_alerts}")
            print(f"   📤 Should Send Alert: {should_send_alert}")
            
            # Categorize the news
            if is_high_impact:
                high_impact_news.append(news_item)
            
            # Check if this should have been an alert but wasn't sent
            if should_send_alert or (is_forex_related and is_high_impact_for_alerts):
                # This is a potential missed alert
                missed_alerts.append({
                    'news_item': news_item,
                    'reason': 'High-impact forex news detected',
                    'forex_related': is_forex_related,
                    'high_impact_for_alerts': is_high_impact_for_alerts,
                    'should_send_alert': should_send_alert
                })
                print(f"   ⚠️  POTENTIAL MISSED ALERT!")
        
        # Summary
        print(f"\n📋 Analysis Summary:")
        print(f"   📊 Total news items: {len(news_items)}")
        print(f"   🎯 High impact news: {len(high_impact_news)}")
        print(f"   ⚠️  Potential missed alerts: {len(missed_alerts)}")
        
        if missed_alerts:
            print(f"\n🚨 MISSED ALERTS ANALYSIS:")
            print("=" * 50)
            
            for i, missed in enumerate(missed_alerts):
                news_item = missed['news_item']
                print(f"\n{i+1}. {news_item.get('title', '')}")
                print(f"   📅 Published: {news_item.get('published_at', '')}")
                print(f"   📡 Source: {news_item.get('source', '')}")
                print(f"   💱 Forex Related: {missed['forex_related']}")
                print(f"   🚨 High Impact for Alerts: {missed['high_impact_for_alerts']}")
                print(f"   📤 Should Send Alert: {missed['should_send_alert']}")
                print(f"   📝 Summary: {news_item.get('summary', '')[:100]}...")
                
                # Analyze why it might have been missed
                reasons = []
                if not missed['should_send_alert']:
                    reasons.append("Failed forex high-impact check")
                if not missed['forex_related']:
                    reasons.append("Not detected as forex related")
                if not missed['high_impact_for_alerts']:
                    reasons.append("Not high impact for alerts")
                
                if reasons:
                    print(f"   🔍 Possible reasons for missing: {', '.join(reasons)}")
        
        # Check recent news (last 24 hours)
        print(f"\n⏰ Recent News Analysis (Last 24 hours):")
        print("=" * 50)
        
        now = datetime.now()
        recent_missed = []
        
        for missed in missed_alerts:
            news_item = missed['news_item']
            published_at = news_item.get('published_at', '')
            
            try:
                # Parse the published time (assuming ISO format)
                if published_at:
                    pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    time_diff = now - pub_time.replace(tzinfo=None)
                    
                    if time_diff.total_seconds() < 86400:  # 24 hours
                        recent_missed.append(missed)
            except:
                # If we can't parse the time, assume it's recent
                recent_missed.append(missed)
        
        print(f"   📊 Recent missed alerts (24h): {len(recent_missed)}")
        
        if recent_missed:
            print(f"\n🚨 RECENT MISSED ALERTS:")
            for i, missed in enumerate(recent_missed):
                news_item = missed['news_item']
                print(f"   {i+1}. {news_item.get('title', '')[:80]}...")
                print(f"      📅 {news_item.get('published_at', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing missed alerts: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alert_processing_for_news(news_item):
    """Test alert processing for a specific news item"""
    print(f"\n🧪 Testing Alert Processing for: {news_item.get('title', '')[:50]}...")
    
    try:
        # Test the alert processing pipeline
        result = news_alert_trigger.process_news_for_alerts([news_item])
        
        print(f"   📊 Processing result: {result}")
        
        if result.get('alerts_sent', 0) > 0:
            print(f"   ✅ Alert would be sent successfully")
        else:
            print(f"   ❌ Alert would not be sent")
            print(f"   🔍 Reasons: {result.get('errors', [])}")
        
        return result.get('alerts_sent', 0) > 0
        
    except Exception as e:
        print(f"   ❌ Error testing alert processing: {e}")
        return False

if __name__ == "__main__":
    success = analyze_missed_alerts()
    if success:
        print("\n🎯 Missed alerts analysis: COMPLETED")
    else:
        print("\n🔧 Missed alerts analysis: FAILED")
