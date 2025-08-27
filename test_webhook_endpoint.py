#!/usr/bin/env python3
"""
Test script to verify the Stripe webhook endpoint is working
"""

import requests
import json
import time

def test_webhook_endpoint():
    """Test the webhook endpoint"""
    url = "https://fxsentinel.io/api/stripe-webhook"
    
    # Test 1: Basic connectivity
    print("🔍 Testing webhook endpoint connectivity...")
    try:
        response = requests.post(
            url,
            headers={
                'Content-Type': 'application/json',
                'Stripe-Signature': 'test_signature'
            },
            data=json.dumps({'test': 'data'}),
            timeout=10
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"✅ Response Headers: {dict(response.headers)}")
        print(f"✅ Response Body: {response.text[:200]}...")
        
        if response.status_code == 400:
            print("✅ Expected 400 error (invalid signature) - endpoint is working!")
            return True
        elif response.status_code == 405:
            print("❌ 405 Method Not Allowed - Vercel configuration issue")
            return False
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_health_endpoint():
    """Test if the API is accessible at all"""
    print("\n🔍 Testing API health...")
    try:
        response = requests.get("https://fxsentinel.io/api/health", timeout=10)
        print(f"✅ Health check status: {response.status_code}")
        print(f"✅ Health check response: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing FXSentinel Webhook Endpoint")
    print("=" * 50)
    
    # Test health first
    health_ok = test_health_endpoint()
    
    # Test webhook
    webhook_ok = test_webhook_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Webhook Endpoint: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    
    if webhook_ok:
        print("\n🎉 Webhook endpoint is working! Stripe should be able to send webhooks.")
        print("💡 Make sure to:")
        print("   1. Deploy the updated vercel.json configuration")
        print("   2. Update your Stripe webhook URL to: https://fxsentinel.io/api/stripe-webhook")
        print("   3. Set the STRIPE_WEBHOOK_SECRET environment variable")
    else:
        print("\n⚠️ Webhook endpoint is not working. Please:")
        print("   1. Deploy the updated vercel.json configuration")
        print("   2. Check Vercel deployment logs")
        print("   3. Verify the API routes are properly configured")

if __name__ == "__main__":
    main()
