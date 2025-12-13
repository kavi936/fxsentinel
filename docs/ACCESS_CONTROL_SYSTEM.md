# FXSentinel Access Control System

## Overview

The FXSentinel access control system ensures that only users with valid subscription status can access the dashboard and premium features. The system implements multiple layers of security to prevent unauthorized access.

## Access Control Layers

### 1. Route Protection (`ProtectedRoute.jsx`)
- **Location**: `src/components/ProtectedRoute.jsx`
- **Purpose**: Primary access control for protected routes
- **Protected Routes**: `/dashboard`, `/trial-welcome`
- **Logic**: Checks subscription status and redirects unauthorized users

### 2. Dashboard Security (`Dashboard.jsx`)
- **Location**: `src/components/Dashboard.jsx`
- **Purpose**: Additional security layer within the dashboard
- **Logic**: Double-checks subscription status on component mount
- **Action**: Redirects to trial-welcome if invalid subscription

### 3. Backend API Security (`stripe_service.py`)
- **Location**: `backend/services/stripe_service.py`
- **Purpose**: Validates subscription status on the server side
- **Endpoint**: `/api/subscription-status/<user_id>`
- **Logic**: Returns subscription data or default trial status

## Valid Subscription Statuses

### ✅ Allowed Access
- **`trial`**: Users on free trial (3 days, 15 analyses/day)
- **`active`**: Users with paid subscription (unlimited analyses)
- **`developer`**: Developer accounts (unlimited access)

### ❌ No Access
- **`expired`**: Trial expired, subscription cancelled
- **`cancelled`**: Subscription cancelled
- **`none`**: No subscription found

## User Flow

### New User Flow
1. **Signup** → `/auth-redirect`
2. **AuthRedirect** → Checks developer status
3. **If Developer** → `/dashboard`
4. **If Regular User** → `/trial-welcome`
5. **Trial Welcome** → User sees benefits and can start trial
6. **Dashboard** → Only after trial activation

### Existing User Flow
1. **Login** → `/auth-redirect`
2. **AuthRedirect** → Checks subscription status
3. **If Valid Subscription** → `/dashboard`
4. **If Invalid/Expired** → `/trial-welcome`

## Implementation Details

### Frontend Components

#### ProtectedRoute.jsx
```javascript
// Valid subscription statuses
const validStatuses = ['trial', 'active', 'developer'];

// Check access
const hasValidAccess = data.status === 'trial' || 
                      data.status === 'active' || 
                      data.status === 'developer';

// Redirect logic
if (!hasAccess) {
  return <Navigate to="/trial-welcome" replace />;
}
```

#### Dashboard.jsx
```javascript
// Additional security check
const validStatuses = ['trial', 'active', 'developer'];
if (!validStatuses.includes(data.status)) {
  navigate('/trial-welcome');
  return;
}
```

### Backend API

#### Subscription Status Endpoint
```python
@app.route('/api/subscription-status/<user_id>', methods=['GET'])
def get_subscription_status(user_id):
    # Check developer status first
    if email and is_developer_email(email):
        return {'status': 'developer', ...}
    
    # Check Firebase for user data
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        # Return default trial status for new users
        return {'status': 'trial', ...}
    
    # Return user's subscription status
    return {'status': user_data.get('subscription_status', 'trial'), ...}
```

## Security Features

### 1. Multiple Validation Layers
- **Route Level**: ProtectedRoute checks before rendering
- **Component Level**: Dashboard validates on mount
- **API Level**: Backend validates subscription status

### 2. Developer Access
- **Email Check**: `kavi.cf412@gmail.com` gets developer status
- **Bypass**: Developer users skip trial welcome
- **Unlimited**: Developer users have unlimited access

### 3. Error Handling
- **Graceful Fallbacks**: Returns trial status for new users
- **Network Errors**: Handles API failures gracefully
- **Invalid Data**: Validates response structure

### 4. User Experience
- **Clear Redirects**: Users know where they're going
- **Loading States**: Shows progress during checks
- **Error Messages**: Clear feedback for issues

## Testing

### Test Scripts
- `test_access_control_system.py`: Basic access control tests
- `test_complete_access_control.py`: Comprehensive system tests
- `test_servers_working.py`: Server connectivity tests

### Test Coverage
- ✅ New user access control
- ✅ Developer user access control
- ✅ Expired user restrictions
- ✅ Route protection
- ✅ API endpoint security
- ✅ Error handling
- ✅ Frontend proxy functionality

## Configuration

### Environment Variables
- `DEVELOPER_EMAILS`: List of developer email addresses
- `TRIAL_DAYS`: Number of trial days (default: 3)
- `TRIAL_LIMIT`: Daily analysis limit for trial users (default: 15)

### Firebase Configuration
- **Collection**: `users`
- **Fields**: `subscription_status`, `trial_end_date`, `daily_analysis_count`
- **Fallback**: Returns trial status if Firebase unavailable

## Monitoring

### Logging
- **Frontend**: Console logs for debugging
- **Backend**: Error logging for API issues
- **Access**: Tracks subscription status checks

### Metrics
- **Access Attempts**: Track unauthorized access attempts
- **Subscription Status**: Monitor user subscription distribution
- **Error Rates**: Track API failure rates

## Maintenance

### Regular Checks
1. **Test Access Control**: Run test scripts regularly
2. **Monitor Logs**: Check for access control errors
3. **Update Developer List**: Keep developer emails current
4. **Review Security**: Periodic security audits

### Updates
- **New Status Types**: Add to valid statuses list
- **Route Changes**: Update ProtectedRoute configuration
- **API Changes**: Update backend validation logic

## Summary

The FXSentinel access control system provides comprehensive protection for the dashboard and premium features. It implements multiple security layers, handles edge cases gracefully, and provides a smooth user experience while maintaining strict access control.

**Key Benefits:**
- ✅ Secure access to premium features
- ✅ Clear user flow for new and existing users
- ✅ Developer access for testing
- ✅ Graceful error handling
- ✅ Comprehensive testing coverage
- ✅ Easy maintenance and updates
