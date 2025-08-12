import React, { useState, useEffect } from 'react';
import { config } from '../config';
import { formatNewsTime, getUserTimezone, getTimezoneAbbreviation } from '../utils/timezoneUtils';
import './LiveNewsFeed.css';

const LiveNewsFeed = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedNews, setSelectedNews] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [filter, setFilter] = useState('all'); // all, high, medium, low
  const [currentTimezone, setCurrentTimezone] = useState(getUserTimezone());

  useEffect(() => {
    fetchNews();
    // Set up auto-refresh every 5 minutes
    const interval = setInterval(fetchNews, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Listen for timezone changes
  useEffect(() => {
    const checkTimezone = () => {
      const newTimezone = getUserTimezone();
      if (newTimezone !== currentTimezone) {
        setCurrentTimezone(newTimezone);
      }
    };

    // Check timezone every second
    const timezoneInterval = setInterval(checkTimezone, 1000);
    
    // Also listen for storage events (when timezone is changed in another tab)
    const handleStorageChange = (e) => {
      if (e.key === 'fxSentinel_userTimezone') {
        setCurrentTimezone(e.newValue || 'UTC');
      }
    };

    // Listen for custom timezone change events
    const handleTimezoneChange = (e) => {
      setCurrentTimezone(e.detail.timezone);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('timezoneChanged', handleTimezoneChange);
    
    return () => {
      clearInterval(timezoneInterval);
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('timezoneChanged', handleTimezoneChange);
    };
  }, [currentTimezone]);

  const fetchNews = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(config.endpoints.news);
      const data = await response.json();
      
      if (response.ok) {
        setNews(data.news || []);
        console.log('API response last_updated:', data.last_updated, typeof data.last_updated);
        // Use current time as fallback if last_updated is not provided or invalid
        const lastUpdatedValue = data.last_updated || new Date().toISOString();
        setLastUpdated(lastUpdatedValue);
      } else {
        throw new Error('Failed to fetch news');
      }
    } catch (err) {
      console.error('Error fetching news:', err);
      // Set empty news array instead of error to show empty state
      setNews([]);
      setError(null);
    } finally {
      setLoading(false);
    }
  };

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem);
    setAiAnalysis(null);
  };

  const analyzeNews = async (newsItem) => {
    try {
      setAnalyzing(true);
      
      const response = await fetch(`${config.endpoints.analysis}/${newsItem.id}`);
      const analysis = await response.json();
      
      if (response.ok) {
        setAiAnalysis(analysis);
      } else {
        throw new Error('Failed to analyze news');
      }
    } catch (err) {
      console.error('Error analyzing news:', err);
      setError('Failed to analyze news. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const getImpactColor = (impact) => {
    switch (impact?.toLowerCase()) {
      case 'high': return '#ff4757';
      case 'medium': return '#ffa502';
      case 'low': return '#2ed573';
      default: return '#747d8c';
    }
  };

  const getImpactIcon = (impact) => {
    switch (impact?.toLowerCase()) {
      case 'high': return '🔥';
      case 'medium': return '⚡';
      case 'low': return '📊';
      default: return '📰';
    }
  };

  const formatTime = (timestamp) => {
    return formatNewsTime(timestamp, currentTimezone);
  };

  const formatTimeAgo = (timestamp) => {
    console.log('formatTimeAgo input:', timestamp, typeof timestamp);
    
    // Handle null/undefined
    if (!timestamp) {
      console.error('Timestamp is null or undefined');
      return 'Recently';
    }
    
    // Ensure timestamp is a valid Date object
    let date;
    if (timestamp instanceof Date) {
      date = timestamp;
    } else if (typeof timestamp === 'string') {
      // Handle ISO string format
      date = new Date(timestamp);
    } else {
      // Try to create Date from any other format
      date = new Date(timestamp);
    }
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid timestamp after conversion:', timestamp, 'converted to:', date);
      return 'Recently';
    }
    
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    console.log('Time calculation:', { now, date, diff, minutes, hours, days });

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const filteredNews = news
    .filter(item => {
      if (filter === 'all') return true;
      return item.impact?.toLowerCase() === filter;
    })
    .sort((a, b) => {
      // Sort by published_at timestamp in descending order (newest first)
      const dateA = new Date(a.published_at);
      const dateB = new Date(b.published_at);
      return dateB - dateA;
    });

  const clearSelection = () => {
    setSelectedNews(null);
    setAiAnalysis(null);
  };

  return (
    <div className="live-news-feed">
      <div className="news-header">
        <div className="header-main">
          <h2 className="news-title">LIVE NEWS + ANALYSIS</h2>
          <div className="news-stats">
            {lastUpdated && (
              <span className="last-updated">
                Updated {formatTimeAgo(lastUpdated)}
              </span>
            )}
          </div>
        </div>
        <div className="news-controls">
          <div className="filter-controls">
            <button 
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All
            </button>
            <button 
              className={`filter-btn ${filter === 'high' ? 'active' : ''}`}
              onClick={() => setFilter('high')}
            >
              H
            </button>
            <button 
              className={`filter-btn ${filter === 'medium' ? 'active' : ''}`}
              onClick={() => setFilter('medium')}
            >
              M
            </button>
            <button 
              className={`filter-btn ${filter === 'low' ? 'active' : ''}`}
              onClick={() => setFilter('low')}
            >
              L
            </button>
          </div>
          <button className="refresh-btn" onClick={fetchNews} disabled={loading}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
            </svg>
          </button>
        </div>
      </div>

      <div className="news-content">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading latest news...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <p>{error}</p>
            <button onClick={fetchNews}>Try Again</button>
          </div>
        ) : filteredNews.length === 0 ? (
          <div className="empty-state">
            <div className="placeholder-icon">📰</div>
            <p className="placeholder-text">No News Available</p>
            <p className="placeholder-subtext">News feed will appear here when available</p>
            <button onClick={fetchNews}>Refresh</button>
          </div>
        ) : (
          <div className="news-list">
            {filteredNews.map((newsItem) => (
              <div 
                key={newsItem.id} 
                className={`news-item ${selectedNews?.id === newsItem.id ? 'selected' : ''}`}
                onClick={() => handleNewsClick(newsItem)}
              >
                <div className="news-item-header">
                  <div className="news-source">
                    <span className="source-name">{newsItem.source}</span>
                    <span className="news-time">{formatTime(newsItem.published_at)}</span>
                  </div>
                  <div className="news-impact">
                    <span 
                      className="impact-badge"
                      style={{ backgroundColor: getImpactColor(newsItem.impact) }}
                    >
                      {getImpactIcon(newsItem.impact)} {newsItem.impact}
                    </span>
                  </div>
                </div>
                
                <div className="news-item-content">
                  <h3 className="news-title">{newsItem.title}</h3>
                  <p className="news-summary">{newsItem.summary}</p>
                  
                  {newsItem.currency_pairs && newsItem.currency_pairs.length > 0 && (
                    <div className="news-currency-pairs">
                      <span className="news-pairs-label">Affected pairs:</span>
                      {newsItem.currency_pairs.map((pair, index) => (
                        <span key={index} className="news-currency-pair">{pair}</span>
                      ))}
                    </div>
                  )}
                </div>

                {selectedNews?.id === newsItem.id && (
                  <div className="news-actions">
                    <button 
                      className="analyze-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        analyzeNews(newsItem);
                      }}
                      disabled={analyzing}
                    >
                      {analyzing ? 'Analyzing...' : 'Analyze with AI'}
                    </button>
                    {newsItem.url && (
                      <a 
                        href={newsItem.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="read-more-btn"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Read Full Article
                      </a>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Analysis Panel */}
      {selectedNews && (
        <div className="ai-analysis-panel">
          <div className="analysis-header">
            <h3>AI Analysis</h3>
            <button className="close-btn" onClick={clearSelection}>×</button>
          </div>
          
          <div className="analysis-content">
            {aiAnalysis ? (
              <div className="analysis-results">
                <div className="analysis-summary">
                  <h4>Market Impact Analysis</h4>
                  <p>{aiAnalysis.summary}</p>
                </div>
                
                {aiAnalysis.currency_pairs && (
                  <div className="pair-analysis">
                    <h4>Currency Pair Analysis</h4>
                    {Object.entries(aiAnalysis.currency_pairs).map(([pair, analysis]) => (
                      <div key={pair} className="pair-analysis-item">
                        <h5>{pair}</h5>
                        <p>{analysis}</p>
                      </div>
                    ))}
                  </div>
                )}
                
                {aiAnalysis.trading_opportunities && (
                  <div className="trading-opportunities">
                    <h4>Trading Opportunities</h4>
                    <p>{aiAnalysis.trading_opportunities}</p>
                  </div>
                )}
                
                <div className="analysis-meta">
                  <span className="confidence">Confidence: {aiAnalysis.confidence}</span>
                  <span className="analysis-time">Analyzed just now</span>
                </div>
              </div>
            ) : (
              <div className="analysis-placeholder">
                <p>Click "Analyze with AI" to get insights on this news item.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveNewsFeed;
