# AI Analysis Usage System - Comprehensive Analysis

## Overview

The FXSentinel platform implements a freemium model for AI Analysis usage tracking, managing user quotas based on subscription tiers (Free, Premium, Developer). This document provides a comprehensive analysis of how the system tracks, enforces, and manages AI Analysis usage across different user types.

---

## System Architecture

### Core Components

1. **StripeService** (`backend/services/stripe_service.py`)
   - Central service managing subscription status and usage tracking
   - Handles Firebase Firestore integration for user data persistence
   - Implements tier-based usage limits and counter management

2. **API Endpoints** (`backend/app.py`)
   - `/api/check-analysis-permission/<user_id>` - Permission checking and usage increment
   - `/api/enhanced-analysis/<news_id>` - AI analysis execution endpoint
   - `/api/subscription-status/<user_id>` - Subscription status retrieval

3. **Frontend Components**
   - `ProfilePopup.jsx` - Displays usage statistics and limits
   - `Dashboard.jsx` - Fetches subscription status
   - `Overview.jsx` - Triggers AI analysis requests

---

## User Tiers & Limits

### 1. Free Tier
- **Limit Type**: Monthly
- **Limit Value**: 15 analyses per month (configurable via `FREE_ANALYSIS_LIMIT` env var)
- **Counter Field**: `monthly_analysis_count`
- **Reset Logic**: Resets on the 1st of each month (`last_monthly_reset`)

### 2. Premium Tier
- **Limit Type**: Daily
- **Limit Value**: 50 analyses per day (configurable via `PREMIUM_ANALYSIS_LIMIT` env var)
- **Counter Field**: `daily_analysis_count`
- **Reset Logic**: Resets daily (`last_daily_reset`)

### 3. Developer Tier
- **Limit Type**: Unlimited
- **Limit Value**: 999,999 (effectively unlimited)
- **Counter Field**: None (no tracking)
- **Identification**: Email-based whitelist (`DEVELOPER_EMAILS` env var)

---

## Usage Tracking Flow

### Step 1: Permission Check
**Endpoint**: `GET /api/check-analysis-permission/<user_id>?email=<user_email>`

**Process**:
1. Checks if user is a developer (bypasses all limits)
2. Retrieves user document from Firestore
3. Resets counters if needed (daily for premium, monthly for free)
4. Checks current usage against tier-specific limits
5. **Increments usage counter** if `can_perform` is `True` and user is not a developer
6. Returns permission status with usage data

**Response Structure**:
```json
{
  "can_perform": true/false,
  "daily_usage": 0,
  "monthly_usage": 0,
  "daily_limit": 50 or null,
  "monthly_limit": 15 or null,
  "status": "free" | "premium" | "developer"
}
```

### Step 2: AI Analysis Execution
**Endpoint**: `POST /api/enhanced-analysis/<news_id>`

**Current Implementation**:
- **Note**: This endpoint does NOT currently check permissions before execution
- It performs the AI analysis directly without usage validation
- This creates a potential security/usage tracking gap

**Process**:
1. Validates event data
2. Fetches live market data
3. Creates GPT market context
4. Executes GPT AI analysis
5. Returns analysis results

---

## Database Schema (Firestore)

### User Document Structure
```javascript
{
  // Subscription Management
  subscription_status: "free" | "premium" | "developer",
  stripe_customer_id: string,
  subscription_id: string,
  
  // Usage Tracking - Free Tier
  monthly_analysis_count: number,
  last_monthly_reset: date,  // First day of current month
  
  // Usage Tracking - Premium Tier
  daily_analysis_count: number,
  last_daily_reset: date,     // Current date
  
  // Timestamps
  account_created: timestamp,
  upgraded_to_premium_at: timestamp,
  downgraded_to_free_at: timestamp,
  webhook_processed_at: timestamp
}
```

---

## Counter Reset Logic

### Daily Reset (Premium Users)
- **Trigger**: When `last_daily_reset != today`
- **Action**: Sets `daily_analysis_count = 0` and updates `last_daily_reset = today`
- **Location**: `can_perform_analysis()` method in `StripeService`

### Monthly Reset (Free Users)
- **Trigger**: When `last_monthly_reset != first_day_of_current_month`
- **Action**: Sets `monthly_analysis_count = 0` and updates `last_monthly_reset = current_month_start`
- **Location**: `can_perform_analysis()` method in `StripeService`

---

## Usage Increment Logic

### Method: `increment_analysis_count(user_id, email=None)`

**Process**:
1. Skips increment for developers
2. Checks Firebase availability
3. Retrieves user document
4. Determines subscription status
5. Increments appropriate counter:
   - Premium: `daily_analysis_count` (Firestore Increment)
   - Free: `monthly_analysis_count` (Firestore Increment)

**Important**: Uses Firestore's `Increment()` operation for atomic counter updates, preventing race conditions.

---

## Frontend Integration

### Usage Display (`ProfilePopup.jsx`)
- Fetches usage data via `/api/check-analysis-permission`
- Displays progress bars for monthly (free) or daily (premium) limits
- Shows warnings when approaching limits (3 remaining for free, 5 remaining for premium)
- Triggers notifications for limit reached/warning states

### Analysis Trigger (`Overview.jsx`)
- **Current Issue**: Directly calls `/api/enhanced-analysis` without permission check
- Does not verify usage limits before requesting analysis
- Relies on backend enforcement (which is currently missing)

