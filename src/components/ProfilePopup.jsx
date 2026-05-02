import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { config } from '../config';
import { PRESET_MARKET_INSTRUMENTS } from '../constants/forexPairs';
import { MAX_TRADER_MARKETS } from '../constants/traderProfileLimits';
import { PRIMARY_GOALS, REFERRAL_SOURCES } from '../constants/onboardingSurveyOptions';
import { parseInstrumentSymbol, filterInstrumentsBySearch } from '../utils/instrumentInput';
import { startOnboardingTour } from './OnboardingTour';
import './ProfilePopup.css';

function buildTraderPrefsFromApi(tp) {
  const pairs =
    Array.isArray(tp?.primary_pairs) && tp.primary_pairs.length ? [...tp.primary_pairs] : ['EUR/USD'];
  return {
    trading_style: tp?.trading_style || 'day',
    experience_level: tp?.experience_level || 'intermediate',
    primary_pairs: pairs,
    marketing_opt_in: !!tp?.marketing_opt_in,
    primary_goal: tp?.primary_goal || 'stay_informed',
    referral_source: tp?.referral_source || 'prefer_not_say'
  };
}

function traderPrefsEqual(a, b) {
  if (!a || !b) return false;
  if (
    a.trading_style !== b.trading_style ||
    a.experience_level !== b.experience_level ||
    a.primary_goal !== b.primary_goal ||
    a.referral_source !== b.referral_source ||
    a.marketing_opt_in !== b.marketing_opt_in
  ) {
    return false;
  }
  const sa = [...(a.primary_pairs || [])].sort().join('\0');
  const sb = [...(b.primary_pairs || [])].sort().join('\0');
  return sa === sb;
}

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
  const [upgradeError, setUpgradeError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activeUsersList, setActiveUsersList] = useState(null);
  const [activeUsersLoading, setActiveUsersLoading] = useState(false);
  const [activeUsersError, setActiveUsersError] = useState(null);
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
  const [traderPrefs, setTraderPrefs] = useState({
    trading_style: 'day',
    experience_level: 'intermediate',
    primary_pairs: ['EUR/USD'],
    marketing_opt_in: false,
    primary_goal: 'stay_informed',
    referral_source: 'prefer_not_say'
  });
  const [traderPrefsLoading, setTraderPrefsLoading] = useState(false);
  const [traderPrefsSaving, setTraderPrefsSaving] = useState(false);
  const [traderPrefsError, setTraderPrefsError] = useState('');
  const [traderPrefsSavedOk, setTraderPrefsSavedOk] = useState(false);
  /** Last saved server state; used for dirty detection and Discard */
  const [traderPrefsBaseline, setTraderPrefsBaseline] = useState(null);
  const [traderCustomPair, setTraderCustomPair] = useState('');
  const [traderMarketSearch, setTraderMarketSearch] = useState('');

  const filteredTraderPresetMarkets = useMemo(
    () => filterInstrumentsBySearch(PRESET_MARKET_INSTRUMENTS, traderMarketSearch),
    [traderMarketSearch]
  );

  const traderPrefsDirty = useMemo(() => {
    if (traderPrefsLoading || !traderPrefsBaseline) return false;
    return !traderPrefsEqual(traderPrefs, traderPrefsBaseline);
  }, [traderPrefs, traderPrefsBaseline, traderPrefsLoading]);

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

  // Option A: fetch active users (admin-only) for user emails/IDs
  const fetchActiveUsers = async (days = 30) => {
    if (!currentUser) return;
    setActiveUsersLoading(true);
    setActiveUsersError(null);
    setActiveUsersList(null);
    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(
        `${config.API_BASE_URL}/api/ai-usage/stats?days=${days}&min_analyses=1`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || err.error || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setActiveUsersList(data.active_users || []);
    } catch (e) {
      setActiveUsersError(e.message || 'Failed to load active users');
    } finally {
      setActiveUsersLoading(false);
    }
  };

  const copyActiveUsersToClipboard = () => {
    if (!activeUsersList?.length) return;
    const text = activeUsersList
      .map((u) => `${u.user_email || '(no email)'}\t${u.user_id}\t${u.user_name || ''}\t${u.total_analyses || 0}`)
      .join('\n');
    const header = 'Email\tUser ID\tName\tTotal analyses\n';
    navigator.clipboard.writeText(header + text);
  };

  // Developer: either hardcoded email (legacy) or API says so (DEVELOPER_EMAILS env)
  const isDeveloper = currentUser?.email === 'kavi.cf412@gmail.com';
  const isDeveloperAccount = isDeveloper || subscriptionStatus?.status === 'developer' || subscriptionStatus?.is_developer === true;

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

  // Upgrade to Premium: create Stripe Checkout session and redirect to payment (for free users)
  const handleUpgradeToPremium = async () => {
    if (!currentUser) return;
    setIsLoadingPortal(true);
    setUpgradeError(null);
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.uid,
          email: currentUser.email,
          name: currentUser.displayName || currentUser.email,
        }),
      });
      const data = await response.json();
      if (response.ok && data.session_url) {
        window.location.href = data.session_url;
        return;
      }
      setUpgradeError(data.message || data.error || 'Could not start checkout. Please try again.');
    } catch (error) {
      console.error('Error creating checkout session:', error);
      setUpgradeError(error.message || 'Network error. Please try again.');
    } finally {
      setIsLoadingPortal(false);
    }
  };

  // Manage existing subscription: Stripe Customer Portal (for premium users)
  const handleManageSubscription = async () => {
    if (!currentUser) return;
    setIsLoadingPortal(true);
    setUpgradeError(null);
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/create-portal-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.uid,
          return_url: window.location.href
        }),
      });
      const data = await response.json();
      if (response.ok && data.url) {
        window.location.href = data.url;
        return;
      }
      setUpgradeError(data.error || 'Could not open billing portal.');
    } catch (error) {
      console.error('Error creating portal session:', error);
      setUpgradeError(error.message || 'Network error. Please try again.');
    } finally {
      setIsLoadingPortal(false);
    }
  };

  const fetchTraderPrefs = async () => {
    if (!currentUser) return;
    setTraderPrefsLoading(true);
    setTraderPrefsError('');
    setTraderPrefsSavedOk(false);
    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${config.API_BASE_URL}/api/user/trader-profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.error || 'Failed to load trading preferences');
      const tp = data.trader_profile || {};
      const next = buildTraderPrefsFromApi(tp);
      setTraderPrefs(next);
      setTraderPrefsBaseline(next);
    } catch (e) {
      setTraderPrefsError(e.message || 'Could not load trading preferences');
      setTraderPrefsBaseline(null);
    } finally {
      setTraderPrefsLoading(false);
    }
  };

  const discardTraderPrefs = useCallback(() => {
    if (!traderPrefsBaseline) return;
    setTraderPrefs({
      ...traderPrefsBaseline,
      primary_pairs: [...traderPrefsBaseline.primary_pairs]
    });
    setTraderCustomPair('');
    setTraderPrefsError('');
    setTraderPrefsSavedOk(false);
  }, [traderPrefsBaseline]);

  const toggleTraderPair = (pair) => {
    setTraderPrefs((prev) => {
      const had = prev.primary_pairs.includes(pair);
      if (had) {
        if (prev.primary_pairs.length <= 1) {
          setTimeout(
            () => setTraderPrefsError('Keep at least one market selected.'),
            0
          );
          return prev;
        }
        setTimeout(() => setTraderPrefsError(''), 0);
        return {
          ...prev,
          primary_pairs: prev.primary_pairs.filter((x) => x !== pair)
        };
      }
      if (prev.primary_pairs.length >= MAX_TRADER_MARKETS) {
        setTimeout(
          () =>
            setTraderPrefsError(
              `You can select at most ${MAX_TRADER_MARKETS} markets. Remove one to add another.`
            ),
          0
        );
        return prev;
      }
      setTimeout(() => setTraderPrefsError(''), 0);
      return { ...prev, primary_pairs: [...prev.primary_pairs, pair] };
    });
  };

  const addTraderCustomPair = () => {
    const p = parseInstrumentSymbol(traderCustomPair);
    if (!p) {
      setTraderPrefsError('Use BASE/QUOTE (e.g. EUR/USD, US500/USD, XAU/USD).');
      return;
    }
    setTraderPrefs((prev) => {
      if (prev.primary_pairs.includes(p)) {
        setTimeout(
          () => setTraderPrefsError('That market is already in your list.'),
          0
        );
        return prev;
      }
      if (prev.primary_pairs.length >= MAX_TRADER_MARKETS) {
        setTimeout(
          () =>
            setTraderPrefsError(
              `At most ${MAX_TRADER_MARKETS} markets. Remove one before adding another.`
            ),
          0
        );
        return prev;
      }
      setTimeout(() => setTraderPrefsError(''), 0);
      return { ...prev, primary_pairs: [...prev.primary_pairs, p] };
    });
    setTraderCustomPair('');
  };

  const saveTraderPrefs = async () => {
    if (!currentUser) return;
    if (!traderPrefs.primary_pairs?.length) {
      setTraderPrefsError('Select at least one market.');
      return;
    }
    if (traderPrefs.primary_pairs.length > MAX_TRADER_MARKETS) {
      setTraderPrefsError(`Reduce to ${MAX_TRADER_MARKETS} markets or fewer before saving.`);
      return;
    }
    setTraderPrefsSaving(true);
    setTraderPrefsError('');
    setTraderPrefsSavedOk(false);
    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${config.API_BASE_URL}/api/user/trader-profile`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          skipped: false,
          trading_style: traderPrefs.trading_style,
          experience_level: traderPrefs.experience_level,
          primary_pairs: traderPrefs.primary_pairs,
          marketing_opt_in: traderPrefs.marketing_opt_in,
          primary_goal: traderPrefs.primary_goal,
          referral_source: traderPrefs.referral_source
        })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.error || 'Save failed');
      const tp = data.trader_profile || {};
      const saved = buildTraderPrefsFromApi(tp);
      setTraderPrefs(saved);
      setTraderPrefsBaseline(saved);
      setTraderPrefsSavedOk(true);
      setTimeout(() => setTraderPrefsSavedOk(false), 4000);
    } catch (e) {
      setTraderPrefsError(e.message || 'Could not save trading preferences');
    } finally {
      setTraderPrefsSaving(false);
    }
  };

  // Fetch subscription status and usage data when component mounts or user changes
  useEffect(() => {
    if (isOpen && currentUser) {
      setUpgradeError(null);
      fetchSubscriptionStatus();
      fetchUsageData();
      fetchTraderPrefs();
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

  useEffect(() => {
    if (!isOpen) setTraderMarketSearch('');
  }, [isOpen]);

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

  // Only notify when we *transition* to limit reached (avoid spamming on every 30s refetch)
  const prevAtLimitRef = useRef(false);
  const prevWarningRef = useRef(false);

  // Check for usage warnings (freemium model)
  useEffect(() => {
    if (!usageData || !subscriptionStatus) return;

    const status = subscriptionStatus.status;
    let remaining = null;
    let used = 0;
    let limit = 0;
    let limitType = 'monthly';

    if (status === 'free') {
      used = usageData.monthly_usage ?? 0;
      limit = usageData.monthly_limit ?? 15;
      remaining = limit - used;
      limitType = 'monthly';
    } else if (status === 'premium') {
      used = usageData.daily_usage ?? 0;
      limit = usageData.daily_limit ?? 50;
      remaining = limit - used;
      limitType = 'daily';
    } else {
      return;
    }

    // Don't treat "limit 0" as at limit - backend uses 0 for no_subscription/unknown; real plans have limit 15 or 50
    const atLimit = remaining !== null && limit > 0 && remaining <= 0;
    const inWarning = remaining !== null && limit > 0 && remaining > 0 && ((limitType === 'monthly' && remaining <= 3) || (limitType === 'daily' && remaining <= 5));

    // Only fire limit_reached when we just crossed into "at limit" (not on every refetch)
    if (atLimit && !prevAtLimitRef.current) {
      addUsageNotification('usage_limit_reached', { used, limit, limitType });
      prevAtLimitRef.current = true;
    }
    if (!atLimit) prevAtLimitRef.current = false;

    // Only fire warning once when entering warning zone (avoid spam)
    if (inWarning && !prevWarningRef.current) {
      addUsageNotification('usage_warning', { used, limit, remaining, limitType });
      prevWarningRef.current = true;
    }
    if (!inWarning) prevWarningRef.current = false;
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
                    {isDeveloperAccount ? 'Developer' : 
                     subscriptionStatus?.status === 'free' ? 'Free Plan' :
                     subscriptionStatus?.status === 'premium' ? 'Premium Plan' :
                     subscriptionStatus?.status === 'past_due' ? 'Payment Due' : 'Free Plan'}
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

                <div className="profile-trader-prefs">
                  <h4 className="profile-trader-prefs-title">Trading preferences</h4>
                  <p className="profile-trader-prefs-hint">
                    FX, commodities, indices, crypto — macro-focused, not individual stocks. Same fields as the
                    post-signup survey.
                  </p>
                  {traderPrefsLoading ? (
                    <p className="profile-trader-prefs-loading">Loading…</p>
                  ) : (
                    <>
                      {traderPrefsError && (
                        <p className="profile-trader-prefs-error" role="alert">
                          {traderPrefsError}
                        </p>
                      )}
                      {traderPrefsSavedOk && (
                        <p className="profile-trader-prefs-saved">Trading preferences saved.</p>
                      )}
                      {traderPrefsBaseline && traderPrefsDirty && (
                        <p className="profile-trader-prefs-unsaved" role="status">
                          You have unsaved changes to trading preferences.
                        </p>
                      )}
                      <div className="form-group">
                        <label>Trading style</label>
                        <select
                          value={traderPrefs.trading_style}
                          disabled={traderPrefsSaving}
                          onChange={(e) =>
                            setTraderPrefs((p) => ({ ...p, trading_style: e.target.value }))
                          }
                        >
                          <option value="day">Day trading</option>
                          <option value="swing">Swing trading</option>
                          <option value="both">Both</option>
                          <option value="unsure">Not sure yet</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Experience level</label>
                        <select
                          value={traderPrefs.experience_level}
                          disabled={traderPrefsSaving}
                          onChange={(e) =>
                            setTraderPrefs((p) => ({ ...p, experience_level: e.target.value }))
                          }
                        >
                          <option value="beginner">Beginner</option>
                          <option value="intermediate">Intermediate</option>
                          <option value="advanced">Advanced</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Primary goal</label>
                        <select
                          value={traderPrefs.primary_goal}
                          disabled={traderPrefsSaving}
                          onChange={(e) =>
                            setTraderPrefs((p) => ({ ...p, primary_goal: e.target.value }))
                          }
                        >
                          {PRIMARY_GOALS.map((o) => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="form-group">
                        <label>How you found us</label>
                        <select
                          value={traderPrefs.referral_source}
                          disabled={traderPrefsSaving}
                          onChange={(e) =>
                            setTraderPrefs((p) => ({ ...p, referral_source: e.target.value }))
                          }
                        >
                          {REFERRAL_SOURCES.map((o) => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Markets you follow</label>
                        <div className="profile-trader-market-search-wrap">
                          <div className="profile-trader-market-search-header">
                            <label
                              className="profile-trader-market-search-label"
                              htmlFor="profile-trader-market-search"
                            >
                              Search markets
                            </label>
                            <span
                              className={`profile-trader-market-selected-pill ${
                                traderPrefs.primary_pairs.length >= MAX_TRADER_MARKETS
                                  ? 'is-at-cap'
                                  : ''
                              }`}
                              aria-live="polite"
                            >
                              {traderPrefs.primary_pairs.length}/{MAX_TRADER_MARKETS} selected
                            </span>
                          </div>
                          <input
                            id="profile-trader-market-search"
                            type="search"
                            className="profile-trader-market-search-input"
                            placeholder="Filter list — JPY, XAU, US500…"
                            value={traderMarketSearch}
                            onChange={(e) => setTraderMarketSearch(e.target.value)}
                            disabled={traderPrefsSaving}
                            autoComplete="off"
                            enterKeyHint="search"
                            aria-controls="profile-trader-preset-markets-grid"
                            aria-describedby="profile-trader-market-search-hint"
                          />
                          <p className="profile-trader-market-search-hint" id="profile-trader-market-search-hint">
                            Saved as <strong>BASE/QUOTE</strong> on your account (same as onboarding).
                          </p>
                          {traderMarketSearch.trim() ? (
                            <p className="profile-trader-market-search-meta" aria-live="polite">
                              {filteredTraderPresetMarkets.length} match
                              {filteredTraderPresetMarkets.length === 1 ? '' : 'es'} in list
                            </p>
                          ) : null}
                        </div>
                        <div className="profile-trader-pair-scroll">
                          {filteredTraderPresetMarkets.length === 0 ? (
                            <p
                              className="profile-trader-market-search-empty"
                              id="profile-trader-preset-markets-grid"
                            >
                              No presets match that search. Try another term, or add a custom{' '}
                              <strong>BASE/QUOTE</strong> below.
                            </p>
                          ) : (
                            <div className="profile-trader-pair-grid" id="profile-trader-preset-markets-grid">
                              {filteredTraderPresetMarkets.map((pair) => (
                                <label key={pair} className="profile-trader-pair-tile">
                                  <input
                                    type="checkbox"
                                    disabled={
                                      traderPrefsSaving ||
                                      (!traderPrefs.primary_pairs.includes(pair) &&
                                        traderPrefs.primary_pairs.length >= MAX_TRADER_MARKETS)
                                    }
                                    checked={traderPrefs.primary_pairs.includes(pair)}
                                    onChange={() => toggleTraderPair(pair)}
                                  />
                                  <span>{pair}</span>
                                </label>
                              ))}
                            </div>
                          )}
                        </div>
                        <p className="profile-trader-custom-label">Not in the list? Add BASE/QUOTE (e.g. US500/USD)</p>
                        <div className="profile-trader-custom-pair">
                          <input
                            type="text"
                            placeholder="e.g. GER40/EUR"
                            value={traderCustomPair}
                            disabled={traderPrefsSaving}
                            onChange={(e) => setTraderCustomPair(e.target.value)}
                            onKeyDown={(e) =>
                              e.key === 'Enter' && (e.preventDefault(), addTraderCustomPair())
                            }
                          />
                          <button
                            type="button"
                            className="secondary-btn"
                            disabled={traderPrefsSaving}
                            onClick={addTraderCustomPair}
                          >
                            Add
                          </button>
                        </div>
                      </div>
                      <label className="profile-trader-marketing">
                        <input
                          type="checkbox"
                          disabled={traderPrefsSaving}
                          checked={traderPrefs.marketing_opt_in}
                          onChange={(e) =>
                            setTraderPrefs((p) => ({ ...p, marketing_opt_in: e.target.checked }))
                          }
                        />
                        <span>Product tips & occasional offers by email</span>
                      </label>
                      <div className="profile-trader-prefs-actions">
                        <button
                          type="button"
                          className="cancel-btn profile-trader-discard-btn"
                          disabled={
                            !traderPrefsBaseline || !traderPrefsDirty || traderPrefsSaving
                          }
                          onClick={discardTraderPrefs}
                        >
                          Discard changes
                        </button>
                        <button
                          type="button"
                          className="save-btn"
                          disabled={
                            traderPrefsSaving ||
                            (traderPrefsBaseline !== null && !traderPrefsDirty)
                          }
                          onClick={saveTraderPrefs}
                        >
                          {traderPrefsSaving ? 'Saving…' : 'Save trading preferences'}
                        </button>
                      </div>
                    </>
                  )}
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

                <div className="profile-tour-section">
                  <button 
                    type="button"
                    className="product-tour-btn"
                    onClick={() => {
                      onClose();
                      startOnboardingTour();
                    }}
                  >
                    Product tour
                  </button>
                  <p className="profile-tour-hint">Replay the dashboard walkthrough</p>
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
              ) : isDeveloperAccount ? (
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

                  <div className="developer-active-users" style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--bg-secondary, #f5f5f5)', borderRadius: '8px' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '14px' }}>Active users (Option A)</h4>
                    <p style={{ margin: '0 0 0.5rem 0', fontSize: '12px', color: 'var(--text-muted, #666)' }}>
                      Users who used AI analysis in the last 30 days (user email & ID).
                    </p>
                    <button
                      type="button"
                      className="edit-btn"
                      style={{ marginRight: '0.5rem' }}
                      onClick={() => fetchActiveUsers(30)}
                      disabled={activeUsersLoading}
                    >
                      {activeUsersLoading ? 'Loading...' : 'Load active users'}
                    </button>
                    {activeUsersList && (
                      <>
                        <button type="button" className="cancel-btn" onClick={copyActiveUsersToClipboard}>
                          Copy to clipboard
                        </button>
                        <ul style={{ marginTop: '0.75rem', paddingLeft: '1.25rem', fontSize: '13px', maxHeight: '200px', overflowY: 'auto' }}>
                          {activeUsersList.length === 0 ? (
                            <li>No active users in the period.</li>
                          ) : (
                            activeUsersList.map((u, i) => (
                              <li key={u.user_id || i}>
                                <strong>{u.user_email || '(no email)'}</strong> — {u.user_id} — {u.total_analyses ?? 0} analyses
                              </li>
                            ))
                          )}
                        </ul>
                      </>
                    )}
                    {activeUsersError && (
                      <p style={{ marginTop: '0.5rem', fontSize: '12px', color: '#c62828' }}>{activeUsersError}</p>
                    )}
                  </div>
                </div>
              ) : subscriptionStatus ? (
                <div className="subscription-details">
                  <div className="subscription-status">
                    <h4>Current Plan</h4>
                    <div className={`status-badge ${subscriptionStatus.status}`}>
                      {subscriptionStatus.status === 'free' ? 'Free Plan' : 
                       subscriptionStatus.status === 'premium' ? 'Premium Plan' : 
                       subscriptionStatus.status === 'past_due' ? 'Payment Due' : 'Free Plan'}
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
                          onClick={handleUpgradeToPremium}
                          disabled={isLoadingPortal}
                        >
                          {isLoadingPortal ? 'Loading...' : 'Upgrade to Premium'}
                        </button>
                        {upgradeError && (
                          <p className="upgrade-error" style={{ color: '#dc3545', marginTop: '8px', fontSize: '14px' }}>{upgradeError}</p>
                        )}
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

                  {!isDeveloperAccount && (
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
