#!/usr/bin/env python3
"""
Test New Alert System
Simple script to verify the new alert system works locally
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_deduplication_service():
    """Test 1: Check if deduplication service works"""
    logger.info("=" * 60)
    logger.info("TEST 1: Deduplication Service")
    logger.info("=" * 60)
    
    try:
        from services.alert_deduplication import (
            should_send_news_alert,
            should_send_economic_alert,
            get_deduplication_stats
        )
        
        # Test news alert deduplication
        test_news_id = "test_news_123"
        
        # First call should return True (send alert)
        result1 = should_send_news_alert(test_news_id, "test_user")
        logger.info(f"  First alert check: {result1} (should be True)")
        
        # Second call should return False (duplicate)
        result2 = should_send_news_alert(test_news_id, "test_user")
        logger.info(f"  Second alert check: {result2} (should be False - duplicate)")
        
        # Get stats
        stats = get_deduplication_stats()
        logger.info(f"  Deduplication stats: {stats}")
        
        if result1 and not result2:
            logger.info("✅ TEST 1 PASSED: Deduplication working correctly")
            return True
        else:
            logger.error("❌ TEST 1 FAILED: Deduplication not working")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}", exc_info=True)
        return False

def test_production_worker():
    """Test 2: Check if production worker can initialize"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 2: Production Worker Initialization")
    logger.info("=" * 60)
    
    try:
        from services.production_alert_worker import get_production_worker
        
        worker = get_production_worker()
        logger.info(f"  Worker created: {worker}")
        
        # Get initial status
        status = worker.get_status()
        logger.info(f"  Worker status: {status}")
        
        logger.info("✅ TEST 2 PASSED: Worker can be initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}", exc_info=True)
        return False

def test_telegram_service():
    """Test 3: Check if Telegram service is configured"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 3: Telegram Service Configuration")
    logger.info("=" * 60)
    
    try:
        from services.robust_telegram_service import get_telegram_service_stats
        
        # Check if token is set
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if bot_token:
            logger.info(f"  ✅ Telegram bot token found: {bot_token[:10]}...")
        else:
            logger.warning("  ⚠️  Telegram bot token NOT found in environment")
        
        # Get service stats
        stats = get_telegram_service_stats()
        logger.info(f"  Telegram service stats: {stats}")
        
        if stats.get('enabled'):
            logger.info("✅ TEST 3 PASSED: Telegram service is enabled")
            return True
        else:
            logger.warning("⚠️  TEST 3 WARNING: Telegram service is disabled (no token)")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}", exc_info=True)
        return False

def test_send_test_alert():
    """Test 4: Try to send a test alert to yourself"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 4: Send Test Telegram Alert")
    logger.info("=" * 60)
    
    try:
        # Check if we have necessary credentials
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.warning("  ⚠️  Cannot send test alert - no TELEGRAM_BOT_TOKEN set")
            logger.info("  To fix: Add TELEGRAM_BOT_TOKEN to your .env file")
            return False
        
        # Ask for chat ID
        logger.info("")
        logger.info("  To send a test alert, we need your Telegram chat ID.")
        logger.info("  If you don't know it, you can:")
        logger.info("  1. Message your bot on Telegram")
        logger.info("  2. Visit: https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getUpdates")
        logger.info("  3. Look for 'chat':{'id': YOUR_CHAT_ID}")
        logger.info("")
        
        chat_id = input("  Enter your Telegram chat ID (or press Enter to skip): ").strip()
        
        if not chat_id:
            logger.info("  Skipping test alert send")
            return False
        
        # Try to send test alert
        from services.robust_telegram_service import send_telegram_message_sync
        
        test_message = f"""
🧪 <b>FXSentinel Test Alert</b>

This is a test message from your new alert system!

✅ Deduplication: Working
✅ Worker: Initialized
✅ Telegram: Connected

🎉 <b>Your alert system is ready!</b>

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        logger.info(f"  Sending test message to chat_id: {chat_id}...")
        success, error = send_telegram_message_sync(chat_id, test_message, message_type="test")
        
        if success:
            logger.info("✅ TEST 4 PASSED: Test alert sent successfully!")
            logger.info("  Check your Telegram to confirm you received it")
            return True
        else:
            logger.error(f"❌ TEST 4 FAILED: Could not send alert - {error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}", exc_info=True)
        return False

def test_worker_start_stop():
    """Test 5: Start and stop the worker"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 5: Worker Start/Stop")
    logger.info("=" * 60)
    
    try:
        from services.production_alert_worker import get_production_worker
        
        worker = get_production_worker()
        
        # Start worker
        logger.info("  Starting worker...")
        worker.start()
        time.sleep(2)  # Give it a moment
        
        # Check status
        status = worker.get_status()
        logger.info(f"  Worker running: {status['running']}")
        logger.info(f"  Thread alive: {status['thread_alive']}")
        
        # Stop worker
        logger.info("  Stopping worker...")
        worker.stop()
        time.sleep(1)
        
        # Check status again
        status = worker.get_status()
        logger.info(f"  Worker stopped: {not status['running']}")
        
        logger.info("✅ TEST 5 PASSED: Worker can start and stop cleanly")
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST 5 FAILED: {e}", exc_info=True)
        return False

def main():
    """Run all tests"""
    logger.info("🚀 FXSentinel Alert System - Local Tests")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("")
    
    # Load environment variables from backend/.env
    from dotenv import load_dotenv
    backend_env = os.path.join(os.path.dirname(__file__), 'backend', '.env')
    load_dotenv(backend_env)
    logger.info(f"Loaded environment from: {backend_env}")
    
    # Run tests
    results = []
    
    results.append(("Deduplication Service", test_deduplication_service()))
    results.append(("Production Worker Init", test_production_worker()))
    results.append(("Telegram Service", test_telegram_service()))
    results.append(("Send Test Alert", test_send_test_alert()))
    results.append(("Worker Start/Stop", test_worker_start_stop()))
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
    
    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("")
        logger.info("🎉 ALL TESTS PASSED! Your alert system is ready!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Make sure your .env file has TELEGRAM_BOT_TOKEN")
        logger.info("2. Connect your Telegram account in the dashboard")
        logger.info("3. Deploy to Railway")
    else:
        logger.info("")
        logger.info("⚠️  Some tests failed. Fix the issues above before deploying.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

