#!/usr/bin/env python3
"""
FXSentinel Background Manager
Centralized management of all background processes to prevent excessive logging and API calls
"""

import os
import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - REDUCE VERBOSITY
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BackgroundTask:
    """Background task configuration"""
    name: str
    function: callable
    interval: int  # seconds
    enabled: bool = True
    last_run: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 3

class BackgroundManager:
    def __init__(self):
        """Initialize the background manager"""
        self.tasks = {}
        self.running = False
        self.thread = None
        
        # Rate limiting to prevent API overusage
        self.api_calls_this_hour = 0
        self.last_api_reset = datetime.now()
        self.max_api_calls_per_hour = 100  # Conservative limit
        
        # Initialize tasks
        self._initialize_tasks()
    
    def _initialize_tasks(self):
        """Initialize background tasks with optimized intervals"""
        try:
            # Import services only when needed
            from .process_monitor import process_monitor
            from .alert_triggers import AlertTriggers
            
            # Create alert triggers instance
            alert_triggers = AlertTriggers()
            
            # Add tasks with optimized intervals
            self.tasks = {
                'process_monitor': BackgroundTask(
                    name='Process Monitor',
                    function=self._run_process_monitor,
                    interval=300,  # 5 minutes instead of 60 seconds
                    enabled=True
                ),
                'alert_monitor': BackgroundTask(
                    name='Alert Monitor',
                    function=self._run_alert_monitor,
                    interval=600,  # 10 minutes instead of 2 minutes
                    enabled=True
                ),
                'health_check': BackgroundTask(
                    name='Health Check',
                    function=self._run_health_check,
                    interval=900,  # 15 minutes
                    enabled=True
                )
            }
            
            logger.info("Background tasks initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing background tasks: {e}")
    
    def start(self):
        """Start the background manager"""
        if self.running:
            logger.warning("Background manager is already running")
            return
        
        self.running = True
        logger.info("Starting FXSentinel Background Manager...")
        
        # Start background thread
        self.thread = threading.Thread(target=self._run_background_loop, daemon=True)
        self.thread.start()
        
        logger.info("Background manager started successfully")
    
    def stop(self):
        """Stop the background manager"""
        self.running = False
        logger.info("Background manager stopped")
    
    def _run_background_loop(self):
        """Main background loop with reduced logging"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check rate limits
                if self._should_reset_api_counter(current_time):
                    self._reset_api_counter()
                
                # Run enabled tasks
                for task_id, task in self.tasks.items():
                    if not task.enabled:
                        continue
                    
                    if self._should_run_task(task, current_time):
                        self._run_task_safely(task_id, task)
                
                # Sleep for 30 seconds (reduced from 60)
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in background loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _should_reset_api_counter(self, current_time: datetime) -> bool:
        """Check if API counter should be reset"""
        return (current_time - self.last_api_reset).total_seconds() >= 3600  # 1 hour
    
    def _reset_api_counter(self):
        """Reset API call counter"""
        self.api_calls_this_hour = 0
        self.last_api_reset = datetime.now()
        logger.debug("API counter reset")
    
    def _should_run_task(self, task: BackgroundTask, current_time: datetime) -> bool:
        """Check if task should run based on interval"""
        if task.last_run is None:
            return True
        
        time_since_last = (current_time - task.last_run).total_seconds()
        return time_since_last >= task.interval
    
    def _run_task_safely(self, task_id: str, task: BackgroundTask):
        """Run a task safely with error handling"""
        try:
            # Check API rate limits
            if self.api_calls_this_hour >= self.max_api_calls_per_hour:
                logger.warning(f"API rate limit reached, skipping {task.name}")
                return
            
            # Run the task
            task.function()
            task.last_run = datetime.now()
            task.error_count = 0
            
            # Increment API counter
            self.api_calls_this_hour += 1
            
            # Log only on first run or after errors
            if task.error_count == 0:
                logger.info(f"✅ {task.name} completed successfully")
            
        except Exception as e:
            task.error_count += 1
            logger.error(f"❌ Error in {task.name}: {e}")
            
            # Disable task if too many errors
            if task.error_count >= task.max_errors:
                logger.warning(f"⚠️ Disabling {task.name} due to repeated errors")
                task.enabled = False
    
    def _run_process_monitor(self):
        """Run process monitoring with reduced frequency"""
        try:
            from .process_monitor import process_monitor
            
            # Only check critical processes
            critical_processes = ['alert_triggers', 'telegram_monitor', 'news_aggregator']
            
            for process_id in critical_processes:
                if process_id in process_monitor.process_definitions:
                    definition = process_monitor.process_definitions[process_id]
                    status = asyncio.run(process_monitor.check_process_health(process_id, definition))
                    
                    # Only log if there's an issue
                    if not status.is_running or status.error_count > 0:
                        logger.warning(f"Process {definition['name']} has issues: {status.status_message}")
            
        except Exception as e:
            logger.error(f"Error in process monitor: {e}")
    
    def _run_alert_monitor(self):
        """Run alert monitoring with reduced frequency"""
        try:
            from .alert_triggers import AlertTriggers
            from .news_aggregator import news_aggregator
            
            # Get recent news (cached to avoid API calls)
            recent_news = news_aggregator.get_recent_news(hours=2)
            
            if recent_news:
                alert_triggers = AlertTriggers()
                results = alert_triggers.process_news_for_alerts(recent_news)
                
                # Only log if alerts were sent
                if results.get('alerts_sent', 0) > 0:
                    logger.info(f"📨 Sent {results['alerts_sent']} alerts")
            
        except Exception as e:
            logger.error(f"Error in alert monitor: {e}")
    
    def _run_health_check(self):
        """Run basic health check"""
        try:
            # Simple health check without making API calls
            import psutil
            
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Only log if resources are high
            if cpu_percent > 80 or memory_percent > 80:
                logger.warning(f"High resource usage: CPU {cpu_percent}%, Memory {memory_percent}%")
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get background manager status"""
        return {
            'running': self.running,
            'api_calls_this_hour': self.api_calls_this_hour,
            'max_api_calls_per_hour': self.max_api_calls_per_hour,
            'tasks': {
                task_id: {
                    'name': task.name,
                    'enabled': task.enabled,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'error_count': task.error_count,
                    'interval': task.interval
                }
                for task_id, task in self.tasks.items()
            }
        }
    
    def enable_task(self, task_id: str):
        """Enable a background task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self.tasks[task_id].error_count = 0
            logger.info(f"Enabled task: {task_id}")
    
    def disable_task(self, task_id: str):
        """Disable a background task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            logger.info(f"Disabled task: {task_id}")

# Global instance
background_manager = BackgroundManager()
