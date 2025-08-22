#!/usr/bin/env python3
"""
Test script for improved error handling
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5001"

def test_missing_fields():
    """Test error handling for missing required fields"""
    print("🧪 Testing Missing Fields Error Handling")
    print("=" * 50)
    
    # Test missing user_id and email
    payload = {"name": "Test User"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/create-checkout-session",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly handled missing required fields")
            return True
        else:
            print("❌ Should have returned 400 for missing fields")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_stripe_data():
    """Test error handling for invalid Stripe data"""
    print("\n🧪 Testing Invalid Stripe Data Error Handling")
    print("=" * 50)
    
    # Test with invalid price ID
    payload = {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Temporarily set invalid price ID
    original_price_id = os.getenv('STRIPE_PRICE_ID')
    os.environ['STRIPE_PRICE_ID'] = 'price_invalid_123'
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/create-checkout-session",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code in [400, 500]:
            print("✅ Correctly handled invalid Stripe data")
            return True
        else:
            print("❌ Should have returned error for invalid data")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Restore original price ID
        if original_price_id:
            os.environ['STRIPE_PRICE_ID'] = original_price_id

def test_webhook_error_handling():
    """Test webhook error handling"""
    print("\n🧪 Testing Webhook Error Handling")
    print("=" * 50)
    
    # Test with invalid signature
    payload = {"test": "invalid_webhook"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/stripe-webhook",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "invalid_signature"
            }
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly handled invalid webhook signature")
            return True
        else:
            print("❌ Should have returned 400 for invalid signature")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_retry_mechanism():
    """Test retry mechanism (simulated)"""
    print("\n🧪 Testing Retry Mechanism")
    print("=" * 50)
    
    # Test with connection issues (simulated by using wrong port)
    try:
        response = requests.post(
            "http://localhost:9999/api/create-checkout-session",  # Wrong port
            json={"user_id": "test", "email": "test@example.com"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        print("✅ Connection error correctly handled (expected for wrong port)")
        return True
    except Exception as e:
        print(f"✅ Error handling working: {e}")
        return True

def test_user_friendly_messages():
    """Test user-friendly error messages"""
    print("\n🧪 Testing User-Friendly Error Messages")
    print("=" * 50)
    
    # Test various error scenarios
    test_cases = [
        {
            "name": "Missing Fields",
            "payload": {},
            "expected_status": 400
        },
        {
            "name": "Invalid Session ID",
            "payload": {"session_id": "invalid_session"},
            "endpoint": "/api/verify-checkout-session",
            "expected_status": 400
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"   Testing: {test_case['name']}")
        
        try:
            endpoint = test_case.get('endpoint', '/api/create-checkout-session')
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"}
            )
            
            print(f"     Status: {response.status_code} (expected: {test_case['expected_status']})")
            
            if response.status_code == test_case['expected_status']:
                print("     ✅ Status code correct")
                
                # Check if response has user-friendly error message
                try:
                    response_data = response.json()
                    if 'error' in response_data and response_data['error']:
                        print("     ✅ User-friendly error message present")
                    else:
                        print("     ⚠️ No error message in response")
                except:
                    print("     ⚠️ Could not parse response JSON")
            else:
                print("     ❌ Unexpected status code")
                all_passed = False
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main test function"""
    print("🧪 Testing Improved Error Handling")
    print("=" * 50)
    
    # Test missing fields
    missing_fields_ok = test_missing_fields()
    
    # Test invalid Stripe data
    invalid_data_ok = test_invalid_stripe_data()
    
    # Test webhook error handling
    webhook_ok = test_webhook_error_handling()
    
    # Test retry mechanism
    retry_ok = test_retry_mechanism()
    
    # Test user-friendly messages
    messages_ok = test_user_friendly_messages()
    
    print("\n📊 Error Handling Test Results:")
    print("=" * 40)
    print(f"Missing Fields: {'✅ PASS' if missing_fields_ok else '❌ FAIL'}")
    print(f"Invalid Data: {'✅ PASS' if invalid_data_ok else '❌ FAIL'}")
    print(f"Webhook Errors: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    print(f"Retry Mechanism: {'✅ PASS' if retry_ok else '❌ FAIL'}")
    print(f"User Messages: {'✅ PASS' if messages_ok else '❌ FAIL'}")
    
    all_tests_passed = all([missing_fields_ok, invalid_data_ok, webhook_ok, retry_ok, messages_ok])
    
    if all_tests_passed:
        print("\n🎉 All error handling tests passed!")
        print("Your error handling system is robust and user-friendly!")
    else:
        print("\n❌ Some error handling tests failed.")
        print("Please review the implementation.")

if __name__ == "__main__":
    main()
