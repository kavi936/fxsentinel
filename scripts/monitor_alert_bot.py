#!/usr/bin/env python3
"""
FXSentinel Alert Bot Continuous Monitor
Continuously monitors the alert bot system and provides real-time status updates
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
import threading

class AlertBotMonitor:
    def __init__(self, base_url: str = "http://localhost:5001", check_interval: int = 30):
        self.base_url = base_url
        self.check_interval = check_interval  # seconds
        self.running = False
        self.last_status = {}
        self.status_history = []
        self.max_history = 100
        
    def get_alert_service_status(self) -> Dict[str, Any]:
        """Get current alert service status"""
        try:
            response = requests.get(f"{self.base_url}/api/health/alerts", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'error': str(e)}
    
    def is_service_active(self, status_data: Dict[str, Any]) -> bool:
        """Determine if the alert service is actively working"""
        try:
            robust_service = status_data.get('robust_service', {})
            
            # Check if service is running
            service_status = robust_service.get('status', 'unknown')
            if service_status != 'running':
                return False
            
            # Check uptime
            uptime = robust_service.get('uptime_seconds', 0)
            if uptime <= 0:
                return False
            
            # Check error count
            error_count = robust_service.get('error_count', 0)
            if error_count >= 10:
                return False
            
            # Check last successful check
            last_check = robust_service.get('last_successful_check')
            if last_check:
                last_check_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                time_since_last = datetime.now().replace(tzinfo=None) - last_check_time.replace(tzinfo=None)
                if time_since_last > timedelta(minutes=10):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def format_status_line(self, status_data: Dict[str, Any]) -> str:
        """Format status for display"""
        try:
            robust_service = status_data.get('robust_service', {})
            
            # Get key metrics
            status = robust_service.get('status', 'unknown')
            uptime = robust_service.get('uptime_seconds', 0)
            alerts_sent = robust_service.get('alerts_sent_today', 0)
            alerts_failed = robust_service.get('alerts_failed_today', 0)
            error_count = robust_service.get('error_count', 0)
            last_check = robust_service.get('last_successful_check')
            
            # Format uptime
            if uptime < 60:
                uptime_str = f"{int(uptime)}s"
            elif uptime < 3600:
                uptime_str = f"{int(uptime // 60)}m"
            else:
                uptime_str = f"{int(uptime // 3600)}h"
            
            # Format last check
            if last_check:
                last_check_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                time_since = datetime.now().replace(tzinfo=None) - last_check_time.replace(tzinfo=None)
                if time_since < timedelta(minutes=1):
                    last_check_str = "now"
                elif time_since < timedelta(hours=1):
                    last_check_str = f"{int(time_since.total_seconds() // 60)}m ago"
                else:
                    last_check_str = f"{int(time_since.total_seconds() // 3600)}h ago"
            else:
                last_check_str = "never"
            
            # Determine status indicator
            is_active = self.is_service_active(status_data)
            status_indicator = "🟢" if is_active else "🔴"
            
            return f"{status_indicator} {status.upper()} | Uptime: {uptime_str} | Alerts: {alerts_sent}✅/{alerts_failed}❌ | Errors: {error_count} | Last: {last_check_str}"
            
        except Exception as e:
            return f"🔴 ERROR: {str(e)}"
    
    def print_status(self, status_data: Dict[str, Any]):
        """Print formatted status"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        status_line = self.format_status_line(status_data)
        print(f"[{timestamp}] {status_line}")
    
    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "=" * 80)
        print("📊 ALERT BOT MONITORING SUMMARY")
        print("=" * 80)
        
        if not self.status_history:
            print("No status history available")
            return
        
        # Calculate statistics
        total_checks = len(self.status_history)
        active_count = sum(1 for status in self.status_history if self.is_service_active(status))
        inactive_count = total_checks - active_count
        
        # Calculate uptime percentage
        uptime_percentage = (active_count / total_checks * 100) if total_checks > 0 else 0
        
        print(f"📈 Total Checks: {total_checks}")
        print(f"✅ Active Periods: {active_count}")
        print(f"❌ Inactive Periods: {inactive_count}")
        print(f"📊 Uptime: {uptime_percentage:.1f}%")
        
        # Show recent activity
        if self.status_history:
            latest = self.status_history[-1]
            robust_service = latest.get('robust_service', {})
            alerts_sent = robust_service.get('alerts_sent_today', 0)
            alerts_failed = robust_service.get('alerts_failed_today', 0)
            
            print(f"📨 Alerts Sent Today: {alerts_sent}")
            print(f"❌ Alerts Failed Today: {alerts_failed}")
            
            if alerts_sent + alerts_failed > 0:
                success_rate = (alerts_sent / (alerts_sent + alerts_failed)) * 100
                print(f"📊 Success Rate: {success_rate:.1f}%")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        print("🚀 Starting FXSentinel Alert Bot Monitor")
        print(f"🔗 Monitoring: {self.base_url}")
        print(f"⏰ Check Interval: {self.check_interval} seconds")
        print("=" * 80)
        print("Format: [TIME] STATUS | Uptime | Alerts (sent/failed) | Errors | Last Check")
        print("=" * 80)
        
        self.running = True
        
        try:
            while self.running:
                # Get current status
                status_data = self.get_alert_service_status()
                
                # Store in history
                self.status_history.append(status_data)
                if len(self.status_history) > self.max_history:
                    self.status_history.pop(0)
                
                # Print status
                self.print_status(status_data)
                
                # Check for significant changes
                if self.last_status and self.has_significant_change(status_data):
                    print("⚠️  SIGNIFICANT STATUS CHANGE DETECTED")
                
                self.last_status = status_data
                
                # Wait for next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        except Exception as e:
            print(f"\n🚨 Monitoring error: {str(e)}")
        finally:
            self.print_summary()
    
    def has_significant_change(self, current_status: Dict[str, Any]) -> bool:
        """Check if there's a significant change in status"""
        if not self.last_status:
            return False
        
        try:
            current_robust = current_status.get('robust_service', {})
            last_robust = self.last_status.get('robust_service', {})
            
            # Check if service status changed
            current_running = current_robust.get('status') == 'running'
            last_running = last_robust.get('status') == 'running'
            
            if current_running != last_running:
                return True
            
            # Check if error count increased significantly
            current_errors = current_robust.get('error_count', 0)
            last_errors = last_robust.get('error_count', 0)
            
            if current_errors > last_errors + 2:  # More than 2 new errors
                return True
            
            return False
            
        except Exception:
            return False
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor FXSentinel Alert Bot')
    parser.add_argument('--url', default='http://localhost:5001', 
                       help='Base URL of the FXSentinel API')
    parser.add_argument('--interval', type=int, default=30,
                       help='Check interval in seconds (default: 30)')
    parser.add_argument('--save-history', action='store_true',
                       help='Save status history to file')
    
    args = parser.parse_args()
    
    # Check if custom URL is provided via environment
    base_url = os.getenv('FXSENTINEL_URL', args.url)
    
    monitor = AlertBotMonitor(base_url, args.interval)
    
    try:
        monitor.start_monitoring()
        
        # Save history if requested
        if args.save_history and monitor.status_history:
            with open('alert_bot_monitor_history.json', 'w') as f:
                json.dump(monitor.status_history, f, indent=2, default=str)
            print("💾 Status history saved to: alert_bot_monitor_history.json")
            
    except Exception as e:
        print(f"🚨 Error: {str(e)}")

if __name__ == "__main__":
    main()
