import stripe
import os
from datetime import datetime, timedelta
from firebase_admin import firestore
from dotenv import load_dotenv

load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class CouponService:
    def __init__(self):
        try:
            self.db = firestore.client()
            self.firebase_available = True
        except Exception as e:
            print(f"⚠️ Firebase not available for Coupon service: {e}")
            self.db = None
            self.firebase_available = False

    def create_free_trial_coupon(self, coupon_code, description="Free trial coupon", max_redemptions=100):
        """Create a Stripe coupon for free trial access"""
        try:
            coupon = stripe.Coupon.create(
                id=coupon_code,
                name=description,
                percent_off=100,  # 100% off
                duration='once',
                max_redemptions=max_redemptions,
                metadata={
                    'type': 'free_trial',
                    'created_by': 'admin',
                    'description': description
                }
            )
            print(f"✅ Created coupon: {coupon_code}")
            return coupon
        except Exception as e:
            print(f"❌ Error creating coupon: {e}")
            return None

    def create_discount_coupon(self, coupon_code, percent_off, description="Discount coupon", max_redemptions=100):
        """Create a Stripe coupon for percentage discount"""
        try:
            coupon = stripe.Coupon.create(
                id=coupon_code,
                name=description,
                percent_off=percent_off,
                duration='once',
                max_redemptions=max_redemptions,
                metadata={
                    'type': 'discount',
                    'percent_off': percent_off,
                    'created_by': 'admin',
                    'description': description
                }
            )
            print(f"✅ Created discount coupon: {coupon_code} ({percent_off}% off)")
            return coupon
        except Exception as e:
            print(f"❌ Error creating discount coupon: {e}")
            return None

    def validate_coupon(self, coupon_code):
        """Validate if a coupon exists and is still valid"""
        try:
            coupon = stripe.Coupon.retrieve(coupon_code)
            
            # Check if coupon is valid
            if coupon.valid:
                return {
                    'valid': True,
                    'coupon': coupon,
                    'type': coupon.metadata.get('type', 'unknown'),
                    'percent_off': coupon.percent_off,
                    'max_redemptions': coupon.max_redemptions,
                    'times_redeemed': coupon.times_redeemed
                }
            else:
                return {'valid': False, 'reason': 'Coupon is invalid'}
                
        except stripe.error.InvalidRequestError:
            return {'valid': False, 'reason': 'Coupon not found'}
        except Exception as e:
            print(f"❌ Error validating coupon: {e}")
            return {'valid': False, 'reason': 'Validation error'}

    def track_coupon_usage(self, coupon_code, user_id, user_email):
        """Track coupon usage in Firebase"""
        if not self.firebase_available or not self.db:
            return False
            
        try:
            # Store coupon usage
            self.db.collection('coupon_usage').add({
                'coupon_code': coupon_code,
                'user_id': user_id,
                'user_email': user_email,
                'used_at': datetime.now(),
                'ip_address': 'tracked_separately'  # You can add IP tracking if needed
            })
            
            # Update user's coupon usage
            self.db.collection('users').document(user_id).update({
                'coupon_used': coupon_code,
                'coupon_used_at': datetime.now()
            })
            
            print(f"✅ Tracked coupon usage: {coupon_code} by {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error tracking coupon usage: {e}")
            return False

    def get_coupon_analytics(self, coupon_code):
        """Get analytics for a specific coupon"""
        if not self.firebase_available or not self.db:
            return None
            
        try:
            # Get usage data from Firebase
            usage_ref = self.db.collection('coupon_usage').where('coupon_code', '==', coupon_code)
            usage_docs = usage_ref.get()
            
            usage_data = []
            for doc in usage_docs:
                data = doc.to_dict()
                usage_data.append({
                    'user_email': data.get('user_email'),
                    'used_at': data.get('used_at'),
                    'user_id': data.get('user_id')
                })
            
            return {
                'coupon_code': coupon_code,
                'total_uses': len(usage_data),
                'usage_data': usage_data
            }
            
        except Exception as e:
            print(f"❌ Error getting coupon analytics: {e}")
            return None

    def list_all_coupons(self):
        """List all active coupons"""
        try:
            coupons = stripe.Coupon.list(limit=100)
            active_coupons = []
            
            for coupon in coupons.data:
                if coupon.valid:
                    active_coupons.append({
                        'id': coupon.id,
                        'name': coupon.name,
                        'percent_off': coupon.percent_off,
                        'times_redeemed': coupon.times_redeemed,
                        'max_redemptions': coupon.max_redemptions,
                        'type': coupon.metadata.get('type', 'unknown'),
                        'description': coupon.metadata.get('description', '')
                    })
            
            return active_coupons
            
        except Exception as e:
            print(f"❌ Error listing coupons: {e}")
            return []

# Example usage functions
def create_influencer_coupons():
    """Create coupons for influencers and friends"""
    coupon_service = CouponService()
    
    # Free trial coupons for influencers
    influencer_coupons = [
        ('INFLUENCER100', 'Influencer Free Trial', 50),
        ('FRIEND100', 'Friend Free Trial', 25),
        ('REVIEWER100', 'Reviewer Free Trial', 10),
        ('BETA100', 'Beta Tester Free Trial', 100)
    ]
    
    created_coupons = []
    for code, description, max_uses in influencer_coupons:
        coupon = coupon_service.create_free_trial_coupon(code, description, max_uses)
        if coupon:
            created_coupons.append({
                'code': code,
                'description': description,
                'max_uses': max_uses,
                'type': '100% off (free trial)'
            })
    
    return created_coupons

def create_discount_coupons():
    """Create discount coupons for promotions"""
    coupon_service = CouponService()
    
    # Discount coupons
    discount_coupons = [
        ('WELCOME50', 50, 'Welcome 50% Off'),
        ('LAUNCH25', 25, 'Launch 25% Off'),
        ('EARLY20', 20, 'Early Adopter 20% Off')
    ]
    
    created_coupons = []
    for code, percent_off, description in discount_coupons:
        coupon = coupon_service.create_discount_coupon(code, percent_off, description)
        if coupon:
            created_coupons.append({
                'code': code,
                'description': description,
                'discount': f'{percent_off}% off',
                'type': 'discount'
            })
    
    return created_coupons
