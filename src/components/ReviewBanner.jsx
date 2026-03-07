import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './ReviewBanner.css';
import tradingViewLogo from '../assets/tradingview-nobg.png';
import trustpilotLogo from '../assets/trustpilot-removebg-preview.png';

const FEEDBACK_DEFER_DAYS = 2; // Don't show feedback banner until after onboarding or this many days of app use
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

const ReviewBanner = ({ onClose }) => {
  const { currentUser } = useAuth();
  const [isVisible, setIsVisible] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  useEffect(() => {
    const userId = currentUser?.uid;
    // Require a logged-in user so we can scope "first visit" and onboarding per user
    if (!userId) return;

    // Defer feedback banner for new users: show only after onboarding is done OR after they've used the app for a while.
    // This avoids overwhelming first-time users with both onboarding and feedback at once.
    const onboardingCompleted = localStorage.getItem(`fxsentinel_onboarding_${userId}`) === 'completed';
    const firstVisitRaw = localStorage.getItem(`fxsentinel_first_dashboard_visit_${userId}`);
    const firstVisitTime = firstVisitRaw ? parseInt(firstVisitRaw, 10) : null;
    const daysSinceFirstVisit = firstVisitTime ? (Date.now() - firstVisitTime) / ONE_DAY_MS : 0;
    // No timestamp = existing user (before this feature); keep showing. Otherwise require onboarding done or 2+ days.
    const eligibleAfterDefer =
      onboardingCompleted ||
      firstVisitTime == null ||
      daysSinceFirstVisit >= FEEDBACK_DEFER_DAYS;

    if (!eligibleAfterDefer) return;

    // Check if user has seen the banner recently
    const lastShown = localStorage.getItem('reviewBannerLastShown');
    const hasReviewed = localStorage.getItem('userHasReviewed');
    const reminderTime = localStorage.getItem('reviewBannerReminder');
    const currentTime = Date.now();

    // Check if reminder time has passed
    if (reminderTime && currentTime < parseInt(reminderTime, 10)) {
      return; // Don't show yet, reminder time hasn't passed
    }

    // Show banner if:
    // 1. User hasn't reviewed yet
    // 2. It's been more than 1 day since last shown
    // 3. 60% chance
    if (!hasReviewed && (!lastShown || currentTime - parseInt(lastShown, 10) > ONE_DAY_MS)) {
      const shouldShow = Math.random() < 0.6;
      if (shouldShow) {
        setIsVisible(true);
        localStorage.setItem('reviewBannerLastShown', currentTime.toString());
      }
    }
  }, [currentUser?.uid]);

  const handleReviewClick = (platform) => {
    setHasInteracted(true);
    localStorage.setItem('userHasReviewed', 'true');
    
    // Track review attempt
    if (window.gtag) {
      window.gtag('event', 'review_clicked', {
        platform: platform,
        event_category: 'engagement'
      });
    }

    // Open review platform or navigate to feedback form
    if (platform === 'feedback') {
      // Navigate to feedback form
      window.location.href = '/feedback';
    } else {
      const reviewUrls = {
        trustpilot: 'https://www.trustpilot.com/review/fxsentinel.io',
        twitter: 'https://x.com/intent/tweet?text=Just%20tried%20%40fxsentinel%20-%20amazing%20AI-powered%20forex%20analysis!%20%23forex%20%23trading%20%23fxsentinel',
        tradingview: 'https://www.tradingview.com/symbols/FOREX/'
      };

      if (reviewUrls[platform]) {
        window.open(reviewUrls[platform], '_blank', 'noopener,noreferrer');
      }
    }
  };

  const handleClose = () => {
    setIsVisible(false);
    setHasInteracted(true);
    if (onClose) onClose();
  };

  const handleRemindLater = () => {
    setIsVisible(false);
    setHasInteracted(true);
    // Set reminder for 1 day later (reduced from 3 days for more frequent prompts)
    const reminderTime = Date.now() + (1 * 24 * 60 * 60 * 1000);
    localStorage.setItem('reviewBannerReminder', reminderTime.toString());
    localStorage.setItem('reviewBannerLastShown', Date.now().toString());
  };

  if (!isVisible || hasInteracted) {
    return null;
  }

  return (
    <div className="review-banner">
      <div className="review-banner-content">
        <div className="review-banner-header">
          <div className="review-banner-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </div>
          <div className="review-banner-text">
            <h3>Got Some Feedback?</h3>
            <p>Good or bad, we want to hear what you think! Help us build a better tool for everyone. Your feedback is extremely valued.</p>
          </div>
          <button className="review-banner-close" onClick={handleClose} aria-label="Close review banner">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <div className="review-banner-actions">
          <div className="review-platforms">
            <button 
              className="review-btn feedback"
              onClick={() => handleReviewClick('feedback')}
            >
              <span className="platform-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  <path d="M13 8H7"/>
                  <path d="M17 12H7"/>
                </svg>
              </span>
              Send Feedback
            </button>
            
            <button 
              className="review-btn primary trustpilot-btn"
              onClick={() => handleReviewClick('trustpilot')}
            >
              <img src={trustpilotLogo} alt="Trustpilot" className="trustpilot-logo" />
            </button>
            
            <button 
              className="review-btn secondary twitter-btn"
              onClick={() => handleReviewClick('twitter')}
            >
              <span className="platform-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
              </span>
              Share on X
            </button>
            
            <button 
              className="review-btn social tradingview-btn"
              onClick={() => handleReviewClick('tradingview')}
            >
              <img src={tradingViewLogo} alt="TradingView" className="tradingview-logo" />
            </button>
          </div>
          
          <div className="review-banner-footer">
            <button className="remind-later-btn" onClick={handleRemindLater}>
              Remind me later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewBanner;
