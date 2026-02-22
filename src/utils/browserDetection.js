/**
 * Browser Detection Utilities
 * Detects embedded in-app browsers (Instagram, Facebook, etc.) for Google OAuth.
 *
 * IMPORTANT: We only flag known app UAs. Generic "webview" / "wv" / iOS heuristics
 * are NOT used here — they caused false positives and blocked real Chrome/Safari users.
 * If someone is in an unknown embedded browser, Google will return disallowed_useragent
 * and we show the "open in Safari/Chrome" message only then (via isGoogleOAuthBlockedError).
 */

/**
 * Detects if the app is running in a known embedded in-app browser (Instagram, Facebook, etc.).
 * Only returns isEmbedded: true when the UA explicitly identifies such an app.
 * @returns {Object} { isEmbedded: boolean, browserName: string, userAgent: string, instructions?: string }
 */
export const detectEmbeddedBrowser = () => {
  if (typeof window === 'undefined' || !navigator) {
    return { isEmbedded: false, browserName: 'unknown', userAgent: '' };
  }

  const userAgent = navigator.userAgent;
  const ua = userAgent.toLowerCase();

  // Only app-specific patterns that reliably identify in-app browsers. No generic webview/wv/iOS heuristics.
  if (/fban|fbav|fbsv|facebook/i.test(ua) || /messenger/i.test(ua)) {
    return {
      isEmbedded: true,
      browserName: 'Facebook/Messenger',
      userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.',
    };
  }

  if (/instagram/i.test(ua)) {
    return {
      isEmbedded: true,
      browserName: 'Instagram',
      userAgent,
      instructions: 'Please tap the menu (⋯) and select "Open in Browser" or "Open in Safari" to sign in with Google.',
    };
  }

  if (/snapchat/i.test(ua)) {
    return {
      isEmbedded: true,
      browserName: 'Snapchat',
      userAgent,
      instructions: 'Please tap the menu and select "Open in Browser" or copy the link and open it in Safari or Chrome to sign in with Google.',
    };
  }

  if (/twitter/i.test(ua)) {
    return {
      isEmbedded: true,
      browserName: 'Twitter',
      userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.',
    };
  }

  if (/linkedinapp/i.test(ua)) {
    return {
      isEmbedded: true,
      browserName: 'LinkedIn',
      userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.',
    };
  }

  // Line app UA usually contains " Line/" to avoid matching "inline" etc.
  if (/ line\//i.test(ua) || /\bline\/\d/i.test(ua)) {
    return {
      isEmbedded: true,
      browserName: 'Line',
      userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.',
    };
  }

  if (/micromessenger/i.test(ua)) {
    return {
      isEmbedded: true,
      browserName: 'WeChat',
      userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.',
    };
  }

  return {
    isEmbedded: false,
    browserName: 'Standard Browser',
    userAgent,
  };
};

/**
 * Checks if Google OAuth is likely to be blocked
 * This is a pre-emptive check before attempting sign-in
 * @returns {boolean}
 */
export const isGoogleOAuthBlocked = () => {
  const detection = detectEmbeddedBrowser();
  return detection.isEmbedded;
};

/**
 * Gets user-friendly instructions for opening in external browser
 * @returns {string}
 */
export const getBrowserSwitchInstructions = () => {
  const detection = detectEmbeddedBrowser();
  
  if (!detection.isEmbedded) {
    return null;
  }

  return detection.instructions || 'Please open this link in Safari or Chrome to sign in with Google.';
};

/**
 * Detects if the error is Google's "disallowed_useragent" / secure-browser block.
 * Do NOT include popup-blocked or popup-closed — those are not embedded-browser issues;
 * they happen in normal Chrome when popups are blocked or the user closes the window.
 * @param {Error} error - The error object from Firebase
 * @returns {boolean}
 */
export const isGoogleOAuthBlockedError = (error) => {
  if (!error) return false;

  const errorMessage = error.message?.toLowerCase() || '';
  const errorCode = error.code?.toLowerCase() || '';

  return (
    errorMessage.includes('disallowed_useragent') ||
    errorMessage.includes('use secure browsers') ||
    errorMessage.includes('does not comply with google') ||
    errorMessage.includes('access blocked') ||
    (errorMessage.includes('403') && (errorMessage.includes('browser') || errorMessage.includes('useragent')))
  );
};
