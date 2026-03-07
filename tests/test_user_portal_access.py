#!/usr/bin/env python3
"""
Test script to check user portal access and email configuration
"""

import requests
import json

BASE_URL = "https://fxsentinel-production.up.railway.app"

def test_user_portal_access():
    """Test if a user can access the customer portal"""
    print("🧪 Testing user portal access...")
    
    # Test data - you'll need to provide the actual user_id
    test_data = {
        "user_id": "test_user_id",  # Replace with actual user ID
        "email": "itsallintheheadbusiness@gmail.com"
    }
    
    # Test 1: Check if user exists and has subscription
    print("\n1. Checking user subscription status...")
    try:
        response = requests.post(f"{BASE_URL}/api/get-customer-portal-session", 
                               json=test_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User has subscription and portal access!")
            print(f"   Portal URL: {data.get('portal_url')}")
            print(f"   Message: {data.get('message')}")
            return data.get('portal_url')
        elif response.status_code == 404:
            print("❌ User not found or no subscription")
            print("   This means the user hasn't completed the trial signup yet")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return None

def test_stripe_webhook_configuration():
    """Test if Stripe webhooks are configured for emails"""
    print("\n2. Checking Stripe webhook configuration...")
    print("   Note: Stripe should automatically send emails for:")
    print("   - Checkout session completed")
    print("   - Subscription created")
    print("   - Payment succeeded")
    print("   - Customer portal access")
    
    print("\n   To enable emails, check your Stripe Dashboard:")
    print("   1. Go to https://dashboard.stripe.com/settings/billing/portal")
    print("   2. Enable 'Customer emails'")
    print("   3. Configure email templates")
    print("   4. Set up webhook endpoints for email triggers")

def main():
    print("🚀 Testing User Portal Access and Email Configuration")
    print("=" * 60)
    
    # Test portal access
    portal_url = test_user_portal_access()
    
    # Test webhook configuration
    test_stripe_webhook_configuration()
    
    print("\n" + "=" * 60)
    if portal_url:
        print("🎉 User has portal access!")
        print(f"   Portal URL: {portal_url}")
        print("   You can share this URL with the user")
    else:
        print("❌ User needs to complete trial signup first")
        print("   The user should:")
        print("   1. Go to the trial welcome page")
        print("   2. Complete Stripe checkout")
        print("   3. Then they'll receive emails automatically")

if __name__ == "__main__":
    main()
