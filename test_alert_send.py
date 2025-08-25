#!/usr/bin/env python3
"""
Test Alert Sender
Send a mock alert to test the alert system
"""

import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.append('backend')

async def test_alert_send():
    """Test sending a mock alert"""
    try:
        from services.alert_service import get_alert_service
        
        # Get the alert service
        alert_service = get_alert_service()
        
        # Create a mock alert
        mock_alert = {
            'title': '🚨 TEST ALERT: FXSentinel Alert System Working',
            'content': f'This is a test alert sent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. Your alert system is working correctly!',
            'type': 'liveNews',
            'impact_level': 'high',
            'source': 'FXSentinel Test'
        }
        
        # Test user settings (you can replace with your actual user ID)
        test_user_settings = {
            'telegram_enabled': True,
            'alert_types': ['liveNews', 'economicCalendar'],
            'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
            'impact_levels': ['high', 'medium'],
            'notification_frequency': 'immediate'
        }
        
        # Test user ID (replace with your actual user ID)
        test_user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"  # This looks like your user ID from earlier logs
        
        print("🚀 Testing Alert System...")
        print(f"📱 Sending test alert to user: {test_user_id}")
        print(f"📨 Alert content: {mock_alert['title']}")
        
        # Send the alert
        success = await alert_service.process_alert(
            mock_alert, 
            test_user_settings, 
            test_user_id
        )
        
        if success:
            print("✅ Test alert sent successfully!")
            print("📱 Check your Telegram for the test message")
        else:
            print("❌ Failed to send test alert")
            
        return success
        
    except Exception as e:
        print(f"🚨 Error sending test alert: {e}")
        return False

def main():
    """Main function"""
    print("🧪 FXSentinel Alert System Test")
    print("=" * 50)
    
    # Run the test
    success = asyncio.run(test_alert_send())
    
    if success:
        print("\n🎉 Alert system is working!")
        print("📱 You should receive a test message on Telegram")
    else:
        print("\n❌ Alert system needs attention")
        print("🔧 Check the logs for more details")

if __name__ == "__main__":
    main()
