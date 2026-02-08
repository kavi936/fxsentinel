/**
 * Browser Detection Utilities
 * Detects embedded browsers and provides information about the current browser environment
 */

/**
 * Detects if the app is running in an embedded browser/webview
 * These browsers are blocked by Google OAuth for security reasons
 * @returns {Object} { isEmbedded: boolean, browserName: string, userAgent: string }
 */
export const detectEmbeddedBrowser = () => {
  if (typeof window === 'undefined' || !navigator) {
    return { isEmbedded: false, browserName: 'unknown', userAgent: '' };
  }

  const userAgent = navigator.userAgent.toLowerCase();
  
  // Common embedded browser user agents
  const embeddedBrowsers = {
    facebook: /fban|fbav|fbsv/i.test(userAgent) || /facebook/i.test(userAgent),
    instagram: /instagram/i.test(userAgent),
    snapchat: /snapchat/i.test(userAgent),
    messenger: /messenger/i.test(userAgent),
    line: /line/i.test(userAgent),
    wechat: /micromessenger/i.test(userAgent),
    twitter: /twitter/i.test(userAgent),
    linkedin: /linkedinapp/i.test(userAgent),
    // Generic webview detection
    webview: /wv/i.test(userAgent) || /webview/i.test(userAgent),
    // iOS webview detection
    iosWebview: /(iphone|ipad|ipod).*safari/i.test(userAgent) && !/(iphone|ipad|ipod).*version/i.test(userAgent),
  };

  // Check for specific embedded browsers
  if (embeddedBrowsers.facebook || embeddedBrowsers.messenger) {
    return { 
      isEmbedded: true, 
      browserName: 'Facebook/Messenger', 
      userAgent: navigator.userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.'
    };
  }

  if (embeddedBrowsers.instagram) {
    return { 
      isEmbedded: true, 
      browserName: 'Instagram', 
      userAgent: navigator.userAgent,
      instructions: 'Please tap the menu (⋯) and select "Open in Browser" or "Open in Safari" to sign in with Google.'
    };
  }

  if (embeddedBrowsers.snapchat) {
    return { 
      isEmbedded: true, 
      browserName: 'Snapchat', 
      userAgent: navigator.userAgent,
      instructions: 'Please tap the menu and select "Open in Browser" or copy the link and open it in Safari or Chrome to sign in with Google.'
    };
  }

  if (embeddedBrowsers.twitter) {
    return { 
      isEmbedded: true, 
      browserName: 'Twitter', 
      userAgent: navigator.userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.'
    };
  }

  if (embeddedBrowsers.linkedin) {
    return { 
      isEmbedded: true, 
      browserName: 'LinkedIn', 
      userAgent: navigator.userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.'
    };
  }

  if (embeddedBrowsers.line) {
    return { 
      isEmbedded: true, 
      browserName: 'Line', 
      userAgent: navigator.userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.'
    };
  }

  if (embeddedBrowsers.wechat) {
    return { 
      isEmbedded: true, 
      browserName: 'WeChat', 
      userAgent: navigator.userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.'
    };
  }

  // Generic webview detection
  if (embeddedBrowsers.webview || embeddedBrowsers.iosWebview) {
    return { 
      isEmbedded: true, 
      browserName: 'In-App Browser', 
      userAgent: navigator.userAgent,
      instructions: 'Please open this link in Safari or Chrome to sign in with Google.'
    };
  }

  return { 
    isEmbedded: false, 
    browserName: 'Standard Browser', 
    userAgent: navigator.userAgent 
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
 * Detects if the error is the specific Google OAuth blocked error
 * @param {Error} error - The error object from Firebase
 * @returns {boolean}
 */
export const isGoogleOAuthBlockedError = (error) => {
  if (!error) return false;
  
  const errorMessage = error.message?.toLowerCase() || '';
  const errorCode = error.code?.toLowerCase() || '';
  
  // Check for various forms of the disallowed_useragent error
  return (
    errorCode.includes('auth/popup-blocked') ||
    errorCode.includes('auth/popup-closed-by-user') ||
    errorMessage.includes('disallowed_useragent') ||
    errorMessage.includes('403') ||
    errorMessage.includes('use secure browsers') ||
    errorMessage.includes('does not comply with google') ||
    errorMessage.includes('access blocked')
  );
};
