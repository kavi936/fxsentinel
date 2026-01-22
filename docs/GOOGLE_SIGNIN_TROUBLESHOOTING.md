# Google Sign-In Troubleshooting Guide

## Critical Firebase Console Configuration

If Google sign-in is not working, check these settings in your Firebase Console:

### 1. Authorized Domains
**Location**: Firebase Console → Authentication → Settings → Authorized domains

**Required domains**:
- `localhost` (for development)
- `fxsentinel.io` (your production domain)
- `fxsentinel.vercel.app` (if using Vercel preview deployments)
- Any other domains where your app is hosted

**How to add**:
1. Go to Firebase Console
2. Select your project (`fxsentinel`)
3. Navigate to Authentication → Settings
4. Scroll to "Authorized domains"
5. Click "Add domain"
6. Enter your domain (without `https://` or `http://`)
7. Click "Add"

### 2. Google Sign-In Provider Enabled
**Location**: Firebase Console → Authentication → Sign-in method

**Check**:
1. Go to Authentication → Sign-in method
2. Find "Google" in the list
3. Ensure it's **Enabled**
4. If disabled, click on it and toggle "Enable"
5. Save the default OAuth client ID (or configure custom)

### 3. OAuth Consent Screen
**Location**: Google Cloud Console → APIs & Services → OAuth consent screen

**Required settings**:
- App name: FXSentinel
- User support email: Your email
- Developer contact information: Your email
- Scopes: `email`, `profile`, `openid` (should be added automatically)

### 4. Environment Variables
**Check your `.env` file** (root directory for frontend):

```bash
VITE_FIREBASE_API_KEY=your_actual_api_key
VITE_FIREBASE_AUTH_DOMAIN=fxsentinel.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=fxsentinel
VITE_FIREBASE_STORAGE_BUCKET=fxsentinel.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=92187574391
VITE_FIREBASE_APP_ID=1:92187574391:web:0b232b7fe364c639434672
VITE_FIREBASE_MEASUREMENT_ID=G-1QMRKVJD8C
```

**For Vercel deployment**:
1. Go to Vercel project settings
2. Navigate to Environment Variables
3. Add all `VITE_FIREBASE_*` variables
4. Redeploy after adding variables

## Common Error Codes and Solutions

### `auth/popup-blocked`
**Cause**: Browser blocked the popup window
**Solution**: 
- The app now automatically falls back to redirect method
- Users can also allow popups for your site

### `auth/popup-closed-by-user`
**Cause**: User closed the popup window
**Solution**: User needs to try again and complete the sign-in

### `auth/unauthorized-domain`
**Cause**: Domain not in authorized domains list
**Solution**: Add the domain to Firebase Console authorized domains (see above)

### `auth/operation-not-allowed`
**Cause**: Google sign-in provider not enabled
**Solution**: Enable Google sign-in in Firebase Console (see above)

### `auth/network-request-failed`
**Cause**: Network connectivity issue
**Solution**: Check internet connection, try again

## Testing Checklist

1. ✅ Test on `localhost` (development)
2. ✅ Test on production domain (`fxsentinel.io`)
3. ✅ Test with popup blocker enabled (should fallback to redirect)
4. ✅ Test on mobile devices (redirect method preferred)
5. ✅ Check browser console for error messages
6. ✅ Verify Firebase environment variables are set correctly

## Debugging Steps

1. **Check browser console**:
   - Open DevTools (F12)
   - Look for error messages starting with `❌` or `⚠️`
   - Check Network tab for failed requests

2. **Verify Firebase config**:
   - Check that `firebase.js` is loading correctly
   - Verify environment variables are not using placeholder values

3. **Test Firebase connection**:
   - Try email/password sign-in (to verify Firebase is working)
   - If email/password works but Google doesn't, it's a Google OAuth issue

4. **Check Firebase Console logs**:
   - Go to Firebase Console → Authentication → Users
   - Check if any sign-in attempts are being logged
   - Look for error messages

## Recent Fixes Applied

The following improvements have been made to the Google sign-in implementation:

1. **Error Logging**: All errors are now logged to console with detailed information
2. **Popup Fallback**: Automatically falls back to redirect method if popup is blocked
3. **Loading States**: Buttons show loading state during sign-in process
4. **Better Error Messages**: Users see specific error messages instead of generic ones
5. **Redirect Handling**: Properly handles redirect result after Google OAuth callback

## Still Not Working?

If Google sign-in still doesn't work after checking all the above:

1. **Verify Firebase project**:
   - Ensure you're using the correct Firebase project
   - Check that the project ID matches in Firebase Console and your config

2. **Check OAuth credentials**:
   - In Firebase Console → Authentication → Settings → OAuth redirect URIs
   - Should include: `https://fxsentinel.io/__/auth/handler`

3. **Contact Support**:
   - Check Firebase status page: https://status.firebase.google.com/
   - Review Firebase documentation: https://firebase.google.com/docs/auth/web/google-signin

