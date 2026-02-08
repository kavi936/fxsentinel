# GTM/GA4 Tracking Testing Guide

> **Purpose**: Test the complete signup conversion tracking flow before pushing to production  
> **Date**: February 2025

---

## 🎯 Testing Overview

This guide helps you verify that:
1. ✅ Google signup conversion tracking works
2. ✅ Email signup conversion tracking works (already working)
3. ✅ UTM parameters persist through redirects
4. ✅ Signups vs logins are properly distinguished
5. ✅ Events fire correctly in dataLayer
6. ✅ GTM receives events (if GTM Preview Mode is enabled)

---

## 📋 Pre-Testing Checklist

### 1. Start Development Servers

```bash
# Option 1: Use the startup script
bash deployment/start_servers.sh

# Option 2: Start manually
# Terminal 1 - Backend
cd backend
python3 app.py

# Terminal 2 - Frontend
npm run dev
```

**Expected Result:**
- Frontend: http://localhost:5173
- Backend: http://localhost:5001

### 2. Open Browser Developer Tools

**Chrome/Edge:**
- Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
- Go to **Console** tab
- Go to **Application** tab → **Storage** → **Session Storage** → `http://localhost:5173`

**Firefox:**
- Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
- Go to **Console** tab
- Go to **Storage** tab → **Session Storage** → `http://localhost:5173`

### 3. Enable GTM Preview Mode (Optional)

