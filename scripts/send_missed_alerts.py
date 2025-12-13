#!/usr/bin/env python3
"""
Send missed alerts manually for high-impact news that should have been sent
"""

import requests
import json
from datetime import datetime

def send_missed_alerts():
    """Send alerts for missed high-impact news"""
    print("🚨 Sending Missed Alerts")
    print("=" * 50)
    
    # List of missed high-impact news that should have been sent
    missed_alerts = [
        {
            'id': 'missed_alert_1',
            'title': 'Trump says he\'s ready to put \'major sanctions\' on Russia if NATO nations do the same',
            'summary': 'President Donald Trump has repeatedly threatened to impose sanctions on Russia over its invasion of Ukraine, and now he\'s saying he\'s ready to put "major sanctions" on Russia if NATO nations do the same.',
            'content': 'President Donald Trump has repeatedly threatened to impose sanctions on Russia over its invasion of Ukraine, and now he\'s saying he\'s ready to put "major sanctions" on Russia if NATO nations do the same. This could have significant impact on forex markets, particularly EUR/USD and USD/RUB pairs.',
            'source': 'CNBC',
            'impact': 'high',
            'published_at': '2025-09-13T13:57:21',
            'url': 'https://www.cnbc.com/2025/09/13/trump-sanctions-russia-nato.html',
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'missed_alert_2',
            'title': 'The $14 Trillion US Stock Rally is Seeking a Fed Cut Playbook',
            'summary': 'A $14 trillion rally that has taken stocks to record highs is heading for an inflection point next week when the Federal Reserve meets to decide on interest rates.',
            'content': 'A $14 trillion rally that has taken stocks to record highs is heading for an inflection point next week when the Federal Reserve meets to decide on interest rates. This is critical forex news as it directly impacts USD pairs and market sentiment.',
            'source': 'Bloomberg',
            'impact': 'high',
            'published_at': '2025-09-13T13:00:00',
            'url': 'https://www.bloomberg.com/news/articles/2025-09-13/fed-cut-playbook',
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'missed_alert_3',
            'title': 'JPMorgan expects the Federal Reserve to cut interest rates by 25bps next week',
            'summary': 'JPMorgan expects the Federal Reserve to cut interest rates by 25bps next week, which could significantly impact forex markets.',
            'content': 'JPMorgan expects the Federal Reserve to cut interest rates by 25bps next week. This is a major forex market mover as it directly affects USD strength and interest rate differentials.',
            'source': 'Telegram - WatcherGuru',
            'impact': 'high',
            'published_at': '2025-09-12T16:15:35+00:00',
            'url': '',
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'missed_alert_4',
            'title': 'ECB\'s Nagel: More rate cuts could threaten price stability',
            'summary': 'ECB Nagel is saying: More rate cuts could threaten price stability. The ECB kept rates unchanged yesterday but this commentary is important for EUR pairs.',
            'content': 'ECB Nagel is saying: More rate cuts could threaten price stability. The ECB kept rates unchanged yesterday but this commentary is important for EUR pairs and European monetary policy outlook.',
            'source': 'ForexLive',
            'impact': 'high',
            'published_at': '2025-09-12T16:32:41',
            'url': 'https://www.forexlive.com/news/ecb-nagel-rate-cuts-20250912',
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'missed_alert_5',
            'title': 'The US dollar sags as we count down to Fed week',
            'summary': 'Treasury yields are 3-6 basis points higher on the day and that initially gave the US dollar a lift but it has since sagged as we count down to Fed week.',
            'content': 'Treasury yields are 3-6 basis points higher on the day and that initially gave the US dollar a lift but it has since sagged as we count down to Fed week. This is direct forex market analysis affecting USD pairs.',
            'source': 'ForexLive',
            'impact': 'high',
            'published_at': '2025-09-12T17:41:48',
            'url': 'https://www.forexlive.com/news/usd-sags-fed-week-20250912',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    main_app_url = "https://fxsentinel-production.up.railway.app"
    total_sent = 0
    
    for i, news_item in enumerate(missed_alerts):
        print(f"\n📰 Sending alert {i+1}/{len(missed_alerts)}: {news_item['title'][:60]}...")
        
        alert_data = {
            'type': 'news',
            'data': news_item
        }
        
        try:
            response = requests.post(
                f"{main_app_url}/api/alerts/trigger",
                json=alert_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                alerts_sent = result.get('alerts_sent', 0)
                print(f"   ✅ Alert sent: {alerts_sent} alerts delivered")
                total_sent += alerts_sent
            else:
                print(f"   ❌ Alert failed: {response.status_code}")
                print(f"   📋 Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error sending alert: {e}")
        
        # Small delay between alerts
        import time
        time.sleep(2)
    
    print(f"\n📋 Summary:")
    print(f"   📨 Total alerts sent: {total_sent}")
    print(f"   📊 Missed alerts processed: {len(missed_alerts)}")
    
    if total_sent > 0:
        print(f"   🎉 Successfully sent {total_sent} missed alerts!")
    else:
        print(f"   ⚠️  No alerts were sent - check system status")
    
    return total_sent > 0

if __name__ == "__main__":
    success = send_missed_alerts()
    if success:
        print("\n🎯 Missed alerts sent: SUCCESS")
    else:
        print("\n🔧 Missed alerts sent: FAILED")
