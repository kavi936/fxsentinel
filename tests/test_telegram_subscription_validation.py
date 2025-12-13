#!/usr/bin/env python3
"""
Test Telegram Bot Subscription Validation
Tests that users with invalid subscriptions cannot access the bot
"""

import requests
import json
import sys
import os

# Add backend to path
sys.path.append('backend')

def test_telegram_bot_subscription_validation():
    """Test that subscription validation works for Telegram bot access"""
    
    print("🧪 Testing Telegram Bot Subscription Validation")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid Trial User',
            'user_id': 'test_trial_user_123',
            'expected_access': True,
            'description': 'User with trial subscription should have access'
        },
        {
            'name': 'Valid Active User',
            'user_id': 'test_active_user_456',
            'expected_access': True,
            'description': 'User with active subscription should have access'
        },
        {
            'name': 'Valid Developer User',
            'user_id': 'test_developer_user_789',
            'expected_access': True,
            'description': 'Developer user should have access'
        },
        {
            'name': 'Expired Trial User',
            'user_id': 'test_expired_user_101',
            'expected_access': False,
            'description': 'User with expired trial should be denied access'
        },
        {
            'name': 'Cancelled Subscription User',
            'user_id': 'test_cancelled_user_202',
            'expected_access': False,
            'description': 'User with cancelled subscription should be denied access'
        },
        {
            'name': 'No Subscription User',
            'user_id': 'test_no_subscription_303',
            'expected_access': False,
            'description': 'User with no subscription should be denied access'
        }
    ]
    
    base_url = "http://localhost:5001"
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   User ID: {test_case['user_id']}")
        
        try:
            # Test Telegram setup endpoint
            setup_response = requests.post(
                f"{base_url}/api/telegram/setup",
                json={'userId': test_case['user_id']},
                timeout=10
            )
            
            setup_data = setup_response.json()
            
            # Check if access was granted or denied as expected
            if test_case['expected_access']:
                if setup_response.status_code == 200 and setup_data.get('success'):
                    print("   ✅ PASS: Access granted as expected")
                    results.append({
                        'test': test_case['name'],
                        'status': 'PASS',
                        'message': 'Access granted as expected'
                    })
                else:
                    print(f"   ❌ FAIL: Expected access but got denied")
                    print(f"      Status: {setup_response.status_code}")
                    print(f"      Response: {setup_data}")
                    results.append({
                        'test': test_case['name'],
                        'status': 'FAIL',
                        'message': f'Expected access but got denied. Status: {setup_response.status_code}'
                    })
            else:
                if setup_response.status_code == 403 and setup_data.get('subscription_required'):
                    print("   ✅ PASS: Access denied as expected (subscription required)")
                    results.append({
                        'test': test_case['name'],
                        'status': 'PASS',
                        'message': 'Access denied as expected (subscription required)'
                    })
                else:
                    print(f"   ❌ FAIL: Expected denial but got access")
                    print(f"      Status: {setup_response.status_code}")
                    print(f"      Response: {setup_data}")
                    results.append({
                        'test': test_case['name'],
                        'status': 'FAIL',
                        'message': f'Expected denial but got access. Status: {setup_response.status_code}'
                    })
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERROR: Request failed - {e}")
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'message': f'Request failed: {e}'
            })
        except Exception as e:
            print(f"   ❌ ERROR: Unexpected error - {e}")
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'message': f'Unexpected error: {e}'
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Errors: {errors}")
    print(f"📈 Total: {len(results)}")
    
    if failed > 0 or errors > 0:
        print("\n❌ Failed Tests:")
        for result in results:
            if result['status'] in ['FAIL', 'ERROR']:
                print(f"   • {result['test']}: {result['message']}")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Subscription validation is working correctly.")
    else:
        print(f"\n⚠️  {failed + errors} test(s) failed. Please check the implementation.")
    
    return passed == len(results)

def test_backend_subscription_check():
    """Test the backend subscription check function directly"""
    
    print("\n🔧 Testing Backend Subscription Check Function")
    print("=" * 50)
    
    try:
        # Import the function
        from backend.app import _check_subscription_status
        
        # Test cases
        test_users = [
            ('test_trial_user_123', True),
            ('test_active_user_456', True),
            ('test_developer_user_789', True),
            ('test_expired_user_101', False),
            ('test_cancelled_user_202', False),
            ('test_no_subscription_303', False)
        ]
        
        for user_id, expected in test_users:
            result = _check_subscription_status(user_id)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"   {user_id}: {result} (expected {expected}) - {status}")
            
    except Exception as e:
        print(f"   ❌ ERROR: Could not test backend function - {e}")

if __name__ == "__main__":
    print("🚀 Starting Telegram Bot Subscription Validation Tests")
    print("Make sure the backend server is running on port 5001")
    print()
    
    # Test API endpoints
    success = test_telegram_bot_subscription_validation()
    
    # Test backend function
    test_backend_subscription_check()
    
    print("\n🏁 Test completed!")
    
    if not success:
        sys.exit(1)
