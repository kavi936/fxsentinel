#!/usr/bin/env python3
"""
Test script for Firebase Realtime Database integration
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Load environment variables
load_dotenv()

async def test_firebase_realtime():
    """Test Firebase Realtime Database functionality"""
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        from services.alert_service import get_alert_service
        
        print("🔍 Testing Firebase Realtime Database...")
        
        # Initialize Firebase storage
        firebase_storage = FirebaseRealtimeStorage()
        
        # Test connection
        print("\n1. Testing connection...")
        if firebase_storage.test_connection():
            print("✅ Firebase connection successful")
        else:
            print("❌ Firebase connection failed")
            return
        
        # Test user alert settings
        print("\n2. Testing user alert settings...")
        test_user_id = "test_user_123"
        
        # Test saving settings
        test_settings = {
            'channels': {
                'telegram': {'enabled': True, 'chatId': '123456789', 'username': '@testuser'},
                'email': {'enabled': False, 'address': ''}
            },
            'preferences': {
                'impactLevels': {'high': True, 'medium': True, 'low': False},
                'alertTypes': {'preNews': True, 'postNews': True, 'liveNews': True, 'technicalAnalysis': False},
                'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
                'quietHours': {'enabled': False, 'start': '22:00', 'end': '06:00', 'timezone': 'UTC'}
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        success = firebase_storage.update_user_alert_settings(test_user_id, test_settings)
        if success:
            print("✅ User alert settings saved successfully")
        else:
            print("❌ Failed to save user alert settings")
        
        # Test retrieving settings
        retrieved_settings = firebase_storage.get_user_alert_settings(test_user_id)
        if retrieved_settings:
            print("✅ User alert settings retrieved successfully")
            print(f"   Telegram enabled: {retrieved_settings.get('channels', {}).get('telegram', {}).get('enabled', False)}")
            print(f"   Chat ID: {retrieved_settings.get('channels', {}).get('telegram', {}).get('chatId', 'Not set')}")
        else:
            print("❌ Failed to retrieve user alert settings")
        
        # Test alert service integration
        print("\n3. Testing Alert Service integration...")
        alert_service = get_alert_service()
        
        # Test getting user settings through alert service
        settings = await alert_service.get_user_alert_settings(test_user_id)
        if settings:
            print("✅ Alert service can retrieve user settings")
        else:
            print("❌ Alert service failed to retrieve user settings")
        
        # Test alert history
        print("\n4. Testing alert history...")
        test_alert = {
            'type': 'liveNews',
            'title': 'Test Alert',
            'content': 'This is a test alert',
            'priority': 'high',
            'currency_pairs': ['EUR/USD'],
            'sent_via': ['telegram'],
            'status': 'sent',
            'sent_at': datetime.now().isoformat()
        }
        
        firebase_storage.log_alert_history(test_user_id, test_alert)
        print("✅ Alert history logged successfully")
        
        # Test retrieving alert history
        history = firebase_storage.get_user_alert_history(test_user_id, limit=10)
        if history:
            print(f"✅ Retrieved {len(history)} alert history items")
        else:
            print("❌ Failed to retrieve alert history")
        
        print("\n🎉 All Firebase Realtime Database tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_firebase_realtime())
