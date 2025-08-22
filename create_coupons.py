#!/usr/bin/env python3
"""
FXSentinel Coupon Generator
Generate coupons for influencers, friends, and promotional campaigns
"""

import os
import sys
from backend.services.coupon_service import CouponService, create_influencer_coupons, create_discount_coupons

def main():
    print("🎫 FXSentinel Coupon Generator")
    print("=" * 40)
    
    coupon_service = CouponService()
    
    while True:
        print("\n📋 Options:")
        print("1. Create influencer coupons (100% off)")
        print("2. Create discount coupons (25-50% off)")
        print("3. Create custom coupon")
        print("4. List all active coupons")
        print("5. Get coupon analytics")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            print("\n🎯 Creating influencer coupons...")
            coupons = create_influencer_coupons()
            
            print("\n✅ Created coupons:")
            for coupon in coupons:
                print(f"   Code: {coupon['code']}")
                print(f"   Description: {coupon['description']}")
                print(f"   Max Uses: {coupon['max_uses']}")
                print(f"   Type: {coupon['type']}")
                print()
                
        elif choice == "2":
            print("\n🎯 Creating discount coupons...")
            coupons = create_discount_coupons()
            
            print("\n✅ Created discount coupons:")
            for coupon in coupons:
                print(f"   Code: {coupon['code']}")
                print(f"   Description: {coupon['description']}")
                print(f"   Discount: {coupon['discount']}")
                print()
                
        elif choice == "3":
            print("\n🎯 Create custom coupon")
            code = input("Coupon code (e.g., FRIEND100): ").strip().upper()
            description = input("Description: ").strip()
            coupon_type = input("Type (free_trial/discount): ").strip()
            max_uses = int(input("Max uses: ").strip())
            
            if coupon_type == "free_trial":
                coupon = coupon_service.create_free_trial_coupon(code, description, max_uses)
            elif coupon_type == "discount":
                percent_off = int(input("Discount percentage: ").strip())
                coupon = coupon_service.create_discount_coupon(code, percent_off, description, max_uses)
            else:
                print("❌ Invalid coupon type")
                continue
                
            if coupon:
                print(f"✅ Created custom coupon: {code}")
            else:
                print("❌ Failed to create coupon")
                
        elif choice == "4":
            print("\n📊 Active coupons:")
            coupons = coupon_service.list_all_coupons()
            
            if not coupons:
                print("   No active coupons found")
            else:
                for coupon in coupons:
                    print(f"   Code: {coupon['id']}")
                    print(f"   Name: {coupon['name']}")
                    print(f"   Discount: {coupon['percent_off']}% off")
                    print(f"   Used: {coupon['times_redeemed']}/{coupon['max_redemptions']}")
                    print(f"   Type: {coupon['type']}")
                    print()
                    
        elif choice == "5":
            print("\n📊 Coupon Analytics")
            code = input("Enter coupon code: ").strip().upper()
            analytics = coupon_service.get_coupon_analytics(code)
            
            if analytics:
                print(f"\n📈 Analytics for {code}:")
                print(f"   Total uses: {analytics['total_uses']}")
                print(f"   Usage data:")
                for usage in analytics['usage_data'][:5]:  # Show first 5
                    print(f"     - {usage['user_email']} at {usage['used_at']}")
                if len(analytics['usage_data']) > 5:
                    print(f"     ... and {len(analytics['usage_data']) - 5} more")
            else:
                print("❌ No analytics found for this coupon")
                
        elif choice == "6":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option")

def quick_setup():
    """Quick setup for common influencer coupons"""
    print("🚀 Quick Setup - Creating Common Coupons")
    print("=" * 50)
    
    coupon_service = CouponService()
    
    # Common influencer coupons
    common_coupons = [
        ('INFLUENCER100', 'Influencer Free Trial', 50),
        ('FRIEND100', 'Friend Free Trial', 25),
        ('REVIEWER100', 'Reviewer Free Trial', 10),
        ('BETA100', 'Beta Tester Free Trial', 100),
        ('LAUNCH50', 'Launch 50% Off', 100),
        ('WELCOME25', 'Welcome 25% Off', 200)
    ]
    
    created = []
    for code, description, max_uses in common_coupons:
        if code.endswith('100'):
            coupon = coupon_service.create_free_trial_coupon(code, description, max_uses)
        else:
            percent_off = int(code.split('50')[0].split('25')[0].split('LAUNCH')[1] or '25')
            coupon = coupon_service.create_discount_coupon(code, percent_off, description, max_uses)
            
        if coupon:
            created.append({
                'code': code,
                'description': description,
                'max_uses': max_uses
            })
    
    print(f"\n✅ Created {len(created)} coupons:")
    for coupon in created:
        print(f"   {coupon['code']} - {coupon['description']} (max: {coupon['max_uses']})")
    
    print("\n📋 Share these codes with your influencers and friends!")
    print("   They can use them during checkout for free/discounted access.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_setup()
    else:
        main()
