#!/usr/bin/env python3
"""
FXSentinel Persistent Alert Service Manager
Keeps the alert bot running continuously with auto-restart
"""

import time
import sys
import signal
import logging
import subprocess
import os
from datetime import datetime, timedelta
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alert_service_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertServiceManager:
    def __init__(self):
        self.running = False
        self.service_process = None
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_delay = 30  # seconds
        self.health_check_interval = 60  # seconds
        self.last_health_check = None
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop_service()
        self.running = False
    
    def start_service(self):
        """Start the robust alert service"""
        try:
            logger.info("🚀 Starting Robust Alert Service...")
            
            # Get the current directory and navigate to backend
            current_dir = os.getcwd()
            backend_dir = os.path.join(current_dir, 'backend')
            
            if not os.path.exists(backend_dir):
                logger.error(f"❌ Backend directory not found: {backend_dir}")
                return False
            
            # Start the service from the backend directory
            self.service_process = subprocess.Popen([
                'python3', '-c', 
                'from services.robust_alert_service import start_robust_alert_service; start_robust_alert_service()'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=backend_dir)
            
            logger.info(f"✅ Service started with PID: {self.service_process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start service: {e}")
            return False
    
    def stop_service(self):
        """Stop the robust alert service"""
        if self.service_process:
            try:
                logger.info(f"🛑 Stopping service (PID: {self.service_process.pid})")
                self.service_process.terminate()
                self.service_process.wait(timeout=10)
                logger.info("✅ Service stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Service didn't stop gracefully, forcing kill")
                self.service_process.kill()
            except Exception as e:
                logger.error(f"❌ Error stopping service: {e}")
            finally:
                self.service_process = None
    
    def is_service_healthy(self):
        """Check if the service is healthy"""
        try:
            response = requests.get('http://localhost:5001/api/health/alerts', timeout=5)
            if response.status_code == 200:
                data = response.json()
                robust_service = data.get('robust_service', {})
                
                # Check if service is running
                status = robust_service.get('status', 'unknown')
                if status != 'running':
                    return False
                
                # Check uptime
                uptime = robust_service.get('uptime_seconds', 0)
                if uptime <= 0:
                    return False
                
                # Check last successful check
                last_check = robust_service.get('last_successful_check')
                if last_check:
                    from datetime import datetime
                    last_check_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                    time_since_last = datetime.now().replace(tzinfo=None) - last_check_time.replace(tzinfo=None)
                    if time_since_last > timedelta(minutes=15):
                        return False
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False
    
    def check_service_process(self):
        """Check if the service process is still running"""
        if self.service_process:
            return self.service_process.poll() is None
        return False
    
    def restart_service(self):
        """Restart the service"""
        logger.info(f"🔄 Restarting service (attempt {self.restart_count + 1}/{self.max_restarts})")
        
        self.stop_service()
        time.sleep(self.restart_delay)
        
        if self.start_service():
            self.restart_count += 1
            logger.info(f"✅ Service restarted successfully")
            return True
        else:
            logger.error(f"❌ Failed to restart service")
            return False
    
    def run(self):
        """Main management loop"""
        logger.info("🚀 FXSentinel Alert Service Manager Starting")
        logger.info(f"⏰ Health check interval: {self.health_check_interval} seconds")
        logger.info(f"🔄 Max restarts: {self.max_restarts}")
        logger.info(f"⏳ Restart delay: {self.restart_delay} seconds")
        
        self.running = True
        
        # Start the service initially
        if not self.start_service():
            logger.error("❌ Failed to start service initially")
            return
        
        while self.running:
            try:
                # Check if process is still running
                if not self.check_service_process():
                    logger.warning("⚠️ Service process has stopped")
                    if self.restart_count < self.max_restarts:
                        if not self.restart_service():
                            logger.error("❌ Failed to restart service, exiting")
                            break
                    else:
                        logger.error(f"❌ Max restarts ({self.max_restarts}) reached, exiting")
                        break
                
                # Check service health periodically
                if (self.last_health_check is None or 
                    datetime.now() - self.last_health_check > timedelta(seconds=self.health_check_interval)):
                    
                    if not self.is_service_healthy():
                        logger.warning("⚠️ Service health check failed")
                        if self.restart_count < self.max_restarts:
                            if not self.restart_service():
                                logger.error("❌ Failed to restart service after health check failure")
                                break
                        else:
                            logger.error(f"❌ Max restarts ({self.max_restarts}) reached, exiting")
                            break
                    else:
                        logger.debug("✅ Service health check passed")
                    
                    self.last_health_check = datetime.now()
                
                # Wait before next check
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"🚨 Error in management loop: {e}")
                time.sleep(30)  # Wait before retry
        
        # Cleanup
        self.stop_service()
        logger.info("🛑 Alert Service Manager stopped")

def main():
    """Main function"""
    manager = AlertServiceManager()
    
    try:
        manager.run()
    except Exception as e:
        logger.error(f"🚨 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
