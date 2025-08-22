# FXSentinel Payment Setup - Quick Start Guide

## 🚀 Get Your Payment System Running in 5 Minutes

### **Step 1: Set Up Stripe Account**

1. **Create Stripe Account** (if you don't have one)
   - Go to [stripe.com](https://stripe.com)
   - Sign up for a free account
   - Complete account verification

2. **Get Your API Keys**
   - Go to Stripe Dashboard → Developers → API Keys
   - Copy your **Publishable Key** (starts with `pk_test_`)
   - Copy your **Secret Key** (starts with `sk_test_`)

3. **Create Product and Price**
   - Go to Stripe Dashboard → Products
   - Click "Add Product"
   - Name: `FXSentinel Premium`
   - Description: `Unlimited AI analysis for forex trading`
   - Pricing: `$20/month`
   - Billing: `Monthly`
   - Copy the **Product ID** (starts with `prod_`)
   - Copy the **Price ID** (starts with `price_`)

4. **Set Up Webhook**
   - Go to Stripe Dashboard → Developers → Webhooks
   - Click "Add endpoint"
   - URL: `https://your-domain.com/webhook/stripe` (update with your domain)
   - Events to listen for:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
   - Copy the **Webhook Secret** (starts with `whsec_`)

### **Step 2: Update Environment Variables**

Add these to your `.env` file:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PRODUCT_ID=prod_your_product_id_here
STRIPE_PRICE_ID=price_your_price_id_here

# Subscription Configuration
TRIAL_DAYS=3
TRIAL_ANALYSIS_LIMIT=15
PAID_ANALYSIS_LIMIT=100
MONTHLY_PRICE=2000

# Frontend Stripe Key (safe to expose)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

### **Step 3: Test the Payment Flow**

1. **Start your backend server:**
   ```bash
   cd backend
   python3 app.py
   ```

2. **Start your frontend:**
   ```bash
   npm run dev
   ```

3. **Run the payment test:**
   ```bash
   python3 test_payment_flow.py
   ```

### **Step 4: Test the User Flow**

1. **Open your app** in the browser
2. **Sign up** for a new account
3. **Complete the trial welcome flow**
4. **Enter test card details:**
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
5. **Verify dashboard access**

## 🔧 Troubleshooting

### **Common Issues:**

#### **1. "Stripe has not loaded yet"**
- Check `VITE_STRIPE_PUBLISHABLE_KEY` is set correctly
- Verify the key starts with `pk_test_` or `pk_live_`

#### **2. "Payment method setup failed"**
- Check `STRIPE_SECRET_KEY` is set correctly
- Verify the key starts with `sk_test_` or `sk_live_`

#### **3. "Webhook verification failed"**
- Check `STRIPE_WEBHOOK_SECRET` is set correctly
- Verify webhook URL is accessible

#### **4. "Customer creation failed"**
- Check Firebase connection
- Verify user authentication

### **Test Card Numbers:**

Use these test cards for testing:

- **Success:** `4242 4242 4242 4242`
- **Declined:** `4000 0000 0000 0002`
- **Insufficient Funds:** `4000 0000 0000 9995`
- **Expired Card:** `4000 0000 0000 0069`

## 📋 Verification Checklist

- [ ] Stripe account created
- [ ] API keys obtained
- [ ] Product and price created
- [ ] Webhook configured
- [ ] Environment variables set
- [ ] Backend server running
- [ ] Frontend server running
- [ ] Payment test passing
- [ ] User flow working
- [ ] Trial activation successful

## 🎯 Next Steps

Once the basic flow is working:

1. **Test with real users** (friends/family)
2. **Monitor Stripe dashboard** for payments
3. **Set up production keys** when ready
4. **Configure webhook for production**
5. **Add subscription management UI**

## 🆘 Need Help?

If you encounter issues:

1. **Check the logs** in your terminal
2. **Verify environment variables** are set correctly
3. **Test with the provided test script**
4. **Check Stripe dashboard** for errors
5. **Review the full implementation guide** (`PAYMENT_IMPLEMENTATION_GUIDE.md`)

## 💡 Pro Tips

- **Always use test keys** during development
- **Test the complete flow** before going live
- **Monitor webhook delivery** in Stripe dashboard
- **Keep your secret keys secure** (never commit to git)
- **Use environment variables** for all sensitive data

Your payment system should now be ready to accept real payments! 🎉
