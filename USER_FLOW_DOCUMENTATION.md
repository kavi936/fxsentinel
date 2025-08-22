# FXSentinel User Flow Documentation

## Current User Journey

### **Current Flow (What's Happening Now):**
1. **Landing Page** → 2. **Login/Signup** → 3. **Trial Welcome Screen** → 4. **Dashboard**

### **Current Button Behavior:**
- **"Start Free Trial"**: Creates Stripe customer → Redirects to Dashboard
- **"Skip for Now"**: Directly redirects to Dashboard (no trial setup)

## **❌ Problems with Current Flow:**

1. **"Skip for Now" doesn't make sense** - Users should be on trial regardless
2. **No clear trial activation** - Users might not understand they're on trial
3. **Missing trial explanation** - Users don't know what they're getting
4. **No upgrade path** - How do users upgrade after trial?

## **✅ Proposed User Flow Options:**

### **Option 1: Automatic Trial (Recommended)**
```
Landing Page → Login/Signup → Dashboard (with trial status)
```

**Button Behavior:**
- **"Start Free Trial"**: Redirects to Dashboard (trial already active)
- **"Skip for Now"**: Redirects to Dashboard (trial already active)

**Benefits:**
- Simpler flow
- All users get trial automatically
- Less friction
- Clear trial status in dashboard

### **Option 2: Trial Welcome with Confirmation**
```
Landing Page → Login/Signup → Trial Welcome → Dashboard
```

**Button Behavior:**
- **"Start Free Trial"**: Confirms trial → Redirects to Dashboard
- **"Skip for Now"**: Shows trial benefits again → Must choose trial

**Benefits:**
- Users understand what they're getting
- Clear trial explanation
- No accidental skips

### **Option 3: Trial Welcome with Upgrade Option**
```
Landing Page → Login/Signup → Trial Welcome → Dashboard
```

**Button Behavior:**
- **"Start Free Trial"**: Activates trial → Redirects to Dashboard
- **"Upgrade Now"**: Goes to payment flow → Premium Dashboard

**Benefits:**
- Immediate upgrade option
- Higher conversion potential
- Clear value proposition

## **🤔 Questions to Clarify:**

1. **Should all users automatically get a trial?**
   - Yes: Simpler, less friction
   - No: More control, explicit consent

2. **What should "Skip for Now" do?**
   - Go to dashboard anyway (trial active)
   - Show trial benefits again
   - Go to limited dashboard
   - Something else?

3. **When should users see upgrade options?**
   - Immediately on trial welcome
   - Only in dashboard
   - When they hit usage limits
   - All of the above?

4. **What happens after trial expires?**
   - Block access until payment
   - Show limited features
   - Grace period
   - Automatic upgrade prompt?

## **🎯 Recommended Flow (Option 1):**

### **Step 1: User Signs Up**
- User creates account
- **Automatically gets 3-day trial**
- **Automatically gets 15 AI analyses/day**

### **Step 2: Trial Welcome Screen**
- **"Start Free Trial"**: Goes to Dashboard (trial already active)
- **"Skip for Now"**: Goes to Dashboard (trial already active)
- **Purpose**: Explain benefits, not activate trial

### **Step 3: Dashboard with Trial Status**
- Shows trial status in header
- Shows usage: "5/15 analyses used today"
- Shows upgrade button
- Shows trial countdown: "2 days remaining"

### **Step 4: Upgrade Flow**
- Upgrade button throughout dashboard
- Payment flow when clicked
- Immediate access to premium features

## **📋 Implementation Plan:**

### **Phase 1: Fix Trial Welcome**
- Remove "Skip for Now" button
- Change to "Get Started" or "Continue to Dashboard"
- Make trial activation automatic on signup

### **Phase 2: Dashboard Integration**
- Add trial status header
- Add usage tracking display
- Add upgrade buttons

### **Phase 3: Upgrade Flow**
- Create payment component
- Integrate with Stripe
- Handle subscription activation

## **✅ Final User Flow (Confirmed)**

### **Business Model:**
- **Sustainable business** - prevent cost overruns
- **Access control** - only trial/paid users can access dashboard
- **Automatic conversion** - trial users become paid after 3 days unless cancelled
- **Payment upfront** - users enter payment method before trial starts

### **User Journey:**
1. **Discovery** → Social media, referrals, mentors
2. **Landing Page** → User reads and decides to try
3. **Sign Up** → Email and credentials
4. **Trial Welcome Screen** → **MUST agree to 3-day trial with payment method**
5. **Dashboard Access** → Only after agreeing to trial
6. **Automatic Conversion** → $20 charged after 3 days unless cancelled

### **Key Requirements:**

#### **1. Trial Agreement & Terms:**
- **Clear trial explanation** - "This is a trial and you are heavily limited on usage"
- **Usage limits** - 15 AI analyses/day during trial
- **Upgrade option** - "Upgrade to increase limit"
- **Terms & Conditions** - User must accept before proceeding
- **Payment method required** - Users enter payment info before trial starts

#### **2. Cancellation:**
- **Stripe cancellation** - Users can cancel through Stripe dashboard
- **No manual cancellation** - Only through Stripe's system
- **Clear instructions** - Show users how to cancel in Stripe

#### **3. Payment Flow:**
- **Payment method upfront** - Required before trial starts
- **Automatic charging** - $20 charged after 3 days if not cancelled
- **No manual billing** - Fully automated through Stripe

#### **4. Access Control:**
- **Dashboard protection** - No access without valid trial/paid account
- **Redirect to signup** - Non-authenticated users go to signup page
- **Developer access** - Special accounts for developers/testers (bypass payment)

### **Button Behavior:**
- **"Start Free Trial"** → Accept terms → Enter payment → Dashboard
- **"Skip for Now"** → Redirect to landing page
- **"Upgrade Now"** → Payment flow for immediate premium

### **Terms & Conditions (Draft):**
```
By starting your free trial, you agree to:

1. **Trial Period**: 3-day free trial with limited usage (15 AI analyses/day)
2. **Automatic Billing**: $20/month will be charged after trial unless cancelled
3. **Usage Limits**: Trial users are heavily limited; upgrade for full access
4. **Cancellation**: Cancel anytime through your Stripe dashboard
5. **No Refunds**: No refunds for partial months
6. **Service Availability**: Service provided "as is" with no guarantees
7. **Data Usage**: Your data is used to provide AI analysis services
8. **Account Termination**: We reserve the right to terminate accounts for abuse

You must enter a valid payment method to start your trial. You will not be charged during the trial period.
```

### **Implementation Plan:**

#### **Phase 1: Trial Welcome Screen**
- Add terms & conditions acceptance
- Add payment method collection
- Fix "Skip for Now" button to redirect to landing page
- Add clear trial limitations explanation

#### **Phase 2: Payment Integration**
- Integrate Stripe payment method collection
- Set up automatic subscription after trial
- Configure webhook for trial expiration

#### **Phase 3: Access Control**
- Protect dashboard routes
- Add developer/test accounts (bypass payment)
- Redirect unauthorized users to signup

#### **Phase 4: Cancellation Flow**
- Add cancellation instructions
- Link to Stripe dashboard
- Handle subscription status updates

### **Developer/Test Accounts:**
- **Special user role** - "developer" or "tester"
- **Bypass payment** - No payment method required
- **Full access** - Unlimited usage for testing
- **Environment variable** - `DEVELOPER_EMAILS` for whitelist 


