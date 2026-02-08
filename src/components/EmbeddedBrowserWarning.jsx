import React, { useState, useEffect } from 'react';
import { detectEmbeddedBrowser, getBrowserSwitchInstructions } from '../utils/browserDetection';
import './EmbeddedBrowserWarning.css';

/**
 * Component that displays a warning when the app is accessed from an embedded browser
 * This is important because Google OAuth doesn't work in embedded browsers
 */
const EmbeddedBrowserWarning = ({ onDismiss }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [browserInfo, setBrowserInfo] = useState(null);

  useEffect(() => {
    const detection = detectEmbeddedBrowser();
    if (detection.isEmbedded) {
      setBrowserInfo(detection);
      setIsVisible(true);
    }
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    if (onDismiss) {
      onDismiss();
    }
  };

  const handleOpenInBrowser = () => {
    // Try to open current URL in external browser
    const currentUrl = window.location.href;
    
    // For iOS, try to open in Safari
    if (/iphone|ipad|ipod/i.test(navigator.userAgent)) {
      // Create a link that will prompt to open in Safari
      window.location.href = currentUrl.replace(/^https?:\/\//, 'x-safari-https://');
    } else {
      // For Android, try to open in Chrome
      window.open(currentUrl, '_system');
    }
  };

  if (!isVisible || !browserInfo) {
    return null;
  }

  return (
    <div className="embedded-browser-warning">
      <div className="embedded-browser-warning-content">
        <div className="embedded-browser-warning-icon">⚠️</div>
        <div className="embedded-browser-warning-text">
          <h3>Google Sign-In Not Available</h3>
          <p>
            You're using {browserInfo.browserName}'s in-app browser. Google sign-in requires a secure browser like Safari or Chrome.
          </p>
          <p className="embedded-browser-instructions">
            {browserInfo.instructions || 'Please open this link in Safari or Chrome to sign in with Google.'}
          </p>
        </div>
        <div className="embedded-browser-warning-actions">
          <button 
            className="embedded-browser-button primary"
            onClick={handleOpenInBrowser}
          >
            Open in Browser
          </button>
          <button 
            className="embedded-browser-button secondary"
            onClick={handleDismiss}
          >
            Continue Anyway
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmbeddedBrowserWarning;
