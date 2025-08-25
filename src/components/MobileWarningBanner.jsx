import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import './MobileWarningBanner.css';

const MobileWarningBanner = ({ onVisibilityChange }) => {
  const location = useLocation();
  const [isVisible, setIsVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [hasDismissed, setHasDismissed] = useState(false);

  useEffect(() => {
    // Only show on dashboard page
    if (location.pathname !== '/dashboard') {
      setIsVisible(false);
      return;
    }

    // Check if user has dismissed the banner
    const dismissed = localStorage.getItem('mobileWarningDismissed');
    if (dismissed) {
      setHasDismissed(true);
      return;
    }

    // Detect mobile device
    const checkMobile = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const isMobileDevice = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
      const isSmallScreen = window.innerWidth <= 768;
      
      const shouldShow = isMobileDevice || isSmallScreen;
      setIsMobile(shouldShow);
      setIsVisible(shouldShow);
      
      // Notify parent component about visibility change
      if (onVisibilityChange) {
        onVisibilityChange(shouldShow);
      }
    };

    // Check on mount
    checkMobile();

    // Check on resize
    const handleResize = () => {
      checkMobile();
    };

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    setHasDismissed(true);
    localStorage.setItem('mobileWarningDismissed', 'true');
    
    // Notify parent component about visibility change
    if (onVisibilityChange) {
      onVisibilityChange(false);
    }
  };

  const handleRemindLater = () => {
    setIsVisible(false);
    // Set reminder for 24 hours later
    const reminderTime = Date.now() + (24 * 60 * 60 * 1000);
    localStorage.setItem('mobileWarningReminder', reminderTime.toString());
    
    // Notify parent component about visibility change
    if (onVisibilityChange) {
      onVisibilityChange(false);
    }
  };

  // Check for reminder
  useEffect(() => {
    // Only check reminder on dashboard page
    if (location.pathname !== '/dashboard') {
      return;
    }

    const reminderTime = localStorage.getItem('mobileWarningReminder');
    if (reminderTime && Date.now() > parseInt(reminderTime)) {
      localStorage.removeItem('mobileWarningReminder');
      if (isMobile && !hasDismissed) {
        setIsVisible(true);
        // Notify parent component about visibility change
        if (onVisibilityChange) {
          onVisibilityChange(true);
        }
      }
    }
  }, [isMobile, hasDismissed, location.pathname]);

  if (!isVisible || hasDismissed) {
    return null;
  }

  return (
    <div className="mobile-warning-banner">
      <div className="mobile-warning-content">
        <div className="mobile-warning-header">
          <div className="mobile-warning-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>
          <div className="mobile-warning-text">
            <h3>Mobile Experience Notice</h3>
            <p>FXSentinel dashboard is optimized for desktop and laptop screens. For the best trading experience, we recommend switching to a larger screen.</p>
          </div>
          <button className="mobile-warning-close" onClick={handleDismiss}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        
        <div className="mobile-warning-actions">
          <button className="mobile-warning-btn primary" onClick={handleDismiss}>
            Got it, continue anyway
          </button>
          <button className="mobile-warning-btn secondary" onClick={handleRemindLater}>
            Remind me later
          </button>
        </div>
        
        <div className="mobile-warning-features">
          <div className="feature-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            </svg>
            <span>Full dashboard view</span>
          </div>
          <div className="feature-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <span>Better charts & analysis</span>
          </div>
          <div className="feature-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 12l2 2 4-4"/>
              <path d="M21 12c-1 0-2-1-2-2s1-2 2-2 2 1 2 2-1 2-2 2z"/>
              <path d="M3 12c1 0 2-1 2-2s-1-2-2-2-2 1-2 2 1 2 2 2z"/>
            </svg>
            <span>Enhanced trading tools</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileWarningBanner;
