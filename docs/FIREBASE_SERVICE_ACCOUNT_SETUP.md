# Firebase Service Account Setup Guide

## Why You Need This

To retrieve user information from Firebase Authentication using the Admin SDK, you need a **Firebase Service Account Key**. This is a JSON file that gives your backend code permission to access Firebase services.

## Step-by-Step: Download Firebase Service Account Key

### Step 1: Go to Firebase Console

1. Open your browser and go to: https://console.firebase.google.com/
2. Select your project: **fxsentinel**

### Step 2: Navigate to Service Accounts

1. Click the **gear icon ⚙️** (top left, next to "Project Overview")
2. Click **"Project Settings"**
3. Click the **"Service Accounts"** tab

### Step 3: Generate Private Key

1. You'll see a section titled **"Firebase Admin SDK"**
2. Make sure **"Node.js"** is selected (the script works with Python too)
3. Click the button: **"Generate New Private Key"**
4. A dialog will appear warning you about keeping the key secure
5. Click **"Generate Key"**

### Step 4: Save the File

1. A JSON file will download to your computer
2. **Rename it** to: `firebase-service-account.json`
3. **Move it** to: `backend/firebase-service-account.json`

**Important**: The file should be in the `backend/` directory, at the same level as `app.py`.

### Step 5: Verify File Location

Your file structure should look like:
```
backend/
├── app.py
├── firebase-service-account.json  ← This file
├── requirements.txt
└── scripts/
    └── list_firebase_users.py
```

### Step 6: Test the Script

```bash
cd backend
python3 scripts/list_firebase_users.py
```

You should now see:
```
✅ Firebase Admin initialized with service account (project: fxsentinel)
📋 Fetching users from Firebase Authentication...
✅ Successfully retrieved X user(s)
```

---

## Security Best Practices

### ⚠️ Never Commit This File to Git

The service account key gives full access to your Firebase project. **Never commit it to version control.**

1. **Add to .gitignore**:
   ```bash
   echo "firebase-service-account.json" >> backend/.gitignore
   ```

2. **Verify it's ignored**:
   ```bash
   git status
   # Should NOT show firebase-service-account.json
   ```

### 🔒 Keep It Secure

- **Don't share** the file publicly
- **Don't email** it or upload it to cloud storage without encryption
- **Rotate keys** periodically (every 6-12 months)
- **Delete old keys** from Firebase Console when no longer needed

### 🌐 For Production/Deployment

When deploying to Railway, Vercel, or other platforms:

**Option 1: Upload as Secret File**
- Upload `firebase-service-account.json` as a secret/environment file
- The script will automatically detect it

**Option 2: Use Environment Variables**
- Some platforms allow uploading the JSON content as an environment variable
- Set `FIREBASE_SERVICE_ACCOUNT_JSON` with the full JSON content

**Option 3: Use Platform Credentials**
- On Google Cloud Platform (GCP), you can use Application Default Credentials
- No file needed if running on GCP

---

## Troubleshooting

### Error: "File not found"

**Problem**: The script can't find `firebase-service-account.json`

**Solution**:
1. Verify the file exists: `ls backend/firebase-service-account.json`
2. Check you're running from the correct directory
3. Verify the file name is exactly `firebase-service-account.json` (case-sensitive)

### Error: "Invalid credentials"

**Problem**: The JSON file is corrupted or invalid

**Solution**:
1. Re-download the key from Firebase Console
2. Make sure you copied the entire file (it should start with `{` and end with `}`)
3. Verify it's valid JSON (you can test with: `python3 -m json.tool firebase-service-account.json`)

### Error: "Permission denied"

**Problem**: The service account doesn't have the right permissions

**Solution**:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Verify the service account has "Firebase Authentication Admin" role
3. If needed, go to Google Cloud Console → IAM & Admin → IAM
4. Find your service account and ensure it has proper roles

### Error: "Project ID mismatch"

**Problem**: The service account is for a different Firebase project

**Solution**:
1. Check the `project_id` in the JSON file
2. It should be `"fxsentinel"` (or match your project)
3. If different, download the key from the correct project

---

## What's Inside the Service Account Key?

The JSON file contains:
- `project_id`: Your Firebase project ID
- `private_key`: Private key for authentication
- `client_email`: Service account email address
- Other authentication details

**Example structure**:
```json
{
  "type": "service_account",
  "project_id": "fxsentinel",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@fxsentinel.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

---

## Alternative: Using Application Default Credentials

If you're running on Google Cloud Platform or have `gcloud` CLI configured, you can use Application Default Credentials instead:

```bash
# Install gcloud CLI (if not installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set project
gcloud config set project fxsentinel
```

Then the script will use these credentials automatically (no JSON file needed).

---

## Next Steps

Once you have the service account key set up:

1. ✅ Test the script: `python3 backend/scripts/list_firebase_users.py`
2. ✅ View users in the terminal
3. ✅ Export to CSV if needed
4. ✅ Use the API endpoint: `GET /api/auth/users`

For more information, see: `docs/FIREBASE_USER_MANAGEMENT.md`
