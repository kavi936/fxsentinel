# Quick Start: Testing GTM/GA4 Tracking

## 🚀 Start Servers

```bash
# Start both frontend and backend
bash deployment/start_servers.sh

# OR start manually:
# Terminal 1:
cd backend && python3 app.py

# Terminal 2:
npm run dev
```

**Frontend URL:** http://localhost:5173  
**Backend URL:** http://localhost:5001

---

## 🧪 Quick Test Steps

### Step 1: Open Browser Console
1. Open http://localhost:5173 in Chrome/Firefox
2. Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
3. Go to **Console** tab

### Step 2: Run Test Script
Copy and paste this into the console:

```javascript
// Quick test script - paste into browser console
(function() {
  console.log('🧪 Testing Tracking Implementation...\n');
  
  // Check analytics tracker (may need page reload to be available)
  const hasTracker = typeof window.analyticsTracker !== 'undefined';
  console.log('Analytics Tracker:', hasTracker ? '✅' : '⚠️  (Reload page if needed)');
  if (hasTracker) {
    console.log('   UTM Params:', window.analyticsTracker.getUTMParams());
    console.log('   Session ID:', window.analyticsTracker.getSessionId());
  }
  
  console.log('DataLayer:', typeof window.dataLayer !== 'undefined' ? '✅' : '❌');
  console.log('SessionStorage:', typeof sessionStorage !== 'undefined' ? '✅' : '❌');
  
  // Check UTM params
  const utms = sessionStorage.getItem('fxsentinel_utm_params');
  console.log('UTM Params Stored:', utms ? '✅' : '⚠️  None (visit with ?utm_source=test)');
  if (utms) {
    console.log('   Params:', JSON.parse(utms));
  }
  
  // Check conversion events
  if (window.dataLayer) {
    const conversions = window.dataLayer.filter(e => e.event === 'conversion' || e.funnel_step === 'signup_completion');
    console.log('Conversion Events:', conversions.length > 0 ? `✅ Found ${conversions.length}` : '⚠️  None yet');
    if (conversions.length > 0) {
      console.log('   Latest:', conversions[conversions.length - 1]);
    }
  }
  
  console.log('\n✅ Basic checks complete!');
  console.log('\n💡 Next: Visit /signup?utm_source=test&utm_medium=social to test UTM persistence');
})();
```

### Step 3: Test UTM Persistence
1. Visit: `http://localhost:5173/signup?utm_source=test&utm_medium=social&utm_campaign=quick_test`
2. Check console for: `📊 Analytics: UTM params persisted`
3. Run this in console:
   ```javascript
   JSON.parse(sessionStorage.getItem('fxsentinel_utm_params'))
   ```
4. Should see UTM params object

### Step 4: Test Email Signup
1. Fill out signup form with test email
2. Click "Create Account"
3. Watch console for:
   - `📊 Analytics: Funnel step tracked` with `signup_completion`
   - `📊 Analytics: Conversion tracked`
4. Check dataLayer:
   ```javascript
   window.dataLayer.filter(e => e.event === 'conversion')
   ```

### Step 5: Test Google Signup (New User)
1. Use a Google account that hasn't signed up before
2. Visit: `http://localhost:5173/signup?utm_source=google_test&utm_medium=social`
3. Click "Continue with Google"
4. Complete OAuth flow
5. Watch console for conversion events
6. Verify UTM params in conversion event:
   ```javascript
   window.dataLayer.filter(e => e.event === 'conversion').pop()
   ```

### Step 6: Test Google Login (Existing User)
1. Log out
2. Go to login page
3. Click "Continue with Google" with SAME account
4. Verify NO conversion events fire (only auth_redirect)

---

## ✅ Success Criteria

- [ ] UTM params persist in sessionStorage
- [ ] Email signup fires conversion event
- [ ] Google signup (new user) fires conversion event
- [ ] Google login (existing user) does NOT fire conversion
- [ ] Conversion events include UTM parameters
- [ ] No JavaScript errors in console

---

## 🐛 Quick Debugging

**No UTM params?**
```javascript
// Manually set UTM params for testing
sessionStorage.setItem('fxsentinel_utm_params', JSON.stringify({
  utm_source: 'manual_test',
  utm_medium: 'test',
  utm_campaign: 'test'
}));
location.reload();
```

**No conversion events?**
```javascript
// Check if trackSignupCompletion exists
import { trackSignupCompletion } from './src/utils/analytics';
trackSignupCompletion('test', { test: true });
```

**Clear everything:**
```javascript
sessionStorage.clear();
window.dataLayer = [];
location.reload();
```

---

## 📚 Full Testing Guide

For comprehensive testing, see: `docs/GTM_GA4_TESTING_GUIDE.md`

---

**Ready?** Start with Step 1 and work through each step!
