# Debugging User Tracking Issues

## Problem: New users not showing in OpenAI dashboard

If you've tested with a new user account but they're not appearing in the OpenAI usage dashboard, follow these debugging steps:

## Step 1: Check Backend Logs

When a user makes an AI analysis request, you should see these log messages:

### Expected Log Messages:

```
🔍 DEBUG: Token user info extracted: {'user_id': '...', 'user_email': '...', 'user_name': '...'}
👤 User info - ID: ..., Email: ..., Name: ...
👤👤👤 PASSING USER INFO TO ANALYZER: {'user_id': '...', 'user_email': '...', 'user_name': '...'}
👤 Tracking analysis for user: user@example.com
👤👤👤 OPENAI USER TRACKING: user@example.com 👤👤👤
✅✅✅ ADDING USER PARAMETER TO OPENAI: user@example.com ✅✅✅
🚀🚀🚀 OPENAI API CALL - Model: gpt-3.5-turbo, User: user@example.com 🚀🚀🚀
```

### If you see these instead:

```
❌❌❌ NO USER INFO TO PASS TO ANALYZER ❌❌❌
❌ user_id: None, user_email: None, user_name: None
❌❌❌ NOT ADDING USER PARAMETER TO OPENAI API CALL ❌❌❌
```

**This means user info is not being extracted properly.**

## Step 2: Check Frontend is Sending Token

### Check Browser Network Tab:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Make an AI analysis request
4. Find the request to `/api/enhanced-analysis/...`
5. Check Request Headers:
   - Should have: `Authorization: Bearer <token>`
   - Should have: `Content-Type: application/json`

### Check Request Body:

Should include:
```json
{
  "event": {...},
  "analysisType": "pre-event",
  "marketContext": {...},
  "user_id": "...",
  "user_email": "...",
  "user_name": "..."
}
```

## Step 3: Verify Token Extraction

The backend tries to extract user from token first, then falls back to request body.

### Check if token extraction works:

Look for this log:
```
👤 Extracted user from token: user@example.com
```

If you see:
```
⚠️ Could not extract user from token: ...
```

Possible causes:
- Token not being sent in Authorization header
- Token expired
- Token invalid
- Firebase Admin SDK not initialized

## Step 4: Check OpenAI API Call

The most important check - verify the `user` parameter is actually being sent to OpenAI.

### Look for these logs:

```
✅✅✅ ADDING USER PARAMETER TO OPENAI: user@example.com ✅✅✅
🚀🚀🚀 OPENAI API CALL - Model: gpt-3.5-turbo, User: user@example.com 🚀🚀🚀
```

If you see:
```
❌❌❌ NOT ADDING USER PARAMETER TO OPENAI API CALL ❌❌❌
```

Then the user parameter is NOT being sent to OpenAI, and usage won't be tracked per user.

## Step 5: Verify in OpenAI Dashboard

1. Go to https://platform.openai.com/usage
2. Wait a few minutes after making API calls (can take up to 5 minutes to appear)
3. Use the "Users" dropdown
4. You should see individual user emails/IDs

### If still only seeing your name:

- Check that the `user` parameter is actually being sent (Step 4)
- Verify the user email/ID is valid (not null/empty)
- Wait a bit longer - OpenAI dashboard updates can be delayed
- Check if you're using cached results (cached results don't make new API calls)

## Common Issues and Fixes

### Issue 1: Frontend not sending Authorization header

**Fix**: Check `src/components/Overview.jsx` - ensure `getIdToken()` is being called and token is added to headers.

### Issue 2: Token extraction failing silently

**Fix**: Check Firebase Admin SDK is initialized in `backend/app.py`. Look for:
```
✅ Firebase initialized successfully
```

### Issue 3: User info is None

**Fix**: 
- Check if `currentUser` exists in frontend
- Verify user is actually logged in
- Check if token is being sent correctly

### Issue 4: Cached results

**Note**: Cached analysis results don't make new OpenAI API calls, so they won't appear in usage dashboard. This is expected behavior.

## Testing Checklist

- [ ] Backend logs show user info being extracted
- [ ] Backend logs show user parameter being added to OpenAI API call
- [ ] Frontend is sending Authorization header
- [ ] Frontend is sending user info in request body
- [ ] Firebase Admin SDK is initialized
- [ ] User is actually logged in
- [ ] Made a fresh (non-cached) analysis request
- [ ] Waited 5+ minutes and checked OpenAI dashboard

## Quick Test Script

Run this to test token extraction:

```python
# In backend directory
from app import _extract_user_from_token
from flask import Flask, request

# You'll need to set up a test request with Authorization header
# Or test via actual API call with logged-in user
```

## Next Steps

If after checking all the above, users still aren't showing:

1. **Check OpenAI API response** - Add logging to see what OpenAI returns
2. **Verify user parameter format** - OpenAI expects string (email or user_id)
3. **Check for API errors** - Maybe OpenAI is rejecting the user parameter
4. **Test with direct API call** - Use curl/Postman to test with token

## Contact for Help

If issue persists, provide:
- Backend logs showing the analysis request
- Network tab screenshot showing request headers
- Any error messages
- OpenAI dashboard screenshot
