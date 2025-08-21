# Stripe Integration Guide for FXSentinel

## Overview

This guide outlines the complete process for integrating Stripe payments into FXSentinel to implement a subscription-based model with the following features:

- **3-day free trial** for new users
- **15 AI analyses per day** during free trial
- **$20 monthly subscription** after trial
- **100 AI analyses per day** for paid subscribers
- **Usage tracking and limits enforcement**

## Table of Contents

1. [Prerequisites and Setup](#prerequisites-and-setup)
2. [Stripe Account Configuration](#stripe-account-configuration)
3. [User Flow Integration Strategy](#user-flow-integration-strategy)
4. [Backend Integration](#backend-integration)
5. [Frontend Integration](#frontend-integration)
6. [Database Schema Updates](#database-schema-updates)
7. [Usage Tracking System](#usage-tracking-system)
8. [Subscription Management](#subscription-management)
9. [Testing and Deployment](#testing-and-deployment)
10. [Security Considerations](#security-considerations)
11. [Troubleshooting](#troubleshooting)

## User Flow Integration Strategy

### Current Flow Analysis
Your current user journey is:
1. **Landing Page** → 2. **Login/Signup** → 3. **Dashboard**

### Recommended Payment Integration Strategy

#### Option 1: Post-Signup Trial Activation (Recommended)
**Flow:** Landing Page → Login/Signup → **Trial Welcome Screen** → Dashboard

**Implementation:**
1. **Signup Process**: User creates account normally
2. **Trial Welcome Screen**: After successful signup, redirect to a welcome screen that:
   - Explains the 3-day free trial
   - Shows the 15 analyses/day limit
   - Displays upgrade benefits (100 analyses/day)
   - Has a "Start Free Trial" button
3. **Dashboard Access**: User proceeds to dashboard with trial status

**Benefits:**
- Low friction signup process
- Clear trial explanation
- Users can experience the product before payment
- Natural upgrade path

#### Option 2: Dashboard-Integrated Payment
**Flow:** Landing Page → Login/Signup → Dashboard (with payment prompts)

**Implementation:**
1. **Dashboard with Trial Status**: Show trial status in dashboard header
2. **Usage Indicators**: Display current usage vs limits
3. **Upgrade Prompts**: Strategic placement of upgrade CTAs
4. **Payment Modal**: In-app subscription flow

**Benefits:**
- Users see value immediately
- Contextual upgrade prompts
- Seamless payment experience

#### Option 3: Hybrid Approach (Best User Experience)
**Flow:** Landing Page → Login/Signup → Trial Welcome → Dashboard (with smart prompts)

**Implementation:**
1. **Trial Welcome Screen**: Brief explanation of trial
2. **Dashboard Integration**: Smart payment prompts based on usage
3. **Progressive Disclosure**: Show payment options as users approach limits

### Recommended Implementation Plan

#### Phase 1: Trial Welcome Screen
Create a new component `TrialWelcome.jsx` that appears after signup:

```jsx
// src/components/TrialWelcome.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './TrialWelcome.css';

const TrialWelcome = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  const handleStartTrial = async () => {
    try {
      // Create Stripe customer and start trial
      const response = await fetch('/api/create-customer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.uid,
          email: currentUser.email,
          name: currentUser.displayName || currentUser.email,
        }),
      });
      
      if (response.ok) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Error starting trial:', error);
      navigate('/dashboard'); // Fallback
    }
  };

  return (
    <div className="trial-welcome">
      <div className="trial-welcome-card">
        <h1>Welcome to FXSentinel!</h1>
        <div className="trial-benefits">
          <h2>Your 3-Day Free Trial Includes:</h2>
          <ul>
            <li>✅ 15 AI analyses per day</li>
            <li>✅ Real-time market insights</li>
            <li>✅ Economic calendar alerts</li>
            <li>✅ Advanced filtering tools</li>
          </ul>
        </div>
        
        <div className="upgrade-benefits">
          <h3>Upgrade to Premium for $20/month:</h3>
          <ul>
            <li>🚀 100 AI analyses per day</li>
            <li>🚀 Priority support</li>
            <li>🚀 Advanced analytics</li>
            <li>🚀 Custom alerts</li>
          </ul>
        </div>
        
        <div className="trial-actions">
          <button onClick={handleStartTrial} className="start-trial-btn">
            Start Free Trial
          </button>
          <button onClick={() => navigate('/dashboard')} className="skip-btn">
            Skip for Now
          </button>
        </div>
      </div>
    </div>
  );
};
```

#### Phase 2: Dashboard Integration
Add subscription status and upgrade prompts to dashboard:

```jsx
// Add to Dashboard.jsx header
const SubscriptionStatus = () => {
  const { subscriptionStatus } = useAuth();
  
  if (!subscriptionStatus) return null;
  
  const { status, daily_analysis_count, analysis_limit } = subscriptionStatus;
  const usagePercentage = (daily_analysis_count / analysis_limit) * 100;
  
  return (
    <div className="subscription-status-bar">
      {status === 'trial' && (
        <div className="trial-banner">
          <span>Free Trial: {daily_analysis_count}/{analysis_limit} analyses used</span>
          <button onClick={() => setShowUpgradeModal(true)}>Upgrade Now</button>
        </div>
      )}
      
      {status === 'expired' && (
        <div className="expired-banner">
          <span>Trial Expired - Upgrade to continue</span>
          <button onClick={() => setShowUpgradeModal(true)}>Subscribe</button>
        </div>
      )}
      
      <div className="usage-progress">
        <div 
          className="usage-fill" 
          style={{ width: `${usagePercentage}%` }}
        ></div>
      </div>
    </div>
  );
};
```

#### Phase 3: Smart Payment Prompts
Implement contextual upgrade prompts:

```jsx
// Usage-based upgrade prompts
const UsageUpgradePrompt = () => {
  const { subscriptionStatus } = useAuth();
  const [showPrompt, setShowPrompt] = useState(false);
  
  useEffect(() => {
    if (subscriptionStatus?.status === 'trial') {
      const { daily_analysis_count, analysis_limit } = subscriptionStatus;
      const usagePercentage = (daily_analysis_count / analysis_limit) * 100;
      
      // Show upgrade prompt at 80% usage
      if (usagePercentage >= 80 && !showPrompt) {
        setShowPrompt(true);
      }
    }
  }, [subscriptionStatus]);
  
  if (!showPrompt) return null;
  
  return (
    <div className="upgrade-prompt">
      <h3>Running out of analyses?</h3>
      <p>Upgrade to Premium for 100 analyses per day</p>
      <button onClick={() => setShowUpgradeModal(true)}>Upgrade Now</button>
      <button onClick={() => setShowPrompt(false)}>Maybe Later</button>
    </div>
  );
};
```

### Updated App.jsx Routing

```jsx
// Updated App.jsx
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/trial-welcome" element={
              <ProtectedRoute>
                <TrialWelcome />
              </ProtectedRoute>
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/subscription" element={
              <ProtectedRoute>
                <Subscription />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}
```

### Updated AuthContext

```jsx
// Add to AuthContext.jsx
const [hasSeenTrialWelcome, setHasSeenTrialWelcome] = useState(false);

const checkTrialWelcome = async (user) => {
  if (user) {
    try {
      const userDoc = await getDoc(doc(db, 'users', user.uid));
      if (userDoc.exists()) {
        const userData = userDoc.data();
        setHasSeenTrialWelcome(userData.hasSeenTrialWelcome || false);
      }
    } catch (error) {
      console.error('Error checking trial welcome:', error);
    }
  }
};

// Update signup function
const signup = async (email, password, firstName, lastName) => {
  try {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(result.user, {
      displayName: `${firstName} ${lastName}`
    });
    
    // Create user document with trial status
    await setDoc(doc(db, 'users', result.user.uid), {
      email,
      displayName: `${firstName} ${lastName}`,
      createdAt: new Date(),
      subscription_status: 'trial',
      trial_start_date: new Date(),
      trial_end_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000), // 3 days
      daily_analysis_count: 0,
      last_analysis_reset: new Date().toDateString(),
      hasSeenTrialWelcome: false
    });
    
    return result;
  } catch (error) {
    throw error;
  }
};
```

### Updated Signup Flow

```jsx
// Update Signup.jsx handleSubmit
const handleSubmit = async (e) => {
  e.preventDefault();
  setIsLoading(true);
  setError('');

  try {
    await signup(formData.email, formData.password, formData.firstName, formData.lastName);
    navigate('/trial-welcome'); // Redirect to trial welcome instead of dashboard
  } catch (err) {
    setError('Failed to create account. Please try again.');
  } finally {
    setIsLoading(false);
  }
};
```

### Payment Prompt Strategy

#### 1. Trial Welcome Screen (Post-Signup)
- Clear explanation of trial benefits
- Preview of premium features
- Low-pressure "Start Trial" button

#### 2. Dashboard Header (Always Visible)
- Current trial status
- Usage progress bar
- Quick upgrade button

#### 3. Usage-Based Prompts (Contextual)
- At 80% usage: "Running out of analyses?"
- At 100% usage: "Upgrade to continue"
- After trial expiration: "Trial expired" banner

#### 4. Feature-Gated Prompts (Strategic)
- When accessing premium features
- Before AI analysis (if limit reached)
- In settings/preferences

### User Experience Considerations

#### Trial Experience
- **Immediate Value**: Users can use core features right away
- **Clear Limits**: Transparent about usage restrictions
- **Easy Upgrade**: Multiple upgrade touchpoints
- **No Surprises**: Clear communication about trial expiration

#### Payment Experience
- **Seamless Flow**: Minimal friction in payment process
- **Clear Pricing**: Transparent about costs
- **Easy Cancellation**: Simple subscription management
- **Value Demonstration**: Show benefits before asking for payment

#### Retention Strategy
- **Usage Monitoring**: Track feature usage patterns
- **Personalized Prompts**: Show relevant upgrade benefits
- **Grace Period**: Allow some flexibility with limits
- **Feedback Loop**: Learn from user behavior

This integration strategy ensures users get immediate value from your product while creating natural opportunities for conversion to paid subscriptions. The trial welcome screen provides a smooth onboarding experience, while the dashboard integration keeps payment options visible without being intrusive.

## Prerequisites and Setup

### Required Accounts and Services

1. **Stripe Account** (your friend's account since they're 18+)
2. **Firebase Project** (already configured)
3. **Python Environment** (already set up)
4. **Node.js Environment** (already set up)

### Required Dependencies

#### Backend Dependencies (Python)
```bash
pip install stripe
pip install firebase-admin
```

#### Frontend Dependencies (Node.js)
```bash
npm install @stripe/stripe-js
npm install @stripe/react-stripe-js
```

## Stripe Account Configuration

### 1. Stripe Dashboard Setup

1. **Access Stripe Dashboard**: Your friend should log into their Stripe account
2. **Navigate to Products**: Go to Products > Add Product
3. **Create Subscription Product**:
   - Name: "FXSentinel Premium"
   - Description: "Unlimited AI analysis for forex trading"
   - Pricing: $20/month
   - Billing: Monthly

### 2. Webhook Configuration

1. **Create Webhook Endpoint**:
   - URL: `https://your-domain.com/webhook/stripe`
   - Events to listen for:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

2. **Get Webhook Secret**: Copy the webhook signing secret for backend verification

### 3. API Keys

1. **Publishable Key**: For frontend (safe to expose)
2. **Secret Key**: For backend (keep secure)
3. **Webhook Secret**: For webhook verification

## Backend Integration

### 1. Environment Variables

Add these to your `.env` file:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Subscription Configuration
TRIAL_DAYS=3
TRIAL_ANALYSIS_LIMIT=15
PAID_ANALYSIS_LIMIT=100
MONTHLY_PRICE=2000  # $20.00 in cents
```

### 2. Stripe Service Module

Create `backend/services/stripe_service.py`:

```python
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
        self.db = firestore.client()
        self.trial_days = int(os.getenv('TRIAL_DAYS', 3))
        self.trial_limit = int(os.getenv('TRIAL_ANALYSIS_LIMIT', 15))
        self.paid_limit = int(os.getenv('PAID_ANALYSIS_LIMIT', 100))
        self.monthly_price = int(os.getenv('MONTHLY_PRICE', 2000))

    def create_customer(self, user_id, email, name):
        """Create a Stripe customer and link to Firebase user"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'firebase_user_id': user_id}
            )
            
            # Store customer ID in Firebase
            self.db.collection('users').document(user_id).update({
                'stripe_customer_id': customer.id,
                'subscription_status': 'trial',
                'trial_start_date': datetime.now(),
                'trial_end_date': datetime.now() + timedelta(days=self.trial_days),
                'daily_analysis_count': 0,
                'last_analysis_reset': datetime.now().date()
            })
            
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

    def get_subscription_status(self, user_id):
        """Get current subscription status for a user"""
        try:
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                return None
            
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

    def can_perform_analysis(self, user_id):
        """Check if user can perform an AI analysis"""
        try:
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                return False
            
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
                    return False
            
            # Check daily limit
            limit = self.get_analysis_limit(user_data)
            current_count = user_data.get('daily_analysis_count', 0)
            
            return current_count < limit
        except Exception as e:
            print(f"Error checking analysis permission: {e}")
            return False

    def increment_analysis_count(self, user_id):
        """Increment the daily analysis count for a user"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'daily_analysis_count': firestore.Increment(1)
            })
        except Exception as e:
            print(f"Error incrementing analysis count: {e}")

    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
            )
            
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
                
        except Exception as e:
            print(f"Webhook error: {e}")
            raise

    def handle_subscription_created(self, subscription):
        """Handle new subscription creation"""
        customer_id = subscription['customer']
        user_id = self.get_user_id_by_customer_id(customer_id)
        
        if user_id:
            self.db.collection('users').document(user_id).update({
                'subscription_status': 'active',
                'subscription_id': subscription['id'],
                'current_period_end': datetime.fromtimestamp(subscription['current_period_end'])
            })

    def handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        customer_id = subscription['customer']
        user_id = self.get_user_id_by_customer_id(customer_id)
        
        if user_id:
            status = 'active' if subscription['status'] == 'active' else 'inactive'
            self.db.collection('users').document(user_id).update({
                'subscription_status': status,
                'current_period_end': datetime.fromtimestamp(subscription['current_period_end'])
            })

    def handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        customer_id = subscription['customer']
        user_id = self.get_user_id_by_customer_id(customer_id)
        
        if user_id:
            self.db.collection('users').document(user_id).update({
                'subscription_status': 'cancelled'
            })

    def handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        customer_id = invoice['customer']
        user_id = self.get_user_id_by_customer_id(customer_id)
        
        if user_id:
            self.db.collection('users').document(user_id).update({
                'last_payment_date': datetime.now(),
                'subscription_status': 'active'
            })

    def handle_payment_failed(self, invoice):
        """Handle failed payment"""
        customer_id = invoice['customer']
        user_id = self.get_user_id_by_customer_id(customer_id)
        
        if user_id:
            self.db.collection('users').document(user_id).update({
                'subscription_status': 'past_due'
            })

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
```

### 3. Flask Backend Routes

Add these routes to your `backend/app.py`:

```python
from services.stripe_service import StripeService
import stripe

stripe_service = StripeService()

@app.route('/api/create-customer', methods=['POST'])
def create_customer():
    """Create a Stripe customer for a new user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        name = data.get('name')
        
        customer = stripe_service.create_customer(user_id, email, name)
        
        return jsonify({
            'success': True,
            'customer_id': customer.id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-subscription', methods=['POST'])
def create_subscription():
    """Create a subscription for a user"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        price_id = data.get('price_id')
        
        subscription = stripe_service.create_subscription(customer_id, price_id)
        
        return jsonify({
            'success': True,
            'subscription_id': subscription.id,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscription-status/<user_id>', methods=['GET'])
def get_subscription_status(user_id):
    """Get subscription status for a user"""
    try:
        status = stripe_service.get_subscription_status(user_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-analysis-permission/<user_id>', methods=['GET'])
def check_analysis_permission(user_id):
    """Check if user can perform an AI analysis"""
    try:
        can_analyze = stripe_service.can_perform_analysis(user_id)
        if can_analyze:
            stripe_service.increment_analysis_count(user_id)
        
        status = stripe_service.get_subscription_status(user_id)
        
        return jsonify({
            'can_analyze': can_analyze,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        stripe_service.handle_webhook(payload, sig_header)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create a payment intent for subscription"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        
        payment_intent = stripe.PaymentIntent.create(
            customer=customer_id,
            amount=2000,  # $20.00 in cents
            currency='usd',
            automatic_payment_methods={'enabled': True},
        )
        
        return jsonify({
            'client_secret': payment_intent.client_secret
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Frontend Integration

### 1. Stripe Provider Setup

Update your `src/App.jsx` to include Stripe provider:

```jsx
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

function App() {
  return (
    <Elements stripe={stripePromise}>
      <AuthProvider>
        {/* Your existing app content */}
      </AuthProvider>
    </Elements>
  );
}
```

### 2. Subscription Component

Create `src/components/Subscription.jsx`:

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import './Subscription.css';

const Subscription = () => {
  const { currentUser } = useAuth();
  const stripe = useStripe();
  const elements = useElements();
  
  const [loading, setLoading] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (currentUser) {
      fetchSubscriptionStatus();
    }
  }, [currentUser]);

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await fetch(`/api/subscription-status/${currentUser.uid}`);
      const data = await response.json();
      setSubscriptionStatus(data);
    } catch (error) {
      console.error('Error fetching subscription status:', error);
    }
  };

  const handleSubscribe = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    if (!stripe || !elements) {
      setError('Stripe has not loaded yet.');
      setLoading(false);
      return;
    }

    try {
      // Create customer if doesn't exist
      if (!subscriptionStatus?.stripe_customer_id) {
        await createCustomer();
      }

      // Create payment intent
      const response = await fetch('/api/create-payment-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: subscriptionStatus.stripe_customer_id,
        }),
      });

      const { client_secret } = await response.json();

      // Confirm payment
      const { error: paymentError } = await stripe.confirmCardPayment(client_secret, {
        payment_method: {
          card: elements.getElement(CardElement),
        },
      });

      if (paymentError) {
        setError(paymentError.message);
      } else {
        // Payment successful, update subscription
        await fetchSubscriptionStatus();
        setError('Payment successful! Your subscription is now active.');
      }
    } catch (error) {
      setError('An error occurred during payment.');
      console.error('Payment error:', error);
    }

    setLoading(false);
  };

  const createCustomer = async () => {
    const response = await fetch('/api/create-customer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: currentUser.uid,
        email: currentUser.email,
        name: currentUser.displayName || currentUser.email,
      }),
    });

    const data = await response.json();
    if (data.success) {
      setSubscriptionStatus(prev => ({
        ...prev,
        stripe_customer_id: data.customer_id
      }));
    }
  };

  const getStatusDisplay = () => {
    if (!subscriptionStatus) return 'Loading...';

    const { status, daily_analysis_count, analysis_limit, trial_end_date } = subscriptionStatus;

    if (status === 'trial') {
      const daysLeft = Math.ceil((new Date(trial_end_date) - new Date()) / (1000 * 60 * 60 * 24));
      return (
        <div className="trial-status">
          <h3>Free Trial Active</h3>
          <p>{daysLeft} days remaining</p>
          <p>Analyses used: {daily_analysis_count}/{analysis_limit}</p>
          <button onClick={() => document.getElementById('subscription-form').scrollIntoView()}>
            Upgrade to Premium
          </button>
        </div>
      );
    }

    if (status === 'active') {
      return (
        <div className="active-status">
          <h3>Premium Subscription Active</h3>
          <p>Analyses used: {daily_analysis_count}/{analysis_limit}</p>
          <p>Next billing: Monthly</p>
        </div>
      );
    }

    if (status === 'expired') {
      return (
        <div className="expired-status">
          <h3>Trial Expired</h3>
          <p>Upgrade to continue using AI analysis</p>
          <button onClick={() => document.getElementById('subscription-form').scrollIntoView()}>
            Subscribe Now
          </button>
        </div>
      );
    }

    return <p>Status: {status}</p>;
  };

  return (
    <div className="subscription-container">
      <div className="subscription-status">
        {getStatusDisplay()}
      </div>

      {(subscriptionStatus?.status === 'trial' || subscriptionStatus?.status === 'expired') && (
        <div id="subscription-form" className="subscription-form">
          <h3>Upgrade to Premium</h3>
          <p>Get unlimited AI analysis for $20/month</p>
          
          <form onSubmit={handleSubscribe}>
            <div className="card-element-container">
              <CardElement
                options={{
                  style: {
                    base: {
                      fontSize: '16px',
                      color: '#424770',
                      '::placeholder': {
                        color: '#aab7c4',
                      },
                    },
                    invalid: {
                      color: '#9e2146',
                    },
                  },
                }}
              />
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <button type="submit" disabled={loading}>
              {loading ? 'Processing...' : 'Subscribe for $20/month'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default Subscription;
```

### 3. Subscription CSS

Create `src/components/Subscription.css`:

```css
.subscription-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.subscription-status {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  text-align: center;
}

.trial-status {
  color: #28a745;
}

.active-status {
  color: #007bff;
}

.expired-status {
  color: #dc3545;
}

.subscription-form {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.card-element-container {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 12px;
  margin: 20px 0;
}

.error-message {
  color: #dc3545;
  margin: 10px 0;
  padding: 10px;
  background: #f8d7da;
  border-radius: 4px;
}

button {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background: #0056b3;
}

button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}
```

### 4. Update AuthContext

Add subscription status to your AuthContext:

```jsx
// Add to AuthContext.jsx
const [subscriptionStatus, setSubscriptionStatus] = useState(null);

const fetchSubscriptionStatus = async () => {
  if (currentUser) {
    try {
      const response = await fetch(`/api/subscription-status/${currentUser.uid}`);
      const data = await response.json();
      setSubscriptionStatus(data);
    } catch (error) {
      console.error('Error fetching subscription status:', error);
    }
  }
};

// Add to useEffect
useEffect(() => {
  const unsubscribe = onAuthStateChanged(auth, (user) => {
    setCurrentUser(user);
    setLoading(false);
    if (user) {
      fetchSubscriptionStatus();
    }
  });

  return () => unsubscribe;
}, []);

// Add to value object
const value = {
  currentUser,
  subscriptionStatus,
  fetchSubscriptionStatus,
  // ... existing methods
};
```

## Database Schema Updates

### Firebase Firestore Collections

Update your Firebase structure to include subscription data:

```javascript
// users/{userId}
{
  email: string,
  displayName: string,
  createdAt: timestamp,
  stripe_customer_id: string,
  subscription_status: 'trial' | 'active' | 'expired' | 'cancelled' | 'past_due',
  trial_start_date: timestamp,
  trial_end_date: timestamp,
  daily_analysis_count: number,
  last_analysis_reset: date,
  subscription_id: string,
  current_period_end: timestamp,
  last_payment_date: timestamp
}

// subscriptions/{subscriptionId}
{
  user_id: string,
  stripe_subscription_id: string,
  status: string,
  created_at: timestamp,
  current_period_start: timestamp,
  current_period_end: timestamp,
  cancel_at_period_end: boolean
}

// analysis_logs/{logId}
{
  user_id: string,
  timestamp: timestamp,
  analysis_type: string,
  success: boolean,
  error_message: string
}
```

## Usage Tracking System

### 1. Analysis Permission Check

Update your AI analysis endpoint to check permissions:

```python
@app.route('/api/analyze', methods=['POST'])
def analyze_news():
    """Analyze news with AI - includes permission check"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        # Check if user can perform analysis
        permission_check = stripe_service.can_perform_analysis(user_id)
        
        if not permission_check['can_analyze']:
            return jsonify({
                'error': 'Analysis limit reached or subscription expired',
                'status': permission_check['status']
            }), 403
        
        # Increment usage count
        stripe_service.increment_analysis_count(user_id)
        
        # Proceed with existing analysis logic
        # ... your existing AI analysis code ...
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 2. Usage Dashboard

Create a usage tracking component:

```jsx
// src/components/UsageDashboard.jsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const UsageDashboard = () => {
  const { subscriptionStatus } = useAuth();

  if (!subscriptionStatus) return <div>Loading...</div>;

  const { daily_analysis_count, analysis_limit, status } = subscriptionStatus;
  const usagePercentage = (daily_analysis_count / analysis_limit) * 100;

  return (
    <div className="usage-dashboard">
      <h3>Daily Usage</h3>
      <div className="usage-bar">
        <div 
          className="usage-fill" 
          style={{ width: `${usagePercentage}%` }}
        ></div>
      </div>
      <p>{daily_analysis_count} / {analysis_limit} analyses used</p>
      <p>Status: {status}</p>
    </div>
  );
};
```

## Subscription Management

### 1. Cancel Subscription

Add cancellation functionality:

```python
@app.route('/api/cancel-subscription', methods=['POST'])
def cancel_subscription():
    """Cancel a user's subscription"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        user_doc = stripe_service.db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        subscription_id = user_data.get('subscription_id')
        
        if subscription_id:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            
            stripe_service.db.collection('users').document(user_id).update({
                'subscription_status': 'cancelling'
            })
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'No active subscription'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 2. Reactivate Subscription

Add reactivation functionality:

```python
@app.route('/api/reactivate-subscription', methods=['POST'])
def reactivate_subscription():
    """Reactivate a cancelled subscription"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        user_doc = stripe_service.db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        subscription_id = user_data.get('subscription_id')
        
        if subscription_id:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            stripe_service.db.collection('users').document(user_id).update({
                'subscription_status': 'active'
            })
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'No subscription found'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Testing and Deployment

### 1. Testing Checklist

- [ ] Test free trial creation
- [ ] Test subscription creation
- [ ] Test payment processing
- [ ] Test usage limits enforcement
- [ ] Test webhook handling
- [ ] Test subscription cancellation
- [ ] Test subscription reactivation
- [ ] Test trial expiration
- [ ] Test payment failure scenarios

### 2. Stripe Test Mode

Use Stripe's test mode for development:

```env
# Test mode keys
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

Test card numbers:
- Success: `4242424242424242`
- Decline: `4000000000000002`
- Insufficient funds: `4000000000009995`

### 3. Production Deployment

1. **Switch to Live Keys**: Update environment variables with live Stripe keys
2. **Update Webhook URL**: Point to production domain
3. **Test Live Payments**: Use real payment methods
4. **Monitor Webhooks**: Check Stripe dashboard for webhook delivery
5. **Set up Monitoring**: Monitor subscription events and payment failures

## Security Considerations

### 1. Webhook Security

- Always verify webhook signatures
- Use HTTPS in production
- Validate webhook payload structure
- Handle webhook failures gracefully

### 2. API Security

- Validate user authentication on all endpoints
- Rate limit API calls
- Sanitize all input data
- Log security events

### 3. Data Protection

- Encrypt sensitive data
- Follow GDPR compliance
- Implement data retention policies
- Secure API key storage

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving Events**
   - Check webhook URL accessibility
   - Verify webhook secret
   - Check server logs for errors

2. **Payment Failures**
   - Verify card details
   - Check Stripe dashboard for error codes
   - Implement proper error handling

3. **Usage Limits Not Working**
   - Check Firebase connection
   - Verify user document structure
   - Check timezone handling

4. **Subscription Status Not Updating**
   - Verify webhook endpoint
   - Check Firebase write permissions
   - Monitor webhook delivery in Stripe dashboard

### Debug Tools

1. **Stripe CLI**: Test webhooks locally
2. **Stripe Dashboard**: Monitor events and payments
3. **Firebase Console**: Check user data
4. **Server Logs**: Monitor backend errors

## Next Steps

1. **Implement the backend services**
2. **Create the frontend components**
3. **Set up Stripe webhooks**
4. **Test the complete flow**
5. **Deploy to production**
6. **Monitor and optimize**

This comprehensive guide provides everything needed to implement Stripe payments in your FXSentinel application. The system will handle free trials, subscription management, usage tracking, and payment processing while maintaining security and reliability.
