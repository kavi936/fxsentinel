import React, { useState, useEffect } from 'react';
import './ReviewBanner.css';

const ReviewBanner = ({ onClose }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  useEffect(() => {
    // Check if user has seen the banner recently
    const lastShown = localStorage.getItem('reviewBannerLastShown');
    const hasReviewed = localStorage.getItem('userHasReviewed');
    const currentTime = Date.now();
    
    // Show banner if:
    // 1. User hasn't reviewed yet
    // 2. It's been more than 7 days since last shown
    // 3. Random chance (30% probability)
    if (!hasReviewed && (!lastShown || currentTime - parseInt(lastShown) > 7 * 24 * 60 * 60 * 1000)) {
      const shouldShow = Math.random() < 0.3; // 30% chance
      if (shouldShow) {
        setIsVisible(true);
        localStorage.setItem('reviewBannerLastShown', currentTime.toString());
      }
    }
  }, []);

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

    // Open review platform
    const reviewUrls = {
      producthunt: 'https://www.producthunt.com/posts/fxsentinel',
      trustpilot: 'https://www.trustpilot.com/review/fxsentinel.io',
      twitter: 'https://twitter.com/intent/tweet?text=Just%20tried%20%40FXSentinel%20-%20amazing%20AI-powered%20forex%20analysis!%20%23forex%20%23trading',
      linkedin: 'https://www.linkedin.com/sharing/share-offsite/?url=https://fxsentinel.io'
    };

    if (reviewUrls[platform]) {
      window.open(reviewUrls[platform], '_blank', 'noopener,noreferrer');
    }
  };

  const handleClose = () => {
    setIsVisible(false);
    setHasInteracted(true);
    if (onClose) onClose();
  };

  const handleRemindLater = () => {
    setIsVisible(false);
    // Set reminder for 3 days later
    const reminderTime = Date.now() + (3 * 24 * 60 * 60 * 1000);
    localStorage.setItem('reviewBannerReminder', reminderTime.toString());
  };

  if (!isVisible || hasInteracted) {
    return null;
  }

  return (
    <div className="review-banner">
      <div className="review-banner-content">
        <div className="review-banner-header">
          <div className="review-banner-icon">⭐</div>
          <div className="review-banner-text">
            <h3>Enjoying FXSentinel?</h3>
            <p>Help us grow and improve by leaving a review!</p>
          </div>
          <button className="review-banner-close" onClick={handleClose}>
            ×
          </button>
        </div>
        
        <div className="review-banner-actions">
          <div className="review-platforms">
            <button 
              className="review-btn primary"
              onClick={() => handleReviewClick('producthunt')}
            >
              <span className="platform-icon">🚀</span>
              Review on Product Hunt
            </button>
            
            <button 
              className="review-btn secondary"
              onClick={() => handleReviewClick('trustpilot')}
            >
              <span className="platform-icon">🛡️</span>
              Review on Trustpilot
            </button>
            
            <button 
              className="review-btn social"
              onClick={() => handleReviewClick('twitter')}
            >
              <span className="platform-icon">🐦</span>
              Share on Twitter
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
