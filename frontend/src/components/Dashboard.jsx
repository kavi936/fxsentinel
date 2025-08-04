import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { config } from '../config';
import './Dashboard.css';

function Dashboard() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNews, setSelectedNews] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [dataSource, setDataSource] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');
  const [error, setError] = useState(null);
  
  // New state for enhanced features
  const [activeTab, setActiveTab] = useState('news');
  const [alerts, setAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState({});
  const [tradingData, setTradingData] = useState({});
  const [aiInsights, setAiInsights] = useState([]);
  const [alertSettings, setAlertSettings] = useState({
    telegram: true,
    email: false,
    highImpact: true,
    mediumImpact: true,
    lowImpact: false
  });

  // Fetch news data on mount
  useEffect(() => {
    fetchNews();
    fetchTradingData();
    fetchAlerts();
    fetchAiInsights();
    fetchAlertSettings();
  }, []);

  const fetchNews = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(config.endpoints.news);
      setNews(response.data.news);
      setDataSource(response.data.source || 'API');
      setLastUpdated(response.data.last_updated);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching news:', error);
      setError('Failed to load news data. Please try again.');
      setLoading(false);
    }
  };

  const fetchAnalysis = async (newsId) => {
    try {
      setAnalysisLoading(true);
      const response = await axios.get(config.endpoints.analysis(newsId));
      setAnalysis(response.data);
      setAnalysisLoading(false);
    } catch (error) {
      console.error('Error fetching analysis:', error);
      setAnalysisLoading(false);
      setError('Failed to generate analysis. Please try again.');
    }
  };

  const fetchTradingData = async () => {
    try {
      const response = await axios.get(config.endpoints.tradingData);
      setTradingData(response.data);
    } catch (error) {
      console.error('Error fetching trading data:', error);
      // Fallback to mock data if API fails
      setTradingData({
        eurUsd: { price: 1.0856, change: 0.12, sentiment: 'bullish' },
        usdJpy: { price: 148.23, change: -0.08, sentiment: 'bearish' },
        gold: { price: 2034.50, change: 0.45, sentiment: 'bullish' },
        marketSentiment: 'neutral',
        volatilityIndex: 15.2
      });
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(config.endpoints.alerts);
      setAlerts(response.data.alerts);
      setAlertStats(response.data.stats);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      // Fallback to mock data if API fails
      setAlerts([
        {
          id: 1,
          type: 'telegram',
          event: 'US CPI Data',
          status: 'sent',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          recipients: 1250
        },
        {
          id: 2,
          type: 'email',
          event: 'ECB Interest Rate Decision',
          status: 'scheduled',
          timestamp: new Date(Date.now() + 7200000).toISOString(),
          recipients: 890
        }
      ]);
      setAlertStats({
        telegramSubscribers: 1250,
        emailSubscribers: 890,
        alertsThisWeek: 24
      });
    }
  };

  const fetchAiInsights = async () => {
    try {
      const response = await axios.get(config.endpoints.aiInsights);
      setAiInsights(response.data.insights);
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      // Fallback to mock data if API fails
      setAiInsights([
        {
          id: 1,
          title: 'EUR/USD Analysis',
          description: 'Strong support at 1.0850 level. Break above 1.0870 could trigger bullish momentum. Key resistance at 1.0900.',
          confidence: 85,
          timeframe: '4H Timeframe'
        },
        {
          id: 2,
          title: 'USD/JPY Analysis',
          description: 'Consolidating near 148.00 support. Bearish pressure building. Watch for break below 147.80 for short opportunities.',
          confidence: 72,
          timeframe: '1H Timeframe'
        },
        {
          id: 3,
          title: 'Gold Analysis',
          description: 'Bullish momentum continues above $2030. Next target $2050. Safe haven demand supporting prices.',
          confidence: 91,
          timeframe: 'Daily Timeframe'
        }
      ]);
    }
  };

  const fetchAlertSettings = async () => {
    try {
      const response = await axios.get(config.endpoints.alertSettings);
      setAlertSettings(response.data);
    } catch (error) {
      console.error('Error fetching alert settings:', error);
      // Fallback to mock data if API fails
      setAlertSettings({
        telegram: true,
        email: false,
        highImpact: true,
        mediumImpact: true,
        lowImpact: false
      });
    }
  };

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem);
    setAnalysis(null); // Clear previous analysis
    fetchAnalysis(newsItem.id);
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'High': return '#ff4444';
      case 'Medium': return '#ffaa00';
      case 'Low': return '#00cc44';
      default: return '#666666';
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return 'TBD';
    return timeStr;
  };

  const refreshData = () => {
    fetchNews();
    fetchTradingData();
    fetchAlerts();
    fetchAiInsights();
    fetchAlertSettings();
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  const updateAlertSettings = (setting, value) => {
    setAlertSettings(prev => ({
      ...prev,
      [setting]: value
    }));
    
    // Save settings to backend
    saveAlertSettings({ ...alertSettings, [setting]: value });
  };

  const saveAlertSettings = async (settings) => {
    try {
      await axios.post(config.endpoints.alertSettings, settings);
    } catch (error) {
      console.error('Error saving alert settings:', error);
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'bullish': return '#00cc44';
      case 'bearish': return '#ff4444';
      case 'neutral': return '#ffaa00';
      default: return '#666666';
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading market news...</p>
        <small>Fetching real-time economic events</small>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Compact Static Navbar */}
      <nav className="dashboard-navbar">
        <div className="navbar-container">
          <div className="navbar-left">
            <div className="navbar-logo">
              <picture>
                <source srcSet="/fxsentinel_logo_nobg.webp" type="image/webp" />
                <img 
                  src="/fxsentinel_logo_nobg.png" 
                  alt="FXSentinel" 
                  style={{ height: '40px', width: 'auto' }}
                  onError={(e) => {
                    console.log('Logo failed to load, using text fallback');
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              </picture>
              <div style={{
                display: 'none',
                fontSize: '24px',
                fontWeight: 'bold',
                color: '#ffffff',
                alignItems: 'center',
                gap: '8px'
              }}>
                <span style={{ color: '#00ff88' }}>FX</span>
                <span>Sentinel</span>
              </div>
            </div>
          </div>
          
          <div className="navbar-center">
            <div className="navbar-tabs">
              <button 
                className={`nav-tab ${activeTab === 'news' ? 'active' : ''}`}
                onClick={() => setActiveTab('news')}
              >
                News & Analysis
              </button>
              <button 
                className={`nav-tab ${activeTab === 'alerts' ? 'active' : ''}`}
                onClick={() => setActiveTab('alerts')}
              >
                Alert Management
              </button>
              <button 
                className={`nav-tab ${activeTab === 'trading' ? 'active' : ''}`}
                onClick={() => setActiveTab('trading')}
              >
                Trading Insights
              </button>
            </div>
          </div>
          
          <div className="navbar-right">
            <div className="market-status">
              <span className="status-dot open"></span>
              <span className="status-text">Markets Open</span>
            </div>
            <button onClick={refreshData} className="refresh-btn" title="Refresh Data">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 4v6h-6M1 20v-6h6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
              </svg>
            </button>
            <button className="notification-btn" title="Notifications">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              <span className="notification-badge">3</span>
            </button>
            <button className="profile-btn" title="User Profile">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </button>
            <button className="settings-btn" title="Settings">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
            </button>
            <Link to="/" className="home-btn" title="Back to Home">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9,22 9,12 15,12 15,22"/>
              </svg>
            </Link>
          </div>
        </div>
      </nav>

      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={refreshData}>Try Again</button>
        </div>
      )}

      <main className="dashboard-main">
        {activeTab === 'news' && (
          <div className="news-grid">
            <div className="news-list">
              <h2>📊 Upcoming Events ({news.length})</h2>
              {news.length === 0 ? (
                <div className="no-events">
                  <p>No upcoming events found.</p>
                  <button onClick={refreshData}>Refresh Data</button>
                </div>
              ) : (
                news.map((item) => (
                  <div 
                    key={item.id} 
                    className={`news-card ${selectedNews?.id === item.id ? 'selected' : ''}`}
                    onClick={() => handleNewsClick(item)}
                  >
                    <div className="news-header">
                      <h3>{item.title}</h3>
                      <span 
                        className="impact-badge"
                        style={{ backgroundColor: getImpactColor(item.impact) }}
                      >
                        {item.impact}
                      </span>
                    </div>
                    <p className="news-description">{item.description}</p>
                    <div className="news-meta">
                      <span className="date">{formatDate(item.date)}</span>
                      <span className="time">{formatTime(item.time)}</span>
                      <span className="currency">{item.currency}</span>
                    </div>
                    <div className="pairs">
                      {item.pairs.map((pair, index) => (
                        <span key={index} className="pair-tag">{pair}</span>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="analysis-panel">
              {selectedNews ? (
                <div className="analysis-content">
                  <h2>🤖 AI Analysis</h2>
                  <div className="selected-news">
                    <h3>{selectedNews.title}</h3>
                    <p>{selectedNews.description}</p>
                    <div className="news-details">
                      <div className="detail">
                        <strong>Expected:</strong> {selectedNews.expected}
                      </div>
                      <div className="detail">
                        <strong>Previous:</strong> {selectedNews.previous}
                      </div>
                    </div>
                  </div>

                  {analysisLoading ? (
                    <div className="analysis-loading">
                      <div className="spinner"></div>
                      <p>Generating AI analysis...</p>
                    </div>
                  ) : analysis ? (
                    <div className="analysis-details">
                      <div className="summary">
                        <h4>📝 Summary</h4>
                        <p>{analysis.summary}</p>
                      </div>
                      
                      <div className="impacts">
                        <h4>📈 Trading Impacts</h4>
                        <div className="impact-item">
                          <strong>EUR/USD:</strong> {analysis.eur_usd_impact}
                        </div>
                        <div className="impact-item">
                          <strong>USD/JPY:</strong> {analysis.usd_jpy_impact}
                        </div>
                        <div className="impact-item">
                          <strong>Gold:</strong> {analysis.gold_impact}
                        </div>
                      </div>

                      <div className="confidence">
                        <strong>Confidence Level:</strong> {analysis.confidence}
                      </div>
                    </div>
                  ) : (
                    <div className="no-analysis">
                      <p>Click on a news event to generate AI analysis.</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="no-selection">
                  <h2>🤖 AI Analysis</h2>
                  <p>Select a news event to see AI-powered analysis and trading insights.</p>
                  <div className="analysis-features">
                    <div className="feature">
                      <span>📊</span>
                      <p>Market Impact Analysis</p>
                    </div>
                    <div className="feature">
                      <span>🎯</span>
                      <p>Currency Pair Insights</p>
                    </div>
                    <div className="feature">
                      <span>⚡</span>
                      <p>Real-time Updates</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="alerts-section">
            <div className="alerts-overview">
              <h2>🔔 Smart Alert System</h2>
              <p>Get instant notifications for important market events via Telegram and Email</p>
              
              <div className="alert-stats">
                <div className="stat-card">
                  <span className="stat-number">{alertStats.telegramSubscribers}</span>
                  <span className="stat-label">Telegram Subscribers</span>
                </div>
                <div className="stat-card">
                  <span className="stat-number">{alertStats.emailSubscribers}</span>
                  <span className="stat-label">Email Subscribers</span>
                </div>
                <div className="stat-card">
                  <span className="stat-number">{alertStats.alertsThisWeek}</span>
                  <span className="stat-label">Alerts This Week</span>
                </div>
              </div>
            </div>

            <div className="alerts-content">
              <div className="alert-settings">
                <h3>⚙️ Alert Preferences</h3>
                <div className="settings-grid">
                  <div className="setting-group">
                    <h4>Notification Channels</h4>
                    <label className="setting-item">
                      <input 
                        type="checkbox" 
                        checked={alertSettings.telegram}
                        onChange={(e) => updateAlertSettings('telegram', e.target.checked)}
                      />
                      <span>📱 Telegram Bot</span>
                    </label>
                    <label className="setting-item">
                      <input 
                        type="checkbox" 
                        checked={alertSettings.email}
                        onChange={(e) => updateAlertSettings('email', e.target.checked)}
                      />
                      <span>📧 Email Alerts</span>
                    </label>
                  </div>
                  
                  <div className="setting-group">
                    <h4>Impact Levels</h4>
                    <label className="setting-item">
                      <input 
                        type="checkbox" 
                        checked={alertSettings.highImpact}
                        onChange={(e) => updateAlertSettings('highImpact', e.target.checked)}
                      />
                      <span>🔴 High Impact Events</span>
                    </label>
                    <label className="setting-item">
                      <input 
                        type="checkbox" 
                        checked={alertSettings.mediumImpact}
                        onChange={(e) => updateAlertSettings('mediumImpact', e.target.checked)}
                      />
                      <span>🟡 Medium Impact Events</span>
                    </label>
                    <label className="setting-item">
                      <input 
                        type="checkbox" 
                        checked={alertSettings.lowImpact}
                        onChange={(e) => updateAlertSettings('lowImpact', e.target.checked)}
                      />
                      <span>🟢 Low Impact Events</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="recent-alerts">
                <h3>📋 Recent Alerts</h3>
                <div className="alerts-list">
                  {alerts.map(alert => (
                    <div key={alert.id} className="alert-item">
                      <div className="alert-icon">
                        {alert.type === 'telegram' ? '📱' : '📧'}
                      </div>
                      <div className="alert-content">
                        <h4>{alert.event}</h4>
                        <p>{alert.status === 'sent' ? 'Delivered' : 'Scheduled'}</p>
                        <small>{new Date(alert.timestamp).toLocaleString()}</small>
                      </div>
                      <div className="alert-recipients">
                        {alert.recipients} recipients
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trading' && (
          <div className="trading-section">
            <div className="trading-overview">
              <h2>📈 Trading Insights & Market Analysis</h2>
              <p>AI-powered analysis of market sentiment and trading opportunities</p>
            </div>

            <div className="trading-grid">
              <div className="market-sentiment">
                <h3>🎯 Market Sentiment</h3>
                <div className="sentiment-indicator">
                  <div className="sentiment-bar">
                    <div 
                      className="sentiment-fill"
                      style={{ 
                        width: '50%',
                        backgroundColor: getSentimentColor(tradingData.marketSentiment)
                      }}
                    ></div>
                  </div>
                  <span className="sentiment-label">{tradingData.marketSentiment}</span>
                </div>
                <div className="volatility-info">
                  <span>Volatility Index: {tradingData.volatilityIndex}</span>
                </div>
              </div>

              <div className="currency-pairs">
                <h3>💱 Key Currency Pairs</h3>
                <div className="pairs-grid">
                  <div className="pair-card">
                    <div className="pair-header">
                      <h4>EUR/USD</h4>
                      <span className="pair-price">{tradingData.eurUsd?.price}</span>
                    </div>
                    <div className="pair-change">
                      <span className={`change ${tradingData.eurUsd?.change > 0 ? 'positive' : 'negative'}`}>
                        {tradingData.eurUsd?.change > 0 ? '+' : ''}{tradingData.eurUsd?.change}%
                      </span>
                      <span className="sentiment" style={{color: getSentimentColor(tradingData.eurUsd?.sentiment)}}>
                        {tradingData.eurUsd?.sentiment}
                      </span>
                    </div>
                  </div>

                  <div className="pair-card">
                    <div className="pair-header">
                      <h4>USD/JPY</h4>
                      <span className="pair-price">{tradingData.usdJpy?.price}</span>
                    </div>
                    <div className="pair-change">
                      <span className={`change ${tradingData.usdJpy?.change > 0 ? 'positive' : 'negative'}`}>
                        {tradingData.usdJpy?.change > 0 ? '+' : ''}{tradingData.usdJpy?.change}%
                      </span>
                      <span className="sentiment" style={{color: getSentimentColor(tradingData.usdJpy?.sentiment)}}>
                        {tradingData.usdJpy?.sentiment}
                      </span>
                    </div>
                  </div>

                  <div className="pair-card">
                    <div className="pair-header">
                      <h4>Gold</h4>
                      <span className="pair-price">${tradingData.gold?.price}</span>
                    </div>
                    <div className="pair-change">
                      <span className={`change ${tradingData.gold?.change > 0 ? 'positive' : 'negative'}`}>
                        {tradingData.gold?.change > 0 ? '+' : ''}{tradingData.gold?.change}%
                      </span>
                      <span className="sentiment" style={{color: getSentimentColor(tradingData.gold?.sentiment)}}>
                        {tradingData.gold?.sentiment}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="ai-insights">
                <h3>🤖 AI Trading Insights</h3>
                <div className="insights-content">
                  {aiInsights.map((insight, index) => (
                    <div key={index} className="insight-card">
                      <h4>📊 {insight.pair} Analysis</h4>
                      <p>{insight.analysis}</p>
                      <div className="insight-meta">
                        <span className="confidence">Confidence: {insight.confidence}%</span>
                        <span className="timeframe">{insight.timeframe} Timeframe</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard; 