#!/usr/bin/env python3
"""
FXSentinel Cost-Optimized Monitor
Reduces API calls and external service usage while maintaining core functionality
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - MINIMAL VERBOSITY
logging.basicConfig(
    level=logging.ERROR,  # Only log errors to reduce noise
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CostOptimizedTask:
    """Cost-optimized task configuration"""
    name: str
    function: callable
    interval: int  # seconds - much longer intervals
    enabled: bool = True
    last_run: Optional[datetime] = None
    cost_estimate: float = 0.0  # Estimated cost per run in USD
    max_daily_cost: float = 1.0  # Maximum daily cost in USD

class CostOptimizedMonitor:
    def __init__(self):
        """Initialize cost-optimized monitor"""
        self.tasks = {}
        self.running = False
        self.daily_costs = {}
        self.last_cost_reset = datetime.now()
        
        # Cost tracking
        self.total_daily_cost = 0.0
        self.max_daily_budget = 5.0  # $5/day maximum
        
        # Initialize tasks with conservative settings
        self._initialize_tasks()
    
    def _initialize_tasks(self):
        """Initialize tasks with cost-optimized intervals"""
        self.tasks = {
            'basic_health_check': CostOptimizedTask(
                name='Basic Health Check',
                function=self._basic_health_check,
                interval=1800,  # 30 minutes instead of 60 seconds
                cost_estimate=0.001,  # $0.001 per check
                max_daily_cost=0.05
            ),
            'alert_quality_check': CostOptimizedTask(
                name='Alert Quality Check',
                function=self._alert_quality_check,
                interval=3600,  # 1 hour instead of continuous
                cost_estimate=0.01,  # $0.01 per check (includes potential GPT calls)
                max_daily_cost=0.50
            ),
            'process_monitor': CostOptimizedTask(
                name='Process Monitor',
                function=self._process_monitor,
                interval=7200,  # 2 hours instead of 60 seconds
                cost_estimate=0.002,  # $0.002 per check
                max_daily_cost=0.10
            )
        }
        
        logger.info("Cost-optimized tasks initialized")
    
    def start(self):
        """Start the cost-optimized monitor"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting cost-optimized monitor...")
        
        # Run in main thread with long intervals
        import threading
        self.thread = threading.Thread(target=self._run_monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the monitor"""
        self.running = False
        logger.info("Cost-optimized monitor stopped")
    
    def _run_monitor_loop(self):
        """Main monitor loop with cost controls"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Reset daily costs if needed
                if self._should_reset_daily_costs(current_time):
                    self._reset_daily_costs()
                
                # Check if we're within budget
                if self.total_daily_cost >= self.max_daily_budget:
                    logger.warning(f"Daily budget exceeded (${self.total_daily_cost:.2f}), pausing tasks")
                    time.sleep(3600)  # Wait 1 hour
                    continue
                
                # Run enabled tasks
                for task_id, task in self.tasks.items():
                    if not task.enabled:
                        continue
                    
                    # Check task-specific daily cost limit
                    task_daily_cost = self.daily_costs.get(task_id, 0.0)
                    if task_daily_cost >= task.max_daily_cost:
                        continue
                    
                    if self._should_run_task(task, current_time):
                        self._run_task_safely(task_id, task)
                
                # Sleep for 5 minutes (much longer than before)
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(600)  # Wait 10 minutes on error
    
    def _should_reset_daily_costs(self, current_time: datetime) -> bool:
        """Check if daily costs should be reset"""
        return (current_time - self.last_cost_reset).total_seconds() >= 86400  # 24 hours
    
    def _reset_daily_costs(self):
        """Reset daily cost tracking"""
        self.daily_costs = {}
        self.total_daily_cost = 0.0
        self.last_cost_reset = datetime.now()
        logger.info("Daily costs reset")
    
    def _should_run_task(self, task: CostOptimizedTask, current_time: datetime) -> bool:
        """Check if task should run based on interval"""
        if task.last_run is None:
            return True
        
        time_since_last = (current_time - task.last_run).total_seconds()
        return time_since_last >= task.interval
    
    def _run_task_safely(self, task_id: str, task: CostOptimizedTask):
        """Run task safely with cost tracking"""
        try:
            # Check if we can afford this task
            task_daily_cost = self.daily_costs.get(task_id, 0.0)
            if task_daily_cost + task.cost_estimate > task.max_daily_cost:
                logger.warning(f"Task {task.name} would exceed daily cost limit")
                return
            
            # Run the task
            task.function()
            task.last_run = datetime.now()
            
            # Track costs
            self.daily_costs[task_id] = task_daily_cost + task.cost_estimate
            self.total_daily_cost += task.cost_estimate
            
            logger.info(f"✅ {task.name} completed (cost: ${task.cost_estimate:.3f})")
            
        except Exception as e:
            logger.error(f"❌ Error in {task.name}: {e}")
    
    def _basic_health_check(self):
        """Basic health check without external API calls"""
        try:
            import psutil
            
            # Check system resources (no API calls)
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Only log if resources are critically high
            if cpu_percent > 90 or memory_percent > 90:
                logger.error(f"Critical resource usage: CPU {cpu_percent}%, Memory {memory_percent}%")
            
        except Exception as e:
            logger.error(f"Error in basic health check: {e}")
    
    def _alert_quality_check(self):
        """Cost-optimized alert quality check"""
        try:
            # Only check quality for high-impact news (reduce GPT calls)
            from .news_aggregator import news_aggregator
            
            # Get cached news to avoid API calls
            recent_news = news_aggregator.get_recent_news(hours=4)  # Longer cache
            
            if not recent_news:
                return
            
            # Only process the most recent high-impact news
            high_impact_news = []
            for news in recent_news[:5]:  # Limit to 5 items
                if self._is_high_impact_news(news):
                    high_impact_news.append(news)
                    if len(high_impact_news) >= 2:  # Only process 2 items max
                        break
            
            if high_impact_news:
                from .alert_quality_enhancer import alert_quality_enhancer
                
                # Process with conservative settings
                for news in high_impact_news:
                    # Use cached user preferences to avoid Firebase calls
                    user_preferences = self._get_cached_user_preferences()
                    
                    quality_score = alert_quality_enhancer.evaluate_alert_quality(
                        news, user_preferences
                    )
                    
                    # Only log if quality is very high or very low
                    if quality_score.overall_score > 0.9 or quality_score.overall_score < 0.3:
                        logger.info(f"Quality alert: {news.get('title', 'Unknown')} - Score: {quality_score.overall_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error in alert quality check: {e}")
    
    def _process_monitor(self):
        """Cost-optimized process monitoring"""
        try:
            import psutil
            
            # Check if main processes are running (no external API calls)
            critical_processes = ['python', 'flask', 'app.py']
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if any(critical in proc_info['name'].lower() for critical in critical_processes):
                        # Process is running, no need to check further
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # If we get here, no critical processes found
            logger.error("No critical processes found running")
            
        except Exception as e:
            logger.error(f"Error in process monitor: {e}")
    
    def _is_high_impact_news(self, news: Dict[str, Any]) -> bool:
        """Check if news is high impact without external calls"""
        title = news.get('title', '').lower()
        
        # Critical keywords that indicate high impact
        critical_keywords = [
            'fed', 'federal reserve', 'ecb', 'european central bank',
            'boe', 'bank of england', 'nfp', 'non-farm payrolls',
            'cpi', 'inflation', 'interest rate', 'breaking', 'urgent'
        ]
        
        return any(keyword in title for keyword in critical_keywords)
    
    def _get_cached_user_preferences(self) -> Dict[str, Any]:
        """Get cached user preferences to avoid Firebase calls"""
        # Return default preferences to avoid external API calls
        return {
            'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
            'impactLevels': {'high': True, 'medium': True, 'low': False},
            'alertTypes': {'liveNews': True, 'preNews': True, 'postNews': True},
            'quietHours': {'enabled': False}
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return {
            'total_daily_cost': self.total_daily_cost,
            'max_daily_budget': self.max_daily_budget,
            'budget_remaining': self.max_daily_budget - self.total_daily_cost,
            'task_costs': self.daily_costs,
            'last_reset': self.last_cost_reset.isoformat()
        }
    
    def set_daily_budget(self, budget: float):
        """Set daily budget limit"""
        self.max_daily_budget = budget
        logger.info(f"Daily budget set to ${budget:.2f}")

# Global instance
cost_optimized_monitor = CostOptimizedMonitor()
