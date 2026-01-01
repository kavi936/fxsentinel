# Firebase Console Checklist
**Date**: January 1, 2026  
**Purpose**: Verify Firebase setup for alert system

---

## Quick Answer

**If alerts are working**: ✅ **No manual updates needed** - Firebase is configured correctly in production.

**If `/status` still doesn't work**: Check the items below.

---

## What to Check in Firebase Console

### 1. Database Rules (Most Important)

**Path**: Firebase Console → Realtime Database → Rules

**Current Status**: Getting 401 errors locally (expected if rules are restrictive)

**What to Verify**:
- Rules should allow read/write to:
  - `telegram_mappings`
  - `alerts/users`
  - `alerts/users/{userId}/settings`
  - `news_cache`
  - `alert_deduplication`

**Recommended Rules** (for production with authentication):
```json
{
  "rules": {
    "telegram_mappings": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "alerts": {
      ".read": "auth != null",
      ".write": "auth != null",
      "users": {
        "$userId": {
          ".read": "auth != null || $userId == auth.uid",
          ".write": "auth != null || $userId == auth.uid"
        }
      }
    },
    "news_cache": {
      ".read": true,
      ".write": "auth != null"
    },
    "alert_deduplication": {
      ".read": "auth != null",
      ".write": "auth != null"
    }
  }
}
```

**Note**: If you're using service account credentials in production, these rules might be different. The 401 errors locally are expected if you don't have credentials set up locally.

---

### 2. Telegram Mapping

**Path**: Realtime Database → `telegram_mappings/8008493413`

**What to Check**:
- Does this path exist?
- Does it have `user_id` field?
- Is `user_id` correct?

**If Missing**: Create it with:
```json
{
  "user_id": "c109c597ebf725f8424269b152d97e5e",
  "chat_id": "8008493413",
  "username": "K7IV_1",
  "status": "active",
  "created_at": "2026-01-01T00:00:00"
}
```

**Note**: The `user_id` here should be your actual Firebase Auth user_id (not hashed). If you're using the hashed version, that's also OK - the system handles both.

---

### 3. User Settings

**Path**: Realtime Database → `alerts/users/c109c597ebf725f8424269b152d97e5e/settings`

**What to Check**:
- Does this path exist?
- Does it have `channels.telegram.enabled = true`?
- Does `channels.telegram.chatId = "8008493413"`?

**Expected Structure**:
```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "chatId": "8008493413",
      "username": "K7IV_1"
    },
    "email": {
      "enabled": false,
      "address": ""
    }
  },
  "preferences": {
    "impactLevels": {
      "high": true,
      "medium": true,
      "low": false
    },
    "alertTypes": {
      "liveNews": true,
      "preNews": true,
      "postNews": true,
      "technicalAnalysis": false
    },
    "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
    "quietHours": {
      "enabled": false,
      "start": "22:00",
      "end": "06:00",
      "timezone": "UTC"
    }
  }
}
```

**If Missing or Incorrect**: Update it with the structure above.

---

### 4. Telegram Chat ID (Top Level)

**Path**: Realtime Database → `alerts/users/c109c597ebf725f8424269b152d97e5e/telegram_chat_id`

**What to Check**:
- Does this path exist?
- Is the value `"8008493413"`?

**If Missing**: Create it with value: `"8008493413"`

**Note**: This is optional but helps with faster lookups.

---

## How to Find Your Actual User ID

If you need to find your original (non-hashed) user_id:

1. **Firebase Console → Authentication**:
   - Look for your user account
   - Copy the User UID (this is your user_id)

2. **Your App's Authentication**:
   - Check browser localStorage for `userId` or `user_id`
   - Check your app's user profile/settings

3. **If Using Hashed IDs**:
   - The system works with hashed IDs too
   - Current hashed ID: `c109c597ebf725f8424269b152d97e5e`
   - This is fine to use in the mapping

---

## Verification Steps

### Step 1: Check if Alerts Work
✅ **You're receiving alerts** - This means:
- Firebase connection is working in production
- User settings are accessible
- Alert system is functional

### Step 2: Check `/status` Command
- Send `/status` in Telegram
- If it works: ✅ No Firebase updates needed
- If it shows error: Check items 2-4 above

### Step 3: Run Verification Script
```bash
python3 scripts/verify_firebase_setup.py
```

This will tell you exactly what's missing.

---

## Common Issues

### Issue: 401 Unauthorized Errors (Local)
**Cause**: Firebase rules require authentication, but local scripts don't have credentials

**Solution**: 
- ✅ **This is expected** - Production has proper credentials
- Local scripts will show 401, but production works fine
- No action needed if alerts are working

### Issue: `/status` Shows "Error retrieving settings"
**Cause**: Settings path doesn't exist or user_id mapping is wrong

**Solution**:
1. Check if `alerts/users/{hashed_user_id}/settings` exists
2. Verify `telegram_mappings/{chat_id}` has correct `user_id`
3. Update if needed (see sections 2-3 above)

### Issue: Settings Exist But `/status` Still Fails
**Cause**: Settings structure might be wrong or user_id mismatch

**Solution**:
1. Verify settings structure matches expected format (section 3)
2. Check that `channels.telegram.chatId` matches your chat_id
3. Ensure `channels.telegram.enabled = true`

---

## Summary

### ✅ If Alerts Are Working:
- **No manual Firebase updates needed**
- System is configured correctly
- `/status` should work (if it doesn't, it's a code issue, not Firebase)

### ⚠️ If `/status` Doesn't Work:
1. Check `telegram_mappings/8008493413` exists
2. Check `alerts/users/c109c597ebf725f8424269b152d97e5e/settings` exists
3. Verify settings structure is correct
4. Check Firebase database rules allow access

### 🔧 Quick Fix:
If you want to ensure everything is set up correctly, you can manually create/verify:

1. **Mapping**: `telegram_mappings/8008493413` → `{"user_id": "c109c597ebf725f8424269b152d97e5e", ...}`
2. **Settings**: `alerts/users/c109c597ebf725f8424269b152d97e5e/settings` → (see structure above)

But since alerts are working, these likely already exist in production.

---

## Recommendation

**Since alerts are working**: ✅ **No action needed**

The 401 errors you see locally are expected (Firebase rules require auth). Production has proper credentials and is working.

If `/status` still doesn't work after the code fixes, then check Firebase Console for the items above.

