#!/usr/bin/env python3
"""
Debug Firebase History Retrieval
"""

import sys
sys.path.append('backend')

def debug_firebase_history():
    """Debug Firebase history retrieval"""
    
    user_id = "demo_user@example.com"
    
    print("🔍 Debugging Firebase History Retrieval")
    print("=" * 50)
    
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase_storage = FirebaseRealtimeStorage()
        
        print(f"1. Testing with user_id: {user_id}")
        
        # Test the exact same call as the endpoint
        history = firebase_storage.get_user_alert_history(user_id, 50)
        
        print(f"2. Retrieved {len(history)} alerts")
        
        if history:
            print("3. Sample alert data:")
            for i, alert in enumerate(history[:2]):
                print(f"   Alert {i+1}:")
                print(f"     ID: {alert.get('id', 'No ID')}")
                print(f"     Title: {alert.get('title', 'No title')}")
                print(f"     Type: {alert.get('alert_type', 'No type')}")
                print(f"     Status: {alert.get('status', 'No status')}")
                print()
        else:
            print("3. No alerts found")
        
        print("✅ Firebase call completed successfully")
        
    except Exception as e:
        print(f"❌ Error in Firebase call: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Debug completed!")

if __name__ == "__main__":
    debug_firebase_history()
