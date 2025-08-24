#!/usr/bin/env python3
"""
FXSentinel Test Coupon Generator
Creates 2 test coupon codes for system verification
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.coupon_service import CouponService

def create_test_coupons():
    """Create 2 test coupon codes"""
    print("🧪 FXSentinel Test Coupon Generator")
    print("=" * 50)
    
    # Initialize coupon service
    coupon_service = CouponService()
    
    # Test coupon codes
    test_codes = [
        ("TEST30A", "Test Coupon A - 30% off"),
        ("TEST30B", "Test Coupon B - 30% off")
    ]
    
    created_coupons = []
    
    for code, description in test_codes:
        print(f"Creating test coupon: {code}")
        
        try:
            coupon = coupon_service.create_discount_coupon(
                code, 
                30,  # 30% off
                description, 
                5    # Allow 5 uses for testing
            )
            
            if coupon:
                created_coupons.append({
                    'code': code,
                    'description': description,
                    'discount': '30% off',
                    'uses': '5 uses for testing'
                })
                print(f"   ✅ Created successfully")
            else:
                print(f"   ❌ Failed to create")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 50)
    print("🧪 TEST COUPON CODES READY")
    print("=" * 50)
    print()
    print("Here are your 2 test coupon codes:")
    print()
    
    for i, coupon in enumerate(created_coupons, 1):
        print(f"{i}. {coupon['code']} - {coupon['discount']} ({coupon['uses']})")
    
    print()
    print("🧪 How to test:")
    print("1. Start your backend server: cd backend && python3 app.py")
    print("2. Start your frontend: npm run dev")
    print("3. Go to the trial welcome page")
    print("4. Enter one of the test codes in the coupon field")
    print("5. Verify the validation works (should show green checkmark)")
    print("6. Proceed to checkout to see the discount applied")
    print()
    print("💡 Test both codes to ensure the system works correctly!")
    
    return created_coupons

if __name__ == "__main__":
    load_dotenv()
    create_test_coupons()
