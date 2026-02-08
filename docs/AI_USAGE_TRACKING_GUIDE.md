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
User Request (with Authorization: Bearer <Firebase ID token>) →
Backend extracts user from token (preferred) or request body →
user_info passed to GPT analyzer →
OpenAI API call includes "user" parameter (email or uid) →
Usage appears in OpenAI Usage dashboard under "Users" dropdown →
Usage also logged to Firestore (ai_usage_logs + users) →
List users via GET /api/ai-usage/stats (admin only)
```

**Important**: The backend **prefers the Firebase token** over the request body for user identity (token is verified; body can be spoofed). Ensure the frontend sends `Authorization: Bearer <idToken>` so the OpenAI dashboard shows per-user usage.

### 2. Where AI Analysis Is Used (all covered for user tracking)

| Entry point | Route | Frontend | Analyzer | User from token/body | OpenAI `user` + Firestore |
|-------------|-------|----------|----------|----------------------|---------------------------|
| **Economic calendar** | `POST /api/enhanced-analysis/<news_id>` | Overview.jsx | GPTAIAnalyzer | ✅ Token preferred, then body | ✅ Yes |
| **Live news (dashboard)** | `GET /api/analysis/<news_id>` | LiveNewsFeed.jsx | MVPNewsAnalyzer | ✅ Token only (GET has no body) | ✅ Yes |
| Calendar fallback (basic) | `GET /api/analysis/<id>` | Overview.jsx | MVP / basic | ✅ Token only | ✅ Yes (if MVP GPT path) |

- **Economic calendar**: User is extracted in `get_enhanced_analysis` (token then body), passed to `gpt_ai_analyzer.analyze_macro_event(..., user_info=user_info)`. Redundant Firestore tracking at API layer.
- **Live news**: User is extracted in `generate_news_analysis` via `_extract_user_from_token()`, passed to `mvp_news_analyzer.analyze_news(..., user_info=token_user_info)`. MVP adds OpenAI `user` and calls `ai_usage_tracker.track_analysis_usage` when GPT is used.
- Both frontends send `Authorization: Bearer <idToken>` when the user is logged in.

### 3. What Gets Tracked

- **User identification**: user_id, user_email, user_name
- **Analysis details**: analysis_type (e.g. pre-event, post-event, news), event_id, model_used
- **Cost tracking**: cost_estimate per analysis
- **Cache status**: Whether result was cached (no OpenAI cost)
- **Timestamps**: When each analysis was performed

### 4. Storage

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

2. **Make some AI analysis requests** (both entry points):
   - Log in as different users
   - **Economic calendar**: click "Analyze" on an event to trigger `/api/enhanced-analysis`
   - **Live news**: click "Analyze" on a news item to trigger `/api/analysis`
   - Check that each user's usage appears separately in Firestore and in the OpenAI Usage dashboard

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

## Getting Users for Feedback (Quick Reference)

1. **Set `DEVELOPER_EMAILS`** in backend `.env` to your admin email (comma-separated for multiple).
2. **Call the API** as a logged-in admin:
   - `GET /api/ai-usage/stats?days=30&min_analyses=1`
   - Send header: `Authorization: Bearer <your Firebase ID token>`
3. **Response** includes `active_users[]` with `user_email`, `user_name`, `total_analyses`, `last_usage`. Use these emails to reach out for feedback.
4. **OpenAI dashboard**: Go to https://platform.openai.com/usage and use the **Users** dropdown to see usage per user (same identifiers you pass as the `user` parameter).

## Contacting Users for Feedback

### Method 1: Export Email List

1. Get active users via API (see above)
2. Extract `user_email` from `active_users`
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

**Causes and fixes**:
- **CORS**: Backend must allow `Authorization` in preflight. The app uses `CORS(..., allow_headers=["Content-Type", "Authorization"])`. If you added custom OPTIONS handlers elsewhere, ensure they include `Authorization` in `Access-Control-Allow-Headers`.
- **Token not sent**: In DevTools → Network, check the request to `/api/enhanced-analysis/...` has header `Authorization: Bearer <token>`. Frontend gets the token via `currentUser.getIdToken()` and adds it to the fetch headers.
- **Token extraction failing**: Backend logs will show `⚠️ Could not extract user from token: ...`. Common causes: Firebase Admin not initialized, wrong project, or expired/invalid token. Ensure `firebase-service-account.json` (or env) is set and Firebase is initialized at startup.
- **User from token**: Backend prefers token over request body. If token is valid, you should see `👤 Extracted user from token: <email or uid>` and then `✅✅✅ ADDING USER PARAMETER TO OPENAI: ...` in logs.

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
