#!/usr/bin/env python3
"""
FXSentinel Friends & Early Testers Discount Coupon Generator
Creates a 30% discount coupon for friends and early testers
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.coupon_service import CouponService

def create_friends_discount():
    """Create a 30% discount coupon for friends and early testers"""
    print("🎫 FXSentinel Friends & Early Testers Discount Generator")
    print("=" * 60)
    
    # Initialize coupon service
    coupon_service = CouponService()
    
    # Coupon details
    coupon_code = "FRIENDS30"
    percent_off = 30
    description = "Friends & Early Testers 30% Discount"
    max_uses = 100  # Adjust based on how many friends/testers you have
    
    print(f"Creating coupon: {coupon_code}")
    print(f"Discount: {percent_off}% off")
    print(f"Description: {description}")
    print(f"Max uses: {max_uses}")
    print()
    
    # Check if coupon already exists
    existing_validation = coupon_service.validate_coupon(coupon_code)
    if existing_validation['valid']:
        print(f"⚠️  Coupon {coupon_code} already exists!")
        print(f"   Current uses: {existing_validation['coupon'].times_redeemed}")
        print(f"   Max uses: {existing_validation['coupon'].max_redemptions}")
        
        response = input("\nDo you want to create a new coupon with a different code? (y/n): ").strip().lower()
        if response == 'y':
            new_code = input("Enter new coupon code (e.g., FRIENDS30B): ").strip().upper()
            if new_code:
                coupon_code = new_code
            else:
                print("❌ No coupon code provided. Exiting.")
                return
        else:
            print("✅ Using existing coupon")
            return
    
    # Create the coupon
    try:
        coupon = coupon_service.create_discount_coupon(
            coupon_code, 
            percent_off, 
            description, 
            max_uses
        )
        
        if coupon:
            print("✅ Successfully created discount coupon!")
            print(f"   Code: {coupon_code}")
            print(f"   Discount: {percent_off}% off")
            print(f"   Description: {description}")
            print(f"   Max uses: {max_uses}")
            print()
            print("📋 How to use:")
            print("1. Share this code with friends and early testers")
            print("2. They can enter it during checkout")
            print("3. The discount will be applied to their subscription")
            print()
            print("💡 Marketing tips:")
            print("- Send this code to friends and family")
            print("- Offer it to early beta testers")
            print("- Use it for influencer partnerships")
            print("- Include it in launch promotions")
        else:
            print("❌ Failed to create coupon")
            
    except Exception as e:
        print(f"❌ Error creating coupon: {e}")

def list_existing_coupons():
    """List all existing coupons"""
    print("\n📊 Existing Coupons:")
    print("-" * 40)
    
    coupon_service = CouponService()
    coupons = coupon_service.list_all_coupons()
    
    if not coupons:
        print("No active coupons found")
        return
    
    for coupon in coupons:
        print(f"Code: {coupon['id']}")
        print(f"  Description: {coupon['description']}")
        print(f"  Discount: {coupon['percent_off']}% off")
        print(f"  Uses: {coupon['times_redeemed']}/{coupon['max_redemptions']}")
        print(f"  Type: {coupon['type']}")
        print()

if __name__ == "__main__":
    load_dotenv()
    
    print("Choose an option:")
    print("1. Create Friends & Early Testers discount (30% off)")
    print("2. List existing coupons")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        create_friends_discount()
    elif choice == "2":
        list_existing_coupons()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice. Exiting.")
