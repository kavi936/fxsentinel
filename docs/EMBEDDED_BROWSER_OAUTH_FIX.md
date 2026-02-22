# Embedded Browser OAuth Fix

## ⚠️ False-Positive Fix (Feb 2026)

**Problem:** Many users were incorrectly blocked from Google sign-in in **Chrome**, **Safari**, or when opening links from **social media** (which often open in the system browser, not the in-app browser). The warning "Google Sign-In Not Available" appeared for normal browsers.

**Root causes:**

1. **Generic webview detection** — We treated any UA containing `wv` or matching a generic "iOS webview" heuristic as embedded. Chrome for Android and some iOS browsers can match these, so real users were blocked.
2. **Over-broad error classification** — `auth/popup-blocked` and `auth/popup-closed-by-user` were treated as "embedded browser blocked", so Chrome users who had popups disabled or closed the popup saw "open in Safari or Chrome" instead of "allow popups" or "try again".

**Changes made:**

- **Detection:** We now **only** flag **known in-app browser** UAs: Facebook, Messenger, Instagram, Snapchat, Twitter, LinkedIn, Line (specific pattern), WeChat. **Generic webview / `wv` / iOS heuristics were removed.** Chrome, Safari, and any browser without an explicit app name in the UA are never pre-emptively blocked.
- **Unknown embedded browsers:** If someone is in an embedded browser we don’t detect, Google will still return `disallowed_useragent`. We show the "open in Safari/Chrome" message only **after** that error (via `isGoogleOAuthBlockedError`).
- **Error classification:** `isGoogleOAuthBlockedError()` no longer includes `auth/popup-blocked` or `auth/popup-closed-by-user`. Those are handled separately in Signup/Login with messages like "Allow popups" and "Sign-in was cancelled".

**Result:** Standalone Chrome and Safari work. Social links that open in the system browser work. Only real in-app browsers (Instagram/Facebook/Snapchat etc. **in-app** viewer) get the proactive warning and block.

---

## Problem Summary

Users accessing the app from embedded browsers (Snapchat, Instagram, Facebook, etc.) were encountering **Error 403: disallowed_useragent** when trying to sign in with Google. This is a security restriction imposed by Google that blocks OAuth authentication in embedded webviews.

## Root Cause

Google has a "Use secure browsers" policy that explicitly blocks OAuth sign-in requests from embedded browsers (webviews) used by social media apps. This is a platform-level security restriction, not a bug in our code.

### Why Google Blocks Embedded Browsers

1. **Security Concerns**: Embedded browsers may not have the same security features as standalone browsers
2. **Phishing Prevention**: Embedded browsers can be more easily manipulated by malicious apps
3. **User Privacy**: Google wants to ensure users are aware of where they're signing in

## Solution Implemented

We've implemented a comprehensive solution that:

1. **Detects embedded browsers** before attempting sign-in
2. **Shows proactive warnings** to users in embedded browsers
3. **Provides clear instructions** on how to open the link in an external browser
4. **Handles errors gracefully** with helpful error messages

## Implementation Details

### 1. Browser Detection Utility (`src/utils/browserDetection.js`)

Created a utility that detects embedded browsers by checking user agent strings:

- **Facebook/Messenger**: `fban`, `fbav`, `fbsv`, or `facebook`, or `messenger`
- **Instagram**: `instagram`
- **Snapchat**: `snapchat`
- **Twitter**: `twitter`
- **LinkedIn**: `linkedinapp`
- **Line**: ` Line/` or `line/\d` (to avoid matching "inline")
- **WeChat**: `micromessenger`
- **Generic webviews**: We do **not** detect generic webview/`wv`/iOS heuristics. Only the app names above are used. This avoids blocking Chrome, Safari, or social links that open in the system browser.

### 2. Enhanced Error Handling (`src/contexts/AuthContext.jsx`)

Updated `signInWithGoogle()` to:

- Check for embedded browsers **before** attempting sign-in
- Throw a custom error with helpful instructions if embedded browser detected
- Catch and enhance Google OAuth blocked errors with user-friendly messages

### 3. Embedded Browser Warning Component (`src/components/EmbeddedBrowserWarning.jsx`)

Created a modal component that:

- Automatically appears when embedded browser is detected
- Shows clear instructions for opening in external browser
- Provides "Open in Browser" button (attempts to open in Safari/Chrome)
- Allows users to dismiss and continue (though sign-in will still fail)

