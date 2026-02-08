# AI Usage Tracking Guide

## Overview

The AI Usage Tracking system tracks which users are using AI analysis features, allowing you to:
1. **Identify active users** - See who's actually using the app
2. **Track usage patterns** - Understand how users interact with AI features
3. **Contact users for feedback** - Reach out to active users for product feedback
4. **Monitor OpenAI costs** - See usage per user in OpenAI dashboard

## How It Works

### 1. User Tracking Flow

```
User Request → Backend extracts user from Firebase token → 
AI Analyzer receives user_info → OpenAI API call includes user parameter →
Usage logged to Firestore → Available via API endpoints
```

### 2. What Gets Tracked

- **User identification**: user_id, user_email, user_name
- **Analysis details**: analysis_type, event_id, model_used
- **Cost tracking**: cost_estimate per analysis
- **Cache status**: Whether result was cached (no OpenAI cost)
- **Timestamps**: When each analysis was performed

### 3. Storage

- **Firestore Collection**: `ai_usage_logs` - Detailed log of every analysis
- **Firestore Collection**: `users` - User documents with aggregated stats:
  - `total_ai_analyses`: Total count
  - `last_ai_usage`: Last usage timestamp
  - `last_ai_usage_type`: Type of last analysis
  - `first_ai_usage`: First usage timestamp
  - `daily_ai_usage.{date}`: Daily usage counts

## Testing

### Quick Test

1. **Run the test script**:
   ```bash
   python scripts/test_ai_usage_tracking.py
   ```

2. **Make some AI analysis requests**:
   - Log in as different users
   - Generate AI analyses from the dashboard
   - Check that each user's usage appears separately

3. **Check OpenAI Dashboard**:
   - Go to https://platform.openai.com/usage
   - Use the "Users" dropdown
   - You should see individual users, not all under one name

### Verify Tracking is Working

1. **Check backend logs** for messages like:
   ```
   👤 Tracking OpenAI usage for user: user@example.com
   ✅ Tracked AI usage for user: user@example.com (pre-event)
   ```

2. **Check Firestore**:
   - Open Firebase Console
   - Navigate to Firestore Database
   - Check `ai_usage_logs` collection for new entries
   - Check `users` collection for updated stats

## Viewing Usage Statistics

### Option 1: Browser Console Script

1. Open your app in browser
2. Log in as admin/developer
3. Open browser console (F12)
4. Load the script:
   ```javascript
   // Copy contents of scripts/view_ai_usage_stats.js into console
   ```
5. Run:
   ```javascript
   viewAIUsageStats(7, 1)  // Last 7 days, min 1 analysis
   ```

### Option 2: API Endpoint (from frontend)

```javascript
// Get active users (last 7 days, min 1 analysis)
const token = await auth.currentUser.getIdToken();
const response = await fetch('http://localhost:5001/api/ai-usage/stats?days=7&min_analyses=1', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const data = await response.json();
console.log('Active users:', data.active_users);
```

### Option 3: Python Script

```python
import requests
from firebase_admin import auth

# Get your Firebase token (you'll need to implement this)
token = get_firebase_token()  # Your implementation

response = requests.get(
    'http://localhost:5001/api/ai-usage/stats?days=7&min_analyses=1',
    headers={'Authorization': f'Bearer {token}'}
)
data = response.json()
print(f"Active users: {data['active_users_count']}")
for user in data['active_users']:
    print(f"- {user['user_email']}: {user['total_analyses']} analyses")
```

## API Endpoints

### GET `/api/ai-usage/stats`

Get list of active users who have used AI features.

**Query Parameters**:
- `days` (default: 7): Number of days to look back
- `min_analyses` (default: 1): Minimum number of analyses to be considered active

**Response**:
```json
{
    "success": true,
    "period_days": 7,
    "min_analyses": 1,
    "active_users_count": 5,
    "active_users": [
        {
            "user_id": "abc123",
            "user_email": "user@example.com",
            "user_name": "John Doe",
            "total_analyses": 15,
            "last_usage": "2026-02-08T10:30:00Z",
            "last_usage_type": "pre-event"
        }
    ],
    "timestamp": "2026-02-08T15:00:00Z"
}
```

### GET `/api/ai-usage/user/<user_id>`

Get detailed usage statistics for a specific user.

**Response**:
```json
{
    "success": true,
    "stats": {
        "user_id": "abc123",
        "user_email": "user@example.com",
        "user_name": "John Doe",
        "total_analyses": 15,
        "last_usage": "2026-02-08T10:30:00Z",
        "last_usage_type": "pre-event",
        "first_usage": "2026-02-01T08:00:00Z",
        "recent_logs": [...]
    }
}
```

## Contacting Users for Feedback

### Method 1: Export Email List

1. Get active users via API
2. Extract email addresses
3. Send feedback request email

### Method 2: Firebase Console

1. Go to Firebase Console → Authentication → Users
2. Find users by email from usage stats
3. Use Firebase Cloud Messaging to send notifications

### Method 3: In-App Notification

Add a feedback request component that shows to active users:
- Show after N analyses
- Show to users who used app in last X days
- Link to feedback form

## Troubleshooting

### Issue: All usage shows under my name in OpenAI dashboard

**Solution**: 
- Verify frontend is sending Authorization header
- Check backend logs for "👤 Tracking OpenAI usage for user" messages
- Ensure `_extract_user_from_token()` is working

### Issue: No usage data in Firestore

**Solution**:
- Check Firebase credentials are configured
- Verify `ai_usage_tracker.firebase_available` is True
- Check backend logs for tracking errors

### Issue: API endpoint returns 403 Forbidden

**Solution**:
- Ensure your email is in `DEVELOPER_EMAILS` env variable
- Verify Firebase token is being sent correctly
- Check token hasn't expired

## Next Steps

1. **Monitor usage** - Check stats weekly to see active users
2. **Identify power users** - Users with high analysis counts
3. **Reach out for feedback** - Contact active users
4. **Track improvements** - Monitor if usage increases after changes
