#!/usr/bin/env python3
"""
FXSentinel 20 Unique Coupon Generator
Creates 20 unique one-time use 30% discount coupons
"""

import os
import sys
import random
import string
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.coupon_service import CouponService

def generate_unique_code():
    """Generate a unique 8-character coupon code"""
    # Use a mix of letters and numbers
    chars = string.ascii_uppercase + string.digits
    # Avoid confusing characters (0, O, 1, I, L)
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
    
    # Generate 8-character code
    code = ''.join(random.choice(chars) for _ in range(8))
    return code

def create_20_unique_coupons():
    """Create 20 unique one-time use 30% discount coupons"""
    print("🎫 FXSentinel 20 Unique Coupon Generator")
    print("=" * 60)
    
    # Initialize coupon service
    coupon_service = CouponService()
    
    # Generate 20 unique codes
    coupon_codes = []
    for i in range(20):
        while True:
            code = generate_unique_code()
            if code not in coupon_codes:
                coupon_codes.append(code)
                break
    
    print(f"Generated {len(coupon_codes)} unique coupon codes:")
    print()
    
    created_coupons = []
    
    for i, code in enumerate(coupon_codes, 1):
        description = f"One-time 30% Discount - Coupon #{i:02d}"
        
        print(f"Creating coupon {i:2d}/20: {code}")
        
        try:
            coupon = coupon_service.create_discount_coupon(
                code, 
                30,  # 30% off
                description, 
                1    # One-time use only
            )
            
            if coupon:
                created_coupons.append({
                    'code': code,
                    'description': description,
                    'discount': '30% off',
                    'uses': '1-time use'
                })
                print(f"   ✅ Created successfully")
            else:
                print(f"   ❌ Failed to create")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("🎉 COUPON CODES READY FOR USE")
    print("=" * 60)
    print()
    print("Here are your 20 unique one-time use 30% off coupon codes:")
    print()
    
    for i, coupon in enumerate(created_coupons, 1):
        print(f"{i:2d}. {coupon['code']} - {coupon['discount']} ({coupon['uses']})")
    
    print()
    print("📋 How to use:")
    print("1. Share these codes with friends and early testers")
    print("2. Each code can only be used once")
    print("3. Users enter the code during checkout")
    print("4. 30% discount is applied automatically")
    print()
    print("💡 Marketing tips:")
    print("- Send individual codes to different people")
    print("- Track which codes get used")
    print("- Use for influencer partnerships")
    print("- Include in launch promotions")
    
    return created_coupons

if __name__ == "__main__":
    load_dotenv()
    create_20_unique_coupons()
