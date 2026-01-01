#!/usr/bin/env python3
"""
24-Hour Alert System Monitor
Monitors alert system health and sends periodic reports
"""

import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class AlertMonitor:
    def __init__(self, duration_hours: int = 24):
        self.duration_hours = duration_hours
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        
        self.metrics = {
            'checks_performed': 0,
            'alerts_triggered': 0,
            'alerts_sent': 0,
            'errors': [],
            'worker_status_checks': [],
            'alert_trigger_tests': []
        }
        
        self.api_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        self.check_interval = 300  # 5 minutes
        
    def check_worker_status(self) -> Dict:
        """Check background worker status"""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'error', 'code': response.status_code}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_backend_health(self) -> Dict:
        """Check backend health"""
        try:
            response = requests.get(f"{self.api_url}/api/hello", timeout=10)
            if response.status_code == 200:
                return {'status': 'healthy'}
            else:
                return {'status': 'error', 'code': response.status_code}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def test_alert_trigger(self) -> Dict:
        """Test alert trigger endpoint"""
        try:
            test_news = {
                'id': f'monitor_test_{datetime.now().timestamp()}',
                'title': 'Monitor Test Alert',
                'source': 'Monitor',
                'impact': 'high',
                'timestamp': datetime.now().isoformat()
            }
            
            alert_data = {
                'type': 'news',
                'data': test_news
            }
            
            response = requests.post(
                f"{self.api_url}/api/alerts/trigger",
                json=alert_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'status': 'success',
                    'alerts_sent': result.get('alerts_sent', 0),
                    'total_users': result.get('total_users', 0)
                }
            else:
                return {'status': 'error', 'code': response.status_code}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_user_count(self) -> int:
        """Get number of users with alerts"""
        try:
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase = FirebaseRealtimeStorage()
            users = firebase.get_all_users_with_alerts()
            return len(users) if users else 0
        except:
            return 0
    
    def run_check(self):
        """Perform a single monitoring check"""
        check_time = datetime.now()
        print(f"\n[{check_time.strftime('%Y-%m-%d %H:%M:%S')}] Performing check...")
        
        self.metrics['checks_performed'] += 1
        
        # Check backend health
        backend_health = self.check_backend_health()
        if backend_health.get('status') != 'healthy':
            self.metrics['errors'].append({
                'time': check_time.isoformat(),
                'type': 'backend_health',
                'error': backend_health.get('error', 'Unknown')
            })
            print("  ⚠️  Backend health check failed")
        else:
            print("  ✅ Backend is healthy")
        
        # Check worker status
        worker_status = self.check_worker_status()
        self.metrics['worker_status_checks'].append({
            'time': check_time.isoformat(),
            'status': worker_status
        })
        
        if worker_status.get('status') == 'healthy':
            print("  ✅ Worker is healthy")
        else:
            print("  ⚠️  Worker status check failed")
            self.metrics['errors'].append({
                'time': check_time.isoformat(),
                'type': 'worker_status',
                'error': worker_status.get('error', 'Unknown')
            })
        
        # Test alert trigger (every 30 minutes)
        if self.metrics['checks_performed'] % 6 == 0:  # Every 30 minutes (6 * 5 min)
            print("  🔄 Testing alert trigger...")
            trigger_result = self.test_alert_trigger()
            self.metrics['alert_trigger_tests'].append({
                'time': check_time.isoformat(),
                'result': trigger_result
            })
            
            if trigger_result.get('status') == 'success':
                alerts_sent = trigger_result.get('alerts_sent', 0)
                if alerts_sent > 0:
                    print(f"  ✅ Alert trigger test: {alerts_sent} alerts sent")
                    self.metrics['alerts_sent'] += alerts_sent
                else:
                    print("  ⚠️  Alert trigger test: No alerts sent")
            else:
                print(f"  ❌ Alert trigger test failed: {trigger_result.get('error', 'Unknown')}")
                self.metrics['errors'].append({
                    'time': check_time.isoformat(),
                    'type': 'alert_trigger',
                    'error': trigger_result.get('error', 'Unknown')
                })
    
    def generate_report(self) -> str:
        """Generate monitoring report"""
        elapsed = datetime.now() - self.start_time
        elapsed_hours = elapsed.total_seconds() / 3600
        
        user_count = self.get_user_count()
        
        report = f"""
{'=' * 70}
  24-HOUR ALERT SYSTEM MONITORING REPORT
{'=' * 70}

Monitoring Period:
  Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
  End: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}
  Elapsed: {elapsed_hours:.1f} hours

System Status:
  Users with alerts: {user_count}
  Checks performed: {self.metrics['checks_performed']}
  Alerts sent: {self.metrics['alerts_sent']}
  Errors encountered: {len(self.metrics['errors'])}

Worker Status:
"""
        
        if self.metrics['worker_status_checks']:
            recent_checks = self.metrics['worker_status_checks'][-10:]
            healthy_count = sum(1 for c in recent_checks if c.get('status', {}).get('status') == 'healthy')
            report += f"  Recent health checks: {healthy_count}/{len(recent_checks)} healthy\n"
        
        if self.metrics['errors']:
            report += f"\nErrors:\n"
            for error in self.metrics['errors'][-10:]:  # Last 10 errors
                report += f"  [{error['time']}] {error['type']}: {error.get('error', 'Unknown')}\n"
        else:
            report += "\n✅ No errors encountered!\n"
        
        report += f"\n{'=' * 70}\n"
        
        return report
    
    def run(self):
        """Run monitoring loop"""
        print(f"""
{'=' * 70}
  ALERT SYSTEM 24-HOUR MONITOR
{'=' * 70}

Starting monitoring...
  Duration: {self.duration_hours} hours
  Check interval: {self.check_interval} seconds (5 minutes)
  Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
  End time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}

Monitoring will run until {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}
Press Ctrl+C to stop early and generate report.
""")
        
        try:
            while datetime.now() < self.end_time:
                self.run_check()
                
                # Calculate time until next check
                time_remaining = (self.end_time - datetime.now()).total_seconds()
                if time_remaining < self.check_interval:
                    break
                
                print(f"  Next check in {self.check_interval // 60} minutes...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring interrupted by user")
        
        # Generate final report
        print(self.generate_report())
        
        # Save report to file
        report_file = f"monitoring_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(self.generate_report())
        print(f"📄 Report saved to: {report_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor alert system for 24 hours')
    parser.add_argument('--hours', type=int, default=24, help='Duration in hours (default: 24)')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds (default: 300 = 5 minutes)')
    
    args = parser.parse_args()
    
    monitor = AlertMonitor(duration_hours=args.hours)
    monitor.check_interval = args.interval
    monitor.run()

if __name__ == "__main__":
    main()

