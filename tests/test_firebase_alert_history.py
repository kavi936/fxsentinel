#!/usr/bin/env python3
"""
Test Firebase Alert History Functionality
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.append('backend')

def test_firebase_alert_history():
    """Test Firebase alert history storage and retrieval"""
    
    print("🧪 Testing Firebase Alert History")
    print("=" * 50)
    
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase_storage = FirebaseRealtimeStorage()
        
        # Test user ID
        user_id = "demo_user@example.com"
        
        print(f"1. Testing alert history storage...")
        
        # Create test alert data
        test_alert = {
            'alert_type': 'test',
            'title': 'Test Alert',
            'content': 'This is a test alert for debugging',
            'timestamp': datetime.now().isoformat(),
            'sent_via': ['telegram'],
            'status': 'sent'
        }
        
        # Save to history
        success = firebase_storage.log_alert_history(user_id, test_alert)
        print(f"   Save result: {'✅ Success' if success else '❌ Failed'}")
        
        print(f"\n2. Testing alert history retrieval...")
        
        # Get history
        history = firebase_storage.get_user_alert_history(user_id, limit=10)
        print(f"   Retrieved {len(history)} alerts")
        
        if history:
            print("   Recent alerts:")
            for i, alert in enumerate(history[:3]):
                print(f"   {i+1}. {alert.get('title', 'No title')} - {alert.get('alert_type', 'Unknown type')}")
        else:
            print("   No alerts found in history")
        
        print(f"\n3. Testing raw Firebase data...")
        
        # Get raw data from Firebase
        import hashlib
        safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
        path = f"alerts/users/{safe_user_id}/history"
        
        raw_data = firebase_storage._make_request('GET', path)
        print(f"   Raw Firebase data: {raw_data}")
        
        if raw_data:
            print(f"   Data type: {type(raw_data)}")
            if isinstance(raw_data, dict):
                print(f"   Keys: {list(raw_data.keys())}")
        
        print("\n" + "=" * 50)
        print("Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_firebase_alert_history()
