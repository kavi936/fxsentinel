#!/usr/bin/env python3
"""
FXSentinel Alert Bot Status Checker
Comprehensive monitoring script to check if the alert bot system is actively working
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

class AlertBotStatusChecker:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.status = {}
        
    def check_health_endpoints(self) -> Dict[str, Any]:
        """Check all health endpoints to assess system status"""
        print("🔍 Checking Alert Bot System Health...")
        print("=" * 60)
        
        endpoints = {
            'main_health': '/api/health',
            'alerts_health': '/api/health/alerts',
            'telegram_health': '/api/health/telegram',
            'calendar_health': '/api/health/calendar',
            'news_health': '/api/health/news',
            'system_health': '/api/health/system'
        }
        
        results = {}
        
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results[name] = {
                        'status': 'healthy',
                        'data': data
                    }
                    print(f"✅ {name.replace('_', ' ').title()}: HEALTHY")
                else:
                    results[name] = {
                        'status': 'unhealthy',
                        'error': f"HTTP {response.status_code}"
                    }
                    print(f"❌ {name.replace('_', ' ').title()}: UNHEALTHY (HTTP {response.status_code})")
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"🚨 {name.replace('_', ' ').title()}: ERROR - {str(e)}")
        
        return results
    
    def check_alert_service_status(self) -> Dict[str, Any]:
        """Check the robust alert service status specifically"""
        print("\n🤖 Checking Alert Service Status...")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/api/health/alerts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Extract key information
                robust_service = data.get('robust_service', {})
                status = robust_service.get('status', 'unknown')
                uptime = robust_service.get('uptime_seconds', 0)
                alerts_sent = robust_service.get('alerts_sent_today', 0)
                alerts_failed = robust_service.get('alerts_failed_today', 0)
                last_check = robust_service.get('last_successful_check')
                error_count = robust_service.get('error_count', 0)
                
                print(f"📊 Service Status: {status.upper()}")
                print(f"⏱️  Uptime: {self.format_uptime(uptime)}")
                print(f"📨 Alerts Sent Today: {alerts_sent}")
                print(f"❌ Alerts Failed Today: {alerts_failed}")
                print(f"🔄 Last Successful Check: {last_check or 'Never'}")
                print(f"⚠️  Error Count: {error_count}")
                
                # Determine if actively working
                is_active = (
                    status == 'running' and 
                    uptime > 0 and 
                    error_count < 10 and
                    (last_check is None or 
                     datetime.fromisoformat(last_check.replace('Z', '+00:00')) > 
                     datetime.now().replace(tzinfo=None) - timedelta(minutes=10))
                )
                
                if is_active:
                    print("✅ Alert Service: ACTIVELY WORKING")
                else:
                    print("❌ Alert Service: NOT ACTIVELY WORKING")
                
                return {
                    'is_active': is_active,
                    'status': status,
                    'uptime': uptime,
                    'alerts_sent': alerts_sent,
                    'alerts_failed': alerts_failed,
                    'last_check': last_check,
                    'error_count': error_count
                }
            else:
                print(f"❌ Failed to get alert service status: HTTP {response.status_code}")
                return {'is_active': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"🚨 Error checking alert service: {str(e)}")
            return {'is_active': False, 'error': str(e)}
    
    def check_recent_activity(self) -> Dict[str, Any]:
        """Check for recent alert activity"""
        print("\n📈 Checking Recent Activity...")
        print("-" * 40)
        
        try:
            # Check if there are any recent logs or activity
            response = requests.get(f"{self.base_url}/api/health/alerts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                robust_service = data.get('robust_service', {})
                
                # Check various activity indicators
                last_check = robust_service.get('last_successful_check')
                alerts_sent = robust_service.get('alerts_sent_today', 0)
                users_processed = robust_service.get('users_processed', 0)
                
                if last_check:
                    last_check_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                    time_since_last = datetime.now().replace(tzinfo=None) - last_check_time.replace(tzinfo=None)
                    
                    print(f"🕐 Last Activity: {last_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"⏰ Time Since Last Check: {self.format_timedelta(time_since_last)}")
                    print(f"👥 Users Processed: {users_processed}")
                    print(f"📨 Total Alerts Sent Today: {alerts_sent}")
                    
                    # Determine if activity is recent
                    is_recent = time_since_last < timedelta(minutes=15)
                    
                    if is_recent:
                        print("✅ Recent Activity: DETECTED")
                    else:
                        print("⚠️  Recent Activity: STALE (No activity in last 15 minutes)")
                    
                    return {
                        'is_recent': is_recent,
                        'last_check': last_check,
                        'time_since_last': time_since_last.total_seconds(),
                        'alerts_sent': alerts_sent,
                        'users_processed': users_processed
                    }
                else:
                    print("❌ No recent activity found")
                    return {'is_recent': False, 'error': 'No last check time available'}
            else:
                print(f"❌ Failed to get activity data: HTTP {response.status_code}")
                return {'is_recent': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"🚨 Error checking recent activity: {str(e)}")
            return {'is_recent': False, 'error': str(e)}
    
    def check_background_processes(self) -> Dict[str, Any]:
        """Check if background processes are running"""
        print("\n🔄 Checking Background Processes...")
        print("-" * 40)
        
        try:
            # Check system health endpoint for process information
            response = requests.get(f"{self.base_url}/api/health/system", timeout=10)
            if response.status_code == 200:
                data = response.json()
                processes = data.get('processes', {})
                
                critical_processes = ['alert_triggers', 'telegram_monitor', 'news_aggregator']
                running_count = 0
                
                for process_id in critical_processes:
                    if process_id in processes:
                        process_info = processes[process_id]
                        is_running = process_info.get('is_running', False)
                        status_msg = process_info.get('status_message', 'Unknown')
                        
                        if is_running:
                            print(f"✅ {process_id}: RUNNING - {status_msg}")
                            running_count += 1
                        else:
                            print(f"❌ {process_id}: STOPPED - {status_msg}")
                    else:
                        print(f"⚠️  {process_id}: NOT MONITORED")
                
                all_running = running_count == len(critical_processes)
                
                if all_running:
                    print("✅ All Critical Processes: RUNNING")
                else:
                    print(f"⚠️  Critical Processes: {running_count}/{len(critical_processes)} RUNNING")
                
                return {
                    'all_running': all_running,
                    'running_count': running_count,
                    'total_critical': len(critical_processes),
                    'processes': processes
                }
            else:
                print(f"❌ Failed to get process data: HTTP {response.status_code}")
                return {'all_running': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"🚨 Error checking background processes: {str(e)}")
            return {'all_running': False, 'error': str(e)}
    
    def check_telegram_connection(self) -> Dict[str, Any]:
        """Check Telegram bot connection status"""
        print("\n📱 Checking Telegram Connection...")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/api/health/alerts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                telegram_status = data.get('telegram_bot', 'disconnected')
                
                if telegram_status == 'connected':
                    print("✅ Telegram Bot: CONNECTED")
                    return {'connected': True, 'status': telegram_status}
                else:
                    print("❌ Telegram Bot: DISCONNECTED")
                    return {'connected': False, 'status': telegram_status}
            else:
                print(f"❌ Failed to get Telegram status: HTTP {response.status_code}")
                return {'connected': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"🚨 Error checking Telegram connection: {str(e)}")
            return {'connected': False, 'error': str(e)}
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run a comprehensive check of the alert bot system"""
        print("🚀 FXSentinel Alert Bot Status Check")
        print("=" * 60)
        print(f"🔗 Checking: {self.base_url}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all checks
        health_results = self.check_health_endpoints()
        alert_status = self.check_alert_service_status()
        recent_activity = self.check_recent_activity()
        background_processes = self.check_background_processes()
        telegram_connection = self.check_telegram_connection()
        
        # Compile overall status
        overall_status = {
            'timestamp': datetime.now().isoformat(),
            'health_endpoints': health_results,
            'alert_service': alert_status,
            'recent_activity': recent_activity,
            'background_processes': background_processes,
            'telegram_connection': telegram_connection
        }
        
        # Determine overall system status
        is_healthy = (
            alert_status.get('is_active', False) and
            recent_activity.get('is_recent', False) and
            background_processes.get('all_running', False) and
            telegram_connection.get('connected', False)
        )
        
        print("\n" + "=" * 60)
        print("📊 OVERALL SYSTEM STATUS")
        print("=" * 60)
        
        if is_healthy:
            print("✅ ALERT BOT SYSTEM: FULLY OPERATIONAL")
            print("🎯 The bot is actively working and searching for new items to alert")
        else:
            print("❌ ALERT BOT SYSTEM: NOT FULLY OPERATIONAL")
            print("🔧 Some components may need attention")
        
        # Print summary
        print(f"\n📋 Summary:")
        print(f"   • Alert Service Active: {'✅' if alert_status.get('is_active') else '❌'}")
        print(f"   • Recent Activity: {'✅' if recent_activity.get('is_recent') else '❌'}")
        print(f"   • Background Processes: {'✅' if background_processes.get('all_running') else '❌'}")
        print(f"   • Telegram Connected: {'✅' if telegram_connection.get('connected') else '❌'}")
        
        return overall_status
    
    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds // 60)} minutes"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} hours"
        else:
            return f"{int(seconds // 86400)} days"
    
    def format_timedelta(self, td: timedelta) -> str:
        """Format timedelta in human readable format"""
        total_seconds = int(td.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds} seconds"
        elif total_seconds < 3600:
            return f"{total_seconds // 60} minutes"
        elif total_seconds < 86400:
            return f"{total_seconds // 3600} hours"
        else:
            return f"{total_seconds // 86400} days"

def main():
    """Main function"""
    # Check if custom URL is provided
    base_url = os.getenv('FXSENTINEL_URL', 'http://localhost:5001')
    
    checker = AlertBotStatusChecker(base_url)
    
    try:
        results = checker.run_comprehensive_check()
        
        # Save results to file
        with open('alert_bot_status.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: alert_bot_status.json")
        
    except KeyboardInterrupt:
        print("\n⏹️  Check interrupted by user")
    except Exception as e:
        print(f"\n🚨 Error during check: {str(e)}")

if __name__ == "__main__":
    main()
