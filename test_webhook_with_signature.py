#!/usr/bin/env python3
"""
Test script to simulate a real Stripe webhook with signature verification
"""
import requests
import json
import os
import hmac
import hashlib
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5001"
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

def create_stripe_signature(payload, secret, timestamp=None):
    """Create a Stripe-like signature for testing"""
    if timestamp is None:
        timestamp = int(time.time())
    
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"t={timestamp},v1={signature}"

def test_webhook_with_signature():
    """Test webhook with proper Stripe signature"""
    print("🧪 Testing Webhook with Stripe Signature")
    print("=" * 50)
    
    if not WEBHOOK_SECRET:
        print("❌ STRIPE_WEBHOOK_SECRET not found in environment")
        return False
    
    # Sample webhook payload (subscription created event)
    webhook_payload = {
        "id": "evt_test_webhook",
        "object": "event",
        "api_version": "2020-08-27",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": "sub_test_123",
                "object": "subscription",
                "customer": "cus_test_123",
                "status": "active",
                "current_period_end": int(time.time()) + 86400 * 30,  # 30 days from now
                "metadata": {
                    "firebase_user_id": "test_user_123"
                }
            }
        },
        "livemode": False,
        "pending_webhooks": 1,
        "request": {
            "id": "req_test_123",
            "idempotency_key": None
        },
        "type": "customer.subscription.created"
    }
    
    payload_bytes = json.dumps(webhook_payload).encode('utf-8')
    signature = create_stripe_signature(payload_bytes, WEBHOOK_SECRET)
    
    print(f"📡 Sending webhook event: {webhook_payload['type']}")
    print(f"🔑 Signature: {signature[:50]}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/stripe-webhook",
            data=payload_bytes,
            headers={
                'Content-Type': 'application/json',
                'Stripe-Signature': signature
            }
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook processed successfully!")
            return True
        else:
            print("❌ Webhook processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_signature():
    """Test webhook with invalid signature"""
    print("\n🧪 Testing Webhook with Invalid Signature")
    print("=" * 50)
    
    webhook_payload = {"test": "invalid_signature"}
    payload_bytes = json.dumps(webhook_payload).encode('utf-8')
    
    # Invalid signature
    invalid_signature = "t=1234567890,v1=invalid_signature"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/stripe-webhook",
            data=payload_bytes,
            headers={
                'Content-Type': 'application/json',
                'Stripe-Signature': invalid_signature
            }
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected invalid signature!")
            return True
        else:
            print("❌ Should have rejected invalid signature")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Comprehensive Webhook Testing")
    print("=" * 50)
    
    # Test with valid signature
    valid_test = test_webhook_with_signature()
    
    # Test with invalid signature
    invalid_test = test_invalid_signature()
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"Valid Signature Test: {'✅ PASS' if valid_test else '❌ FAIL'}")
    print(f"Invalid Signature Test: {'✅ PASS' if invalid_test else '❌ FAIL'}")
    
    if valid_test and invalid_test:
        print("\n🎉 All webhook tests passed!")
        print("Your webhook endpoint is ready for production!")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
