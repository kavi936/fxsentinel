#!/usr/bin/env python3
"""
Deployment Recovery Script
Ensures FXSentinel bot is healthy after GitHub deployments
"""

import requests
import time
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_bot_health_after_deployment():
    """Ensure bot is healthy after deployment"""
    
    # Get deployment URL from environment or use default
    deployment_url = os.getenv('DEPLOYMENT_URL', 'https://your-app.railway.app')
    
    logger.info(f"🔍 Starting deployment health check for: {deployment_url}")
    
    # Wait for deployment to complete
    logger.info("⏳ Waiting 30 seconds for deployment to complete...")
    time.sleep(30)
    
    # Check health multiple times
    for attempt in range(5):
        try:
            logger.info(f"🔍 Health check attempt {attempt + 1}/5")
            
            # Check deployment health
            response = requests.get(f"{deployment_url}/api/deployment-health-check", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📊 Health check response: {data}")
                
                if data.get('status') == 'healthy':
                    logger.info("✅ Bot is healthy after deployment!")
                    return True
                else:
                    logger.warning(f"⚠️ Bot needs attention: {data.get('message', 'Unknown issue')}")
                    
                    # Check which services are down
                    services = data.get('services', {})
                    for service, status in services.items():
                        if not status:
                            logger.warning(f"❌ Service down: {service}")
                    
                    # Trigger restart if background worker is down
                    if not services.get('background_worker', True):
                        logger.info("🔄 Triggering background worker restart...")
                        restart_response = requests.post(f"{deployment_url}/api/restart-background-worker", timeout=30)
                        if restart_response.status_code == 200:
                            logger.info("✅ Background worker restart triggered")
                        else:
                            logger.error(f"❌ Failed to restart background worker: {restart_response.status_code}")
                    
                    # Wait before next attempt
                    time.sleep(30)
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Health check timeout on attempt {attempt + 1}")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection error on attempt {attempt + 1}")
        except Exception as e:
            logger.error(f"❌ Health check error on attempt {attempt + 1}: {e}")
        
        # Wait before next attempt
        if attempt < 4:  # Don't wait after the last attempt
            time.sleep(30)
    
    logger.error("❌ Bot health check failed after deployment")
    
    # Send notification to admin
    try:
        notification_data = {
            'message': f'Bot health check failed after deployment at {datetime.now().isoformat()}',
            'deployment_url': deployment_url,
            'severity': 'high'
        }
        
        # Try to send notification to admin endpoint
        requests.post(f"{deployment_url}/api/admin/notify", 
                     json=notification_data, 
                     timeout=10)
        logger.info("📧 Admin notification sent")
    except Exception as e:
        logger.error(f"❌ Failed to send admin notification: {e}")
    
    return False

def check_bot_status():
    """Simple bot status check"""
    deployment_url = os.getenv('DEPLOYMENT_URL', 'https://your-app.railway.app')
    
    try:
        response = requests.get(f"{deployment_url}/api/health/alert-service", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"📊 Bot status: {data.get('service_status', 'unknown')}")
            return data.get('service_status') == 'healthy'
        else:
            logger.error(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        # Just check status
        success = check_bot_status()
        sys.exit(0 if success else 1)
    else:
        # Full deployment health check
        success = ensure_bot_health_after_deployment()
        sys.exit(0 if success else 1)
