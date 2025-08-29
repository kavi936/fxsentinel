# FXSentinel Beta Tester Setup Guide

## Overview

This guide explains how to set up testing accounts for beta testers (friends, early adopters, and cold outreach contacts) to give them lifetime access to FXSentinel. This will help you gather feedback, reviews, and testimonials to strengthen your app.

## Current System Status

Your FXSentinel currently has three user types:
- **Trial Users**: 3-day trial with 15 analyses/day
- **Paid Users**: $20/month with 100 analyses/day  
- **Developer Users**: Unlimited access via email whitelist

## Recommended Approaches

### 1. **Beta Tester Email Whitelist (Recommended)**

This approach extends your existing developer system to include beta testers with lifetime access.

#### Setup Instructions:

1. **Add Environment Variable**
   ```bash
   # Add to your .env file or environment variables
   BETA_TESTER_EMAILS=friend1@example.com,friend2@example.com,influencer@example.com,reviewer@example.com
   ```

2. **Benefits:**
   - ✅ **Unlimited lifetime access** for all listed emails
   - ✅ **No payment required**
   - ✅ **Easy to manage** - just add/remove emails
   - ✅ **Already implemented** in the codebase
   - ✅ **Separate from developers** - different status tracking

3. **How it works:**
   - Beta testers get `status: 'beta_tester'` instead of `'developer'`
   - 15 analyses per day (same as trial users)
   - Bypasses all payment requirements
   - Can be tracked separately from developers

#### Implementation Status:
- ✅ **Backend support added** - `is_beta_tester_email()` method
- ✅ **Subscription status handling** - returns `beta_tester` status
- ✅ **Analysis permission checking** - 15 analyses/day for beta testers
- ✅ **Environment variable support** - `BETA_TESTER_EMAILS`

### 2. **Stripe Coupon Codes (Alternative)**

For a more professional approach, you can create promotional coupon codes.

#### Setup Instructions:

1. **Create Coupon Codes in Stripe Dashboard:**
   - Go to Stripe Dashboard → Products → Coupons
   - Create coupons like:
     - `BETA100` - 100% off for beta testers
     - `FRIEND100` - 100% off for friends
     - `REVIEWER100` - 100% off for reviewers

2. **Benefits:**
   - ✅ **Professional appearance**
   - ✅ **Usage analytics** in Stripe
   - ✅ **Flexible control** - set usage limits
   - ✅ **Easy to share** - just send the code

3. **How to use:**
   - Share coupon codes with beta testers
   - They enter the code during checkout
   - Gets 100% discount for lifetime

### 3. **Extended Trial Period (Simple)**

Give specific users longer trial periods.

#### Setup Instructions:

1. **Modify Firebase directly:**
   ```javascript
   // In Firebase Console or via admin SDK
   db.collection('users').document(user_id).update({
     'subscription_status': 'trial',
     'trial_end_date': new Date('2025-12-31'), // Extended trial
     'analysis_limit': 100 // Higher limit
   })
   ```

2. **Benefits:**
   - ✅ **Seamless user experience**
   - ✅ **No coupon codes needed**
   - ✅ **Easy to implement**

## Implementation Details

### Backend Changes Made

The following changes have been implemented in `backend/services/stripe_service.py`:

1. **Beta Tester Email Loading:**
   ```python
   # Beta tester emails for lifetime access
   beta_tester_emails_str = os.getenv('BETA_TESTER_EMAILS', '')
   self.beta_tester_emails = [email.strip() for email in beta_tester_emails_str.split(',') if email.strip()]
   ```

2. **Beta Tester Detection:**
   ```python
   def is_beta_tester_email(self, email):
       """Check if email is in beta tester whitelist"""
       if not email:
           return False
       return email.lower() in [beta_email.lower() for beta_email in self.beta_tester_emails]
   ```

