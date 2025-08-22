import React, { createContext, useContext, useState, useEffect } from 'react';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [bannerNotifications, setBannerNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Add a new notification
  const addNotification = (notification) => {
    const newNotification = {
      id: Date.now() + Math.random(),
      timestamp: new Date(),
      read: false,
      ...notification
    };
    
    setNotifications(prev => [newNotification, ...prev]);
    setUnreadCount(prev => prev + 1);
    
    // Auto-remove after 7 days
    setTimeout(() => {
      removeNotification(newNotification.id);
    }, 7 * 24 * 60 * 60 * 1000);
  };

  // Add a banner notification
  const addBannerNotification = (banner) => {
    const newBanner = {
      id: Date.now() + Math.random(),
      timestamp: new Date(),
      ...banner
    };
    
    setBannerNotifications(prev => [...prev, newBanner]);
    
    // Auto-remove after specified duration or default 5 seconds
    const duration = banner.duration || 5000;
    setTimeout(() => {
      removeBannerNotification(newBanner.id);
    }, duration);
  };

  // Remove a notification
  const removeNotification = (id) => {
    setNotifications(prev => {
      const notification = prev.find(n => n.id === id);
      if (notification && !notification.read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
      return prev.filter(n => n.id !== id);
    });
  };

  // Remove a banner notification
  const removeBannerNotification = (id) => {
    setBannerNotifications(prev => prev.filter(b => b.id !== id));
  };

  // Mark notification as read
  const markAsRead = (id) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, read: true }
          : notification
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  // Mark all notifications as read
  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
    setUnreadCount(0);
  };

  // Clear all notifications
  const clearAllNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  // Subscription event notifications
  const addSubscriptionNotification = (event, data = {}) => {
    switch (event) {
      case 'trial_started':
        addNotification({
          type: 'subscription',
          title: 'Free Trial Started',
          message: 'Your 3-day free trial has been activated! Enjoy unlimited access to premium features.',
          priority: 'high',
          icon: '🎉'
        });
        addBannerNotification({
          type: 'success',
          title: 'Trial Activated!',
          message: 'Your 3-day free trial is now active. Enjoy premium features!',
          duration: 8000
        });
        break;

      case 'trial_ending_soon':
        addNotification({
          type: 'subscription',
          title: 'Trial Ending Soon',
          message: `Your trial ends in ${data.daysRemaining} day${data.daysRemaining !== 1 ? 's' : ''}. Upgrade now to continue using premium features.`,
          priority: 'high',
          icon: '⏰',
          action: {
            label: 'Upgrade Now',
            url: '/trial-welcome'
          }
        });
        addBannerNotification({
          type: 'warning',
          title: 'Trial Ending Soon',
          message: `Your trial ends in ${data.daysRemaining} day${data.daysRemaining !== 1 ? 's' : ''}. Upgrade to continue!`,
          duration: 10000,
          action: {
            label: 'Upgrade',
            url: '/trial-welcome'
          }
        });
        break;

      case 'trial_expired':
        addNotification({
          type: 'subscription',
          title: 'Trial Expired',
          message: 'Your free trial has expired. Upgrade to continue using premium features.',
          priority: 'high',
          icon: '❌',
          action: {
            label: 'Upgrade Now',
            url: '/trial-welcome'
          }
        });
        addBannerNotification({
          type: 'error',
          title: 'Trial Expired',
          message: 'Your trial has expired. Upgrade to continue using premium features.',
          duration: 12000,
          action: {
            label: 'Upgrade',
            url: '/trial-welcome'
          }
        });
        break;

      case 'payment_success':
        addNotification({
          type: 'subscription',
          title: 'Payment Successful',
          message: 'Your payment has been processed successfully. Welcome to Premium!',
          priority: 'high',
          icon: '✅'
        });
        addBannerNotification({
          type: 'success',
          title: 'Payment Successful!',
          message: 'Welcome to Premium! Your subscription is now active.',
          duration: 8000
        });
        break;

      case 'payment_failed':
        addNotification({
          type: 'subscription',
          title: 'Payment Failed',
          message: 'Your payment could not be processed. Please update your payment method.',
          priority: 'high',
          icon: '💳',
          action: {
            label: 'Update Payment',
            url: '/profile'
          }
        });
        addBannerNotification({
          type: 'error',
          title: 'Payment Failed',
          message: 'Your payment could not be processed. Please update your payment method.',
          duration: 10000,
          action: {
            label: 'Fix Payment',
            url: '/profile'
          }
        });
        break;

      case 'subscription_cancelled':
        addNotification({
          type: 'subscription',
          title: 'Subscription Cancelled',
          message: 'Your subscription has been cancelled. You can reactivate anytime.',
          priority: 'medium',
          icon: '📋'
        });
        break;

      default:
        break;
    }
  };

  // Usage notifications
  const addUsageNotification = (event, data = {}) => {
    switch (event) {
      case 'usage_warning':
        addNotification({
          type: 'usage',
          title: 'Usage Limit Warning',
          message: `You've used ${data.used}/${data.limit} AI analyses today. ${data.remaining} remaining.`,
          priority: 'medium',
          icon: '⚠️'
        });
        break;

      case 'usage_limit_reached':
        addNotification({
          type: 'usage',
          title: 'Daily Limit Reached',
          message: 'You\'ve reached your daily AI analysis limit. Upgrade to Premium for unlimited access.',
          priority: 'high',
          icon: '🚫',
          action: {
            label: 'Upgrade',
            url: '/trial-welcome'
          }
        });
        addBannerNotification({
          type: 'warning',
          title: 'Daily Limit Reached',
          message: 'You\'ve reached your daily AI analysis limit. Upgrade for unlimited access.',
          duration: 8000,
          action: {
            label: 'Upgrade',
            url: '/trial-welcome'
          }
        });
        break;

      case 'usage_reset':
        addNotification({
          type: 'usage',
          title: 'Daily Limit Reset',
          message: 'Your daily AI analysis limit has been reset. You can now perform new analyses.',
          priority: 'low',
          icon: '🔄'
        });
        break;

      default:
        break;
    }
  };

  // System notifications
  const addSystemNotification = (event, data = {}) => {
    switch (event) {
      case 'feature_update':
        addNotification({
          type: 'system',
          title: 'New Feature Available',
          message: data.message || 'New features have been added to your dashboard.',
          priority: 'medium',
          icon: '🆕'
        });
        break;

      case 'maintenance':
        addNotification({
          type: 'system',
          title: 'Scheduled Maintenance',
          message: data.message || 'Scheduled maintenance will occur soon.',
          priority: 'medium',
          icon: '🔧'
        });
        break;

      default:
        break;
    }
  };

  const value = {
    notifications,
    bannerNotifications,
    unreadCount,
    addNotification,
    addBannerNotification,
    removeNotification,
    removeBannerNotification,
    markAsRead,
    markAllAsRead,
    clearAllNotifications,
    addSubscriptionNotification,
    addUsageNotification,
    addSystemNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
