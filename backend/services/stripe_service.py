import stripe
import os
from datetime import datetime, timedelta, timezone
from firebase_admin import firestore
from dotenv import load_dotenv

load_dotenv()


def _date_to_firestore(d):
    """Firestore does not accept datetime.date; use start-of-day UTC as datetime."""
    if d is None:
        return None
    if hasattr(d, 'date') and callable(getattr(d, 'date', None)):
        d = d.date()
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)


def _firestore_to_date(v):
    """Normalize a Firestore timestamp/datetime to date for comparison with today."""
    if v is None:
        return None
    if hasattr(v, 'date') and callable(v.date):
        return v.date()
    return v

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripeService:
    def __init__(self):
        try:
            self.db = firestore.client()
            self.firebase_available = True
        except Exception as e:
            print(f"⚠️ Firebase not available for Stripe service: {e}")
            self.db = None
            self.firebase_available = False
            
        # Freemium model configuration
        self.free_limit = int(os.getenv('FREE_ANALYSIS_LIMIT', 15))  # Per month
        self.premium_limit = int(os.getenv('PREMIUM_ANALYSIS_LIMIT', 50))  # Per day
        self.premium_price = int(os.getenv('PREMIUM_MONTHLY_PRICE', 1499))  # $14.99 in cents
        self.product_id = os.getenv('STRIPE_PRODUCT_ID', 'prod_TG0y9LajTpBv6g')
        self.price_id = os.getenv('STRIPE_PRICE_ID', 'price_1SJUw5JNDWyJv8IpGZOmCT6j')
        
        # Developer emails for bypassing payment
        developer_emails_str = os.getenv('DEVELOPER_EMAILS', '')
        self.developer_emails = [email.strip() for email in developer_emails_str.split(',') if email.strip()]
        
        print(f"🔧 Developer emails loaded: {self.developer_emails}")
        print(f"💰 Freemium Model: Free={self.free_limit}/month, Premium={self.premium_limit}/day, Price=${self.premium_price/100}")

    def is_developer_email(self, email):
        """Check if email is in developer whitelist"""
        if not email:
            return False
        return email.lower() in [dev_email.lower() for dev_email in self.developer_emails]

    @staticmethod
    def _normalize_subscription_status(raw):
        """Map Firestore/legacy/Stripe status to one of: free, premium, past_due. Avoids 'Unknown' for existing users."""
        if raw is None:
            return 'free'
        s = (str(raw).strip().lower() if str(raw).strip() else '') or 'free'
        if s in ('premium', 'active'):
            return 'premium'
        if s == 'past_due':
            return 'past_due'
        return 'free'

    def _ensure_user_doc_exists(self, user_id, email=None, initial_monthly_count=0, initial_daily_count=0):
        """
        Create Firestore users/<user_id> doc if it does not exist (free tier).
        Fixes billing/UI not updating for new users who never went through Stripe checkout.
        """
        if not self.firebase_available or not self.db:
            return False
        try:
            user_ref = self.db.collection('users').document(user_id)
            if user_ref.get().exists:
                return True
            today = datetime.now().date()
            current_month_start = today.replace(day=1)
            user_ref.set({
                'subscription_status': 'free',
                'monthly_analysis_count': initial_monthly_count,
                'daily_analysis_count': initial_daily_count,
                'last_monthly_reset': _date_to_firestore(current_month_start),
                'last_daily_reset': _date_to_firestore(today),
                'account_created': datetime.now(timezone.utc),
                **({'user_email': email} if email else {}),
            })
            return True
        except Exception as e:
            print(f"Error ensuring user doc exists: {e}")
            return False

    def get_developer_access_status(self, email):
        """Get developer access status for an email"""
        is_developer = self.is_developer_email(email)
        if is_developer:
            return {
                'is_developer': True,
                'status': 'developer',
                'daily_usage': 0,
                'monthly_usage': 0,
                'daily_limit': 999999,  # Unlimited for developers
                'monthly_limit': 999999,
                'can_perform': True
            }
        return {'is_developer': False}

    def create_customer(self, user_id, email, name):
        """Create a Stripe customer and link to Firebase user with free tier"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'firebase_user_id': user_id}
            )
            
            # Store customer ID in Firebase if available and set to free tier
            if self.firebase_available and self.db:
                try:
                    today = datetime.now().date()
                    self.db.collection('users').document(user_id).update({
                        'stripe_customer_id': customer.id,
                        'subscription_status': 'free',  # Default to free tier
                        'monthly_analysis_count': 0,
                        'daily_analysis_count': 0,
                        'last_monthly_reset': _date_to_firestore(today.replace(day=1)),
                        'last_daily_reset': _date_to_firestore(today),
                        'account_created': datetime.now(timezone.utc)
                    })
                except Exception as firebase_error:
                    print(f"⚠️ Firebase update failed, but Stripe customer created: {firebase_error}")
            else:
                print("⚠️ Firebase not available - customer created in Stripe only")
            
            return customer
        except Exception as e:
            print(f"Error creating Stripe customer: {e}")
            raise

    def create_subscription(self, customer_id, price_id):
        """Create a premium subscription for a customer"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
            )
            return subscription
        except Exception as e:
            print(f"Error creating subscription: {e}")
            raise

    def setup_payment_method(self, customer_id, payment_method_id):
        """Attach payment method to customer for future use"""
        try:
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id,
                },
            )
            
            return True
        except Exception as e:
            print(f"Error setting up payment method: {e}")
            raise

    def get_subscription_status(self, user_id, email=None):
        """Get current subscription status for a user"""
        try:
            # Check if user is a developer first
            if email and self.is_developer_email(email):
                return {
                    'status': 'developer',
                    'monthly_analysis_count': 0,
                    'daily_analysis_count': 0,
                    'monthly_limit': 999999,
                    'daily_limit': 999999,
                    'stripe_customer_id': None,
                    'is_developer': True
                }
            
            if not self.firebase_available or not self.db:
                # Return default free status if Firebase not available
                return {
                    'status': 'free',
                    'monthly_analysis_count': 0,
                    'daily_analysis_count': 0,
                    'monthly_limit': self.free_limit,
                    'daily_limit': None,
                    'stripe_customer_id': None,
                    'is_developer': False
                }
            
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                # Create user doc so billing UI and increment_analysis_count work for new users
                self._ensure_user_doc_exists(user_id, email=email, initial_monthly_count=0, initial_daily_count=0)
                user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                return {
                    'status': 'free',
                    'monthly_analysis_count': 0,
                    'daily_analysis_count': 0,
                    'monthly_limit': self.free_limit,
                    'daily_limit': None,
                    'stripe_customer_id': None,
                    'is_developer': False
                }

            user_data = user_doc.to_dict()
            status = self._normalize_subscription_status(user_data.get('subscription_status'))
            return {
                'status': status,
                'monthly_analysis_count': user_data.get('monthly_analysis_count', 0),
                'daily_analysis_count': user_data.get('daily_analysis_count', 0),
                'monthly_limit': self.free_limit if status == 'free' else None,
                'daily_limit': self.premium_limit if status == 'premium' else None,
                'stripe_customer_id': user_data.get('stripe_customer_id'),
                'is_developer': False
            }
        except Exception as e:
            print(f"Error getting subscription status: {e}")
            # Always return a valid response object, never None
            # Default to free tier for new users or on errors
            return {
                'status': 'free',
                'monthly_analysis_count': 0,
                'daily_analysis_count': 0,
                'monthly_limit': self.free_limit,
                'daily_limit': None,
                'stripe_customer_id': None,
                'is_developer': False
            }

    def get_analysis_limit(self, user_data):
        """Get the analysis limit based on subscription status"""
        status = self._normalize_subscription_status(user_data.get('subscription_status'))
        if status == 'premium':
            return {'type': 'daily', 'limit': self.premium_limit}
        elif status == 'developer':
            return {'type': 'unlimited', 'limit': 999999}
        else:  # free
            return {'type': 'monthly', 'limit': self.free_limit}

    def can_perform_analysis(self, user_id, email=None):
        """Check if user can perform an AI analysis based on their tier"""
        try:
            # Check if user is a developer first
            if email and self.is_developer_email(email):
                return {
                    'can_perform': True,
                    'daily_usage': 0,
                    'monthly_usage': 0,
                    'daily_limit': 999999,
                    'monthly_limit': 999999,
                    'status': 'developer'
                }
            
            if not self.firebase_available:
                # Default to allowing analysis if Firebase is not available
                return {
                    'can_perform': True,
                    'daily_usage': 0,
                    'monthly_usage': 0,
                    'daily_limit': None,
                    'monthly_limit': self.free_limit,
                    'status': 'free'
                }
            
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                # Create user doc so new users get 0/15 and can perform first analysis
                self._ensure_user_doc_exists(user_id, email=email, initial_monthly_count=0, initial_daily_count=0)
                user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                # Return free-tier shape so UI shows 0/15 instead of "limit reached" (monthly_limit 0 was triggering that)
                return {
                    'can_perform': True,
                    'daily_usage': 0,
                    'monthly_usage': 0,
                    'daily_limit': None,
                    'monthly_limit': self.free_limit,
                    'status': 'free'
                }

            user_data = user_doc.to_dict()
            status = self._normalize_subscription_status(user_data.get('subscription_status'))
            today = datetime.now().date()
            current_month_start = today.replace(day=1)

            # Reset counters if needed (Firestore returns datetime/timestamp; normalize to date for comparison)
            last_daily_reset = _firestore_to_date(user_data.get('last_daily_reset'))
            last_monthly_reset = _firestore_to_date(user_data.get('last_monthly_reset'))

            updates = {}

            # Reset daily count if it's a new day (for premium users)
            if last_daily_reset != today:
                updates['daily_analysis_count'] = 0
                updates['last_daily_reset'] = _date_to_firestore(today)
                user_data['daily_analysis_count'] = 0

            # Reset monthly count if it's a new month (for free users)
            if last_monthly_reset != current_month_start:
                updates['monthly_analysis_count'] = 0
                updates['last_monthly_reset'] = _date_to_firestore(current_month_start)
                user_data['monthly_analysis_count'] = 0
            
            # Apply updates if any
            if updates:
                self.db.collection('users').document(user_id).update(updates)
            
            # Check limits based on subscription status
            if status == 'premium':
                # Premium users: check daily limit
                daily_count = user_data.get('daily_analysis_count', 0)
                can_perform = daily_count < self.premium_limit
                return {
                    'can_perform': can_perform,
                    'daily_usage': daily_count,
                    'monthly_usage': 0,
                    'daily_limit': self.premium_limit,
                    'monthly_limit': None,
                    'status': 'premium'
                }
            else:  # free
                # Free users: check monthly limit
                monthly_count = user_data.get('monthly_analysis_count', 0)
                can_perform = monthly_count < self.free_limit
                return {
                    'can_perform': can_perform,
                    'daily_usage': 0,
                    'monthly_usage': monthly_count,
                    'daily_limit': None,
                    'monthly_limit': self.free_limit,
                    'status': 'free'
                }
                
        except Exception as e:
            print(f"Error checking analysis permission: {e}")
            # Default to allowing analysis if there's an error
            return {
                'can_perform': True,
                'daily_usage': 0,
                'monthly_usage': 0,
                'daily_limit': None,
                'monthly_limit': self.free_limit,
                'status': 'free'
            }

    def increment_analysis_count(self, user_id, email=None):
        """Increment the analysis count for a user based on their tier. Called only when an AI analysis actually runs.
        Returns True if the count was updated, False otherwise (e.g. Firestore unavailable or database not created)."""
        try:
            # Skip for developers
            if email and self.is_developer_email(email):
                return True

            if not self.firebase_available or not self.db:
                return False

            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            if not user_doc.exists:
                # New user: create doc with count 1 so billing UI and limits work (no more silent no-op)
                self._ensure_user_doc_exists(user_id, email=email, initial_monthly_count=1, initial_daily_count=0)
                return True
            user_data = user_doc.to_dict()
            status = self._normalize_subscription_status(user_data.get('subscription_status'))
            today = datetime.now().date()
            current_month_start = today.replace(day=1)

            # Ensure reset fields exist so can_perform_analysis doesn't zero the count on next read
            updates = {}
            if status == 'premium':
                if _firestore_to_date(user_data.get('last_daily_reset')) != today:
                    updates['last_daily_reset'] = _date_to_firestore(today)
                updates['daily_analysis_count'] = firestore.Increment(1)
            else:
                if _firestore_to_date(user_data.get('last_monthly_reset')) != current_month_start:
                    updates['last_monthly_reset'] = _date_to_firestore(current_month_start)
                updates['monthly_analysis_count'] = firestore.Increment(1)

            if updates:
                user_ref.update(updates)
            return True
        except Exception as e:
            print(f"Error incrementing analysis count: {e}")
            return False

    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
            if not webhook_secret:
                print("❌ STRIPE_WEBHOOK_SECRET not configured")
                raise ValueError("Webhook secret not configured")
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            print(f"📡 Processing webhook event: {event['type']}")
            
            if event['type'] == 'customer.subscription.created':
                self.handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                self.handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                self.handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                self.handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                self.handle_payment_failed(event['data']['object'])
            else:
                print(f"⚠️ Unhandled webhook event type: {event['type']}")
                
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            raise

    def handle_subscription_created(self, subscription):
        """Handle new subscription creation - upgrade user to premium"""
        try:
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            print(f"📝 Processing subscription created: {subscription_id} for customer: {customer_id}")
            
            user_id = self.get_user_id_by_customer_id(customer_id)
            
            if user_id and self.firebase_available and self.db:
                today = datetime.now().date()
                self.db.collection('users').document(user_id).update({
                    'subscription_status': 'premium',
                    'subscription_id': subscription_id,
                    'current_period_end': datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc),
                    'daily_analysis_count': 0,
                    'last_daily_reset': _date_to_firestore(today),
                    'upgraded_to_premium_at': datetime.now(timezone.utc),
                    'webhook_processed_at': datetime.now(timezone.utc)
                })
                print(f"✅ Updated user {user_id} subscription status to premium")
            else:
                print(f"⚠️ Could not update user for customer {customer_id} - user_id: {user_id}, firebase_available: {self.firebase_available}")
        except Exception as e:
            print(f"❌ Error handling subscription created: {e}")
            raise

    def handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        try:
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            status = subscription['status']
            print(f"📝 Processing subscription updated: {subscription_id} for customer: {customer_id}, status: {status}")
            
            user_id = self.get_user_id_by_customer_id(customer_id)
            
            if user_id and self.firebase_available and self.db:
                # Map Stripe status to our status
                if status == 'active':
                    mapped_status = 'premium'
                elif status == 'past_due':
                    mapped_status = 'past_due'
                elif status == 'canceled' or status == 'cancelled':
                    mapped_status = 'free'  # Downgrade to free on cancellation
                else:
                    mapped_status = 'free'  # Default to free for any other status
                
                update_data = {
                    'subscription_status': mapped_status,
                    'current_period_end': datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc),
                    'webhook_processed_at': datetime.now(timezone.utc)
                }
                
                # Reset to monthly counting if downgrading to free
                if mapped_status == 'free':
                    today = datetime.now().date()
                    update_data['monthly_analysis_count'] = 0
                    update_data['last_monthly_reset'] = _date_to_firestore(today.replace(day=1))
                    update_data['downgraded_to_free_at'] = datetime.now(timezone.utc)
                
                self.db.collection('users').document(user_id).update(update_data)
                print(f"✅ Updated user {user_id} subscription status to {mapped_status}")
            else:
                print(f"⚠️ Could not update user for customer {customer_id} - user_id: {user_id}, firebase_available: {self.firebase_available}")
        except Exception as e:
            print(f"❌ Error handling subscription updated: {e}")
            raise

    def handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation - downgrade to free tier"""
        try:
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            print(f"📝 Processing subscription deleted: {subscription_id} for customer: {customer_id}")
            
            user_id = self.get_user_id_by_customer_id(customer_id)
            
            if user_id and self.firebase_available and self.db:
                today = datetime.now().date()
                self.db.collection('users').document(user_id).update({
                    'subscription_status': 'free',  # Downgrade to free tier
                    'subscription_cancelled_at': datetime.now(timezone.utc),
                    'monthly_analysis_count': 0,
                    'last_monthly_reset': _date_to_firestore(today.replace(day=1)),
                    'webhook_processed_at': datetime.now(timezone.utc)
                })
                print(f"✅ Updated user {user_id} subscription status to free (downgraded from premium)")
            else:
                print(f"⚠️ Could not update user for customer {customer_id} - user_id: {user_id}, firebase_available: {self.firebase_available}")
        except Exception as e:
            print(f"❌ Error handling subscription deleted: {e}")
            raise

    def handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        try:
            customer_id = invoice['customer']
            invoice_id = invoice['id']
            amount_paid = invoice.get('amount_paid', 0)
            print(f"💰 Processing payment succeeded: {invoice_id} for customer: {customer_id}, amount: ${amount_paid/100}")
            
            user_id = self.get_user_id_by_customer_id(customer_id)
            
            if user_id and self.firebase_available and self.db:
                self.db.collection('users').document(user_id).update({
                    'last_payment_date': datetime.now(timezone.utc),
                    'subscription_status': 'premium',
                    'last_payment_amount': amount_paid,
                    'webhook_processed_at': datetime.now(timezone.utc)
                })
                print(f"✅ Updated user {user_id} payment status to premium")
            else:
                print(f"⚠️ Could not update user for customer {customer_id} - user_id: {user_id}, firebase_available: {self.firebase_available}")
        except Exception as e:
            print(f"❌ Error handling payment succeeded: {e}")
            raise

    def handle_payment_failed(self, invoice):
        """Handle failed payment"""
        try:
            customer_id = invoice['customer']
            invoice_id = invoice['id']
            amount_due = invoice.get('amount_due', 0)
            print(f"❌ Processing payment failed: {invoice_id} for customer: {customer_id}, amount due: ${amount_due/100}")
            
            user_id = self.get_user_id_by_customer_id(customer_id)
            
            if user_id and self.firebase_available and self.db:
                self.db.collection('users').document(user_id).update({
                    'subscription_status': 'past_due',
                    'last_payment_failure': datetime.now(timezone.utc),
                    'amount_due': amount_due,
                    'webhook_processed_at': datetime.now(timezone.utc)
                })
                print(f"⚠️ Updated user {user_id} subscription status to past_due")
            else:
                print(f"⚠️ Could not update user for customer {customer_id} - user_id: {user_id}, firebase_available: {self.firebase_available}")
        except Exception as e:
            print(f"❌ Error handling payment failed: {e}")
            raise

    def get_user_id_by_customer_id(self, customer_id):
        """Get Firebase user ID from Stripe customer ID"""
        try:
            users = self.db.collection('users').where('stripe_customer_id', '==', customer_id).limit(1).stream()
            for user in users:
                return user.id
            return None
        except Exception as e:
            print(f"Error getting user by customer ID: {e}")
            return None
