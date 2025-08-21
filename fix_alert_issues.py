#!/usr/bin/env python3
"""
Fix Alert Issues
Comprehensive fix for alert formatting, data population, and duplicate prevention
"""

import sys
sys.path.append('backend')

from services.news_alert_trigger import news_alert_trigger
from services.firebase_realtime_storage import FirebaseRealtimeStorage
from datetime import datetime, timedelta
import requests

def fix_alert_message_formatting():
    """Fix the alert message formatting to use proper HTML for Telegram"""
    
    # Update the _create_alert_message method in news_alert_trigger.py
    print("🔧 Fixing alert message formatting...")
    
    # Create a test news item with proper data
    test_news = {
        'title': 'Fed Announces Interest Rate Decision',
        'summary': 'The Federal Reserve has announced a 25 basis point rate hike.',
        'source': 'Reuters',
        'url': 'https://example.com/article',
        'timestamp': datetime.now().isoformat(),
        'impact': 'high',
        'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
        'published_at': datetime.now().isoformat()
    }
    
    # Test the current message creation
    current_message = news_alert_trigger._create_alert_message(test_news)
    print("Current message format:")
    print(current_message)
    print("\n" + "="*50)
    
    # Create improved message format
    def create_improved_alert_message(news_item, ai_analysis=None):
        """Create properly formatted alert message with HTML tags"""
        try:
            title = news_item.get('title', 'Unknown Title')
            source = news_item.get('source', 'Unknown Source')
            url = news_item.get('url', '')
            timestamp = news_item.get('timestamp', '')
            summary = news_item.get('summary', '')
            
            # Get currency pairs
            affected_pairs = news_item.get('currency_pairs', [])
            if not affected_pairs:
                affected_pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD']  # Default pairs
            pairs_text = ', '.join(affected_pairs)
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M UTC')
            except:
                formatted_time = datetime.now().strftime('%H:%M UTC')
            
            # Create properly formatted message with HTML tags
            message = f"""🚨 <b>BREAKING FOREX NEWS</b>

<b>{title}</b>

📊 <b>Details:</b>
• Time: {formatted_time}
• Source: {source}
• Currency Pairs: {pairs_text}"""
            
            # Add summary if available
            if summary:
                message += f"\n\n📝 <b>Summary:</b>\n{summary}"
            
            # Add AI analysis if available
            if ai_analysis and isinstance(ai_analysis, dict):
                analysis_text = ai_analysis.get('analysis', '')
                if analysis_text:
                    if len(analysis_text) > 300:
                        analysis_text = analysis_text[:297] + "..."
                    message += f"\n\n🤖 <b>AI Analysis:</b>\n{analysis_text}"
                else:
                    message += "\n\n🤖 <b>AI Analysis:</b> Available on dashboard"
            else:
                message += "\n\n📈 <b>Market Impact:</b> Monitor for price action"
            
            # Add footer
            if url:
                message += f"\n\n🔗 <a href='{url}'>Read Full Article</a>"
            message += "\n📱 Check dashboard for detailed analysis"
            
            return message
            
        except Exception as e:
            print(f"Error creating improved alert message: {e}")
            return f"🚨 <b>Breaking Forex News:</b> {title}"
    
    # Test the improved message
    improved_message = create_improved_alert_message(test_news)
    print("Improved message format:")
    print(improved_message)
    
    return create_improved_alert_message

