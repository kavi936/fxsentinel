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
  const [emailInput, setEmailInput] = useState('');
  const [showEmailSetup, setShowEmailSetup] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  
  // Test alert functionality
  const [testAlertLoading, setTestAlertLoading] = useState(false);
  const [testAlertStatus, setTestAlertStatus] = useState(null);

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

  // Load alert history when history tab is active
  useEffect(() => {
    if (activeTab === 'history' && currentUser) {
      loadAlertHistory();
    }
  }, [activeTab, currentUser]);

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

  // Clear test alert status when user changes
  useEffect(() => {
    setTestAlertStatus(null);
  }, [currentUser]);

  // Telegram Bot Setup Flow
  const setupTelegramBot = async () => {
    if (!currentUser) {
      alert('Please log in to set up Telegram alerts');
      return;
    }
    
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
            '1. Click the link below to start the bot',
            '2. Send /start to begin setup',
            '3. Follow the bot instructions to complete setup',
            '4. Return here and click "Verify Connection"'
          ],
          botLink: data.botLink,
          loading: false
        });
      } else {
        throw new Error(data.error || 'Failed to setup Telegram bot');
      }
    } catch (error) {
      console.error('Error setting up Telegram bot:', error);
      alert('Failed to setup Telegram bot. Please try again.');
      setTelegramSetup(prev => ({ ...prev, loading: false }));
    }
  };

  const verifyTelegramConnection = async () => {
    if (!currentUser) {
      alert('Please log in to verify Telegram connection');
      return;
    }
    
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
        setTelegramSetup({ step: 'complete', loading: false });
        const updatedPreferences = {
          ...alertPreferences,
          channels: {
            ...alertPreferences.channels,
            telegram: { enabled: true, chatId: data.chatId, username: data.username }
          }
        };
        setAlertPreferences(updatedPreferences);
        // Save immediately when Telegram is connected
        await saveAlertPreferences(updatedPreferences);
      } else if (data.success && !data.connected) {
        // User has access but bot not connected yet
        alert('Bot setup not completed. Please complete the bot setup first.');
        setTelegramSetup(prev => ({ ...prev, loading: false }));
      } else {
        throw new Error(data.error || 'Failed to verify connection');
      }
    } catch (error) {
      console.error('Error verifying Telegram connection:', error);
      alert('Failed to verify Telegram connection. Please try again.');
      setTelegramSetup(prev => ({ ...prev, loading: false }));
    }
  };

  const setupEmailAlerts = () => {
    if (emailInput && emailInput.includes('@')) {
      const updatedPreferences = {
        ...alertPreferences,
        channels: {
          ...alertPreferences.channels,
          email: { enabled: true, address: emailInput }
        }
      };
      setAlertPreferences(updatedPreferences);
      setShowEmailSetup(false);
      setEmailInput('');
      // Save immediately when email is connected
      saveAlertPreferences(updatedPreferences);
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
    
    // Save to backend using the function passed from Dashboard
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
    
    // Save to backend
    if (updateAlertSettings) {
      updateAlertSettings('preferences', updatedPreferences.preferences);
    }
  };

  // Disconnect Telegram
  const disconnectTelegram = () => {
    const updatedPreferences = {
      ...alertPreferences,
      channels: {
        ...alertPreferences.channels,
        telegram: { enabled: false, chatId: '', username: '' }
      }
    };
    setAlertPreferences(updatedPreferences);
    setTelegramSetup({ step: 'connect', loading: false });
    // Clear test alert status when disconnecting
    setTestAlertStatus(null);
    // Save immediately when Telegram is disconnected
    saveAlertPreferences(updatedPreferences);
  };

  // Disconnect Email
  const disconnectEmail = () => {
    const updatedPreferences = {
      ...alertPreferences,
      channels: {
        ...alertPreferences.channels,
        email: { enabled: false, address: '' }
      }
    };
    setAlertPreferences(updatedPreferences);
    // Save immediately when email is disconnected
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
          <button 
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
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
              <div className="setup-grid">
                
                {/* Telegram Setup */}
                <div className="setup-card">
                  <h3>Telegram Bot Setup</h3>
                  <p>Connect your Telegram account to receive instant alerts</p>
                  
                  {telegramSetup.step === 'connect' && (
                    <div className="setup-step">
                      <div className="setup-info">
                        <p>• Instant notifications on your phone</p>
                        <p>• AI-powered market analysis</p>
                        <p>• Real-time breaking news alerts</p>
                      </div>
                      <button 
                        className="setup-telegram-btn"
                        onClick={setupTelegramBot}
                        disabled={telegramSetup.loading}
                      >
                        {telegramSetup.loading ? 'Setting up...' : 'Connect Telegram Bot'}
                      </button>
                    </div>
                  )}
                  
                  {telegramSetup.step === 'verify' && (
                    <div className="setup-step">
                      <div className="bot-instructions">
                        {telegramSetup.instructions.map((instruction, index) => (
                          <p key={index}>{instruction}</p>
                        ))}
                      </div>
                      <a 
                        href={telegramSetup.botLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="bot-link-btn"
                      >
                        Start @{telegramSetup.botUsername}
                      </a>
                      <button 
                        className="verify-connection-btn"
                        onClick={verifyTelegramConnection}
                        disabled={telegramSetup.loading}
                      >
                        {telegramSetup.loading ? 'Verifying...' : 'I\'ve Completed Setup'}
                      </button>
                    </div>
                  )}
                  
                  {telegramSetup.step === 'complete' && (
                    <div className="setup-complete">
                      <div className="success-icon">✓</div>
                      <p>Telegram bot connected successfully!</p>
                      <p>You'll now receive alerts on Telegram</p>
                      <div className="test-alert-section">
                        <button 
                          className="test-alert-btn"
                          onClick={sendTestAlert}
                          disabled={testAlertLoading}
                        >
                          {testAlertLoading ? 'Sending...' : 'Send Test Alert'}
                        </button>
                        {testAlertStatus && (
                          <p className={`test-alert-status ${testAlertStatus.type}`}>
                            {testAlertStatus.message}
                          </p>
                        )}
                      </div>
                      <button 
                        className="disconnect-btn"
                        onClick={disconnectTelegram}
                      >
                        Disconnect
                      </button>
                    </div>
                  )}
                </div>

                {/* Email Setup */}
                <div className="setup-card email-setup-card">
                  <div className="coming-soon-overlay">
                    <div className="coming-soon-content">
                      <div className="coming-soon-icon">🚀</div>
                      <h4>Coming Soon</h4>
                      <p>Email alerts will be available in the next update</p>
                      <div className="coming-soon-badge">MVP: Telegram Only</div>
                    </div>
                  </div>
                  
                  <h3>Email Alerts Setup</h3>
                  <p>Receive alerts via email as backup or primary method</p>
                  
                  {!alertPreferences.channels.email.enabled ? (
                    <div className="setup-step">
                      <div className="setup-info">
                        <p>• Backup notification method</p>
                        <p>• Detailed market analysis</p>
                        <p>• Professional formatting</p>
                      </div>
                      <div className="email-input-group">
                        <input
                          type="email"
                          placeholder="Enter your email address"
                          value={emailInput}
                          onChange={(e) => setEmailInput(e.target.value)}
                          className="email-input"
                          disabled
                        />
                        <button 
                          className="setup-email-btn"
                          onClick={setupEmailAlerts}
                          disabled={true}
                        >
                          Coming Soon
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="setup-complete">
                      <div className="success-icon">✓</div>
                      <p>Email alerts connected!</p>
                      <p>Alerts will be sent to: {alertPreferences.channels.email.address}</p>
                      <button 
                        className="disconnect-btn"
                        onClick={disconnectEmail}
                      >
                        Disconnect
                      </button>
                    </div>
                  )}
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
                  <h3>Alert Types</h3>
                  <p>Choose which types of alerts you want to receive</p>
                  
                  <div className="preference-group">
                    <label className="preference-item">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.alertTypes.liveNews}
                        onChange={(e) => updatePreference('alertTypes', 'liveNews', e.target.checked)}
                      />
                      <div className="preference-info">
                        <span className="preference-label">Live Breaking News</span>
                        <span className="preference-desc">Real-time breaking news with AI analysis</span>
                      </div>
                    </label>
                    
                    <label className="preference-item">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.alertTypes.preNews}
                        onChange={(e) => updatePreference('alertTypes', 'preNews', e.target.checked)}
                      />
                      <div className="preference-info">
                        <span className="preference-label">Pre-News Alerts</span>
                        <span className="preference-desc">Upcoming economic events and expectations</span>
                      </div>
                    </label>
                    
                    <label className="preference-item">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.alertTypes.postNews}
                        onChange={(e) => updatePreference('alertTypes', 'postNews', e.target.checked)}
                      />
                      <div className="preference-info">
                        <span className="preference-label">Post-News Analysis</span>
                        <span className="preference-desc">AI analysis after news release</span>
                      </div>
                    </label>
                    
                    <label className="preference-item">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.alertTypes.technicalAnalysis}
                        onChange={(e) => updatePreference('alertTypes', 'technicalAnalysis', e.target.checked)}
                      />
                      <div className="preference-info">
                        <span className="preference-label">Technical Analysis</span>
                        <span className="preference-desc">Price movements and technical breakouts</span>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Impact Levels */}
                <div className="preference-card">
                  <h3>Impact Levels</h3>
                  <p>Select which impact levels you want to be alerted about</p>
                  
                  <div className="preference-group">
                    <label className="preference-item">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.impactLevels.high}
                        onChange={(e) => updatePreference('impactLevels', 'high', e.target.checked)}
                      />
                      <div className="preference-info">
                        <span className="preference-label">🔴 High Impact Events</span>
                        <span className="preference-desc">CPI, NFP, Fed meetings, major political events</span>
                      </div>
                    </label>
                    
                    <label className="preference-item">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.impactLevels.medium}
                        onChange={(e) => updatePreference('impactLevels', 'medium', e.target.checked)}
                      />
                      <div className="preference-info">
                        <span className="preference-label">🟡 Medium Impact Events</span>
                        <span className="preference-desc">Retail sales, manufacturing data, employment</span>
                      </div>
                    </label>
                    
                    <label className="preference-item">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.impactLevels.low}
                        onChange={(e) => updatePreference('impactLevels', 'low', e.target.checked)}
                      />
                      <div className="preference-info">
                        <span className="preference-label">🟢 Low Impact Events</span>
                        <span className="preference-desc">Minor economic indicators and news</span>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Currency Pairs */}
                <div className="preference-card">
                  <h3>💱 Currency Pairs</h3>
                  <p>Select which currency pairs you want alerts for</p>
                  
                  <div className="currency-pairs-section">
                    <div className="currency-pairs-list">
                      {alertPreferences.preferences.currencyPairs.map(pair => (
                        <div key={pair} className="currency-pair-tag">
                          <span>{pair}</span>
                          <button 
                            className="remove-pair-btn"
                            onClick={() => removeCurrencyPair(pair)}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                    
                    <div className="add-pair-section">
                      <select 
                        className="pair-select"
                        onChange={(e) => {
                          if (e.target.value) {
                            addCurrencyPair(e.target.value);
                            e.target.value = '';
                          }
                        }}
                      >
                        <option value="">Add currency pair...</option>
                        <option value="EUR/USD">EUR/USD</option>
                        <option value="USD/JPY">USD/JPY</option>
                        <option value="GBP/USD">GBP/USD</option>
                        <option value="USD/CHF">USD/CHF</option>
                        <option value="AUD/USD">AUD/USD</option>
                        <option value="USD/CAD">USD/CAD</option>
                        <option value="NZD/USD">NZD/USD</option>
                        <option value="EUR/GBP">EUR/GBP</option>
                        <option value="EUR/JPY">EUR/JPY</option>
                        <option value="GBP/JPY">GBP/JPY</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Quiet Hours */}
                <div className="preference-card">
                  <h3>🌙 Quiet Hours</h3>
                  <p>Set times when you don't want to receive alerts</p>
                  
                  <div className="quiet-hours-section">
                    <label className="quiet-hours-toggle">
                      <input 
                        type="checkbox" 
                        checked={alertPreferences.preferences.quietHours.enabled}
                        onChange={(e) => updatePreference('quietHours', 'enabled', e.target.checked)}
                      />
                      <span>Enable quiet hours</span>
                    </label>
                    
                    {alertPreferences.preferences.quietHours.enabled && (
                      <div className="quiet-hours-inputs">
                        <div className="time-input-group">
                          <label>Start Time:</label>
                          <input 
                            type="time" 
                            value={alertPreferences.preferences.quietHours.start}
                            onChange={(e) => updatePreference('quietHours', 'start', e.target.value)}
                          />
                        </div>
                        <div className="time-input-group">
                          <label>End Time:</label>
                          <input 
                            type="time" 
                            value={alertPreferences.preferences.quietHours.end}
                            onChange={(e) => updatePreference('quietHours', 'end', e.target.value)}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="history-content">
              <div className="history-header">
                <h3>📋 Alert History</h3>
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
          )}
        </div>
      </div>
    </div>
  );
}

export default Alerts;
