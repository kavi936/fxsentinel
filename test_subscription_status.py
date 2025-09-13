#!/usr/bin/env python3
"""
Test script to check subscription status for the real user
"""

import sys
import os
sys.path.append('backend')

from backend.services.stripe_service import StripeService
from backend.services.subscription_cache import subscription_cache

def test_subscription_status():
    """Test subscription status for the real user"""
    print("🔍 Testing Subscription Status")
    print("=" * 40)
    
    # Your user ID
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    try:
        # Test Stripe service directly
        print(f"\n1️⃣ Testing Stripe Service Directly...")
        stripe_service = StripeService()
        
        # Try with email (if available)
        subscription_data = stripe_service.get_subscription_status(user_id, email="kavi.cf412@gmail.com")
        
        print(f"   📊 Subscription data: {subscription_data}")
        
        if subscription_data:
            status = subscription_data.get('status', 'unknown')
            print(f"   ✅ Status: {status}")
            
            if status in ['active', 'trial', 'developer', 'beta_tester']:
                print(f"   🎉 Subscription is valid!")
                return True
            else:
                print(f"   ❌ Subscription is invalid: {status}")
                return False
        else:
            print(f"   ❌ No subscription data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error testing subscription: {e}")
        return False

def test_subscription_cache():
    """Test subscription cache"""
    print(f"\n2️⃣ Testing Subscription Cache...")
    
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    try:
        # Test sync version
        is_valid, error = subscription_cache.get_subscription_status_sync(user_id)
        
        print(f"   📊 Cache result: is_valid={is_valid}, error={error}")
        
        if is_valid:
            print(f"   ✅ Cache shows valid subscription")
            return True
        else:
            print(f"   ❌ Cache shows invalid subscription: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing cache: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Subscription Status Test")
    print("=" * 50)
    
    # Test Stripe service
    stripe_success = test_subscription_status()
    
    # Test subscription cache
    cache_success = test_subscription_cache()
    
    print(f"\n📋 Summary:")
    print(f"   Stripe Service: {'✅' if stripe_success else '❌'}")
    print(f"   Subscription Cache: {'✅' if cache_success else '❌'}")
    
    if stripe_success and cache_success:
        print(f"\n🎉 All subscription checks passed!")
    else:
        print(f"\n🔧 Subscription issues found - this explains why alerts aren't being sent")
