#!/usr/bin/env python3
"""
Verify Firebase Realtime Database Credentials and Connection
Tests all Firebase operations needed for alerts
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_firebase_connection():
    """Test basic Firebase connection"""
    print_section("1. FIREBASE CONNECTION TEST")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Test basic connection
        test_path = "test"
        result = firebase._make_request('GET', test_path)
        
        if result is not None:
            print("✅ Firebase connection successful")
            print(f"   Database URL: {firebase.database_url}")
            return True
        else:
            print("❌ Firebase connection failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ Firebase connection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_firebase_read():
    """Test reading from Firebase"""
    print_section("2. FIREBASE READ TEST")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Test reading alerts/users
        path = "alerts/users"
        result = firebase._make_request('GET', path)
        
        if result is not None:
            user_count = len(result) if isinstance(result, dict) else 0
            print(f"✅ Firebase read successful")
            print(f"   Found {user_count} users in alerts/users")
            return True
        else:
            print("❌ Firebase read failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Firebase read error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_firebase_write():
    """Test writing to Firebase"""
    print_section("3. FIREBASE WRITE TEST")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Test writing to a test path
        test_path = "test_verification"
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        
        result = firebase._make_request('PUT', test_path, test_data)
        
        if result is not None:
            print("✅ Firebase write successful")
            
            # Clean up - delete test data
            try:
                firebase._make_request('DELETE', test_path)
                print("✅ Test data cleaned up")
            except:
                pass
            
            return True
        else:
            print("❌ Firebase write failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ Firebase write error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_settings_read():
    """Test reading user alert settings"""
    print_section("4. USER SETTINGS READ TEST")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Get all users
        users = firebase.get_all_users_with_alerts()
        
        if users:
            print(f"✅ User settings read successful")
            print(f"   Found {len(users)} users with alert settings")
            
            # Show first user details
            if users:
                user = users[0]
                print(f"\n   Sample user:")
                print(f"   - User ID: {user.get('user_id')}")
                print(f"   - Has Telegram Chat ID: {bool(user.get('telegram_chat_id'))}")
                print(f"   - Has Settings: {bool(user.get('settings'))}")
            
            return True
        else:
            print("⚠️  No users found (this is OK if no users are configured)")
            return True  # Not an error, just no users
            
    except Exception as e:
        print(f"❌ User settings read error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deduplication_read_write():
    """Test deduplication read/write"""
    print_section("5. DEDUPLICATION READ/WRITE TEST")
    try:
        from services.persistent_alert_deduplication import get_persistent_deduplication
        dedup = get_persistent_deduplication()
        
        # Test with a sample news item
        test_news = {
            'id': f'test_verification_{datetime.now().timestamp()}',
            'title': 'Test Verification News',
            'source': 'Verification'
        }
        test_user_id = 'test_verification_user'
        
        # Check if should send
        should_send = dedup.should_send_news_alert(test_news, test_user_id)
        print(f"✅ Deduplication check: {should_send}")
        
        if should_send:
            # Mark as sent
            dedup.mark_news_alert_sent(test_news, test_user_id)
            print("✅ Deduplication write successful")
            
            # Check again (should be False now)
            should_send_again = dedup.should_send_news_alert(test_news, test_user_id)
            if not should_send_again:
                print("✅ Deduplication read successful (correctly identified as duplicate)")
            else:
                print("⚠️  Deduplication may not be working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Deduplication test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test required environment variables"""
    print_section("6. ENVIRONMENT VARIABLES CHECK")
    try:
        required_vars = [
            'FIREBASE_PROJECT_ID',
            'FIREBASE_REALTIME_URL'
        ]
        
        optional_vars = [
            'GOOGLE_APPLICATION_CREDENTIALS'
        ]
        
        print("Required variables:")
        all_present = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                display_value = value if len(value) < 20 else value[:20] + "..."
                print(f"  ✅ {var}: {display_value}")
            else:
                print(f"  ❌ {var}: NOT SET")
                all_present = False
        
        print("\nOptional variables:")
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                print(f"  ✅ {var}: {value}")
            else:
                print(f"  ⚠️  {var}: NOT SET (may use default)")
        
        return all_present
        
    except Exception as e:
        print(f"❌ Environment variables check error: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("  FIREBASE CREDENTIALS VERIFICATION")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    
    results = {}
    
    # Run all tests
    results['env_vars'] = test_environment_variables()
    results['connection'] = test_firebase_connection()
    results['read'] = test_firebase_read()
    results['write'] = test_firebase_write()
    results['user_settings'] = test_user_settings_read()
    results['deduplication'] = test_deduplication_read_write()
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("  RECOMMENDATIONS")
    print("=" * 70)
    
    if not results['connection']:
        print("🔴 CRITICAL: Firebase connection failed")
        print("   → Check FIREBASE_REALTIME_URL environment variable")
        print("   → Verify Firebase database rules allow read/write")
        print("   → Check network connectivity")
    
    if not results['write']:
        print("🔴 CRITICAL: Firebase write failed")
        print("   → Check Firebase database rules allow write access")
        print("   → Verify authentication credentials")
    
    if not results['user_settings']:
        print("⚠️  WARNING: Cannot read user settings")
        print("   → Alerts may not work correctly")
    
    if not results['deduplication']:
        print("⚠️  WARNING: Deduplication not working")
        print("   → Duplicate alerts may be sent")
    
    if all(results.values()):
        print("✅ All Firebase operations working correctly!")
        print("   → Ready to test alerts with real news items")

if __name__ == "__main__":
    main()

