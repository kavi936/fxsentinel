# FXSentinel Payment Implementation Guide

## Overview

This guide covers the complete payment implementation for FXSentinel, including the user flow, technical implementation, and testing procedures.

## User Flow Summary

### **Complete User Journey:**
1. **Landing Page** → User discovers FXSentinel
2. **Sign Up** → User creates account with email/password
3. **Trial Welcome Screen** → User sees trial benefits and terms
4. **Payment Setup** → User enters payment method (no charge during trial)
5. **Dashboard Access** → User gets 3-day trial with 15 analyses/day
6. **Automatic Billing** → $20 charged after 3 days unless cancelled
7. **Upgrade Options** → User can upgrade anytime during trial

### **Key Business Rules:**
- **3-day free trial** with 15 AI analyses per day
- **Payment method required** before trial starts (no charge during trial)
- **$20/month** automatic billing after trial
- **100 AI analyses per day** for paid subscribers
- **Cancellation** through Stripe dashboard only

## Technical Implementation

### **Backend Components**

#### 1. Stripe Service (`backend/services/stripe_service.py`)
```python
class StripeService:
    def __init__(self):
        # Configuration from environment variables
        self.trial_days = 3
        self.trial_limit = 15
        self.paid_limit = 100
        self.monthly_price = 2000  # $20.00 in cents
        
    def create_customer(self, user_id, email, name)
    def create_trial_subscription(self, customer_id)
    def setup_payment_method(self, customer_id, payment_method_id)
    def get_subscription_status(self, user_id)
    def can_perform_analysis(self, user_id)
    def increment_analysis_count(self, user_id)
    def handle_webhook(self, payload, sig_header)
```

#### 2. API Endpoints (`backend/app.py`)
```python
# Customer Management
POST /api/create-customer
GET /api/subscription-status/<user_id>

# Payment Processing
POST /api/create-payment-intent
POST /api/setup-trial-subscription
POST /api/upgrade-subscription

# Usage Tracking
GET /api/check-analysis-permission/<user_id>

# Webhook Handling
POST /webhook/stripe
```

#### 3. Database Schema (Firebase Firestore)
```javascript
// users/{userId}
{
  email: string,
  displayName: string,
  createdAt: timestamp,
  stripe_customer_id: string,
  subscription_status: 'trial' | 'active' | 'expired' | 'cancelled',
  trial_start_date: timestamp,
  trial_end_date: timestamp,
  daily_analysis_count: number,
  last_analysis_reset: date,
  subscription_id: string,
  current_period_end: timestamp
}
```

### **Frontend Components**

#### 1. Trial Welcome Screen (`src/components/TrialWelcome.jsx`)
- Terms and conditions acceptance
- Payment method collection
- Trial activation flow
- Upgrade options

#### 2. Subscription Status Component (`src/components/SubscriptionStatus.jsx`)
- Real-time subscription status
- Usage tracking display
- Upgrade prompts
- Trial countdown

#### 3. Stripe Integration (`src/App.jsx`)
```jsx
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);
```

## Environment Configuration

### **Required Environment Variables**
```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PRODUCT_ID=prod_SuHsXyARgMiS3e
STRIPE_PRICE_ID=price_1RyTIYJNDWyJv8IpeKw3dzRB

# Subscription Configuration
TRIAL_DAYS=3
TRIAL_ANALYSIS_LIMIT=15
PAID_ANALYSIS_LIMIT=100
MONTHLY_PRICE=2000

# Frontend Stripe Key (safe to expose)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

## Payment Flow Implementation

### **Step 1: User Signup**
```javascript
// User creates account normally
// No payment required at this stage
```

### **Step 2: Trial Welcome Screen**
```javascript
// User sees trial benefits and terms
// Must accept terms and conditions
// Clicks "Start Free Trial"
```

### **Step 3: Payment Method Collection**
```javascript
// Create Stripe customer
const customer = await fetch('/api/create-customer', {
  method: 'POST',
  body: JSON.stringify({
    user_id: currentUser.uid,
    email: currentUser.email,
    name: currentUser.displayName
  })
});

// Create setup intent
const setupIntent = await fetch('/api/create-payment-intent', {
  method: 'POST',
  body: JSON.stringify({ customer_id: customer.id })
});

