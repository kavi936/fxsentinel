#!/usr/bin/env python3
"""
Live monitoring of FXSentinel system
"""

import requests
import json
import time
from datetime import datetime

def get_system_status():
    """Get current system status"""
    try:
        # Check main app
        main_response = requests.get("https://fxsentinel-production.up.railway.app/api/health", timeout=5)
        main_ok = main_response.status_code == 200
        
        # Check worker
        worker_response = requests.get("https://fxsentinel-background-worker-v2-production.up.railway.app/api/health", timeout=5)
        worker_ok = worker_response.status_code == 200
        
        # Check alert service
        alert_response = requests.get("https://fxsentinel-production.up.railway.app/api/health/alert-service", timeout=5)
        alert_ok = alert_response.status_code == 200
        
        # Get news count
        news_response = requests.get("https://fxsentinel-background-worker-v2-production.up.railway.app/api/news", timeout=5)
        news_count = 0
        if news_response.status_code == 200:
            news_data = news_response.json()
            news_count = len(news_data.get('news', []))
        
        return {
            'main_app': main_ok,
            'worker': worker_ok,
            'alert_service': alert_ok,
            'news_count': news_count,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    except Exception as e:
        return {
            'main_app': False,
            'worker': False,
            'alert_service': False,
            'news_count': 0,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'error': str(e)
        }

def monitor_live():
    """Monitor system live"""
    print("🔴 FXSentinel Live Monitor")
    print("=" * 40)
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            status = get_system_status()
            
            # Clear screen (works on most terminals)
            print("\033[2J\033[H", end="")
            
            print("🔴 FXSentinel Live Monitor")
            print("=" * 40)
            print(f"⏰ {status['timestamp']}")
            print()
            
            # Status indicators
            main_icon = "✅" if status['main_app'] else "❌"
            worker_icon = "✅" if status['worker'] else "❌"
            alert_icon = "✅" if status['alert_service'] else "❌"
            
            print(f"🏥 Main App:     {main_icon}")
            print(f"🔧 Worker:       {worker_icon}")
            print(f"📡 Alert Service: {alert_icon}")
            print(f"📰 News Items:   {status['news_count']}")
            
            if 'error' in status:
                print(f"❌ Error: {status['error']}")
            
            # Overall status
            all_ok = status['main_app'] and status['worker'] and status['alert_service']
            overall_icon = "🟢" if all_ok else "🔴"
            print(f"\n🎯 System: {overall_icon} {'HEALTHY' if all_ok else 'ISSUES'}")
            
            print(f"\n⏳ Refreshing in 10 seconds...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped")

if __name__ == "__main__":
    monitor_live()
