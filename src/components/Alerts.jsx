import React, { useState, useEffect } from 'react';
import { formatTimeForTimezone } from '../utils/timezoneUtils';
import { config } from '../config';
import { useAuth } from '../contexts/AuthContext';
import './Alerts.css';

function Alerts({ alerts, alertStats, alertSettings, updateAlertSettings }) {
  const { currentUser } = useAuth();
  
  // State for different sections and functionality
  const [activeTab, setActiveTab] = useState('setup'); // setup, preferences, history
  const [telegramSetup, setTelegramSetup] = useState({
    step: 'connect', // connect, verify, complete
    botUsername: '@FXSentinelBot',
    instructions: [],
    botLink: '',
    loading: false
  });
  
  const [alertPreferences, setAlertPreferences] = useState({
    channels: {
      telegram: { enabled: false, chatId: '', username: '' },
      email: { enabled: false, address: '' }
    },
    preferences: {
      impactLevels: { high: true, medium: true, low: false },
      alertTypes: { preNews: true, postNews: true, liveNews: true, technicalAnalysis: false },
      currencyPairs: ['EUR/USD', 'USD/JPY', 'GBP/USD'],
      quietHours: { enabled: false, start: '22:00', end: '06:00', timezone: 'UTC' }
    }
  });

  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  
  // Test alert functionality
  const [testAlertLoading, setTestAlertLoading] = useState(false);
  const [testAlertStatus, setTestAlertStatus] = useState(null);

  // Inline errors (replaces alert() for setup/verify) and disconnect confirmation
  const [setupError, setSetupError] = useState(null);
  const [verifyError, setVerifyError] = useState(null);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);

  // Alert history functionality
  const [alertHistory, setAlertHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyFilters, setHistoryFilters] = useState({
    channel: 'all',
    type: 'all'
  });

  // Get authenticated user ID
  const getUserId = () => {
    if (!currentUser) {
      throw new Error('User not authenticated');
    }
    return currentUser.uid || currentUser.email || 'authenticated_user';
  };

  // Load saved preferences on component mount
  useEffect(() => {
    if (currentUser) {
      loadAlertPreferences();
      checkTelegramConnection();
    }
  }, [currentUser]);

  // Load alert history when history tab is active (tab commented out for now)
  // useEffect(() => {
  //   if (activeTab === 'history' && currentUser) {
  //     loadAlertHistory();
  //   }
  // }, [activeTab, currentUser]);

  // Check current Telegram connection status
  const checkTelegramConnection = async () => {
    try {
      const userId = getUserId();
      const response = await fetch(`${config.API_BASE_URL}/api/telegram/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.connected) {
          // User has Telegram connected, update both states
          setTelegramSetup(prev => ({
            ...prev,
            step: 'complete'
          }));
          
          // Update alert preferences if not already set
          setAlertPreferences(prev => ({
            ...prev,
            channels: {
              ...prev.channels,
              telegram: { 
                enabled: true, 
                chatId: data.chatId || '', 
                username: data.username || '' 
              }
            }
          }));
          
          console.log('✅ Telegram connection verified and updated');
        }
      }
    } catch (error) {
      console.error('Error checking Telegram connection:', error);
    }
  };

  // Load alert preferences from backend
  const loadAlertPreferences = async () => {
    try {
      setLoading(true);
      const userId = getUserId();
      const response = await fetch(`${config.API_BASE_URL}/api/alerts/user-settings?userId=${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.settings) {
          setAlertPreferences(prev => ({
            ...prev,
            ...data.settings
          }));
          console.log('✅ Loaded saved alert preferences');
          
          // Check if Telegram is already connected and update telegramSetup state
          const telegramSettings = data.settings.channels?.telegram;
          if (telegramSettings?.enabled && telegramSettings?.chatId) {
            setTelegramSetup(prev => ({
              ...prev,
              step: 'complete'
            }));
            console.log('✅ Telegram already connected, setting step to complete');
          }
        }
      } else {
        console.log('No saved preferences found, using defaults');
      }
    } catch (error) {
      console.error('Error loading alert preferences:', error);
      // Continue with default preferences
    } finally {
      setLoading(false);
    }
  };

  // Save alert preferences to backend
  const saveAlertPreferences = async (newPreferences) => {
    try {
      setSavingSettings(true);
      const userId = getUserId();
      const response = await fetch(`${config.API_BASE_URL}/api/alerts/user-settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: userId,
          settings: newPreferences
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('✅ Alert preferences saved successfully');
        } else {
          console.error('Failed to save preferences:', data.error);
        }
      } else {
        console.error('Failed to save preferences:', response.status);
      }
    } catch (error) {
      console.error('Error saving alert preferences:', error);
    } finally {
      setSavingSettings(false);
    }
  };

  // Save preferences whenever they change (with debouncing)
  useEffect(() => {
    if (currentUser) {
      const timeoutId = setTimeout(() => {
        saveAlertPreferences(alertPreferences);
      }, 1000); // Save after 1 second of no changes

      return () => clearTimeout(timeoutId);
    }
  }, [alertPreferences, currentUser]);

  // Clear test alert status and inline errors when user changes
  useEffect(() => {
    setTestAlertStatus(null);
    setSetupError(null);
    setVerifyError(null);
  }, [currentUser]);

  // Telegram Bot Setup Flow
  const setupTelegramBot = async () => {
    if (!currentUser) {
      setSetupError('Please log in to set up Telegram alerts.');
      return;
    }
    setSetupError(null);
    setTelegramSetup(prev => ({ ...prev, loading: true }));
    try {
      const userId = getUserId();
      const response = await fetch(`${config.API_BASE_URL}/api/telegram/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId })
      });
      const data = await response.json();
      if (data.success) {
        setTelegramSetup({
          step: 'verify',
          botUsername: data.botUsername,
          instructions: [
            'Click the link below to open Telegram (or "Open in app" if on mobile).',
            "You'll be connected automatically—no need to type anything.",
            "Return here and click \"I've completed setup in Telegram\" to finish."
          ],
          botLink: data.botLink,
          loading: false
        });
      } else {
        if (data.subscription_required) {
          setSetupError('Subscription required. Please renew your subscription to use Telegram alerts.');
          setTelegramSetup(prev => ({ ...prev, loading: false }));
          return;
        }
        throw new Error(data.error || 'Failed to setup Telegram bot');
      }
    } catch (error) {
      console.error('Error setting up Telegram bot:', error);
      setSetupError(error.message || 'Failed to setup Telegram bot. Please try again.');
      setTelegramSetup(prev => ({ ...prev, loading: false }));
    }
  };

  const verifyTelegramConnection = async () => {
    if (!currentUser) {
      setVerifyError('Please log in to verify your connection.');
      return;
    }
    setVerifyError(null);
    setTelegramSetup(prev => ({ ...prev, loading: true }));
    try {
      const userId = getUserId();
      const response = await fetch(`${config.API_BASE_URL}/api/telegram/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId })
      });
      const data = await response.json();
      if (data.success && data.connected) {
        setTelegramSetup({
          step: 'complete',
          botUsername: data.botUsername || '@FXSentinelBot',
          instructions: [],
          loading: false
        });
        setAlertPreferences(prev => ({
          ...prev,
          channels: {
            ...prev.channels,
            telegram: {
              enabled: true,
              chatId: data.chatId || '',
              username: data.username || ''
            }
          }
        }));
      } else {
        if (data.subscription_required) {
          setVerifyError('Subscription required. Please renew to use Telegram alerts.');
          setTelegramSetup(prev => ({ ...prev, loading: false }));
          return;
        }
        throw new Error(data.error || 'Verification failed. Complete the steps in Telegram and try again.');
      }
    } catch (error) {
      console.error('Error verifying Telegram connection:', error);
      setVerifyError(error.message || 'Failed to verify. Complete setup in Telegram and try again.');
      setTelegramSetup(prev => ({ ...prev, loading: false }));
    }
  };

  const updatePreference = (category, setting, value) => {
    const updatedPreferences = {
      ...alertPreferences,
      preferences: {
        ...alertPreferences.preferences,
        [category]: {
          ...alertPreferences.preferences[category],
          [setting]: value
        }
      }
    };
    setAlertPreferences(updatedPreferences);
    if (updateAlertSettings) {
      updateAlertSettings('preferences', updatedPreferences.preferences);
    }
  };

  const setAllAlertTypes = (checked) => {
    const updatedPreferences = {
      ...alertPreferences,
      preferences: {
        ...alertPreferences.preferences,
        alertTypes: {
          liveNews: checked,
          preNews: checked,
          postNews: checked,
          technicalAnalysis: checked
        }
      }
    };
    setAlertPreferences(updatedPreferences);
    if (updateAlertSettings) {
      updateAlertSettings('preferences', updatedPreferences.preferences);
    }
  };

  const addCurrencyPair = (pair) => {
    if (pair && !alertPreferences.preferences.currencyPairs.includes(pair)) {
      const updatedPreferences = {
        ...alertPreferences,
        preferences: {
          ...alertPreferences.preferences,
          currencyPairs: [...alertPreferences.preferences.currencyPairs, pair]
        }
      };
      setAlertPreferences(updatedPreferences);
      
      // Save to backend
      if (updateAlertSettings) {
        updateAlertSettings('preferences', updatedPreferences.preferences);
      }
    }
  };

  const removeCurrencyPair = (pair) => {
    const updatedPreferences = {
      ...alertPreferences,
      preferences: {
        ...alertPreferences.preferences,
        currencyPairs: alertPreferences.preferences.currencyPairs.filter(p => p !== pair)
      }
    };
    setAlertPreferences(updatedPreferences);
    if (updateAlertSettings) {
      updateAlertSettings('preferences', updatedPreferences.preferences);
    }
  };

  const CURRENCY_PAIRS_OPTIONS = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD', 'NZD/USD', 'EUR/GBP', 'EUR/JPY', 'GBP/JPY'];

  const setAllCurrencyPairs = (pairs) => {
    const updatedPreferences = {
      ...alertPreferences,
      preferences: {
        ...alertPreferences.preferences,
        currencyPairs: pairs
      }
    };
    setAlertPreferences(updatedPreferences);
    if (updateAlertSettings) {
      updateAlertSettings('preferences', updatedPreferences.preferences);
    }
  };

  const confirmDisconnectTelegram = () => {
    setShowDisconnectConfirm(true);
  };

  const disconnectTelegram = () => {
    setShowDisconnectConfirm(false);
    const updatedPreferences = {
      ...alertPreferences,
      channels: {
        ...alertPreferences.channels,
        telegram: { enabled: false, chatId: '', username: '' }
      }
    };
    setAlertPreferences(updatedPreferences);
    setTelegramSetup({ step: 'connect', loading: false });
    setTestAlertStatus(null);
    saveAlertPreferences(updatedPreferences);
  };

  // Send test alert
  const sendTestAlert = async () => {
    if (!currentUser) {
      alert('Please log in to send test alerts');
      return;
    }

    setTestAlertLoading(true);
    setTestAlertStatus(null);
    
    try {
      const userId = getUserId();
      const response = await fetch(`${config.API_BASE_URL}/api/alerts/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          userId: userId,
          alertType: 'test',
          message: 'This is a test alert from FXSentinel to verify your connection is working!'
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setTestAlertStatus({
          type: 'success',
          message: '✅ Test alert sent successfully! Check your Telegram.'
        });
      } else {
        throw new Error(data.error || 'Failed to send test alert');
      }
    } catch (error) {
      console.error('Error sending test alert:', error);
      setTestAlertStatus({
        type: 'error',
        message: `❌ Failed to send test alert: ${error.message}`
      });
    } finally {
      setTestAlertLoading(false);
    }
  };

  // Load alert history from backend
  const loadAlertHistory = async () => {
    try {
      setHistoryLoading(true);
      const userId = getUserId();
      const response = await fetch(`${config.API_BASE_URL}/api/alerts/history?userId=${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.history) {
          setAlertHistory(data.history);
          console.log('✅ Loaded alert history');
        } else {
          console.log('No history found for user');
          setAlertHistory([]);
        }
      } else {
        console.error('Failed to load alert history:', response.status);
        setAlertHistory([]);
      }
    } catch (error) {
      console.error('Error loading alert history:', error);
      setAlertHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Filter alert history based on current filters
  const getFilteredHistory = () => {
    return alertHistory.filter(alert => {
      // Filter by channel
      if (historyFilters.channel !== 'all') {
        if (historyFilters.channel === 'telegram' && !alert.sent_via?.includes('telegram')) {
          return false;
        }
        if (historyFilters.channel === 'email' && !alert.sent_via?.includes('email')) {
          return false;
        }
      }
      
      // Filter by type
      if (historyFilters.type !== 'all') {
        if (alert.alert_type !== historyFilters.type) {
          return false;
        }
      }
      
      return true;
    });
  };

  // Get alert type display name
  const getAlertTypeDisplay = (type) => {
    const typeMap = {
      'liveNews': 'Live News',
      'preNews': 'Pre-News',
      'postNews': 'Post-News',
      'preEvent': 'Pre-Event',
      'test': 'Test Alert',
      'technicalAnalysis': 'Technical Analysis'
    };
    return typeMap[type] || type;
  };

  // Get alert icon based on type
  const getAlertIcon = (type) => {
    const iconMap = {
      'liveNews': '📰',
      'preNews': '⏰',
      'postNews': '📊',
      'preEvent': '📅',
      'test': '🧪',
      'technicalAnalysis': '📈'
    };
    return iconMap[type] || '📢';
  };

  return (
    <div className="alerts-tab">
      <div className="alerts-container">
        {/* Navigation Tabs */}
        <div className="alerts-tabs">
          <button 
            className={`tab-btn ${activeTab === 'setup' ? 'active' : ''}`}
            onClick={() => setActiveTab('setup')}
          >
            Setup
          </button>
          <button 
            className={`tab-btn ${activeTab === 'preferences' ? 'active' : ''}`}
            onClick={() => setActiveTab('preferences')}
          >
            Preferences
          </button>
          {/* History tab – commented out for now; logic kept for potential future use */}
          {/* <button 
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button> */}
        </div>

        {/* Settings Save Indicator */}
        {savingSettings && (
          <div className="settings-save-indicator">
            <span>Saving settings...</span>
          </div>
        )}

        {/* Tab Content */}
        <div className="alerts-tab-content">
          
          {/* Setup Tab */}
          {activeTab === 'setup' && (
            <div className="setup-content">
              <div className="setup-grid setup-grid-single">
                <div className="telegram-card">
                  <header className="telegram-card-header">
                    <h2 className="telegram-card-title">Telegram Alerts</h2>
                    <p className="telegram-card-subtitle">Receive high-impact events and breaking news on your phone</p>
                  </header>
                  <div className="telegram-card-body">
                    {telegramSetup.step === 'connect' && (
                      <>
                        <div className="telegram-benefits">
                          <span className="telegram-benefit">Instant notifications</span>
                          <span className="telegram-benefit">Pre-news & post-news analysis</span>
                          <span className="telegram-benefit">NFP, CPI, Fed & major events</span>
                        </div>
                        {setupError && (
                          <div className="telegram-inline-error" role="alert">
                            {setupError}
                          </div>
                        )}
                        <button
                          type="button"
                          className="telegram-cta-btn"
                          onClick={setupTelegramBot}
                          disabled={telegramSetup.loading}
                        >
                          {telegramSetup.loading && <span className="telegram-btn-spinner" aria-hidden="true" />}
                          <span>{telegramSetup.loading ? 'Preparing link…' : 'Connect Telegram'}</span>
                        </button>
                      </>
                    )}

                    {telegramSetup.step === 'verify' && (
                      <>
                        <ol className="telegram-steps">
                          {telegramSetup.instructions.map((instruction, index) => (
                            <li key={index}>{instruction}</li>
                          ))}
                        </ol>
                        <a
                          href={telegramSetup.botLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="telegram-open-bot-btn"
                        >
                          Open {telegramSetup.botUsername.replace('@', '')} in Telegram
                        </a>
                        {verifyError && (
                          <div className="telegram-inline-error" role="alert">
                            {verifyError}
                          </div>
                        )}
                        <button
                          type="button"
                          className="telegram-cta-btn telegram-cta-btn-secondary"
                          onClick={verifyTelegramConnection}
                          disabled={telegramSetup.loading}
                        >
                          {telegramSetup.loading && <span className="telegram-btn-spinner" aria-hidden="true" />}
                          <span>{telegramSetup.loading ? 'Verifying…' : "I've completed setup in Telegram"}</span>
                        </button>
                      </>
                    )}

                    {telegramSetup.step === 'complete' && (
                      <>
                        <div className="telegram-success-block">
                          <span className="telegram-success-icon" aria-hidden="true">✓</span>
                          <p className="telegram-success-title">You're connected</p>
                          <p className="telegram-success-desc">Alerts will be sent for the event types you choose in Preferences.</p>
                        </div>
                        <div className="telegram-test-block">
                          <button
                            type="button"
                            className="telegram-test-btn"
                            onClick={sendTestAlert}
                            disabled={testAlertLoading}
                          >
                            {testAlertLoading && <span className="telegram-btn-spinner telegram-btn-spinner-sm" aria-hidden="true" />}
                            <span>{testAlertLoading ? 'Sending…' : 'Send test alert'}</span>
                          </button>
                          {testAlertStatus && (
                            <p className={`telegram-test-status telegram-test-status-${testAlertStatus.type}`}>
                              {testAlertStatus.message}
                            </p>
                          )}
                        </div>
                        {showDisconnectConfirm ? (
                          <div className="telegram-disconnect-confirm">
                            <p>Stop receiving alerts on Telegram?</p>
                            <div className="telegram-disconnect-actions">
                              <button type="button" className="telegram-disconnect-cancel" onClick={() => setShowDisconnectConfirm(false)}>Cancel</button>
                              <button type="button" className="telegram-disconnect-do" onClick={disconnectTelegram}>Disconnect</button>
                            </div>
                          </div>
                        ) : (
                          <button type="button" className="telegram-link-btn" onClick={confirmDisconnectTelegram}>
                            Disconnect Telegram
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="preferences-content">
              <div className="preferences-grid">
                {/* Alert Types */}
                <div className="preference-card">
                  <header className="preference-card-header preference-card-header-with-actions">
                    <div className="preference-card-header-text">
                      <h3 className="preference-card-title">Alert Types</h3>
                      <p className="preference-card-desc">Which kinds of alerts to receive</p>
                    </div>
                    <div className="preference-actions">
                      <button type="button" className="preference-action-btn" onClick={() => setAllAlertTypes(true)}>Select all</button>
                      <button type="button" className="preference-action-btn" onClick={() => setAllAlertTypes(false)}>Clear all</button>
                    </div>
                  </header>
                  <div className="preference-card-body">
                    {Object.keys(alertPreferences.preferences.alertTypes).every(k => !alertPreferences.preferences.alertTypes[k]) && (
                      <p className="preference-warning" role="status">Enable at least one type to receive alerts.</p>
                    )}
                    <div className="preference-group">
                      <label className="preference-item">
                        <input type="checkbox" checked={alertPreferences.preferences.alertTypes.liveNews} onChange={(e) => updatePreference('alertTypes', 'liveNews', e.target.checked)} />
                        <div className="preference-info">
                          <span className="preference-label">Live Breaking News</span>
                          <span className="preference-desc">Real-time breaking news with AI analysis</span>
                        </div>
                      </label>
                      <label className="preference-item">
                        <input type="checkbox" checked={alertPreferences.preferences.alertTypes.preNews} onChange={(e) => updatePreference('alertTypes', 'preNews', e.target.checked)} />
                        <div className="preference-info">
                          <span className="preference-label">Pre-News Alerts</span>
                          <span className="preference-desc">Upcoming economic events and expectations</span>
                        </div>
                      </label>
                      <label className="preference-item">
                        <input type="checkbox" checked={alertPreferences.preferences.alertTypes.postNews} onChange={(e) => updatePreference('alertTypes', 'postNews', e.target.checked)} />
                        <div className="preference-info">
                          <span className="preference-label">Post-News Analysis</span>
                          <span className="preference-desc">AI analysis after news release</span>
                        </div>
                      </label>
                      <label className="preference-item">
                        <input type="checkbox" checked={alertPreferences.preferences.alertTypes.technicalAnalysis} onChange={(e) => updatePreference('alertTypes', 'technicalAnalysis', e.target.checked)} />
                        <div className="preference-info">
                          <span className="preference-label">Technical Analysis</span>
                          <span className="preference-desc">Price movements and technical breakouts</span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Impact Levels */}
                <div className="preference-card">
                  <header className="preference-card-header">
                    <h3 className="preference-card-title">Impact Levels</h3>
                    <p className="preference-card-desc">Which event impacts to be notified about</p>
                  </header>
                  <div className="preference-card-body">
                    <div className="preference-group">
                      <label className="preference-item">
                        <input type="checkbox" checked={alertPreferences.preferences.impactLevels.high} onChange={(e) => updatePreference('impactLevels', 'high', e.target.checked)} />
                        <div className="preference-info">
                          <span className="preference-label">🔴 High Impact</span>
                          <span className="preference-desc">CPI, NFP, Fed meetings, major political events</span>
                        </div>
                      </label>
                      <label className="preference-item">
                        <input type="checkbox" checked={alertPreferences.preferences.impactLevels.medium} onChange={(e) => updatePreference('impactLevels', 'medium', e.target.checked)} />
                        <div className="preference-info">
                          <span className="preference-label">🟡 Medium Impact</span>
                          <span className="preference-desc">Retail sales, manufacturing data, employment</span>
                        </div>
                      </label>
                      <label className="preference-item">
                        <input type="checkbox" checked={alertPreferences.preferences.impactLevels.low} onChange={(e) => updatePreference('impactLevels', 'low', e.target.checked)} />
                        <div className="preference-info">
                          <span className="preference-label">🟢 Low Impact</span>
                          <span className="preference-desc">Minor economic indicators and news</span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Currency Pairs */}
                <div className="preference-card">
                  <header className="preference-card-header preference-card-header-with-actions">
                    <div className="preference-card-header-text">
                      <h3 className="preference-card-title">Currency Pairs</h3>
                      <p className="preference-card-desc">Alerts for these pairs only</p>
                    </div>
                    <div className="preference-actions">
                      <button type="button" className="preference-action-btn" onClick={() => setAllCurrencyPairs(CURRENCY_PAIRS_OPTIONS)}>Select all</button>
                      <button type="button" className="preference-action-btn" onClick={() => setAllCurrencyPairs([])}>Clear all</button>
                    </div>
                  </header>
                  <div className="preference-card-body">
                    <div className="currency-pairs-section">
                      <div className={`currency-pairs-list ${alertPreferences.preferences.currencyPairs.length === 0 ? 'currency-pairs-list-empty' : ''}`}>
                        {alertPreferences.preferences.currencyPairs.length === 0 ? (
                          <p className="currency-pairs-empty-hint">Add at least one pair to get alerts for those markets.</p>
                        ) : (
                          alertPreferences.preferences.currencyPairs.map(pair => (
                            <div key={pair} className="currency-pair-tag">
                              <span>{pair}</span>
                              <button type="button" className="remove-pair-btn" onClick={() => removeCurrencyPair(pair)} aria-label={`Remove ${pair}`}>×</button>
                            </div>
                          ))
                        )}
                      </div>
                      <div className="add-pair-section">
                        <select
                          className="pair-select"
                          onChange={(e) => {
                            if (e.target.value) { addCurrencyPair(e.target.value); e.target.value = ''; }
                          }}
                          aria-label="Add currency pair"
                        >
                          <option value="">Add currency pair...</option>
                          {CURRENCY_PAIRS_OPTIONS.map(p => (
                            <option key={p} value={p}>{p}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Quiet Hours */}
                <div className="preference-card">
                  <header className="preference-card-header">
                    <h3 className="preference-card-title">Quiet Hours</h3>
                    <p className="preference-card-desc">No alerts during this time range</p>
                  </header>
                  <div className="preference-card-body">
                    <div className="quiet-hours-section">
                      <label className="quiet-hours-toggle">
                        <input type="checkbox" checked={alertPreferences.preferences.quietHours.enabled} onChange={(e) => updatePreference('quietHours', 'enabled', e.target.checked)} />
                        <span>Enable quiet hours</span>
                      </label>
                      {alertPreferences.preferences.quietHours.enabled && (
                        <>
                          <p className="quiet-hours-timezone-hint">Times in {alertPreferences.preferences.quietHours.timezone || 'UTC'}</p>
                          <div className="quiet-hours-inputs">
                            <div className="time-input-group">
                              <label htmlFor="quiet-start">Start</label>
                              <input id="quiet-start" type="time" value={alertPreferences.preferences.quietHours.start} onChange={(e) => updatePreference('quietHours', 'start', e.target.value)} />
                            </div>
                            <div className="time-input-group">
                              <label htmlFor="quiet-end">End</label>
                              <input id="quiet-end" type="time" value={alertPreferences.preferences.quietHours.end} onChange={(e) => updatePreference('quietHours', 'end', e.target.value)} />
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* History Tab – commented out for now; logic kept for potential future use */}
          {/* {activeTab === 'history' && (
            <div className="history-content">
              <div className="history-header">
                <h3>Alert History</h3>
                <div className="history-filters">
                  <select 
                    className="filter-select"
                    value={historyFilters.channel}
                    onChange={(e) => setHistoryFilters(prev => ({ ...prev, channel: e.target.value }))}
                  >
                    <option value="all">All Alerts</option>
                    <option value="telegram">Telegram</option>
                    <option value="email">Email</option>
                  </select>
                  <select 
                    className="filter-select"
                    value={historyFilters.type}
                    onChange={(e) => setHistoryFilters(prev => ({ ...prev, type: e.target.value }))}
                  >
                    <option value="all">All Types</option>
                    <option value="liveNews">Live News</option>
                    <option value="preNews">Pre-News</option>
                    <option value="postNews">Post-News</option>
                    <option value="technicalAnalysis">Technical Analysis</option>
                  </select>
                </div>
              </div>
              
              <div className="alerts-list">
                {historyLoading ? (
                  <div className="loading-alerts">
                    <p>Loading alert history...</p>
                  </div>
                ) : getFilteredHistory().length === 0 ? (
                  <div className="no-alerts">
                    <p>No alerts found matching your filters.</p>
                  </div>
                ) : (
                  getFilteredHistory().map(alert => (
                    <div key={alert.id} className="alert-item">
                      <div className="alert-icon">
                        {getAlertIcon(alert.alert_type)}
                      </div>
                      <div className="alert-content">
                        <h4>{alert.title || alert.event_title || 'Alert'}</h4>
                        <p className="alert-type">{getAlertTypeDisplay(alert.alert_type)}</p>
                        {alert.content && (
                          <p className="alert-message">{alert.content}</p>
                        )}
                        <small>{formatTimeForTimezone(alert.timestamp || alert.sent_at, null, 'datetime')}</small>
                      </div>
                      <div className="alert-status">
                        <span className={`status-badge ${alert.status}`}>
                          {alert.status === 'sent' ? '✓ Delivered' : '⏳ Scheduled'}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )} */}
        </div>
      </div>
    </div>
  );
}

export default Alerts;
