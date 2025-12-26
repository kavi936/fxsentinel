# Firebase Checklist - What and Where to Check

## Overview

Your app uses **Firebase Realtime Database** (not Firestore) for persistent storage. The 401 Unauthorized errors indicate an authentication/authorization issue.

---

## 1. Firebase Console - Project Settings

### Where to Check:
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (likely `fxsentinel` or similar)
3. Click the gear icon ⚙️ → **Project Settings**

### What to Check:

#### A. Project ID
- **Location**: Project Settings → General tab
- **What to verify**: Note your **Project ID** (e.g., `fxsentinel-default-rtdb`)
- **Why**: This is used to construct the database URL

#### B. Realtime Database URL
- **Location**: Project Settings → General tab → Your apps section
- **What to verify**: Find the **Realtime Database URL**
- **Format**: `https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com`
- **Example**: `https://fxsentinel-default-rtdb.firebaseio.com`

---

## 2. Firebase Realtime Database - Database Rules

### Where to Check:
1. Firebase Console → Your project
2. Left sidebar → **Realtime Database**
3. Click **Rules** tab

### What to Check:

#### Current Rules (Likely Issue)
Your rules might look like this (restrictive):
```json
{
  "rules": {
    ".read": "auth != null",
    ".write": "auth != null"
  }
}
```

**Problem**: These rules require authentication, but your app is making unauthenticated requests.

#### Required Rules (For Your Use Case)
Since your code uses REST API without authentication tokens, you need:

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

**OR** (if you want to be more secure but still allow unauthenticated access):

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
    "$other": {
      ".read": false,
      ".write": false
    }
  }
}
```

**Action**: Update the rules and click **Publish**

---

## 3. Railway Environment Variables

### Where to Check:
1. Railway Dashboard → Your project
2. Select your service (main app or worker)
3. Go to **Variables** tab

### What to Check:

#### Required Variables:
- `FIREBASE_PROJECT_ID` - Should match your Firebase project ID
- `FIREBASE_REALTIME_URL` - Should be your Realtime Database URL

#### Example Values:
```
FIREBASE_PROJECT_ID=fxsentinel
FIREBASE_REALTIME_URL=https://fxsentinel-default-rtdb.firebaseio.com
```

**Action**: 
1. Verify these variables exist
2. Verify they match your Firebase project
3. If missing, add them

---

## 4. Firebase Realtime Database - Data Structure

### Where to Check:
1. Firebase Console → Your project
2. Left sidebar → **Realtime Database**
3. Click **Data** tab

### What to Check:

#### Expected Structure:
Your app writes to these **exact paths**:
- `news_cache/current` - Current news cache (where 401 errors occur)
- `news_cache/history` - News history
- `alerts/users/{user_id}/settings` - User alert settings
- `alert_history/{alert_id}` - Alert history

**The 401 error is happening at**: `news_cache/current`

**Action**: 
1. Check if these paths exist
2. If they don't exist, the first write should create them
3. If you see 401 errors in the data, it means writes are failing

---

## 5. Firebase Realtime Database - Location/Region

### Where to Check:
1. Firebase Console → Your project
2. Left sidebar → **Realtime Database**
3. Check the database location

### What to Check:
- **Location**: Should be set (e.g., `us-central1`, `europe-west1`)
- **Why**: If database doesn't exist, you need to create it first

**Action**: If no database exists:
1. Click **Create Database**
2. Choose location (closest to your Railway deployment)
3. Start in **test mode** (allows read/write) or set custom rules

---

## 6. Test Firebase Connection

### Quick Test:
You can test if Firebase is accessible by checking the URL directly:

```bash
# Replace YOUR-PROJECT-ID with your actual project ID
# Test read access (should return data or null, not 401)
curl https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/news_cache/current.json

# Expected results:
# - 401 Unauthorized = Database rules are blocking access (MOST LIKELY ISSUE)
# - 404 Not Found = Path doesn't exist (but connection works, rules allow access)
# - 200 OK with data = Working correctly!
# - 200 OK with null = Working, but no data yet
```

**Example** (if your project is `fxsentinel`):
```bash
curl https://fxsentinel-default-rtdb.firebaseio.com/news_cache/current.json
```

---

## Most Likely Issue

Based on the 401 errors, the **most likely problem is Database Rules**.

### Quick Fix:
1. Go to Firebase Console → Realtime Database → Rules
2. Change rules to allow read/write for your paths:

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

3. Click **Publish**
4. Test again

---

## Security Note

⚠️ **Warning**: The rules above allow **anyone** to read/write. This is fine for:
- Development/testing
- Internal tools
- If you add authentication later

For production, consider:
- Adding authentication tokens
- Using Firebase Admin SDK with service account
- Restricting rules to specific paths
- Adding rate limiting

---

## Summary Checklist

- [ ] Firebase Project ID matches `FIREBASE_PROJECT_ID` in Railway
- [ ] Firebase Realtime Database URL matches `FIREBASE_REALTIME_URL` in Railway
- [ ] Database Rules allow read/write for `news_cache`, `alerts`, `alert_history`
- [ ] Realtime Database exists and is created
- [ ] Test curl command returns data (not 401)

---

## If Still Not Working

1. **Check Railway Logs**: Look for the exact Firebase URL being used
2. **Check Firebase Console**: Look for failed requests in the Realtime Database usage tab
3. **Verify Environment Variables**: Make sure they're set in Railway (not just locally)
4. **Check Database Location**: Make sure it's accessible from Railway's region

