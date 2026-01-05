import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { config } from '../config';
import './ProfilePopup.css';

const ProfilePopup = ({ isOpen, onClose }) => {
  const { currentUser, logout } = useAuth();
  const { addSubscriptionNotification, addUsageNotification } = useNotifications();
  const [activeTab, setActiveTab] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [usageData, setUsageData] = useState(null);
  const [isLoadingSubscription, setIsLoadingSubscription] = useState(false);
  const [isLoadingPortal, setIsLoadingPortal] = useState(false);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [formData, setFormData] = useState({
    displayName: currentUser?.displayName || '',
    email: currentUser?.email || '',
    timezone: 'UTC',
    notifications: {
      email: true,
      telegram: true,
      push: false
    }
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNotificationChange = (type, value) => {
    setFormData(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [type]: value
      }
    }));
  };

  const handleSave = () => {
    // Here you would typically save to backend
    console.log('Saving profile data:', formData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setFormData({
      displayName: currentUser?.displayName || '',
      email: currentUser?.email || '',
      timezone: 'UTC',
      notifications: {
        email: true,
        telegram: true,
        push: false
      }
    });
    setIsEditing(false);
  };

  const handleLogout = async () => {
    try {
      await logout();
      onClose();
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  // Check if user is developer
  const isDeveloper = currentUser?.email === 'kavi.cf412@gmail.com';

  // Check if user is beta tester
  const isBetaTester = subscriptionStatus?.status === 'beta_tester' || subscriptionStatus?.is_beta_tester === true;

  // Fetch subscription status
  const fetchSubscriptionStatus = async () => {
    if (!currentUser) return;
    
    setIsLoadingSubscription(true);
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/subscription-status/${currentUser.uid}?email=${encodeURIComponent(currentUser.email)}`);
      if (response.ok) {
        const data = await response.json();
        // Handle null response gracefully
        if (data && typeof data === 'object') {
          setSubscriptionStatus(data);
          setLastUpdated(new Date());
        } else {
          console.warn('⚠️ Invalid subscription status response in ProfilePopup');
          // Set default free status
          setSubscriptionStatus({
            status: 'free',
            monthly_analysis_count: 0,
            daily_analysis_count: 0,
            monthly_limit: 10,
            daily_limit: null,
            is_developer: false
          });
        }
      }
    } catch (error) {
      console.error('Error fetching subscription status:', error);
    } finally {
      setIsLoadingSubscription(false);
    }
  };

  // Fetch usage data
  const fetchUsageData = async () => {
    if (!currentUser) return;
    
    setIsLoadingUsage(true);
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/check-analysis-permission/${currentUser.uid}?email=${currentUser.email}`);
      if (response.ok) {
        const data = await response.json();
        setUsageData(data);
      }
    } catch (error) {
      console.error('Error fetching usage data:', error);
    } finally {
      setIsLoadingUsage(false);
    }
  };

  // Handle subscription management
  const handleManageSubscription = async () => {
    if (!currentUser) return;
    
    setIsLoadingPortal(true);
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/create-portal-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.uid,
          return_url: window.location.href
        }),
      });
      
      if (response.ok) {
        const { url } = await response.json();
        window.location.href = url; // Redirect to Stripe Customer Portal
      } else {
        console.error('Failed to create portal session');
      }
    } catch (error) {
      console.error('Error creating portal session:', error);
    } finally {
      setIsLoadingPortal(false);
    }
  };

  // Fetch subscription status and usage data when component mounts or user changes
  useEffect(() => {
    if (isOpen && currentUser) {
      fetchSubscriptionStatus();
      fetchUsageData();
    }
  }, [isOpen, currentUser]);

  // Refresh subscription status when returning from Stripe portal
  useEffect(() => {
    const handleFocus = () => {
      if (isOpen && currentUser) {
        // Refresh status when user returns from Stripe portal
        fetchSubscriptionStatus();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [isOpen, currentUser]);

  // Auto-refresh subscription status and usage data every 30 seconds when popup is open
  useEffect(() => {
    if (!isOpen || !currentUser) return;

    const interval = setInterval(() => {
      fetchSubscriptionStatus();
      fetchUsageData();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [isOpen, currentUser]);

  const getUserDisplayName = (truncate = false) => {
    if (!currentUser) return 'Guest';
    
    let displayName = '';
    
    if (currentUser.displayName) {
      displayName = currentUser.displayName;
    } else if (currentUser.email) {
      const emailName = currentUser.email.split('@')[0];
      const nameParts = emailName.split('.');
      if (nameParts.length > 0) {
        displayName = nameParts[0].charAt(0).toUpperCase() + nameParts[0].slice(1);
      } else {
        displayName = emailName;
      }
    } else {
      displayName = 'User';
    }
    
    // Only truncate if requested (for navbar use)
    if (truncate && displayName.length > 8) {
      return displayName.substring(0, 8);
    }
    
    return displayName;
  };

  const getUserInitials = () => {
    const name = getUserDisplayName();
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  // Check for usage warnings (freemium model)
  useEffect(() => {
    if (usageData && subscriptionStatus) {
      const status = subscriptionStatus.status;
      
      if (status === 'free') {
        // Free tier: monthly limit
        const { monthly_usage, monthly_limit } = usageData;
        const remaining = monthly_limit - monthly_usage;
        
        if (remaining === 0) {
          addUsageNotification('usage_limit_reached', { used: monthly_usage, limit: monthly_limit });
        } else if (remaining <= 3) {
          addUsageNotification('usage_warning', { used: monthly_usage, limit: monthly_limit, remaining });
        }
      } else if (status === 'premium') {
        // Premium tier: daily limit
        const { daily_usage, daily_limit } = usageData;
        const remaining = daily_limit - daily_usage;
        
        if (remaining === 0) {
          addUsageNotification('usage_limit_reached', { used: daily_usage, limit: daily_limit });
        } else if (remaining <= 5) {
          addUsageNotification('usage_warning', { used: daily_usage, limit: daily_limit, remaining });
        }
      }
    }
  }, [usageData, subscriptionStatus, addUsageNotification]);

  if (!isOpen) return null;

  return (
    <div className="profile-popup-overlay" onClick={onClose}>
      <div className="profile-popup" onClick={(e) => e.stopPropagation()}>
        <div className="profile-popup-header">
          <h2>User Profile</h2>
          <button className="close-button" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="profile-popup-tabs">
          <button 
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Profile
          </button>

          <button 
            className={`tab-btn ${activeTab === 'billing' ? 'active' : ''}`}
            onClick={() => setActiveTab('billing')}
          >
            Billing
          </button>
          <button 
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
          <button 
            className={`tab-btn ${activeTab === 'support' ? 'active' : ''}`}
            onClick={() => setActiveTab('support')}
          >
            Support
          </button>
          <button 
            className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            Security
          </button>
        </div>

        <div className="profile-popup-content">
          {activeTab === 'profile' && (
            <div className="profile-section">
              <div className="profile-avatar-section">
                <div className="profile-avatar">
                  <span className="avatar-initials">{getUserInitials()}</span>
                </div>
                <div className="profile-info">
                  <h3>{getUserDisplayName()}</h3>
                  <p className="user-email">{currentUser?.email || 'No email'}</p>
                  <p className="user-status">
                    {isDeveloper ? 'Developer' : 
                     subscriptionStatus?.status === 'free' ? 'Free Plan' :
                     subscriptionStatus?.status === 'premium' ? 'Premium Plan' :
                     subscriptionStatus?.status === 'developer' ? 'Developer' : 'Free Plan'}
                  </p>
                </div>
              </div>

              <div className="profile-form">
                <div className="form-group">
                  <label>Display Name</label>
                  <input
                    type="text"
                    value={formData.displayName}
                    onChange={(e) => handleInputChange('displayName', e.target.value)}
                    disabled={!isEditing}
                    placeholder="Enter display name"
                  />
                </div>

                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    disabled={!isEditing}
                    placeholder="Enter email"
                  />
                </div>

                <div className="form-group">
                  <label>Timezone</label>
                  <select
                    value={formData.timezone}
                    onChange={(e) => handleInputChange('timezone', e.target.value)}
                    disabled={!isEditing}
                  >
                    <option value="UTC">UTC</option>
                    <option value="EST">Eastern Time</option>
                    <option value="PST">Pacific Time</option>
                    <option value="GMT">GMT</option>
                    <option value="CET">Central European Time</option>
                  </select>
                </div>

                <div className="profile-actions">
                  {!isEditing ? (
                    <button 
                      className="edit-btn"
                      onClick={() => setIsEditing(true)}
                    >
                      Edit Profile
                    </button>
                  ) : (
                    <div className="edit-actions">
                      <button 
                        className="save-btn"
                        onClick={handleSave}
                      >
                        Save Changes
                      </button>
                      <button 
                        className="cancel-btn"
                        onClick={handleCancel}
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="settings-section">
              <h3>Notification Preferences</h3>
              
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Email Notifications</h4>
                    <p>Receive important updates via email</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={formData.notifications.email}
                      onChange={(e) => handleNotificationChange('email', e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Telegram Alerts</h4>
                    <p>Get instant alerts on Telegram</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={formData.notifications.telegram}
                      onChange={(e) => handleNotificationChange('telegram', e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Push Notifications</h4>
                    <p>Browser push notifications</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={formData.notifications.push}
                      onChange={(e) => handleNotificationChange('push', e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <div className="settings-group">
                <h4>Data & Privacy</h4>
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Data Export</h4>
                    <p>Download your data</p>
                  </div>
                  <button className="secondary-btn">Export</button>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Delete Account</h4>
                    <p>Permanently delete your account</p>
                  </div>
                  <button className="danger-btn">Delete</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="billing-section">
              <h3>Subscription & Billing</h3>
              
              {isLoadingSubscription ? (
                <div className="loading-state">
                  <p>Loading subscription details...</p>
                </div>
              ) : isDeveloper ? (
                <div className="subscription-details developer-account">
                  <div className="subscription-status">
                    <h4>Current Plan</h4>
                    <div className="status-badge developer">
                      Developer Account
                    </div>
                  </div>

                  <div className="developer-info">
                    <p><strong>Account Type:</strong> Developer</p>
                    <p><strong>Access Level:</strong> Unlimited</p>
                    <p><strong>Daily Limit:</strong> Unlimited AI analyses</p>
                    <p><strong>Payment Required:</strong> No</p>
                    <p><strong>Purpose:</strong> Development & Testing</p>
                  </div>

                  <div className="developer-note">
                    <p>This is a developer account with full access for testing purposes. No payment required.</p>
                  </div>
                </div>
              ) : subscriptionStatus ? (
                <div className="subscription-details">
                  <div className="subscription-status">
                    <h4>Current Plan</h4>
                    <div className={`status-badge ${subscriptionStatus.status}`}>
                      {subscriptionStatus.status === 'free' ? 'Free Plan' : 
                       subscriptionStatus.status === 'premium' ? 'Premium Plan' : 
                       subscriptionStatus.status === 'past_due' ? 'Payment Due' : 'Unknown'}
                    </div>
                  </div>

                  {subscriptionStatus.status === 'free' && (
                    <div className="free-info">
                      <p><strong>Plan:</strong> Free Forever</p>
                      <p><strong>Monthly Limit:</strong> {subscriptionStatus.monthly_analysis_count !== undefined ? `${subscriptionStatus.monthly_analysis_count}/15` : 'Loading...'} AI analyses</p>
                      <p><strong>Cost:</strong> $0/month</p>
                      <p><strong>Resets:</strong> Monthly on the 1st</p>
                      
                      {subscriptionStatus.monthly_analysis_count !== undefined && (
                        <div className="usage-progress">
                          <div className="usage-bar">
                            <div 
                              className="usage-fill" 
                              style={{ 
                                width: `${Math.min((subscriptionStatus.monthly_analysis_count / 15) * 100, 100)}%`,
                                backgroundColor: subscriptionStatus.monthly_analysis_count >= 15 ? '#f44336' : '#4caf50'
                              }}
                            ></div>
                          </div>
                          <small>
                            {subscriptionStatus.monthly_analysis_count >= 15 
                              ? 'Monthly limit reached' 
                              : `${15 - subscriptionStatus.monthly_analysis_count} remaining this month`}
                          </small>
                        </div>
                      )}
                      
                      <div className="upgrade-prompt">
                        <h4>Want More?</h4>
                        <p>Upgrade to Premium for 50 AI analyses per day!</p>
                        <ul className="premium-features">
                          <li>50 analyses per day (~1,500/month)</li>
                          <li>Priority support</li>
                          <li>Advanced features</li>
                          <li>Only $14.99/month</li>
                        </ul>
                        <button 
                          className="upgrade-btn"
                          onClick={handleManageSubscription}
                          disabled={isLoadingPortal}
                        >
                          {isLoadingPortal ? 'Loading...' : 'Upgrade to Premium'}
                        </button>
                      </div>
                    </div>
                  )}

                  {subscriptionStatus.status === 'premium' && (
                    <div className="premium-info">
                      <p><strong>Plan:</strong> Premium ($14.99/month)</p>
                      <p><strong>Daily Limit:</strong> {subscriptionStatus.daily_analysis_count !== undefined ? `${subscriptionStatus.daily_analysis_count}/50` : 'Loading...'} AI analyses</p>
                      {subscriptionStatus.current_period_end && (
                        <p><strong>Next Billing:</strong> {new Date(subscriptionStatus.current_period_end * 1000).toLocaleDateString()}</p>
                      )}
                      <p><strong>Resets:</strong> Daily at midnight</p>
                      
                      {subscriptionStatus.daily_analysis_count !== undefined && (
                        <div className="usage-progress">
                          <div className="usage-bar">
                            <div 
                              className="usage-fill" 
                              style={{ 
                                width: `${Math.min((subscriptionStatus.daily_analysis_count / 50) * 100, 100)}%`,
                                backgroundColor: subscriptionStatus.daily_analysis_count >= 50 ? '#f44336' : '#4caf50'
                              }}
                            ></div>
                          </div>
                          <small>
                            {subscriptionStatus.daily_analysis_count >= 50 
                              ? 'Daily limit reached' 
                              : `${50 - subscriptionStatus.daily_analysis_count} remaining today`}
                          </small>
                        </div>
                      )}
                      
                      <div className="premium-perks">
                        <p>Thank you for being a Premium member!</p>
                      </div>
                    </div>
                  )}

                  {!isDeveloper && (
                    <div className="billing-actions">
                      <button 
                        className="primary-btn"
                        onClick={() => window.location.href = 'https://billing.stripe.com/p/login/4gM28s2oMbKSbhO4lt83C00'}
                      >
                        Manage Subscription
                      </button>
                      
                      <button 
                        className="secondary-btn"
                        onClick={() => {
                          fetchSubscriptionStatus();
                          fetchUsageData();
                        }}
                        disabled={isLoadingSubscription || isLoadingUsage}
                        style={{ marginTop: '10px' }}
                      >
                        {isLoadingSubscription || isLoadingUsage ? 'Refreshing...' : 'Refresh Status'}
                      </button>
                      
                      {lastUpdated && (
                        <div className="last-updated">
                          <small>Last updated: {lastUpdated.toLocaleTimeString()}</small>
                        </div>
                      )}
                    </div>
                  )}

                  {isBetaTester && (
                    <div className="beta-tester-actions">
                      <button 
                        className="secondary-btn"
                        onClick={() => {
                          fetchSubscriptionStatus();
                          fetchUsageData();
                        }}
                        disabled={isLoadingSubscription || isLoadingUsage}
                      >
                        {isLoadingSubscription || isLoadingUsage ? 'Refreshing...' : 'Refresh Status'}
                      </button>
                      
                      {lastUpdated && (
                        <div className="last-updated">
                          <small>Last updated: {lastUpdated.toLocaleTimeString()}</small>
                        </div>
                      )}
                    </div>
                  )}

                  {!isBetaTester && (
                    <div className="billing-help">
                      <h4>Need Help?</h4>
                      <p>You can manage your subscription, update payment methods, and cancel anytime through your Stripe dashboard.</p>
                      <ul>
                        <li>Update payment method</li>
                        <li>View billing history</li>
                        <li>Cancel subscription</li>
                        <li>Download invoices</li>
                      </ul>
                    </div>
                  )}

                  {isBetaTester && (
                    <div className="beta-tester-help">
                      <h4>Beta Tester Support</h4>
                      <p>As a beta tester, you have lifetime access to FXSentinel. No payment management needed!</p>
                      <ul>
                        <li>Lifetime access to all features</li>
                        <li>15 AI analyses per day</li>
                        <li>Premium features included</li>
                        <li>Direct support for feedback</li>
                      </ul>
                      <div className="beta-tester-feedback">
                        <p><strong>Have feedback?</strong> We'd love to hear from you!</p>
                        <button 
                          className="secondary-btn"
                          onClick={() => window.open('mailto:fxsentinelapp@gmail.com?subject=Beta Tester Feedback', '_blank')}
                        >
                          Send Feedback
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="no-subscription">
                  <p>Loading subscription information...</p>
                  <p>If this persists, please refresh the page or contact support.</p>
                  <button className="primary-btn" onClick={() => window.location.reload()}>
                    Refresh Page
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'support' && (
            <div className="support-section">
              <h3>Customer Support</h3>
              
              <div className="support-grid">
                <div className="support-card">
                  <div className="support-icon"></div>
                  <h4>Contact Support</h4>
                  <p>Get help with billing, technical issues, or general questions</p>
                  <button 
                    className="primary-btn"
                    onClick={() => window.open('mailto:fxsentinelapp@gmail.com?subject=FXSentinel Support Request', '_blank')}
                  >
                    Email Support
                  </button>
                </div>

                <div className="support-card">
                  <div className="support-icon"></div>
                  <h4>FAQ</h4>
                  <p>Find answers to common questions about FXSentinel</p>
                  <button 
                    className="secondary-btn"
                    onClick={() => setActiveTab('faq')}
                  >
                    View FAQ
                  </button>
                </div>

                <div className="support-card">
                  <div className="support-icon"></div>
                  <h4>Refund Policy</h4>
                  <p>Learn about our refund and cancellation policies</p>
                  <button 
                    className="secondary-btn"
                    onClick={() => setActiveTab('refund-policy')}
                  >
                    View Policy
                  </button>
                </div>

                <div className="support-card">
                  <div className="support-icon"></div>
                  <h4>Request Refund</h4>
                  <p>Submit a refund request for your subscription</p>
                  <button 
                    className="secondary-btn"
                    onClick={() => setActiveTab('refund-request')}
                  >
                    Request Refund
                  </button>
                </div>
              </div>

              <div className="support-info">
                <h4>Support Hours</h4>
                <p>We respond within max 24 hours during business days.</p>
                <p><strong>Email:</strong> fxsentinelapp@gmail.com</p>
                <p><strong>Response Time:</strong> 24-48 hours</p>
              </div>
            </div>
          )}

          {activeTab === 'faq' && (
            <div className="faq-section">
              <div className="faq-header">
                <button className="back-btn" onClick={() => setActiveTab('support')}>
                  ← Back to Support
                </button>
                <h3>Frequently Asked Questions</h3>
              </div>

              <div className="faq-list">
                <div className="faq-item">
                  <h4>What's included in the Free plan?</h4>
                  <p>The Free plan includes 15 AI analyses per month, access to all economic calendar events, live news feeds, and Telegram alerts. No credit card required, free forever.</p>
                </div>

                <div className="faq-item">
                  <h4>What's the difference between Free and Premium?</h4>
                  <p>Free gives you 15 analyses per month. Premium gives you 50 analyses per day (~1,500/month) for $14.99/month, plus priority support and advanced features.</p>
                </div>

                <div className="faq-item">
                  <h4>How do I upgrade to Premium?</h4>
                  <p>Go to Profile → Billing → Upgrade to Premium. You'll be redirected to Stripe for secure payment. Instant access after payment.</p>
                </div>

                <div className="faq-item">
                  <h4>How do I cancel my Premium subscription?</h4>
                  <p>Go to Profile → Billing → Manage Subscription. You can cancel anytime. You'll be downgraded to the Free plan (15/month) with no data loss.</p>
                </div>

                <div className="faq-item">
                  <h4>When do usage limits reset?</h4>
                  <p>Free plan resets monthly on the 1st. Premium plan resets daily at midnight UTC. Developer accounts have unlimited access.</p>
                </div>

                <div className="faq-item">
                  <h4>Can I get a refund?</h4>
                  <p>Yes! We offer a 30-day money-back guarantee. Contact fxsentinelapp@gmail.com for refund requests.</p>
                </div>

                <div className="faq-item">
                  <h4>What payment methods do you accept?</h4>
                  <p>We accept all major credit cards, debit cards, and digital wallets through Stripe.</p>
                </div>

                <div className="faq-item">
                  <h4>Is my data secure?</h4>
                  <p>Absolutely. We use bank-level encryption and never store your payment information.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'refund-policy' && (
            <div className="refund-policy-section">
              <div className="policy-header">
                <button className="back-btn" onClick={() => setActiveTab('support')}>
                  ← Back to Support
                </button>
                <h3>Refund Policy</h3>
              </div>

              <div className="policy-content">
                <div className="policy-section">
                  <h4>30-Day Money-Back Guarantee</h4>
                  <p>We're confident you'll love FXSentinel. If you're not satisfied within 30 days of your first payment, we'll give you a full refund.</p>
                </div>

                <div className="policy-section">
                  <h4>How to Request a Refund</h4>
                  <ul>
                    <li>Email us at fxsentinelapp@gmail.com</li>
                    <li>Include your account email and reason for refund</li>
                    <li>We'll process your request within 3-5 business days</li>
                    <li>Refunds are issued to your original payment method</li>
                  </ul>
                </div>

                <div className="policy-section">
                  <h4>Refund Processing</h4>
                  <ul>
                    <li>Refunds typically appear in 5-10 business days</li>
                    <li>Processing time depends on your bank/card issuer</li>
                    <li>You'll receive an email confirmation when processed</li>
                  </ul>
                </div>

                <div className="policy-section">
                  <h4>Exceptions</h4>
                  <p>Refunds may be denied if we detect abuse of our service or violation of our terms of service.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'refund-request' && (
            <div className="refund-request-section">
              <div className="request-header">
                <button className="back-btn" onClick={() => setActiveTab('support')}>
                  ← Back to Support
                </button>
                <h3>Request a Refund</h3>
              </div>

              <div className="refund-form">
                <div className="form-group">
                  <label>Account Email</label>
                  <input 
                    type="email" 
                    value={currentUser?.email || ''} 
                    disabled 
                    className="disabled-input"
                  />
                </div>

                <div className="form-group">
                  <label>Reason for Refund *</label>
                  <select className="form-select">
                    <option value="">Select a reason</option>
                    <option value="not-satisfied">Not satisfied with the service</option>
                    <option value="technical-issues">Technical issues</option>
                    <option value="billing-error">Billing error</option>
                    <option value="unexpected-charges">Unexpected charges</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Additional Details</label>
                  <textarea 
                    placeholder="Please provide more details about your refund request..."
                    rows="4"
                    className="form-textarea"
                  ></textarea>
                </div>

                <div className="form-actions">
                  <button 
                    className="primary-btn"
                    onClick={async () => {
                      try {
                        // Get form data
                        const reasonSelect = document.querySelector('.form-select');
                        const detailsTextarea = document.querySelector('.form-textarea');
                        
                        const reason = reasonSelect ? reasonSelect.value : '';
                        const details = detailsTextarea ? detailsTextarea.value : '';
                        
                        if (!reason) {
                          alert('Please select a reason for the refund request.');
                          return;
                        }
                        
                        // Submit refund request
                        const response = await fetch(config.endpoints.requestRefund, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json',
                          },
                          body: JSON.stringify({
                            email: currentUser?.email || '',
                            reason: reason,
                            details: details
                          })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                          alert(result.message);
                          setActiveTab('support');
                        } else {
                          alert('Failed to submit refund request. Please try again or contact support directly.');
                        }
                      } catch (error) {
                        console.error('Error submitting refund request:', error);
                        alert('Failed to submit refund request. Please try again or contact support directly.');
                      }
                    }}
                  >
                    Submit Refund Request
                  </button>
                  <button 
                    className="secondary-btn"
                    onClick={() => setActiveTab('support')}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="security-section">
              <h3>Security Settings</h3>
              
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Change Password</h4>
                    <p>Update your account password</p>
                  </div>
                  <button className="secondary-btn">Change</button>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Two-Factor Authentication</h4>
                    <p>Add an extra layer of security</p>
                  </div>
                  <button className="secondary-btn">Enable</button>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Active Sessions</h4>
                    <p>Manage your active sessions</p>
                  </div>
                  <button className="secondary-btn">View</button>
                </div>
              </div>

              <div className="settings-group">
                <h4>Account Actions</h4>
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Logout</h4>
                    <p>Sign out of your account</p>
                  </div>
                  <button className="logout-btn" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfilePopup;
