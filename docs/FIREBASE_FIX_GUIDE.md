# Firebase Firestore API Fix Guide

## 🚨 **Current Issue**

The alerts system is working perfectly, but there's a Firebase Firestore API error preventing user preferences from being stored:

```
ERROR: 403 Cloud Firestore API has not been used in project fxsentinel before or it is disabled.
```

## 🔍 **Root Cause**

The Firebase Firestore API needs to be enabled in your Google Cloud Console before the alerts system can store user preferences.

## ✅ **What's Working (Despite the Error)**

- ✅ Telegram bot setup and connection
- ✅ Alert detection and triggering
- ✅ API endpoints responding
- ✅ Alert sending functionality
- ✅ AI analysis integration

## 🚀 **Step-by-Step Fix**

### **Step 1: Access Google Cloud Console**

1. **Go to**: https://console.cloud.google.com/
2. **Select your project**: `fxsentinel`
3. **Make sure you're in the right project** (check the project selector at the top)

### **Step 2: Enable Firestore API**

1. **Navigate to APIs & Services**:
   - Click the hamburger menu (☰) in the top left
   - Go to "APIs & Services" → "Library"

2. **Search for Firestore**:
   - In the search bar, type: `Cloud Firestore API`
   - Click on "Cloud Firestore API" from the results

3. **Enable the API**:
   - Click the "Enable" button
   - Wait for the API to be enabled (usually takes 1-2 minutes)

### **Step 3: Verify API is Enabled**

1. **Check API Status**:
   - Go to "APIs & Services" → "Enabled APIs"
   - You should see "Cloud Firestore API" in the list
   - Status should show "Enabled"

### **Step 4: Test the Fix**

1. **Restart your backend server**:
   ```bash
   cd backend
   pkill -f "python3 app.py"
   python3 app.py &
   ```

2. **Test the alerts settings endpoint**:
   ```bash
   curl "http://localhost:5001/api/alerts/settings?userId=test_user_123"
   ```

3. **Expected response**:
   ```json
   {
     "success": true,
     "settings": {
       "impact_levels": {"high": true, "medium": true, "low": false},
       "alert_types": {"preNews": true, "postNews": true, "liveNews": true},
       "currency_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
       "quiet_hours": {"enabled": false, "start": "22:00", "end": "06:00", "timezone": "UTC"}
     }
   }
   ```

## 🔧 **Alternative Solutions (If API Enable Doesn't Work)**

### **Option 1: Check Firebase Console**

1. **Go to**: https://console.firebase.google.com/
2. **Select your project**: `fxsentinel`
3. **Go to Firestore Database**:
   - Click "Firestore Database" in the left sidebar
   - If you see a "Create Database" button, click it
   - Choose "Start in test mode" for development

### **Option 2: Verify Service Account Permissions**

1. **Check service account role**:
   - Go to Google Cloud Console → IAM & Admin → IAM
   - Find your service account: `firebase-adminsdk-fbsvc@fxsentinel.iam.gserviceaccount.com`
   - Make sure it has "Cloud Datastore User" or "Firebase Admin" role

### **Option 3: Create New Service Account (If Needed)**

1. **Go to**: Google Cloud Console → IAM & Admin → Service Accounts
2. **Create new service account**:
   - Click "Create Service Account"
   - Name: `fxsentinel-alerts-admin`
   - Description: `Service account for FXSentinel alerts system`
3. **Assign roles**:
   - "Firebase Admin"
   - "Cloud Datastore User"
4. **Create and download new key**:
   - Click "Create Key" → JSON
   - Download and replace the existing key file

## 🧪 **Testing After Fix**

### **Test 1: User Settings**
```bash
# Test getting user settings
curl "http://localhost:5001/api/alerts/settings?userId=test_user_123"

# Test updating user settings
curl -X PUT http://localhost:5001/api/alerts/settings \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test_user_123",
    "settings": {
      "impact_levels": {"high": true, "medium": false, "low": false},
      "alert_types": {"preNews": true, "postNews": true, "liveNews": true},
      "currency_pairs": ["EUR/USD", "USD/JPY"]
    }
  }'
```

### **Test 2: Alert History**
```bash
# Test alert history endpoint
curl "http://localhost:5001/api/alerts/history?userId=test_user_123"
```

### **Test 3: Complete System Test**
```bash
# Run the full test suite
python3 test_alerts_system.py
```

## 🎯 **Expected Results After Fix**

### **✅ What Should Work:**
- ✅ User alert preferences saved to Firebase
- ✅ Alert history stored and retrieved
- ✅ No more "SERVICE_DISABLED" errors
- ✅ Complete end-to-end functionality

### **📊 Success Indicators:**
- API responses include actual user data
- No Firebase errors in server logs
- Test script shows all components passing
- User preferences persist between sessions

## 🚨 **Troubleshooting**

### **If API Enable Doesn't Work:**

1. **Check project billing**:
   - Ensure your Google Cloud project has billing enabled
   - Firestore requires an active billing account

2. **Wait for propagation**:
   - API changes can take 5-10 minutes to propagate
   - Try again after waiting

3. **Check service account permissions**:
   - Verify the service account has proper roles
   - Consider creating a new service account

4. **Alternative: Use Firebase Realtime Database**:
   - If Firestore continues to have issues
   - We can modify the code to use Realtime Database instead

## 📞 **Need Help?**

If you encounter any issues:

1. **Check the error message** in the server logs
2. **Verify you're in the correct Google Cloud project**
3. **Ensure billing is enabled** for the project
4. **Wait 5-10 minutes** after enabling the API

## 🎉 **After the Fix**

Once Firebase is working:

1. **Test the complete user flow** from frontend to backend
2. **Verify alert preferences** are saving correctly
3. **Test alert delivery** to Telegram
4. **Deploy to production** on Railway

The alerts system will be fully functional with persistent user data!