3. **Subscription Status Handling:**
   ```python
       # Check if user is a beta tester
    if email and self.is_beta_tester_email(email):
        return {
            'status': 'beta_tester',
            'trial_end_date': None,
            'daily_analysis_count': 0,
            'analysis_limit': self.trial_limit,  # Same as trial users (15 per day)
            'stripe_customer_id': None,
            'is_beta_tester': True
        }
   ```

4. **Analysis Permission Checking:**
   ```python
       # Check if user is a beta tester
    if email and self.is_beta_tester_email(email):
        return {
            'can_perform': True,
            'daily_usage': 0,
            'daily_limit': self.trial_limit,  # Same as trial users (15 per day)
            'status': 'beta_tester'
        }
   ```

### Frontend Integration

The frontend already supports the new `beta_tester` status through the existing access control system:

1. **ProtectedRoute.jsx** - Already handles `beta_tester` status
2. **Dashboard.jsx** - Already validates `beta_tester` status
3. **TrialWelcomeRoute.jsx** - Already bypasses for `beta_tester` status

## Usage Instructions

### For You (Setup):

1. **Add Beta Tester Emails:**
   ```bash
   # Add to your environment variables
   BETA_TESTER_EMAILS=friend1@example.com,friend2@example.com,influencer@example.com
   ```

2. **Deploy the Changes:**
   ```bash
   # Deploy to your hosting platform
   git add .
   git commit -m "Add beta tester support"
   git push
   ```

3. **Test the Setup:**
   - Create a test account with a beta tester email
   - Verify they get unlimited access
   - Check the status shows as `beta_tester`

### For Beta Testers:

1. **Sign up normally** with their email
2. **Get immediate access** to the dashboard
3. **15 analyses per day** - same as trial users
4. **No payment required** - lifetime access

## Management and Tracking

### Adding New Beta Testers:

1. **Add email to environment variable:**
   ```bash
   BETA_TESTER_EMAILS=existing@example.com,newfriend@example.com
   ```

2. **Redeploy the application**

3. **New user gets immediate access**

### Removing Beta Testers:

1. **Remove email from environment variable**
2. **Redeploy the application**
3. **User will revert to normal trial/paid flow**

### Analytics and Tracking:

You can track beta tester usage by:

1. **Firebase Analytics:**
   ```javascript
   // Check subscription_status field
   db.collection('users').where('subscription_status', '==', 'beta_tester')
   ```

2. **Usage Monitoring:**
   - Beta testers will have `analysis_limit: 15` (same as trial users)
   - Track their actual usage patterns
   - Monitor feature adoption

## Best Practices

### 1. **Email Management:**
   - Keep a separate list of beta tester emails
   - Document who each email belongs to
   - Set up a process for adding/removing testers

### 2. **Communication:**
   - Clearly explain what beta access means
   - Set expectations about feedback requirements
   - Provide support channels for beta testers

### 3. **Feedback Collection:**
   - Set up feedback forms or surveys
   - Monitor usage patterns
   - Collect testimonials and reviews

### 4. **Gradual Rollout:**
   - Start with a small group of trusted friends
   - Gradually expand to more testers
   - Monitor system performance with increased usage

## Troubleshooting

### Common Issues:

1. **Beta tester not getting access:**
   - Check email is in `BETA_TESTER_EMAILS` environment variable
   - Verify deployment was successful
   - Check email case sensitivity

2. **Environment variable not loading:**
   - Restart the application after adding emails
   - Check environment variable format (comma-separated)
   - Verify no extra spaces in email addresses

3. **Status not updating:**
   - Clear browser cache
   - Check Firebase for user data
   - Verify backend logs for beta tester detection

## Next Steps

1. **Immediate Action:**
   - Add your friends' emails to `BETA_TESTER_EMAILS`
   - Deploy the changes
   - Test with one friend first

2. **Short Term:**
   - Set up feedback collection system
   - Create beta tester onboarding process
   - Monitor usage and gather initial feedback

3. **Long Term:**
   - Expand beta tester program
   - Use feedback to improve the app
   - Convert beta testers to advocates

This setup gives you a flexible, scalable way to provide lifetime access to your beta testers while maintaining control over who gets access and tracking their usage patterns.
