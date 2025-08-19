import React, { useState, useEffect } from 'react';
import { formatTimeForTimezone } from '../utils/timezoneUtils';
import { config } from '../config';
import './Alerts.css';

function Alerts({ alerts, alertStats, alertSettings, updateAlertSettings }) {
  // State for different sections and functionality
  const [activeTab, setActiveTab] = useState('overview'); // overview, setup, preferences, history
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

  // Telegram Bot Setup Flow
  const setupTelegramBot = async () => {
    setTelegramSetup(prev => ({ ...prev, loading: true }));
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/telegram/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: 'current_user_id' })
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
      }
    } catch (error) {
      console.error('Error setting up Telegram bot:', error);
      setTelegramSetup(prev => ({ ...prev, loading: false }));
    }
  };

  const verifyTelegramConnection = async () => {
    setTelegramSetup(prev => ({ ...prev, loading: true }));
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/telegram/verify`);
      const data = await response.json();
      
      if (data.connected) {
        setTelegramSetup({ step: 'complete', loading: false });
        setAlertPreferences(prev => ({
          ...prev,
          channels: {
            ...prev.channels,
            telegram: { enabled: true, chatId: data.chatId, username: data.username }
          }
        }));
      }
    } catch (error) {
      console.error('Error verifying Telegram connection:', error);
      setTelegramSetup(prev => ({ ...prev, loading: false }));
    }
  };

  const setupEmailAlerts = () => {
    if (emailInput && emailInput.includes('@')) {
      setAlertPreferences(prev => ({
        ...prev,
        channels: {
          ...prev.channels,
          email: { enabled: true, address: emailInput }
        }
      }));
      setShowEmailSetup(false);
      setEmailInput('');
    }
  };

  const updatePreference = (category, setting, value) => {
    setAlertPreferences(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [category]: {
          ...prev.preferences[category],
          [setting]: value
        }
      }
    }));
  };

  const addCurrencyPair = (pair) => {
    if (pair && !alertPreferences.preferences.currencyPairs.includes(pair)) {
      setAlertPreferences(prev => ({
        ...prev,
        preferences: {
          ...prev.preferences,
          currencyPairs: [...prev.preferences.currencyPairs, pair]
        }
      }));
    }
  };

  const removeCurrencyPair = (pair) => {
    setAlertPreferences(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        currencyPairs: prev.preferences.currencyPairs.filter(p => p !== pair)
      }
    }));
  };

  return (
    <div className="alerts-tab">
      <div className="alerts-container">
        {/* Navigation Tabs */}
        <div className="alerts-tabs">
          <button 
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
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

        {/* Tab Content */}
        <div className="alerts-tab-content">
          
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="alerts-overview-content">
              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Telegram Alerts</h3>
                  <div className="alert-status-indicator">
                    {alertPreferences.channels.telegram.enabled ? (
                      <div className="status-success">
                        <span className="status-icon">✓</span>
                        <span>Connected as @{alertPreferences.channels.telegram.username}</span>
                      </div>
                    ) : (
                      <div className="status-warning">
                        <span className="status-icon">!</span>
                        <span>Not connected</span>
                      </div>
                    )}
                  </div>
                  <button 
                    className="setup-btn"
                    onClick={() => setActiveTab('setup')}
                  >
                    {alertPreferences.channels.telegram.enabled ? 'Manage' : 'Connect'}
                  </button>
                </div>

                <div className="overview-card">
                  <h3>Email Alerts</h3>
                  <div className="alert-status-indicator">
                    {alertPreferences.channels.email.enabled ? (
                      <div className="status-success">
                        <span className="status-icon">✓</span>
                        <span>Connected to {alertPreferences.channels.email.address}</span>
                      </div>
                    ) : (
                      <div className="status-warning">
                        <span className="status-icon">!</span>
                        <span>Not connected</span>
                      </div>
                    )}
                  </div>
                  <button 
                    className="setup-btn"
                    onClick={() => setActiveTab('setup')}
                  >
                    {alertPreferences.channels.email.enabled ? 'Manage' : 'Connect'}
                  </button>
                </div>

                <div className="overview-card">
                  <h3>Alert Types</h3>
                  <div className="alert-types-summary">
                    <div className="type-item">
                      <span className="type-icon">•</span>
                      <span>Live News: {alertPreferences.preferences.alertTypes.liveNews ? 'ON' : 'OFF'}</span>
                    </div>
                    <div className="type-item">
                      <span className="type-icon">•</span>
                      <span>Pre-News: {alertPreferences.preferences.alertTypes.preNews ? 'ON' : 'OFF'}</span>
                    </div>
                    <div className="type-item">
                      <span className="type-icon">•</span>
                      <span>Post-News: {alertPreferences.preferences.alertTypes.postNews ? 'ON' : 'OFF'}</span>
                    </div>
                  </div>
                  <button 
                    className="setup-btn"
                    onClick={() => setActiveTab('preferences')}
                  >
                    Configure
                  </button>
                </div>

                <div className="overview-card">
                  <h3>Impact Levels</h3>
                  <div className="impact-summary">
                    <div className="impact-item high">
                      <span className="impact-dot">●</span>
                      <span>High: {alertPreferences.preferences.impactLevels.high ? 'ON' : 'OFF'}</span>
                    </div>
                    <div className="impact-item medium">
                      <span className="impact-dot">●</span>
                      <span>Medium: {alertPreferences.preferences.impactLevels.medium ? 'ON' : 'OFF'}</span>
                    </div>
                    <div className="impact-item low">
                      <span className="impact-dot">●</span>
                      <span>Low: {alertPreferences.preferences.impactLevels.low ? 'ON' : 'OFF'}</span>
                    </div>
                  </div>
                  <button 
                    className="setup-btn"
                    onClick={() => setActiveTab('preferences')}
                  >
                    Configure
                  </button>
                </div>
              </div>

              <div className="recent-alerts-preview">
                <h3>Recent Alerts</h3>
                <div className="alerts-preview-list">
                  {alerts.slice(0, 3).map(alert => (
                    <div key={alert.id} className="alert-preview-item">
                      <div className="alert-preview-icon">
                        {alert.type === 'telegram' ? 'T' : 'E'}
                      </div>
                      <div className="alert-preview-content">
                        <h4>{alert.event}</h4>
                        <p>{alert.status === 'sent' ? 'Delivered' : 'Scheduled'}</p>
                        <small>{formatTimeForTimezone(alert.timestamp, null, 'datetime')}</small>
                      </div>
                    </div>
                  ))}
                  {alerts.length === 0 && (
                    <div className="no-alerts">
                      <p>No alerts sent yet. Set up your preferences to start receiving alerts!</p>
                    </div>
                  )}
                </div>
                <button 
                  className="view-all-btn"
                  onClick={() => setActiveTab('history')}
                >
                  View All Alerts
                </button>
              </div>
            </div>
          )}

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
                      <button 
                        className="disconnect-btn"
                        onClick={() => {
                          setTelegramSetup({ step: 'connect', loading: false });
                          setAlertPreferences(prev => ({
                            ...prev,
                            channels: {
                              ...prev.channels,
                              telegram: { enabled: false, chatId: '', username: '' }
                            }
                          }));
                        }}
                      >
                        Disconnect
                      </button>
                    </div>
                  )}
                </div>

                {/* Email Setup */}
                <div className="setup-card">
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
                        />
                        <button 
                          className="setup-email-btn"
                          onClick={setupEmailAlerts}
                          disabled={!emailInput || !emailInput.includes('@')}
                        >
                          Connect Email
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
                        onClick={() => {
                          setAlertPreferences(prev => ({
                            ...prev,
                            channels: {
                              ...prev.channels,
                              email: { enabled: false, address: '' }
                            }
                          }));
                        }}
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
                  <select className="filter-select">
                    <option value="all">All Alerts</option>
                    <option value="telegram">Telegram</option>
                    <option value="email">Email</option>
                  </select>
                  <select className="filter-select">
                    <option value="all">All Types</option>
                    <option value="liveNews">Live News</option>
                    <option value="preNews">Pre-News</option>
                    <option value="postNews">Post-News</option>
                    <option value="technicalAnalysis">Technical Analysis</option>
                  </select>
                </div>
              </div>
              
              <div className="alerts-list">
                {alerts.map(alert => (
                  <div key={alert.id} className="alert-item">
                    <div className="alert-icon">
                      {alert.type === 'telegram' ? '📱' : '📧'}
                    </div>
                    <div className="alert-content">
                      <h4>{alert.event}</h4>
                      <p>{alert.status === 'sent' ? 'Delivered' : 'Scheduled'}</p>
                      <small>{formatTimeForTimezone(alert.timestamp, null, 'datetime')}</small>
                    </div>
                    <div className="alert-recipients">
                      {alert.recipients} recipients
                    </div>
                  </div>
                ))}
                {alerts.length === 0 && (
                  <div className="no-alerts">
                    <p>No alerts sent yet. Set up your preferences to start receiving alerts!</p>
                  </div>
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
