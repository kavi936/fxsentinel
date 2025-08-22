import React from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import './BannerNotifications.css';

const BannerNotifications = () => {
  const { bannerNotifications, removeBannerNotification } = useNotifications();

  const handleActionClick = (banner) => {
    if (banner.action && banner.action.url) {
      window.location.href = banner.action.url;
    }
    removeBannerNotification(banner.id);
  };

  const getBannerIcon = (type) => {
    switch (type) {
      case 'success':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22,4 12,14.01 9,11.01"/>
          </svg>
        );
      case 'warning':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        );
      case 'error':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        );
      case 'info':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
        );
      default:
        return null;
    }
  };

  if (bannerNotifications.length === 0) {
    return null;
  }

  return (
    <div className="banner-notifications-container">
      {bannerNotifications.map((banner) => (
        <div
          key={banner.id}
          className={`banner-notification ${banner.type}`}
          style={{
            animationDelay: `${bannerNotifications.indexOf(banner) * 0.1}s`
          }}
        >
          <div className="banner-content">
            <div className="banner-icon">
              {getBannerIcon(banner.type)}
            </div>
            <div className="banner-text">
              <h4 className="banner-title">{banner.title}</h4>
              <p className="banner-message">{banner.message}</p>
            </div>
            <div className="banner-actions">
              {banner.action && (
                <button
                  className="banner-action-btn"
                  onClick={() => handleActionClick(banner)}
                >
                  {banner.action.label}
                </button>
              )}
              <button
                className="banner-close-btn"
                onClick={() => removeBannerNotification(banner.id)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>
          <div className="banner-progress">
            <div 
              className="banner-progress-bar"
              style={{
                animationDuration: `${banner.duration || 5000}ms`
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

export default BannerNotifications;