### 4. Updated Signup/Login Components

Both `Signup.jsx` and `Login.jsx` now:

- Display the `EmbeddedBrowserWarning` component
- Handle embedded browser errors with specific error messages
- Show full error messages with instructions when OAuth is blocked

## User Experience Flow

### Scenario 1: User Opens Link in Snapchat/Instagram

1. **On Page Load**: `EmbeddedBrowserWarning` modal appears with instructions
2. **User Clicks "Open in Browser"**: Attempts to open link in Safari/Chrome
3. **User Clicks "Continue Anyway"**: Modal dismisses, but sign-in will show error
4. **User Attempts Google Sign-In**: Gets clear error message with instructions

### Scenario 2: User Ignores Warning and Tries to Sign In

1. **User Clicks "Continue with Google"**: 
   - Detection happens before Firebase call
   - Error thrown immediately with instructions
   - Error message displayed: "Google sign-in is not available in [Browser Name]. Please open this link in Safari or Chrome."

### Scenario 3: Error Occurs Despite Detection

1. **Firebase Returns Error**: 
   - Error is caught and checked for OAuth blocked patterns
   - Error message enhanced with instructions
   - User sees helpful message instead of generic error

## Error Messages

### Embedded Browser Detected (Pre-emptive)
```
Google sign-in is not available in [Browser Name]. [Specific instructions for that browser].
```

### Google OAuth Blocked Error (After Attempt)
```
Google sign-in is blocked in this browser. Please try opening this link in Safari or Chrome instead.
```

## Browser-Specific Instructions

- **Instagram**: "Please tap the menu (⋯) and select 'Open in Browser' or 'Open in Safari' to sign in with Google."
- **Snapchat**: "Please tap the menu and select 'Open in Browser' or copy the link and open it in Safari or Chrome to sign in with Google."
- **Facebook/Messenger**: "Please open this link in Safari or Chrome to sign in with Google."
- **Generic**: "Please open this link in Safari or Chrome to sign in with Google."

## Testing

### Manual Testing Checklist

- [ ] Test in Instagram in-app browser
- [ ] Test in Snapchat in-app browser
- [ ] Test in Facebook in-app browser
- [ ] Test in Messenger in-app browser
- [ ] Verify warning appears on page load
- [ ] Verify error message appears on sign-in attempt
- [ ] Test "Open in Browser" button functionality
- [ ] Test "Continue Anyway" button functionality
- [ ] Verify normal browsers (Safari, Chrome) still work

### Test User Agents

You can test detection by modifying user agent in browser dev tools:

```javascript
// Instagram
navigator.userAgent = "Instagram 123.0.0.0.0 (iPhone; iOS 14_0; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15"

// Snapchat
navigator.userAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Snapchat/10.0.0"

// Facebook
navigator.userAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone12,1;FBMD/iPhone;FBSN/iOS;FBSV/14.0;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5]"
```

## Limitations

1. **No Universal Solution**: There's no way to make Google OAuth work in embedded browsers - this is a Google policy restriction
2. **Browser Opening**: The "Open in Browser" button may not work on all devices/apps - it depends on the app's implementation
3. **User Agent Spoofing**: Some apps may spoof user agents, making detection less reliable

## Future Improvements

1. **Deep Linking**: Consider implementing deep links that open directly in external browsers
2. **QR Code**: Generate QR code for users to scan and open in external browser
3. **Copy Link**: Add "Copy Link" button so users can manually paste into browser
4. **Analytics**: Track how many users encounter this issue to measure impact

## Related Files

- `src/utils/browserDetection.js` - Browser detection utility
- `src/contexts/AuthContext.jsx` - Enhanced error handling
- `src/components/EmbeddedBrowserWarning.jsx` - Warning modal component
- `src/components/EmbeddedBrowserWarning.css` - Warning modal styles
- `src/components/Signup.jsx` - Updated signup component
- `src/components/Login.jsx` - Updated login component

## References

- [Google OAuth Troubleshooting](https://developers.google.com/identity/sign-in/web/troubleshooting)
- [Firebase Auth Error Codes](https://firebase.google.com/docs/auth/web/errors)
- [Stack Overflow: Error 403 disallowed_useragent](https://stackoverflow.com/questions/61796991/firebase-provider-sign-in-is-not-working-inside-facebook-messenger-instagram-in)

## Date Implemented

February 8, 2026
