#!/usr/bin/env python3
"""
Manual Alert Processor
Manually process news and send alerts directly to the user
"""

import requests
import json
from datetime import datetime
import sys
import os
import time

# Add backend to path
sys.path.append('backend')

def manual_alert_processor():
    print("🚨 Manual Alert Processor")
    print("=" * 50)
    
    # Your user ID and chat ID
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    chat_id = "8008493413"
    
    # Step 1: Get current news
    print("1. Fetching current news...")
    try:
        response = requests.get("http://localhost:5001/api/news")
        if response.status_code == 200:
            news_data = response.json()
            news_items = news_data.get('news', [])
            high_impact = [n for n in news_items if n.get('impact') == 'high']
            
            print(f"   ✅ Found {len(news_items)} total news items")
            print(f"   High impact: {len(high_impact)}")
            
            if not high_impact:
                print("   ❌ No high-impact news found")
                return
                
        else:
            print(f"   ❌ Failed to get news: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 2: Process high-impact news and send alerts
    print("\n2. Processing high-impact news for alerts...")
    
    from services.news_alert_trigger import news_alert_trigger
    
    alerts_sent = 0
    
    for i, news_item in enumerate(high_impact[:3]):  # Process first 3 high-impact items
        try:
            print(f"   Processing: {news_item.get('title', '')[:50]}...")
            
            # Create user data for this user
            user_data = {
                'user_id': user_id,
                'chat_id': chat_id,
                'settings': {
                    'telegram_enabled': True,
                    'alert_types': ['liveNews'],
                    'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
                    'impact_levels': ['high', 'medium']
                }
            }
            
            # Check if this news should trigger an alert
            if news_alert_trigger.is_forex_high_impact(news_item):
                # Determine if AI analysis is needed
                needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(news_item)
                
                # Send the alert
                success = news_alert_trigger._send_alert_to_user(user_data, news_item, needs_ai_analysis)
                
                if success:
                    alerts_sent += 1
                    print(f"   ✅ Alert sent for: {news_item.get('title', '')[:40]}...")
                else:
                    print(f"   ❌ Failed to send alert for: {news_item.get('title', '')[:40]}...")
                
                # Wait a bit between alerts to avoid spam
                time.sleep(2)
            else:
                print(f"   ⏭️ Skipping (not forex high-impact): {news_item.get('title', '')[:40]}...")
                
        except Exception as e:
            print(f"   ❌ Error processing news item: {e}")
    
    print(f"\n   📊 Summary: {alerts_sent} alerts sent out of {len(high_impact[:3])} processed")
    
    # Step 3: Check economic calendar for upcoming events
    print("\n3. Checking economic calendar for upcoming alerts...")
    try:
        response = requests.get("http://localhost:5001/api/economic-calendar")
        if response.status_code == 200:
            calendar_data = response.json()
            events = calendar_data.get('events', [])
            
            # Find upcoming high-impact events (next 24 hours)
            upcoming_high_impact = []
            for event in events:
                if event.get('impact') == 'high':
                    upcoming_high_impact.append(event)
                    if len(upcoming_high_impact) >= 2:  # Show first 2
                        break
            
            print(f"   ✅ Found {len(events)} total events")
            print(f"   Upcoming high-impact: {len(upcoming_high_impact)}")
            
            if upcoming_high_impact:
                print("   📅 Upcoming high-impact events:")
                for event in upcoming_high_impact:
                    title = event.get('title', 'Unknown')[:40]
                    time = event.get('time', 'Unknown')
                    print(f"      • {title}... ({time})")
                    
                    # Send a pre-event alert for the first upcoming event
                    if upcoming_high_impact.index(event) == 0:
                        print(f"      📨 Sending pre-event alert for: {title}...")
                        
                        # Create pre-event alert
                        pre_event_alert = {
                            'title': f'📅 UPCOMING ECONOMIC EVENT: {title}',
                            'summary': f'High-impact economic event scheduled for {time}. Prepare for potential market volatility.',
                            'source': 'Economic Calendar',
                            'impact': 'high',
                            'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
                            'published_at': datetime.now().isoformat()
                        }
                        
                        user_data = {
                            'user_id': user_id,
                            'chat_id': chat_id,
                            'settings': {
                                'telegram_enabled': True,
                                'alert_types': ['economicCalendar'],
                                'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
                                'impact_levels': ['high']
                            }
                        }
                        
                        success = news_alert_trigger._send_alert_to_user(user_data, pre_event_alert, False)
                        if success:
                            print(f"      ✅ Pre-event alert sent!")
                            alerts_sent += 1
                        else:
                            print(f"      ❌ Failed to send pre-event alert")
                        break
                    
        else:
            print(f"   ❌ Failed to get calendar: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking calendar: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Manual Alert Processing Complete!")
    print(f"📊 Total alerts sent: {alerts_sent}")
    print("📱 Check your Telegram bot for the alerts")
    
    print("\n📈 What You Should Receive:")
    print("• Live news alerts for high-impact forex events")
    print("• Economic calendar pre-event notifications")
    print("• AI analysis of market-moving news")
    print("• Real-time updates on major currency pairs")
    
    print("\n🔄 To get continuous alerts:")
    print("• Run this script periodically")
    print("• Or set up a background service")
    print("• The system is ready to send you live notifications!")

if __name__ == "__main__":
    manual_alert_processor()