---

## Security & Enforcement Gaps

### Identified Issues

1. **Missing Permission Check in Analysis Endpoint**
   - `/api/enhanced-analysis` does not validate permissions before execution
   - Users could potentially bypass usage limits by calling this endpoint directly
   - **Recommendation**: Add permission check at the start of `get_enhanced_analysis()`

2. **Frontend Permission Check Timing**
   - Frontend calls `check-analysis-permission` separately from analysis request
   - No guarantee that permission check happens before analysis execution
   - **Recommendation**: Integrate permission check into analysis endpoint or enforce client-side blocking

3. **Race Condition Potential**
   - Permission check increments counter, but analysis might fail
   - Counter increment happens before analysis completion
   - **Recommendation**: Consider incrementing only after successful analysis, or implement rollback mechanism

---

## Configuration

### Environment Variables
```bash
# Usage Limits
FREE_ANALYSIS_LIMIT=15          # Monthly limit for free tier
PREMIUM_ANALYSIS_LIMIT=50       # Daily limit for premium tier
PREMIUM_MONTHLY_PRICE=1499      # Price in cents ($14.99)

# Stripe Configuration
STRIPE_SECRET_KEY=sk_...
STRIPE_PRODUCT_ID=prod_...
STRIPE_PRICE_ID=price_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Developer Access
DEVELOPER_EMAILS=dev1@example.com,dev2@example.com
```

---

## Webhook Integration

### Stripe Webhooks
The system handles Stripe webhook events to update subscription status:

1. **`customer.subscription.created`**
   - Upgrades user to premium
   - Resets daily counter
   - Sets `subscription_status = 'premium'`

2. **`customer.subscription.updated`**
   - Updates subscription status based on Stripe status
   - Handles downgrades (premium → free)
   - Resets counters appropriately

3. **`customer.subscription.deleted`**
   - Downgrades user to free tier
   - Resets monthly counter
   - Sets `subscription_status = 'free'`

4. **`invoice.payment_succeeded`**
   - Confirms premium status
   - Updates payment timestamps

5. **`invoice.payment_failed`**
   - Sets status to `past_due`
   - Tracks payment failure

---

## Error Handling

### Firebase Unavailable
- System defaults to allowing analysis if Firebase is unavailable
- Returns free tier status with default limits
- Logs warnings but continues operation

### User Document Missing
- Returns `no_subscription` status
- `can_perform` set to `False`
- Usage limits set to 0

### Developer Email Check
- Case-insensitive email matching
- Bypasses all usage tracking
- Returns unlimited limits (999,999)

---

## Testing

### Test Files
- `tests/test_usage_tracking.py` - Usage limit enforcement tests
- `tests/test_payment_flow.py` - Subscription flow tests
- `tests/test_developer_access.py` - Developer bypass tests

### Test Scenarios Covered
1. Free tier monthly limit enforcement
2. Premium tier daily limit enforcement
3. Counter reset logic (daily/monthly)
4. Developer bypass functionality
5. Subscription status transitions

---

## Recommendations

### Immediate Improvements

1. **Add Permission Check to Analysis Endpoint**
   ```python
   @app.route('/api/enhanced-analysis/<news_id>', methods=['GET', 'POST'])
   def get_enhanced_analysis(news_id):
       # Get user_id from request (headers or body)
       user_id = request.headers.get('X-User-ID') or request.json.get('user_id')
       email = request.headers.get('X-User-Email') or request.json.get('email')
       
       # Check permissions before proceeding
       if user_id:
           permission = stripe_service.can_perform_analysis(user_id, email)
           if not permission.get('can_perform'):
               return jsonify({
                   'error': 'Usage limit reached',
                   'status': permission.get('status'),
                   'daily_usage': permission.get('daily_usage'),
                   'monthly_usage': permission.get('monthly_usage'),
                   'daily_limit': permission.get('daily_limit'),
                   'monthly_limit': permission.get('monthly_limit')
               }), 403
       
       # Continue with analysis...
   ```

2. **Move Counter Increment to Analysis Completion**
   - Only increment after successful analysis
   - Prevents counting failed analyses
   - More accurate usage tracking

3. **Add Usage Tracking to Analysis Endpoint**
   - Track which users are making analysis requests
   - Log analysis requests for auditing
   - Better analytics and monitoring

### Long-term Improvements

1. **Implement Usage Analytics Dashboard**
   - Track usage patterns per user
   - Identify heavy users
   - Optimize limits based on usage data

2. **Add Rate Limiting**
   - Prevent abuse beyond usage limits
   - Implement per-user rate limits
   - Protect against API abuse

3. **Usage Notifications**
   - Email notifications when approaching limits
   - In-app notifications for limit reached
   - Upgrade prompts at strategic usage points

---

## Summary

The AI Analysis usage system implements a tier-based freemium model with:
- **Free tier**: 15 analyses/month
- **Premium tier**: 50 analyses/day
- **Developer tier**: Unlimited access

The system tracks usage via Firestore counters that reset automatically (daily for premium, monthly for free). However, there's a critical gap: the analysis endpoint doesn't enforce permissions, potentially allowing users to bypass limits. The recommended fix is to add permission checks directly in the analysis endpoint before execution.
