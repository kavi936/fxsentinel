#!/usr/bin/env python3
"""
FXSentinel Process Monitor
Monitors the health of all background services and provides alerts when processes fail
"""

import os
import asyncio
import logging
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessStatus:
    """Status information for a monitored process"""
    name: str
    is_running: bool
    last_check: datetime
    last_heartbeat: Optional[datetime]
    error_count: int
    uptime: Optional[timedelta]
    memory_usage: Optional[float]
    cpu_usage: Optional[float]
    status_message: str

class ProcessMonitor:
    def __init__(self):
        """Initialize the process monitor"""
        self.monitored_processes = {}
        self.health_check_interval = 60  # Check every 60 seconds
        self.heartbeat_timeout = 300  # 5 minutes without heartbeat = unhealthy
        self.max_errors = 3  # Max consecutive errors before alert
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        
        # Process definitions
        self.process_definitions = {
            'alert_triggers': {
                'name': 'Alert Triggers Service',
                'description': 'Background monitoring for news alerts',
                'health_endpoint': '/api/health/alerts',
                'process_name': 'alert_triggers',
                'critical': True
            },
            'telegram_monitor': {
                'name': 'Telegram Monitor Service',
                'description': 'WatcherGuru channel monitoring',
                'health_endpoint': '/api/health/telegram',
                'process_name': 'telegram_monitor',
                'critical': True
            },
            'economic_calendar': {
                'name': 'Economic Calendar Service',
                'description': 'Economic event monitoring',
                'health_endpoint': '/api/health/calendar',
                'process_name': 'economic_calendar',
                'critical': False
            },
            'news_aggregator': {
                'name': 'News Aggregator Service',
                'description': 'News feed aggregation',
                'health_endpoint': '/api/health/news',
                'process_name': 'news_aggregator',
                'critical': True
            },
            'ai_analyzer': {
                'name': 'AI Analysis Service',
                'description': 'GPT analysis service',
                'health_endpoint': '/api/health/ai',
                'process_name': 'ai_analyzer',
                'critical': False
            }
        }
    
    async def start_monitoring(self):
        """Start the process monitoring service"""
        logger.info("Starting FXSentinel Process Monitor...")
        
        while True:
            try:
                await self.check_all_processes()
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in process monitoring: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error
    
    async def check_all_processes(self):
        """Check the health of all monitored processes"""
        for process_id, definition in self.process_definitions.items():
            try:
                status = await self.check_process_health(process_id, definition)
                self.monitored_processes[process_id] = status
                
                # Check if process is unhealthy
                if self.is_process_unhealthy(status):
                    await self.handle_unhealthy_process(process_id, status)
                    
            except Exception as e:
                logger.error(f"Error checking process {process_id}: {e}")
                # Mark process as failed
                self.monitored_processes[process_id] = ProcessStatus(
                    name=definition['name'],
                    is_running=False,
                    last_check=datetime.now(),
                    last_heartbeat=None,
                    error_count=self.monitored_processes.get(process_id, ProcessStatus('', False, datetime.now(), None, 0, None, None, None, '')).error_count + 1,
                    uptime=None,
                    memory_usage=None,
                    cpu_usage=None,
                    status_message=f"Error checking process: {e}"
                )
    
    async def check_process_health(self, process_id: str, definition: Dict[str, Any]) -> ProcessStatus:
        """Check the health of a specific process"""
        try:
            # Check if process is running
            is_running = self.is_process_running(definition['process_name'])
            
            # Get system metrics if process is running
            memory_usage = None
            cpu_usage = None
            uptime = None
            
            if is_running:
                memory_usage = self.get_process_memory_usage(definition['process_name'])
                cpu_usage = self.get_process_cpu_usage(definition['process_name'])
                uptime = self.get_process_uptime(definition['process_name'])
            
            # Check health endpoint if available
            last_heartbeat = None
            status_message = "Process running normally"
            
            if definition.get('health_endpoint'):
                try:
                    response = requests.get(
                        f"{self.api_base_url}{definition['health_endpoint']}", 
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        last_heartbeat = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
                        status_message = data.get('status', 'Healthy')
                    else:
                        status_message = f"Health check failed: {response.status_code}"
                except Exception as e:
                    status_message = f"Health check error: {e}"
            
            # Get previous error count
            previous_status = self.monitored_processes.get(process_id)
            error_count = 0 if is_running else (previous_status.error_count + 1 if previous_status else 1)
            
            return ProcessStatus(
                name=definition['name'],
                is_running=is_running,
                last_check=datetime.now(),
                last_heartbeat=last_heartbeat,
                error_count=error_count,
                uptime=uptime,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                status_message=status_message
            )
            
        except Exception as e:
            logger.error(f"Error checking process health for {process_id}: {e}")
            return ProcessStatus(
                name=definition['name'],
                is_running=False,
                last_check=datetime.now(),
                last_heartbeat=None,
                error_count=self.monitored_processes.get(process_id, ProcessStatus('', False, datetime.now(), None, 0, None, None, None, '')).error_count + 1,
                uptime=None,
                memory_usage=None,
                cpu_usage=None,
                status_message=f"Health check failed: {e}"
            )
    
    def is_process_running(self, process_name: str) -> bool:
        """Check if a process is running by name"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if process_name in proc.info['name'] or any(process_name in cmd for cmd in proc.info['cmdline'] if cmd):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking if process {process_name} is running: {e}")
            return False
    
    def get_process_memory_usage(self, process_name: str) -> Optional[float]:
        """Get memory usage for a process in MB"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                if process_name in proc.info['name']:
                    return proc.info['memory_info'].rss / 1024 / 1024  # Convert to MB
            return None
        except Exception as e:
            logger.error(f"Error getting memory usage for {process_name}: {e}")
            return None
    
    def get_process_cpu_usage(self, process_name: str) -> Optional[float]:
        """Get CPU usage for a process as percentage"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if process_name in proc.info['name']:
                    return proc.cpu_percent(interval=1)
            return None
        except Exception as e:
            logger.error(f"Error getting CPU usage for {process_name}: {e}")
            return None
    
    def get_process_uptime(self, process_name: str) -> Optional[timedelta]:
        """Get uptime for a process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                if process_name in proc.info['name']:
                    create_time = datetime.fromtimestamp(proc.info['create_time'])
                    return datetime.now() - create_time
            return None
        except Exception as e:
            logger.error(f"Error getting uptime for {process_name}: {e}")
            return None
    
    def is_process_unhealthy(self, status: ProcessStatus) -> bool:
        """Determine if a process is unhealthy"""
        # Process is not running
        if not status.is_running:
            return True
        
        # Too many consecutive errors
        if status.error_count >= self.max_errors:
            return True
        
        # No heartbeat for too long
        if status.last_heartbeat and (datetime.now() - status.last_heartbeat).total_seconds() > self.heartbeat_timeout:
            return True
        
        # High memory usage (over 500MB)
        if status.memory_usage and status.memory_usage > 500:
            return True
        
        # High CPU usage (over 80% for extended period)
        if status.cpu_usage and status.cpu_usage > 80:
            return True
        
        return False
    
    async def handle_unhealthy_process(self, process_id: str, status: ProcessStatus):
        """Handle an unhealthy process"""
        definition = self.process_definitions[process_id]
        
        logger.warning(f"Unhealthy process detected: {definition['name']}")
        logger.warning(f"Status: {status.status_message}")
        logger.warning(f"Error count: {status.error_count}")
        
        # Send alert if critical process
        if definition.get('critical', False):
            await self.send_process_alert(process_id, status)
        
        # Attempt restart for critical processes
        if definition.get('critical', False) and status.error_count >= self.max_errors:
            await self.attempt_process_restart(process_id, definition)
    
    async def send_process_alert(self, process_id: str, status: ProcessStatus):
        """Send alert about unhealthy process"""
        try:
            # Send to admin users via Telegram
            from .alert_service import get_alert_service
            alert_service = get_alert_service()
            
            alert_data = {
                'title': f"🚨 Process Alert: {status.name}",
                'content': f"""
**Process Status Alert**

**Process:** {status.name}
**Status:** {'❌ Not Running' if not status.is_running else '⚠️ Unhealthy'}
**Error Count:** {status.error_count}
**Last Check:** {status.last_check.strftime('%H:%M:%S')}
**Status Message:** {status.status_message}

**System Metrics:**
• Memory Usage: {f'{status.memory_usage:.1f}MB' if status.memory_usage else 'N/A'}
• CPU Usage: {f'{status.cpu_usage:.1f}%' if status.cpu_usage else 'N/A'}
• Uptime: {str(status.uptime).split('.')[0] if status.uptime else 'N/A'}

**Action Required:** Check system logs and restart if necessary
                """.strip(),
                'priority': 'high',
                'type': 'system_alert'
            }
            
            # Send to admin users (you can configure admin user IDs)
            admin_user_ids = ['admin_user_id']  # Configure this
            for user_id in admin_user_ids:
                user_settings = await alert_service.get_user_alert_settings(user_id)
                await alert_service.process_alert(alert_data, user_settings)
                
        except Exception as e:
            logger.error(f"Error sending process alert: {e}")
    
    async def attempt_process_restart(self, process_id: str, definition: Dict[str, Any]):
        """Attempt to restart a critical process"""
        try:
            logger.info(f"Attempting to restart critical process: {definition['name']}")
            
            # This would typically involve restarting the specific service
            # For now, we'll just log the attempt
            logger.info(f"Restart attempt logged for {process_id}")
            
            # You can implement actual restart logic here:
            # - Restart specific Python processes
            # - Restart Docker containers
            # - Restart system services
            
        except Exception as e:
            logger.error(f"Error attempting process restart: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_processes = len(self.process_definitions)
        running_processes = sum(1 for status in self.monitored_processes.values() if status.is_running)
        critical_processes = sum(1 for pid, defn in self.process_definitions.items() if defn.get('critical', False))
        critical_running = sum(1 for pid, status in self.monitored_processes.items() 
                             if status.is_running and self.process_definitions[pid].get('critical', False))
        
        return {
            'overall_status': 'healthy' if critical_running == critical_processes else 'degraded',
            'total_processes': total_processes,
            'running_processes': running_processes,
            'critical_processes': critical_processes,
            'critical_running': critical_running,
            'last_check': datetime.now().isoformat(),
            'processes': {
                pid: {
                    'name': status.name,
                    'is_running': status.is_running,
                    'last_heartbeat': status.last_heartbeat.isoformat() if status.last_heartbeat else None,
                    'error_count': status.error_count,
                    'memory_usage_mb': status.memory_usage,
                    'cpu_usage_percent': status.cpu_usage,
                    'uptime_seconds': status.uptime.total_seconds() if status.uptime else None,
                    'status_message': status.status_message,
                    'is_critical': self.process_definitions[pid].get('critical', False)
                }
                for pid, status in self.monitored_processes.items()
            }
        }

# Global instance
process_monitor = ProcessMonitor()
