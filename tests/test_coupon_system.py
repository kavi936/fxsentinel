#!/usr/bin/env python3
"""
Test script for FXSentinel Coupon System
Tests coupon creation, validation, and checkout integration
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.coupon_service import CouponService

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:5000"

def test_coupon_creation():
    """Test creating a 30% discount coupon"""
    print("🧪 Testing Coupon Creation")
    print("=" * 50)
    
    coupon_service = CouponService()
    
    # Test coupon details
    coupon_code = "TEST30"
    percent_off = 30
    description = "Test 30% Discount"
    max_uses = 10
    
    print(f"Creating coupon: {coupon_code}")
    print(f"Discount: {percent_off}% off")
    print(f"Description: {description}")
    print(f"Max uses: {max_uses}")
    
    try:
        # Create the coupon
        coupon = coupon_service.create_discount_coupon(
            coupon_code, 
            percent_off, 
            description, 
            max_uses
        )
        
        if coupon:
            print("✅ Coupon created successfully!")
            print(f"   Coupon ID: {coupon.id}")
            print(f"   Percent off: {coupon.percent_off}%")
            print(f"   Max redemptions: {coupon.max_redemptions}")
            return True
        else:
            print("❌ Failed to create coupon")
            return False
            
    except Exception as e:
        print(f"❌ Error creating coupon: {e}")
        return False

def test_coupon_validation():
    """Test coupon validation via API"""
    print("\n🧪 Testing Coupon Validation API")
    print("=" * 50)
    
    # Test valid coupon
    valid_coupon = "TEST30"
    print(f"Testing valid coupon: {valid_coupon}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/validate-coupon",
            json={"coupon_code": valid_coupon},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print("✅ Valid coupon validation successful!")
                print(f"   Discount: {data['coupon']['percent_off']}%")
                print(f"   Description: {data['coupon']['description']}")
            else:
                print("❌ Coupon validation failed")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    
    # Test invalid coupon
    invalid_coupon = "INVALID123"
    print(f"\nTesting invalid coupon: {invalid_coupon}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/validate-coupon",
            json={"coupon_code": invalid_coupon},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            data = response.json()
            print("✅ Invalid coupon correctly rejected!")
            print(f"   Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Expected 400 error, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    
    return True

def test_checkout_with_coupon():
    """Test checkout session creation with coupon"""
    print("\n🧪 Testing Checkout with Coupon")
    print("=" * 50)
    
    # Test data
    test_data = {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "coupon_code": "TEST30"
    }
    
    print(f"Creating checkout session with coupon: {test_data['coupon_code']}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/create-checkout-session",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('session_url'):
                print("✅ Checkout session created successfully!")
                print(f"   Session URL: {data['session_url'][:50]}...")
                return True
            else:
                print("❌ No session URL in response")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False

def test_coupon_analytics():
    """Test coupon analytics and listing"""
    print("\n🧪 Testing Coupon Analytics")
    print("=" * 50)
    
    coupon_service = CouponService()
    
    try:
        # List all coupons
        coupons = coupon_service.list_all_coupons()
        
        if coupons:
            print("✅ Found active coupons:")
            for coupon in coupons:
                print(f"   Code: {coupon['id']}")
                print(f"   Description: {coupon['description']}")
                print(f"   Discount: {coupon['percent_off']}% off")
                print(f"   Uses: {coupon['times_redeemed']}/{coupon['max_redemptions']}")
                print(f"   Type: {coupon['type']}")
                print()
        else:
            print("ℹ️  No active coupons found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error listing coupons: {e}")
        return False

def main():
    """Run all tests"""
    print("🎫 FXSentinel Coupon System Test Suite")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("⚠️  Backend server might not be running")
            print("   Start it with: cd backend && python3 app.py")
            print()
    except requests.exceptions.RequestException:
        print("⚠️  Backend server is not running")
        print("   Start it with: cd backend && python3 app.py")
        print()
    
    # Run tests
    tests = [
        ("Coupon Creation", test_coupon_creation),
        ("Coupon Validation", test_coupon_validation),
        ("Checkout with Coupon", test_checkout_with_coupon),
        ("Coupon Analytics", test_coupon_analytics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Coupon system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
