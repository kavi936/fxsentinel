# Firebase User Script Setup Guide

## Quick Fix for "Project ID Required" Error

If you see the error: `A project ID is required to access the auth service`, use one of these solutions:

### Option 1: Set Environment Variable (Easiest)

```bash
export FIREBASE_PROJECT_ID=fxsentinel
cd backend
python3 scripts/list_firebase_users.py
```

### Option 2: Add to .env File

Create or edit `backend/.env` and add:

```bash
FIREBASE_PROJECT_ID=fxsentinel
```

Then run:
```bash
cd backend
python3 scripts/list_firebase_users.py
```

### Option 3: Use Service Account Key (Most Reliable) ⭐ RECOMMENDED

**This is the proper way to authenticate with Firebase Admin SDK.**

1. **Download Service Account Key**:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project (`fxsentinel`)
   - Click gear icon ⚙️ → Project Settings
   - Go to "Service Accounts" tab
   - Click "Generate New Private Key"
   - Save the JSON file

2. **Place the file**:
   ```bash
   # Move/rename the downloaded file to:
   backend/firebase-service-account.json
   ```

3. **Run the script**:
   ```bash
   cd backend
   python3 scripts/list_firebase_users.py
   ```

**📖 Detailed instructions**: See `docs/FIREBASE_SERVICE_ACCOUNT_SETUP.md` for step-by-step guide with screenshots.

### Option 4: One-Line Command

```bash
FIREBASE_PROJECT_ID=fxsentinel python3 backend/scripts/list_firebase_users.py
```

---

## Verification

After running the script, you should see:
```
✅ Firebase Admin initialized with service account (project: fxsentinel)
# OR
✅ Firebase Admin initialized with default credentials (project: fxsentinel)

📋 Fetching users from Firebase Authentication...
✅ Successfully retrieved X user(s)
```

---

## Troubleshooting

### Still Getting "Project ID Required"?

1. **Check your project ID**:
   - Your project ID is `fxsentinel` (from `src/config/firebase.js`)
   - Verify in Firebase Console → Project Settings

2. **Verify environment variable**:
   ```bash
   echo $FIREBASE_PROJECT_ID
   # Should output: fxsentinel
   ```

3. **Check service account permissions**:
   - Service account needs "Firebase Authentication Admin" role
   - Go to Firebase Console → Project Settings → Service Accounts

4. **Try explicit project ID**:
   ```bash
   export GOOGLE_CLOUD_PROJECT=fxsentinel
   export FIREBASE_PROJECT_ID=fxsentinel
   python3 backend/scripts/list_firebase_users.py
   ```

---

## For Production/Deployment

If deploying to Railway, GCP, or similar platforms:

1. **Set environment variable** in your platform's dashboard:
   - Variable: `FIREBASE_PROJECT_ID`
   - Value: `fxsentinel`

2. **Or use service account**:
   - Upload `firebase-service-account.json` as a secret/environment file
   - The script will automatically detect and use it