// Collect payment method (no charge)
const { setupIntent, error } = await stripe.confirmCardSetup(
  client_secret,
  { payment_method: { card: elements.getElement(CardElement) } }
);
```

### **Step 4: Trial Subscription Setup**
```javascript
// Setup trial subscription with payment method
const trial = await fetch('/api/setup-trial-subscription', {
  method: 'POST',
  body: JSON.stringify({
    user_id: currentUser.uid,
    customer_id: customer.id,
    payment_method_id: setupIntent.payment_method
  })
});
```

### **Step 5: Dashboard Access**
```javascript
// User gets access to dashboard with trial status
// 15 AI analyses per day limit
// Trial countdown displayed
```

## Usage Tracking Implementation

### **Analysis Permission Check**
```python
def can_perform_analysis(self, user_id):
    """Check if user can perform an AI analysis"""
    # Get user data from Firebase
    user_data = self.db.collection('users').document(user_id).get().to_dict()
    
    # Check trial status
    if user_data.get('subscription_status') == 'trial':
        trial_end = user_data.get('trial_end_date')
        if datetime.now() > trial_end:
            # Trial expired
            return False
    
    # Check daily limit
    limit = self.get_analysis_limit(user_data)
    current_count = user_data.get('daily_analysis_count', 0)
    
    return current_count < limit
```

### **Usage Increment**
```python
def increment_analysis_count(self, user_id):
    """Increment the daily analysis count"""
    user_ref = self.db.collection('users').document(user_id)
    user_ref.update({
        'daily_analysis_count': firestore.Increment(1)
    })
```

## Webhook Handling

### **Stripe Webhook Events**
```python
def handle_webhook(self, payload, sig_header):
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
```

### **Webhook Endpoint Configuration**
```python
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    stripe_service.handle_webhook(payload, sig_header)
    return jsonify({'success': True}), 200
```

## Testing Procedures

### **1. Environment Test**
```bash
python3 test_payment_flow.py
```

### **2. Backend API Test**
```bash
# Test customer creation
curl -X POST http://localhost:5001/api/create-customer \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","email":"test@example.com","name":"Test User"}'

# Test subscription status
curl http://localhost:5001/api/subscription-status/test_user

# Test analysis permission
curl http://localhost:5001/api/check-analysis-permission/test_user
```

### **3. Frontend Flow Test**
1. Start the development server
2. Navigate to signup page
3. Create a test account
4. Complete trial welcome flow
5. Verify dashboard access
6. Test usage tracking

### **4. Stripe Dashboard Verification**
1. Check customer creation in Stripe dashboard
2. Verify subscription setup
3. Test webhook delivery
4. Verify payment method attachment

## Security Considerations

### **1. Payment Method Security**
- Never store full card details
- Use Stripe Elements for secure input
- Validate payment methods server-side

### **2. Webhook Security**
- Verify webhook signatures
- Use HTTPS for webhook endpoints
- Validate event data

### **3. Access Control**
- Protect dashboard routes
- Validate user permissions
- Rate limit API endpoints

### **4. Data Protection**
- Encrypt sensitive data
- Use secure environment variables
- Implement proper error handling

## Deployment Checklist

### **Production Environment**
- [ ] Set production Stripe keys
- [ ] Configure webhook endpoints
- [ ] Set up SSL certificates
- [ ] Configure Firebase security rules
- [ ] Set up monitoring and logging

### **Testing Environment**
- [ ] Use Stripe test keys
- [ ] Test webhook delivery
- [ ] Verify payment flows
- [ ] Test subscription management
- [ ] Validate usage tracking

### **Monitoring**
- [ ] Set up error tracking
- [ ] Monitor webhook failures
- [ ] Track payment success rates
- [ ] Monitor usage patterns
- [ ] Set up alerts for issues

## Troubleshooting

### **Common Issues**

#### 1. Payment Method Setup Fails
- Check Stripe API keys
- Verify webhook configuration
- Check network connectivity

#### 2. Trial Not Activating
- Verify Firebase connection
- Check user document creation
- Validate trial dates

#### 3. Usage Tracking Issues
- Check daily reset logic
- Verify Firebase updates
- Validate permission checks

#### 4. Webhook Failures
- Check webhook endpoint URL
- Verify signature validation
- Check event handling logic

### **Debug Commands**
```bash
# Check environment variables
python3 -c "import os; print([k for k in os.environ if 'STRIPE' in k])"

# Test Firebase connection
python3 -c "from firebase_admin import firestore; print('Firebase OK')"

# Test Stripe connection
python3 -c "import stripe; stripe.api_key='test'; print('Stripe OK')"
```

## Next Steps

### **Immediate Actions**
1. Set up Stripe account and get API keys
2. Configure environment variables
3. Test the payment flow
4. Deploy to staging environment

### **Future Enhancements**
1. Add subscription management UI
2. Implement usage analytics
3. Add payment method management
4. Create admin dashboard
5. Add billing history

### **Monitoring and Maintenance**
1. Set up automated testing
2. Monitor payment success rates
3. Track user conversion rates
4. Optimize pricing strategy
5. Improve user experience

This implementation provides a complete, secure, and scalable payment system for FXSentinel that follows best practices and industry standards.
