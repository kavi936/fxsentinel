import React, { useState, useEffect } from 'react';
import { detectEmbeddedBrowser } from '../utils/browserDetection';
import './EmbeddedBrowserWarning.css';

/**
 * Component that displays a warning when the app is accessed from an embedded browser
 * This is important because Google OAuth doesn't work in embedded browsers
 */
const EmbeddedBrowserWarning = ({ onDismiss }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [browserInfo, setBrowserInfo] = useState(null);
  const [copyStatus, setCopyStatus] = useState(null);

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

  const handleCopyLink = async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus(null), 2500);
    } catch {
      setCopyStatus('error');
      setTimeout(() => setCopyStatus(null), 2500);
    }
  };

  // Redirect to external browser — often does NOT work inside social app in-app browsers
  // (Instagram, Facebook, etc. block custom URL schemes). Primary path: app menu (⋯) or Copy link.
  const handleOpenInBrowser = () => {
    const url = window.location.href;
    if (/iphone|ipad|ipod/i.test(navigator.userAgent)) {
      window.location.href = url.replace(/^https?:\/\//, 'x-safari-https://');
    } else {
      window.open(url, '_system');
    }
  };

  if (!isVisible || !browserInfo) {
    return null;
  }

  return (
    <div className="embedded-browser-warning">
      <div className="embedded-browser-warning-content">
        <div className="embedded-browser-warning-icon" aria-hidden>⚠️</div>
        <div className="embedded-browser-warning-text">
          <h3>Google sign-in isn’t available here</h3>
          <p>
            You’re in {browserInfo.browserName}’s in-app browser. The “Open in Safari” button often doesn’t work here — use the app menu (⋯) and choose <strong>Open in Browser</strong> or <strong>Open in Safari</strong>, or copy the link and paste it in Safari.
          </p>
        </div>
        <div className="embedded-browser-warning-actions">
          <button
            type="button"
            className="embedded-browser-button primary"
            onClick={handleCopyLink}
            disabled={copyStatus === 'copied'}
          >
            {copyStatus === 'copied' ? 'Link copied — paste in Safari' : copyStatus === 'error' ? 'Copy failed' : 'Copy link'}
          </button>
          <button
            type="button"
            className="embedded-browser-button secondary"
            onClick={handleOpenInBrowser}
          >
            Try Open in Safari
          </button>
          <button
            type="button"
            className="embedded-browser-button secondary"
            onClick={handleDismiss}
          >
            Sign in with email
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmbeddedBrowserWarning;
