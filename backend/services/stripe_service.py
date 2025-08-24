import stripe
import os
from datetime import datetime, timedelta
from firebase_admin import firestore
from dotenv import load_dotenv

load_dotenv()

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
            
        self.trial_days = int(os.getenv('TRIAL_DAYS', 3))
        self.trial_limit = int(os.getenv('TRIAL_ANALYSIS_LIMIT', 15))
        self.paid_limit = int(os.getenv('PAID_ANALYSIS_LIMIT', 100))
        self.monthly_price = int(os.getenv('MONTHLY_PRICE', 2000))
        self.product_id = os.getenv('STRIPE_PRODUCT_ID', 'prod_SuHsXyARgMiS3e')
        self.price_id = os.getenv('STRIPE_PRICE_ID', 'price_1RyTIYJNDWyJv8IpeKw3dzRB')
        
        # Developer emails for bypassing payment
        developer_emails_str = os.getenv('DEVELOPER_EMAILS', '')
        self.developer_emails = [email.strip() for email in developer_emails_str.split(',') if email.strip()]
        print(f"🔧 Developer emails loaded: {self.developer_emails}")

    def is_developer_email(self, email):
        """Check if email is in developer whitelist"""
        if not email:
            return False
        return email.lower() in [dev_email.lower() for dev_email in self.developer_emails]

    def get_developer_access_status(self, email):
        """Get developer access status for an email"""
        is_developer = self.is_developer_email(email)
        if is_developer:
            return {
                'is_developer': True,
                'status': 'developer',
                'daily_usage': 0,
                'daily_limit': 999999,  # Unlimited for developers
                'can_perform': True
            }
        return {'is_developer': False}

    def create_customer(self, user_id, email, name):
        """Create a Stripe customer and link to Firebase user"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'firebase_user_id': user_id}
            )
            
            # Store customer ID in Firebase if available
            if self.firebase_available and self.db:
                try:
                    self.db.collection('users').document(user_id).update({
                        'stripe_customer_id': customer.id,
                        'subscription_status': 'trial',
                        'trial_start_date': datetime.now(),
                        'trial_end_date': datetime.now() + timedelta(days=self.trial_days),
                        'daily_analysis_count': 0,
                        'last_analysis_reset': datetime.now().date()
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
        """Create a subscription for a customer"""
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

    def create_trial_subscription(self, customer_id):
        """Create a subscription that starts after trial period"""
        try:
            # Create subscription with trial period
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': self.price_id}],
                trial_period_days=self.trial_days,
                payment_settings={'save_default_payment_method': 'on_subscription'},
                metadata={'trial_subscription': 'true'}
            )
            return subscription
        except Exception as e:
            print(f"Error creating trial subscription: {e}")
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

    def create_subscription_after_trial(self, customer_id):
        """Create a subscription that starts immediately (after trial)"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': self.price_id}],
                payment_settings={'save_default_payment_method': 'on_subscription'},
                metadata={'post_trial_subscription': 'true'}
            )
            return subscription
        except Exception as e:
            print(f"Error creating post-trial subscription: {e}")
            raise

    def get_subscription_status(self, user_id, email=None):
        """Get current subscription status for a user"""
        try:
            # Check if user is a developer first
            if email and self.is_developer_email(email):
                return {
                    'status': 'developer',
                    'trial_end_date': None,
                    'daily_analysis_count': 0,
                    'analysis_limit': 999999,  # Unlimited for developers
                    'stripe_customer_id': None,
                    'is_developer': True
                }
            
            if not self.firebase_available or not self.db:
                # Return default trial status if Firebase not available
                return {
                    'status': 'trial',
                    'trial_end_date': (datetime.now() + timedelta(days=self.trial_days)).isoformat(),
                    'daily_analysis_count': 0,
                    'analysis_limit': self.trial_limit,
                    'stripe_customer_id': None
                }
            
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                # Return default trial status for new users
                return {
                    'status': 'trial',
                    'trial_end_date': (datetime.now() + timedelta(days=self.trial_days)).isoformat(),
                    'daily_analysis_count': 0,
                    'analysis_limit': self.trial_limit,
                    'stripe_customer_id': None
                }
            
            user_data = user_doc.to_dict()
            return {
                'status': user_data.get('subscription_status', 'trial'),
                'trial_end_date': user_data.get('trial_end_date'),
                'daily_analysis_count': user_data.get('daily_analysis_count', 0),
                'analysis_limit': self.get_analysis_limit(user_data),
                'stripe_customer_id': user_data.get('stripe_customer_id')
            }
        except Exception as e:
            print(f"Error getting subscription status: {e}")
            return None

    def get_analysis_limit(self, user_data):
        """Get the daily analysis limit based on subscription status"""
        status = user_data.get('subscription_status', 'trial')
        if status == 'active':
            return self.paid_limit
        return self.trial_limit

    def can_perform_analysis(self, user_id, email=None):
        """Check if user can perform an AI analysis"""
        try:
            # Check if user is a developer first
            if email and self.is_developer_email(email):
                return {
                    'can_perform': True,
                    'daily_usage': 0,
                    'daily_limit': 999999,  # Unlimited for developers
                    'status': 'developer'
                }
            
            if not self.firebase_available:
                # Default to allowing analysis if Firebase is not available
                return {
                    'can_perform': True,
                    'daily_usage': 0,
                    'daily_limit': self.trial_limit,
                    'status': 'trial'
                }
            
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                return {
                    'can_perform': False,
                    'daily_usage': 0,
                    'daily_limit': 0,
                    'status': 'no_subscription'
                }
            
            user_data = user_doc.to_dict()
            today = datetime.now().date()
            last_reset = user_data.get('last_analysis_reset')
            
            # Reset daily count if it's a new day
            if last_reset != today:
                self.db.collection('users').document(user_id).update({
                    'daily_analysis_count': 0,
                    'last_analysis_reset': today
                })
                user_data['daily_analysis_count'] = 0
                user_data['last_analysis_reset'] = today
            
            # Check trial status
            if user_data.get('subscription_status') == 'trial':
                trial_end = user_data.get('trial_end_date')
                if trial_end and datetime.now() > trial_end:
                    # Trial expired, update status
                    self.db.collection('users').document(user_id).update({
                        'subscription_status': 'expired'
                    })
                    return {
                        'can_perform': False,
                        'daily_usage': user_data.get('daily_analysis_count', 0),
                        'daily_limit': self.get_analysis_limit(user_data),
                        'status': 'expired'
                    }
            
            # Check daily limit
            limit = self.get_analysis_limit(user_data)
            current_count = user_data.get('daily_analysis_count', 0)
            can_perform = current_count < limit
            
            return {
                'can_perform': can_perform,
                'daily_usage': current_count,
                'daily_limit': limit,
                'status': user_data.get('subscription_status', 'trial')
            }
        except Exception as e:
            print(f"Error checking analysis permission: {e}")
            # Default to allowing analysis if there's an error
            return {
                'can_perform': True,
                'daily_usage': 0,
                'daily_limit': self.trial_limit,
                'status': 'trial'
            }

    def increment_analysis_count(self, user_id):
        """Increment the daily analysis count for a user"""
        try:
            if not self.firebase_available or not self.db:
                # Skip increment if Firebase not available
                return
                
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'daily_analysis_count': firestore.Increment(1)
            })
        except Exception as e:
            print(f"Error incrementing analysis count: {e}")

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
        """Handle new subscription creation"""
        try:
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            print(f"📝 Processing subscription created: {subscription_id} for customer: {customer_id}")
            
            user_id = self.get_user_id_by_customer_id(customer_id)
            
            if user_id and self.firebase_available and self.db:
                self.db.collection('users').document(user_id).update({
                    'subscription_status': 'active',
                    'subscription_id': subscription_id,
                    'current_period_end': datetime.fromtimestamp(subscription['current_period_end']),
                    'webhook_processed_at': datetime.now()
                })
                print(f"✅ Updated user {user_id} subscription status to active")
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
                    mapped_status = 'active'
                elif status == 'trialing':
                    mapped_status = 'trial'
                elif status == 'past_due':
                    mapped_status = 'past_due'
                elif status == 'canceled':
                    mapped_status = 'cancelled'
                else:
                    mapped_status = 'inactive'
                
                self.db.collection('users').document(user_id).update({
                    'subscription_status': mapped_status,
                    'current_period_end': datetime.fromtimestamp(subscription['current_period_end']),
                    'webhook_processed_at': datetime.now()
                })
                print(f"✅ Updated user {user_id} subscription status to {mapped_status}")
            else:
                print(f"⚠️ Could not update user for customer {customer_id} - user_id: {user_id}, firebase_available: {self.firebase_available}")
        except Exception as e:
            print(f"❌ Error handling subscription updated: {e}")
            raise

    def handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        try:
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            print(f"📝 Processing subscription deleted: {subscription_id} for customer: {customer_id}")
            
            user_id = self.get_user_id_by_customer_id(customer_id)
            
            if user_id and self.firebase_available and self.db:
                self.db.collection('users').document(user_id).update({
                    'subscription_status': 'cancelled',
                    'subscription_cancelled_at': datetime.now(),
                    'webhook_processed_at': datetime.now()
                })
                print(f"✅ Updated user {user_id} subscription status to cancelled")
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
                    'last_payment_date': datetime.now(),
                    'subscription_status': 'active',
                    'last_payment_amount': amount_paid,
                    'webhook_processed_at': datetime.now()
                })
                print(f"✅ Updated user {user_id} payment status to active")
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
                    'last_payment_failure': datetime.now(),
                    'amount_due': amount_due,
                    'webhook_processed_at': datetime.now()
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

    def check_trial_eligibility(self, email):
        """Check if email is eligible for a trial (hasn't used one before)"""
        if not email or not self.firebase_available or not self.db:
            return True  # Allow trial if we can't check
            
        try:
            # Check if this email has ever had a trial or paid subscription
            users_ref = self.db.collection('users')
            query = users_ref.where('email', '==', email.lower()).limit(1)
            docs = query.get()
            
            for doc in docs:
                user_data = doc.to_dict()
                # Check if user has ever had a trial or paid subscription
                subscription_status = user_data.get('subscription_status')
                has_used_trial = user_data.get('has_used_trial', False)
                
                if subscription_status in ['trial', 'active', 'expired', 'cancelled'] or has_used_trial:
                    print(f"❌ Email {email} has already used a trial or had a subscription")
                    return False
            
            print(f"✅ Email {email} is eligible for trial")
            return True
            
        except Exception as e:
            print(f"⚠️ Error checking trial eligibility for {email}: {e}")
            return True  # Allow trial if we can't check

    def mark_trial_used(self, user_id, email):
        """Mark that this email has used a trial"""
        if not self.firebase_available or not self.db:
            return
            
        try:
            # Update current user
            self.db.collection('users').document(user_id).update({
                'has_used_trial': True,
                'trial_used_at': datetime.now()
            })
            
            # Also mark in a separate collection for easy querying
            self.db.collection('trial_history').add({
                'email': email.lower(),
                'user_id': user_id,
                'trial_started_at': datetime.now(),
                'ip_address': 'tracked_separately'  # You can add IP tracking if needed
            })
            
            print(f"✅ Marked trial as used for {email}")
            
        except Exception as e:
            print(f"❌ Error marking trial as used for {email}: {e}")

    def get_trial_history(self, email):
        """Get trial history for an email"""
        if not email or not self.firebase_available or not self.db:
            return []
            
        try:
            # Check trial history collection
            trial_ref = self.db.collection('trial_history')
            query = trial_ref.where('email', '==', email.lower()).order_by('trial_started_at', direction=firestore.Query.DESCENDING)
            docs = query.get()
            
            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append({
                    'user_id': data.get('user_id'),
                    'trial_started_at': data.get('trial_started_at'),
                    'email': data.get('email')
                })
            
            return history
            
        except Exception as e:
            print(f"❌ Error getting trial history for {email}: {e}")
            return []