If you want to test GTM integration:
1. Go to [tagmanager.google.com](https://tagmanager.google.com)
2. Select your container: **GTM-M64QPF8Z**
3. Click **Preview** button
4. Enter your URL: `http://localhost:5173`
5. Click **Connect**

---

## 🧪 Test Cases

### Test 1: UTM Parameter Persistence

**Goal**: Verify UTM parameters are captured and persisted

**Steps:**
1. Clear sessionStorage:
   ```javascript
   // Run in browser console
   sessionStorage.clear();
   ```

2. Navigate to signup page with UTM params:
   ```
   http://localhost:5173/signup?utm_source=test&utm_medium=social&utm_campaign=testing
   ```

3. Check console logs:
   - Look for: `📊 Analytics: UTM params persisted`
   - Should see UTM parameters logged

4. Check sessionStorage:
   ```javascript
   // Run in browser console
   JSON.parse(sessionStorage.getItem('fxsentinel_utm_params'))
   ```
   **Expected Result:**
   ```json
   {
     "utm_source": "test",
     "utm_medium": "social",
     "utm_campaign": "testing",
     "utm_content": "none",
     "utm_term": "none",
     "referrer": "..."
   }
   ```

**✅ Pass Criteria:**
- UTM params appear in console log
- UTM params stored in sessionStorage
- Params match URL parameters

---

### Test 2: Email Signup Conversion Tracking

**Goal**: Verify email signup fires conversion event

**Steps:**
1. Navigate to signup page:
   ```
   http://localhost:5173/signup?utm_source=email_test&utm_medium=test
   ```

2. Fill out signup form:
   - First Name: `Test`
   - Last Name: `User`
   - Email: `test+email@example.com` (use a unique email)
   - Password: `Test123456!`
   - Confirm Password: `Test123456!`
   - Check Terms checkbox

3. Click **Create Account**

4. Watch console logs:
   - Look for: `📊 Analytics: Funnel step tracked` with `signup_completion`
   - Look for: `📊 Analytics: Conversion tracked` with `conversion_type: "signup"`

5. Check dataLayer (in console):
   ```javascript
   // Run in browser console after signup
   window.dataLayer
   ```
   **Expected Result:**
   - Should see events with `event: "funnel_step"` and `funnel_step: "signup_completion"`
   - Should see events with `event: "conversion"` and `conversion_type: "signup"`
   - UTM parameters should be included: `utm_source: "email_test"`

6. Check sessionStorage still has UTM params:
   ```javascript
   JSON.parse(sessionStorage.getItem('fxsentinel_utm_params'))
   ```
   **Expected Result:** UTM params still present after redirect

**✅ Pass Criteria:**
- Console shows conversion tracking logs
- dataLayer contains conversion events
- UTM parameters included in events
- UTM params persist after redirect

---

### Test 3: Google Signup Conversion Tracking (New User)

**Goal**: Verify Google signup fires conversion event for NEW users only

**Steps:**
1. **Important**: Use a Google account that has NEVER signed up before, OR delete the user from Firebase Console first

2. Navigate to signup page with UTM params:
   ```
   http://localhost:5173/signup?utm_source=google_test&utm_medium=social&utm_campaign=test_signup
   ```

3. Click **Continue with Google**

4. Complete Google OAuth flow:
   - Select Google account
   - Grant permissions
   - Popup should close

5. Watch console logs:
   - Look for: `📊 Analytics: Funnel step tracked` with `signup_completion`
   - Look for: `📊 Analytics: Conversion tracked` with `conversion_type: "signup"`
   - Should see: `method: "google"` or `provider: "google.com"`

6. Check dataLayer:
   ```javascript
   // Run in browser console after signup
   window.dataLayer.filter(e => e.event === 'conversion' || e.event === 'funnel_step')
   ```
   **Expected Result:**
   - Should see conversion events
   - Should include `utm_source: "google_test"`
   - Should include `method: "google"` or `provider: "google.com"`

7. Verify you're redirected to `/auth-redirect` then `/dashboard`

**✅ Pass Criteria:**
- Console shows conversion tracking logs
- dataLayer contains conversion events
- UTM parameters included
- Only fires for NEW users (not returning logins)

---

### Test 4: Google Login (Existing User) - No Conversion

**Goal**: Verify returning users do NOT trigger conversion events

**Steps:**
1. **Important**: Use the SAME Google account you just signed up with in Test 3

2. Log out (if logged in):
   - Go to dashboard
   - Click logout

3. Navigate to login page:
   ```
   http://localhost:5173/login?utm_source=google_test&utm_medium=social
   ```

4. Click **Continue with Google**

5. Complete Google OAuth flow with the SAME account

6. Watch console logs:
   - Should NOT see: `📊 Analytics: Conversion tracked`
   - Should NOT see: `signup_completion` funnel step
   - Should see: `📊 Analytics: Funnel step tracked` with `auth_redirect` (this is OK)

7. Check dataLayer:
   ```javascript
   // Run in browser console after login
   window.dataLayer.filter(e => e.event === 'conversion' || e.funnel_step === 'signup_completion')
   ```
   **Expected Result:**
   - Should be EMPTY or only contain old events from previous tests
   - Should NOT contain new conversion events

**✅ Pass Criteria:**
- No conversion events fired
- No signup_completion funnel step
- User successfully logged in without false conversion

---

### Test 5: UTM Parameters Through Full Flow

**Goal**: Verify UTM parameters persist from landing → signup → conversion

**Steps:**
1. Clear sessionStorage:
   ```javascript
   sessionStorage.clear();
   ```

2. Start at landing page with UTM params:
   ```
   http://localhost:5173/?utm_source=full_flow_test&utm_medium=organic&utm_campaign=test_campaign
   ```

3. Check sessionStorage:
   ```javascript
   JSON.parse(sessionStorage.getItem('fxsentinel_utm_params'))
   ```
   Should show UTM params.

4. Navigate to signup page (click signup button):
   ```
   http://localhost:5173/signup
   ```

5. Check sessionStorage again:
   ```javascript
   JSON.parse(sessionStorage.getItem('fxsentinel_utm_params'))
   ```
   **Expected Result:** UTM params still present

6. Complete signup (email or Google)

7. After redirect to `/auth-redirect`, check sessionStorage:
   ```javascript
   JSON.parse(sessionStorage.getItem('fxsentinel_utm_params'))
   ```
   **Expected Result:** UTM params still present

8. Check conversion event in dataLayer:
   ```javascript
   window.dataLayer.filter(e => e.event === 'conversion').pop()
   ```
   **Expected Result:**
   - Should include `utm_source: "full_flow_test"`
   - Should include `utm_medium: "organic"`
   - Should include `utm_campaign: "test_campaign"`

**✅ Pass Criteria:**
- UTM params persist through entire flow
- Conversion events include original UTM params
- No UTM params lost during redirects

---

## 🔍 Debugging Commands

### Check Current UTM Params
```javascript
// Get current UTM params from analytics tracker
window.analyticsTracker?.getUTMParams()
```

### Check Session Storage
```javascript
// View persisted UTM params
JSON.parse(sessionStorage.getItem('fxsentinel_utm_params'))
```

### Check DataLayer Events
```javascript
// View all events
window.dataLayer

// View only conversion events
window.dataLayer.filter(e => e.event === 'conversion')

// View only funnel_step events
window.dataLayer.filter(e => e.event === 'funnel_step')

// View signup_completion events
window.dataLayer.filter(e => e.funnel_step === 'signup_completion')
```

### Clear Everything (Start Fresh)
```javascript
// Clear sessionStorage
sessionStorage.clear();

// Clear dataLayer (if needed)
window.dataLayer = [];

// Reload page
location.reload();
```

### Test UTM Extraction Manually
```javascript
// Simulate UTM params
const url = new URL(window.location.href);
url.searchParams.set('utm_source', 'manual_test');
url.searchParams.set('utm_medium', 'test');
window.history.pushState({}, '', url);
location.reload();
```

---

## 🐛 Common Issues & Solutions

### Issue 1: UTM Params Not Persisting

**Symptoms:**
- UTM params disappear after redirect
- Conversion events missing UTM parameters

**Solution:**
1. Check browser console for errors
2. Verify sessionStorage is enabled (not in incognito/private mode)
3. Check if sessionStorage is being cleared elsewhere

**Debug:**
```javascript
// Check if sessionStorage is available
typeof Storage !== 'undefined' && window.sessionStorage

// Check if params were stored
sessionStorage.getItem('fxsentinel_utm_params')
```

### Issue 2: Conversion Events Not Firing

**Symptoms:**
- No console logs for conversion tracking
- dataLayer empty or missing events

**Solution:**
1. Check browser console for JavaScript errors
2. Verify Firebase is initialized correctly
3. Check if `trackSignupCompletion` is being called

**Debug:**
```javascript
// Check if analytics tracker exists
window.analyticsTracker

// Check if dataLayer exists
window.dataLayer

// Manually trigger conversion (for testing)
import { trackSignupCompletion } from './src/utils/analytics';
trackSignupCompletion('test', { test: true });
```

### Issue 3: Google Signup Always Fires Conversion

**Symptoms:**
- Conversion fires even for returning users

**Solution:**
1. Verify `isNewUser` check is working
2. Check Firebase `additionalUserInfo` structure

**Debug:**
```javascript
// After Google signup, check result structure
// In Signup.jsx, add console.log:
console.log('Google signup result:', {
  user: result.user,
  additionalUserInfo: result.additionalUserInfo,
  isNewUser: result.additionalUserInfo?.isNewUser
});
```

### Issue 4: GTM Preview Mode Not Showing Events

**Symptoms:**
- Events appear in dataLayer but not in GTM Preview

**Solution:**
1. Verify GTM container is loaded (check Network tab)
2. Check GTM Preview mode is connected to correct URL
3. Verify GTM tag triggers are configured correctly

**Debug:**
```javascript
// Check if GTM is loaded
window.google_tag_manager

// Check GTM container ID
document.querySelector('script[src*="gtm.js"]')
```

---

## ✅ Final Verification Checklist

Before pushing to production, verify:

- [ ] **Test 1 Passed**: UTM parameters persist in sessionStorage
- [ ] **Test 2 Passed**: Email signup fires conversion events
- [ ] **Test 3 Passed**: Google signup fires conversion for NEW users
- [ ] **Test 4 Passed**: Google login does NOT fire conversion for existing users
- [ ] **Test 5 Passed**: UTM params persist through full flow
- [ ] **Console Logs**: No JavaScript errors
- [ ] **DataLayer**: Events contain correct structure and UTM params
- [ ] **GTM Preview** (if testing): Events appear in GTM Preview Mode
- [ ] **Browser Compatibility**: Tested in Chrome/Firefox/Safari

---

## 📊 Expected Console Output

### Successful Email Signup:
```
📊 Analytics: UTM params persisted {utm_source: "test", ...}
📊 Analytics: Engagement tracked {event_name: "signup_form_submit", ...}
📊 Analytics: Funnel step tracked {funnel_step: "signup_completion", ...}
📊 Analytics: Conversion tracked {conversion_type: "signup", ...}
```

### Successful Google Signup (New User):
```
📊 Analytics: UTM params persisted {utm_source: "google_test", ...}
📊 Analytics: Funnel step tracked {funnel_step: "signup_completion", ...}
📊 Analytics: Conversion tracked {conversion_type: "signup", method: "google", ...}
```

### Google Login (Existing User):
```
📊 Analytics: Funnel step tracked {funnel_step: "auth_redirect", ...}
(No conversion events should appear)
```

---

## 🚀 Next Steps After Testing

1. **If all tests pass:**
   - Commit changes
   - Push to production
   - Monitor GA4 Realtime for first few conversions

2. **If tests fail:**
   - Review error messages in console
   - Check the debugging section above
   - Fix issues and re-test

3. **After deployment:**
   - Test on production URL with UTM params
   - Verify GTM Preview Mode works on production
   - Check GA4 Realtime reports
   - Monitor for 24-48 hours to ensure tracking is stable

---

## 📝 Notes

- **Test Accounts**: Use test email addresses or create test Google accounts
- **Firebase Console**: You may need to delete test users between tests
- **Session Storage**: Cleared when browser tab closes (by design)
- **Local Storage**: Not used (sessionStorage is preferred for session-based tracking)

---

**Ready to test?** Start with Test 1 and work through each test case systematically.