def fix_economic_calendar_duplicates():
    """Fix duplicate economic calendar alerts by implementing proper tracking"""
    
    print("\n🔧 Fixing economic calendar duplicate alerts...")
    
    class EconomicCalendarTracker:
        def __init__(self):
            self.sent_events = {}  # Track sent events with timing
            self.alert_times = [120, 60, 10]  # 2 hours, 1 hour, 10 minutes before
            
        def should_send_alert(self, event_id, event_time):
            """Check if alert should be sent for this event at this time"""
            now = datetime.now()
            
            try:
                # Parse event time
                event_dt = datetime.strptime(event_time, '%H:%M UTC')
                event_dt = event_dt.replace(year=now.year, month=now.month, day=now.day)
                
                # Calculate time until event
                time_until_event = event_dt - now
                minutes_until_event = time_until_event.total_seconds() / 60
                
                # Check if we should send an alert
                for alert_minutes in self.alert_times:
                    if 0 <= minutes_until_event <= alert_minutes and minutes_until_event >= alert_minutes - 5:
                        # Check if we already sent this alert
                        alert_key = f"{event_id}_{alert_minutes}"
                        if alert_key not in self.sent_events:
                            self.sent_events[alert_key] = now
                            return True, alert_minutes
                
                return False, None
                
            except Exception as e:
                print(f"Error checking alert timing: {e}")
                return False, None
        
        def get_alert_message(self, event, minutes_before):
            """Create economic calendar alert message"""
            title = event.get('title', 'Unknown Event')
            event_time = event.get('time', 'Unknown Time')
            currency = event.get('currency', 'USD')
            expected = event.get('expected', 'N/A')
            previous = event.get('previous', 'N/A')
            
            time_text = {
                120: "2 hours",
                60: "1 hour", 
                10: "10 minutes"
            }.get(minutes_before, f"{minutes_before} minutes")
            
            message = f"""📅 <b>UPCOMING ECONOMIC EVENT</b>

<b>{title}</b> - Event starts in {time_text}

📊 <b>Event Details:</b>
• Time: {event_time} UTC
• Currency: {currency}
• Expected: {expected}
• Previous: {previous}

💱 <b>Affected Pairs:</b> {currency}/USD, EUR/{currency}

🎯 <b>Prepare for Market Volatility!</b>
📱 Check dashboard for detailed analysis"""
            
            return message
    
    tracker = EconomicCalendarTracker()
    
    # Test with a sample event
    test_event = {
        'id': 'test_event_123',
        'title': 'US CPI Data Release',
        'time': '13:30 UTC',
        'currency': 'USD',
        'expected': '3.2%',
        'previous': '3.1%',
        'impact': 'high'
    }
    
    should_send, minutes = tracker.should_send_alert('test_event_123', '13:30 UTC')
    print(f"Should send alert: {should_send}, Minutes before: {minutes}")
    
    if should_send:
        alert_message = tracker.get_alert_message(test_event, minutes)
        print("Economic calendar alert message:")
        print(alert_message)
    
    return tracker

def fix_data_population():
    """Fix the data population issue in alert messages"""
    
    print("\n🔧 Fixing data population in alerts...")
    
    def create_data_rich_alert(news_item):
        """Create alert with properly populated data"""
        
        # Ensure all required fields are present
        title = news_item.get('title', 'Unknown Title')
        source = news_item.get('source', 'Unknown Source')
        url = news_item.get('url', '')
        timestamp = news_item.get('timestamp', '')
        summary = news_item.get('summary', '')
        
        # Get currency pairs
        currency_pairs = news_item.get('currency_pairs', [])
        if not currency_pairs:
            # Try to extract from title or summary
            text = f"{title} {summary}".lower()
            if 'eur' in text and 'usd' in text:
                currency_pairs.append('EUR/USD')
            if 'usd' in text and 'jpy' in text:
                currency_pairs.append('USD/JPY')
            if 'gbp' in text and 'usd' in text:
                currency_pairs.append('GBP/USD')
            if not currency_pairs:
                currency_pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD']
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%H:%M UTC')
        except:
            formatted_time = datetime.now().strftime('%H:%M UTC')
        
        # Create rich alert data
        rich_news_item = {
            'title': title,
            'source': source,
            'url': url,
            'timestamp': timestamp,
            'summary': summary,
            'currency_pairs': currency_pairs,
            'formatted_time': formatted_time,
            'impact': news_item.get('impact', 'medium')
        }
        
        return rich_news_item
    
    # Test with sample data
    sample_news = {
        'title': 'Fed Announces Interest Rate Decision',
        'summary': 'The Federal Reserve has announced a 25 basis point rate hike, bringing the target range to 5.25-5.50%.',
        'source': 'Reuters',
        'url': 'https://www.reuters.com/markets/us/fed-raises-rates-25-basis-points-2023-07-26/',
        'timestamp': datetime.now().isoformat(),
        'impact': 'high'
    }
    
    rich_news = create_data_rich_alert(sample_news)
    print("Rich news data:")
    for key, value in rich_news.items():
        print(f"  {key}: {value}")
    
    return create_data_rich_alert

def main():
    """Main function to apply all fixes"""
    print("🚀 FXSentinel Alert System Fixes")
    print("=" * 50)
    
    # Fix 1: Message formatting
    improved_message_creator = fix_alert_message_formatting()
    
    # Fix 2: Economic calendar duplicates
    calendar_tracker = fix_economic_calendar_duplicates()
    
    # Fix 3: Data population
    data_enricher = fix_data_population()
    
    print("\n" + "=" * 50)
    print("✅ All fixes prepared!")
    print("\n📋 Next Steps:")
    print("1. Update the alert message creation function")
    print("2. Implement economic calendar tracking")
    print("3. Ensure proper data population")
    print("4. Test the fixes with real alerts")

if __name__ == "__main__":
    main()
