# Firebase Realtime Database Rules Fix
**Date**: January 2, 2026  
**Issue**: 401 Unauthorized errors for `telegram_mappings` and `alert_deduplication` paths

## Current Rules (Incomplete)

```json
{
  "rules": {
    "news_cache": {
      ".read": true,
      ".write": true
    },
    "alerts": {
      ".read": true,
      ".write": true
    },
    "alert_history": {
      ".read": true,
      ".write": true
    }
  }
}
```

## Problem

The current rules only allow access to:
- `news_cache`
- `alerts`
- `alert_history`

But the system also needs access to:
- `telegram_mappings` - for user lookup by Telegram chat ID
- `alert_deduplication` - for deduplication state (content hashes and alert records)

## Updated Rules (Complete)

```json
{
  "rules": {
    "news_cache": {
      ".read": true,
      ".write": true
    },
    "alerts": {
      ".read": true,
      ".write": true
    },
    "alert_history": {
      ".read": true,
      ".write": true
    },
    "telegram_mappings": {
      ".read": true,
      ".write": true
    },
    "alert_deduplication": {
      ".read": true,
      ".write": true
    }
  }
}
```

## How to Update

1. Go to Firebase Console: https://console.firebase.google.com
2. Select your project: `fxsentinel`
3. Go to **Realtime Database** → **Rules** tab
4. Replace the rules with the updated JSON above
5. Click **Publish**

## What This Fixes

1. **`telegram_mappings` access**:
   - Allows the system to look up users by Telegram chat ID
   - Fixes "Not Connected" status issues
   - Enables automatic mapping creation

2. **`alert_deduplication` access**:
   - Allows global content hash deduplication
   - Prevents duplicate alerts from being sent
   - Stores per-user alert deduplication state

## Security Note

These rules allow public read/write access. For production, you may want to add authentication:

```json
{
  "rules": {
    "news_cache": {
      ".read": true,
      ".write": "auth != null"
    },
    "alerts": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "alert_history": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "telegram_mappings": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "alert_deduplication": {
      ".read": "auth != null",
      ".write": "auth != null"
    }
  }
}
```

However, since your backend uses service account credentials, the current open rules should work for server-side access.

