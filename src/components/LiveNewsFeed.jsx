import React, { useState, useEffect } from 'react';
import { config } from '../config';
import { formatNewsTime, getUserTimezone, getTimezoneAbbreviation } from '../utils/timezoneUtils';
import './LiveNewsFeed.css';

const LiveNewsFeed = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [filter, setFilter] = useState('all'); // all, high, medium, low
  const [currentTimezone, setCurrentTimezone] = useState(getUserTimezone());
  const [activeTab, setActiveTab] = useState('live'); // live, history
  const [newsHistory, setNewsHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyStats, setHistoryStats] = useState(null);
  const [selectedNews, setSelectedNews] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Debug useEffect to monitor state changes
  useEffect(() => {
    console.log('🦊 React app - State changed - selectedNews:', selectedNews);
    console.log('🦊 React app - State changed - aiAnalysis:', aiAnalysis);
    console.log('🦊 React app - State changed - analyzing:', analyzing);
    console.log('🦊 React app - State changed - error:', error);
  }, [selectedNews, aiAnalysis, analyzing, error]);

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
      
      // Debug logging (only in development)
      if (window.location.hostname === 'localhost') {
        console.log('🦊 React app - API_BASE_URL:', config.API_BASE_URL);
        console.log('🦊 React app - News endpoint:', config.endpoints.news);
        console.log('🦊 React app - Analysis endpoint:', config.endpoints.analysis('test'));
      }
      
      const response = await fetch(config.endpoints.news);
      const data = await response.json();
      
      if (response.ok) {
        // Ensure all news item IDs are preserved as strings to prevent precision loss
        const processedNews = (data.news || []).map(item => ({
          ...item,
          id: String(item.id) // Force ID to be string to preserve precision
        }));
        
        setNews(processedNews);
        // Debug logging (only in development)
        if (window.location.hostname === 'localhost') {
          console.log('🦊 React app - News response status:', response.status);
          console.log('🦊 React app - News count:', processedNews?.length || 0);
          console.log('🦊 React app - First 3 news items:', processedNews?.slice(0, 3).map(item => ({
            id: item.id,
            title: item.title,
            source: item.source,
            idType: typeof item.id,
            idAsString: String(item.id),
            idAsNumber: Number(item.id)
          })));
          console.log('API response last_updated:', data.last_updated, typeof data.last_updated);
        }
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

  const fetchNewsHistory = async (hours = 24) => {
    try {
      setHistoryLoading(true);
      
      const response = await fetch(`${config.API_BASE_URL}/api/news-history?hours=${hours}`);
      const data = await response.json();
      
      if (response.ok) {
        setNewsHistory(data.history || []);
        setHistoryStats(data.analysis_stats);
        console.log('History loaded:', {
          total_items: data.total_items,
          analyzed_items: data.analyzed_items,
          analysis_stats: data.analysis_stats
        });
      } else {
        throw new Error('Failed to fetch news history');
      }
    } catch (err) {
      console.error('Error fetching news history:', err);
      setNewsHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem);
    setAiAnalysis(null);
    setError(null);
  };

  const getCachedAnalysis = async (newsItem) => {
    try {
      setAnalyzing(true);
      setError(null);
      
      console.log('🦊 React app - Getting cached analysis for news item:', {
        id: newsItem.id,
        title: newsItem.title,
        source: newsItem.source
      });
      
      // Ensure news ID is treated as string to preserve precision
      const newsId = String(newsItem.id);
      const requestUrl = `${config.API_BASE_URL}/api/get-cached-analysis/${newsId}`;
      console.log('🦊 React app - Making cached analysis request to:', requestUrl);
      
      // Make API call to get cached analysis
      const response = await fetch(requestUrl);
      console.log('🦊 React app - Cached analysis response status:', response.status);
      
      if (response.ok) {
        const analysis = await response.json();
        console.log('🦊 React app - Cached analysis received:', analysis);
        
        setAiAnalysis(analysis);
        setSelectedNews(newsItem);
        console.log('🦊 React app - Cached analysis displayed successfully');
      } else {
        const errorData = await response.json();
        console.error('🦊 React app - Cached analysis request failed:', response.status, errorData);
        throw new Error(errorData.error || `Failed to get cached analysis: ${response.status}`);
      }
      
    } catch (err) {
      console.error('🦊 React app - Error getting cached analysis:', err);
      
      let errorMessage = 'Failed to load cached analysis';
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        errorMessage = 'Network error - check your connection';
      } else if (err.message.includes('Failed to get cached analysis:')) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setAiAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const analyzeNews = async (newsItem) => {
    try {
      setAnalyzing(true);
      setError(null);
      
      console.log('🦊 React app - Starting analysis for news item:', {
        id: newsItem.id,
        title: newsItem.title,
        source: newsItem.source,
        type: typeof newsItem.id,
        idAsString: String(newsItem.id),
        idAsNumber: Number(newsItem.id)
      });
      
      // Debug: Log the request URL
      // Ensure news ID is treated as string to preserve precision
      const newsId = String(newsItem.id);
      const requestUrl = config.endpoints.analysis(newsId) + '?t=' + Date.now();
      console.log('🦊 React app - Using news ID as string:', newsId);
      console.log('🦊 React app - Making analysis request to:', requestUrl);
      console.log('🦊 React app - Using API_BASE_URL:', config.API_BASE_URL);
      console.log('🦊 React app - News item:', newsItem);
      
      // Make API call to get real GPT analysis
      const response = await fetch(requestUrl);
      console.log('🦊 React app - Response status:', response.status);
      console.log('🦊 React app - Response headers:', Object.fromEntries(response.headers.entries()));
      
      const analysis = await response.json();
      console.log('🦊 React app - Analysis received:', analysis);
      console.log('🦊 React app - Analysis type:', analysis.analysis_type);
      console.log('🦊 React app - News impact:', analysis.news_impact);
      console.log('🦊 React app - Trading implications:', analysis.trading_implications);
      console.log('🦊 React app - Analysis structure:', Object.keys(analysis));
      console.log('🦊 React app - Analysis news_impact type:', typeof analysis.news_impact);
      console.log('🦊 React app - Analysis trading_implications type:', typeof analysis.trading_implications);
      console.log('🦊 React app - Analysis immediate_reaction:', analysis.immediate_reaction);
      console.log('🦊 React app - Analysis confidence:', analysis.confidence);
      console.log('🦊 React app - Analysis key_pairs:', analysis.key_pairs);
      console.log('🦊 React app - Analysis volatility:', analysis.volatility);
      console.log('🦊 React app - Analysis timeframe:', analysis.timeframe);
      console.log('🦊 React app - Analysis risk_assessment:', analysis.risk_assessment);
      console.log('🦊 React app - Analysis market_context:', analysis.market_context);
      
      if (response.ok) {
        console.log('🦊 React app - Setting AI analysis in state:', analysis);
        console.log('🦊 React app - Analysis type in state:', analysis.analysis_type);
        console.log('🦊 React app - News impact in state:', analysis.news_impact);
        console.log('🦊 React app - Trading implications in state:', analysis.trading_implications);
        console.log('🦊 React app - Full analysis object being set:', JSON.stringify(analysis, null, 2));
        console.log('🦊 React app - About to call setAiAnalysis with:', analysis);
        setAiAnalysis(analysis);
        console.log('🦊 React app - About to call setSelectedNews with:', newsItem);
        setSelectedNews(newsItem);
        
        // Refresh history if we're on the history tab to show the new analysis
        if (activeTab === 'history') {
          fetchNewsHistory();
        }
      } else {
        console.error('🦊 React app - Analysis request failed:', response.status, response.statusText);
        console.error('🦊 React app - Response body:', analysis);
        throw new Error(`Failed to analyze news: ${response.status} ${response.statusText}`);
      }
      
    } catch (err) {
      console.error('🦊 React app - Error analyzing news:', err);
      console.error('🦊 React app - Error name:', err.name);
      console.error('🦊 React app - Error message:', err.message);
      console.error('🦊 React app - Error stack:', err.stack);
      
      // Provide more specific error messages
      let errorMessage = 'Failed AI analysis try again';
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        errorMessage = 'Network error - check your connection';
      } else if (err.message.includes('Failed to analyze news:')) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setAiAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const closeAnalysis = () => {
    setSelectedNews(null);
    setAiAnalysis(null);
    setError(null);
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

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'bullish': return '#2ed573';
      case 'bearish': return '#ff4757';
      case 'neutral': return '#ffa502';
      default: return '#747d8c';
    }
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'bullish': return '📈';
      case 'bearish': return '📉';
      case 'neutral': return '➡️';
      default: return '📊';
    }
  };

  const formatTime = (timestamp) => {
    return formatNewsTime(timestamp, currentTimezone);
  };

  const formatTimeAgo = (timestamp) => {
    // Handle null/undefined
    if (!timestamp) {
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

  const getCurrentNewsList = () => {
    const currentList = activeTab === 'live' ? news : newsHistory;
    
    console.log('🦊 React app - getCurrentNewsList - Original news items:', currentList.slice(0, 3).map(item => ({
      id: item.id,
      title: item.title,
      idType: typeof item.id,
      is_analyzed: item.is_analyzed
    })));
    
    // Remove duplicates based on title similarity
    const uniqueNews = removeDuplicateNews(currentList);
    
    console.log('🦊 React app - getCurrentNewsList - After removeDuplicateNews:', uniqueNews.slice(0, 3).map(item => ({
      id: item.id,
      title: item.title,
      idType: typeof item.id,
      is_analyzed: item.is_analyzed
    })));
    
    const filteredAndSorted = uniqueNews
      .filter(item => {
        // For history tab, only show analyzed news items
        if (activeTab === 'history' && !item.is_analyzed) {
          return false;
        }
        
        // Apply impact filter
        if (filter === 'all') return true;
        return item.impact?.toLowerCase() === filter;
      })
      .sort((a, b) => {
        // Sort by published_at timestamp in descending order (newest first)
        const dateA = new Date(a.published_at);
        const dateB = new Date(b.published_at);
        return dateB - dateA;
      });
    
    console.log('🦊 React app - getCurrentNewsList - Final result:', filteredAndSorted.slice(0, 3).map(item => ({
      id: item.id,
      title: item.title,
      idType: typeof item.id,
      is_analyzed: item.is_analyzed
    })));
    
    return filteredAndSorted;
  };

  const cleanNewsTitle = (title) => {
    if (!title) return title;
    
    // Remove common prefixes that make titles look unprofessional
    // Order matters: put longer patterns first to avoid partial matches
    const prefixesToRemove = [
      '**JUST IN:**',  // **JUST IN:**
      '**BREAKING:**', // **BREAKING:**
      '**UPDATE:**',   // **UPDATE:**
      '**LIVE:**',     // **LIVE:**
      '**URGENT:**',   // **URGENT:**
      'JUST IN:',      // JUST IN:
      'BREAKING:',     // BREAKING:
      'UPDATE:',       // UPDATE:
      'LIVE:',         // LIVE:
      'URGENT:',       // URGENT:
    ];
    
    let cleanedTitle = title;
    
    // Remove each prefix pattern (case insensitive)
    prefixesToRemove.forEach(prefix => {
      const regex = new RegExp(prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      cleanedTitle = cleanedTitle.replace(regex, '');
    });
    
    // Clean up extra whitespace and punctuation
    cleanedTitle = cleanedTitle.replace(/\s+/g, ' '); // Multiple spaces to single space
    cleanedTitle = cleanedTitle.trim();
    
    // Remove leading/trailing punctuation
    cleanedTitle = cleanedTitle.replace(/^[:\s\-_]+/, ''); // Remove leading colons, spaces, dashes
    cleanedTitle = cleanedTitle.replace(/[:\s\-_]+$/, ''); // Remove trailing colons, spaces, dashes
    
    return cleanedTitle;
  };

  const removeDuplicateNews = (newsList) => {
    const uniqueNews = [];
    const seenTitles = new Set();
    const seenUrls = new Set();
    
    for (const newsItem of newsList) {
      if (!newsItem || !newsItem.title) continue;
      
      // Clean the title first
      const cleanedTitle = cleanNewsTitle(newsItem.title.trim());
      const url = newsItem.url?.trim();
      
      // Create simplified title key (first 5 words, lowercase, no punctuation)
      const simpleTitle = cleanedTitle.toLowerCase().replace(/[^\w\s]/g, '').split(' ').slice(0, 5).join(' ');
      
      // Create source + title combination
      const source = newsItem.source?.toLowerCase() || '';
      const sourceTitleKey = `${source}_${simpleTitle}`;
      
      // Check if this is a duplicate
      const isDuplicate = seenTitles.has(simpleTitle) || 
                         (url && seenUrls.has(url.toLowerCase())) ||
                         seenTitles.has(sourceTitleKey);
      
      if (!isDuplicate) {
        seenTitles.add(simpleTitle);
        if (url) seenUrls.add(url.toLowerCase());
        seenTitles.add(sourceTitleKey);
        
        // Create a copy of the news item with cleaned title and preserved string ID
        const cleanedNewsItem = { 
          ...newsItem, 
          title: cleanedTitle,
          id: String(newsItem.id) // Ensure ID remains as string
        };
        uniqueNews.push(cleanedNewsItem);
      }
    }
    
    return uniqueNews;
  };

  const clearSelection = () => {
    setSelectedNews(null);
    setAiAnalysis(null);
    setError(null);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedNews(null);
    setAiAnalysis(null);
    setError(null);
    
    if (tab === 'history' && newsHistory.length === 0) {
      fetchNewsHistory();
    }
  };

  return (
    <div className="live-news-feed">
      <div className="news-header">
        <div className="header-main">
          <h2 className="news-title">LIVE NEWS + ANALYSIS</h2>
        </div>
        <div className="news-controls">
          <div className="tab-controls">
            <button 
              className={`tab-btn ${activeTab === 'live' ? 'active' : ''}`}
              onClick={() => handleTabChange('live')}
              title="Live News"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12,6 12,12 16,14"></polyline>
              </svg>
            </button>
            <button 
              className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => handleTabChange('history')}
              title="News History"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 3v18h18"></path>
                <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path>
              </svg>
            </button>
          </div>
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
          <button className="news-refresh-btn" onClick={activeTab === 'live' ? fetchNews : () => fetchNewsHistory()} disabled={loading || historyLoading}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
            </svg>
          </button>
        </div>
      </div>

      <div className="news-content">
        {(loading && activeTab === 'live') || (historyLoading && activeTab === 'history') ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading {activeTab === 'live' ? 'latest news' : 'news history'}...</p>
          </div>
        ) : getCurrentNewsList().length === 0 ? (
          <div className="empty-state">
            <div className="placeholder-icon">
              {activeTab === 'live' ? '📰' : '📊'}
            </div>
            <p className="placeholder-text">No {activeTab === 'live' ? 'News' : 'Analyzed News'} Available</p>
            <p className="placeholder-subtext">
              {activeTab === 'live' 
                ? 'News feed will appear here when available' 
                : 'Analyzed news items will appear here. Click "Get AI Analysis" on any news item to start building your history.'
              }
            </p>
            {activeTab === 'history' && (
              <div className="history-empty-actions">
                <button onClick={() => handleTabChange('live')} className="switch-tab-btn">
                  Switch to Live News
                </button>
                <button onClick={() => fetchNewsHistory()} className="news-refresh-btn">
                  Refresh History
                </button>
              </div>
            )}
            {activeTab === 'live' && (
              <button onClick={fetchNews}>Refresh</button>
            )}
          </div>
        ) : (
          <div className="news-list">
            {getCurrentNewsList().map((newsItem) => (
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
                  
                  {/* Analysis Status Indicator */}
                  {newsItem.is_analyzed && (
                    <div className="analysis-status-indicator">
                      <div className="analysis-badge">
                        <span className="analysis-icon">📊</span>
                        <span className="analysis-text">Analyzed</span>
                        {activeTab === 'history' && (
                          <button 
                            className="view-analysis-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleNewsClick(newsItem);
                              // Get the cached analysis for this news item
                              getCachedAnalysis(newsItem);
                            }}
                            title="View Analysis"
                          >
                            View Analysis
                          </button>
                        )}
                      </div>
                      {newsItem.analysis_summary && (
                        <div className="analysis-summary">
                          <span className="analysis-type">{newsItem.analysis_summary.type === 'gpt_enhanced' ? 'AI Enhanced' : 'Free Analysis'}</span>
                          <span className="analysis-confidence">{newsItem.analysis_summary.confidence}%</span>
                          <span className={`analysis-reaction ${newsItem.analysis_summary.reaction}`}>
                            {newsItem.analysis_summary.reaction?.replace('_', ' ').toUpperCase()}
                          </span>
                          {newsItem.analysis_summary.cost > 0 && (
                            <span className="analysis-cost">${newsItem.analysis_summary.cost.toFixed(4)}</span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="news-actions">
                  <button 
                    className="analyze-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('🦊 React app - Analyze button clicked for news item:', newsItem);
                      console.log('🦊 React app - News item ID:', newsItem.id);
                      console.log('🦊 React app - News item ID type:', typeof newsItem.id);
                      console.log('🦊 React app - News item title:', newsItem.title);
                      console.log('🦊 React app - News item ID as string:', String(newsItem.id));
                      console.log('🦊 React app - News item ID as number:', Number(newsItem.id));
                      console.log('🦊 React app - Full news item object:', JSON.stringify(newsItem, null, 2));
                      setSelectedNews(newsItem);
                      analyzeNews(newsItem);
                    }}
                    disabled={analyzing && selectedNews?.id === newsItem.id}
                  >
                    {analyzing && selectedNews?.id === newsItem.id ? 'Analyzing...' : 'Get AI Analysis'}
                  </button>
                  
                  <a 
                    href={newsItem.url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="read-more-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!newsItem.url) {
                        e.preventDefault();
                        alert('No URL available for this news item');
                      }
                    }}
                  >
                    Read Full Article
                  </a>
                </div>

                {/* AI Analysis Section - Expandable within the news item */}
                {(() => {
                  const shouldShow = selectedNews?.id === newsItem.id && (aiAnalysis || analyzing || error);
                  console.log('🦊 React app - Analysis section condition:', {
                    selectedNewsId: selectedNews?.id,
                    newsItemId: newsItem.id,
                    hasAiAnalysis: !!aiAnalysis,
                    isAnalyzing: analyzing,
                    hasError: !!error,
                    shouldShow
                  });
                  
                  // Additional debugging for the specific news item
                  if (selectedNews?.id === newsItem.id) {
                    console.log('🦊 React app - This news item is selected!');
                    console.log('🦊 React app - aiAnalysis state:', aiAnalysis);
                    console.log('🦊 React app - analyzing state:', analyzing);
                    console.log('🦊 React app - error state:', error);
                  }
                  
                  return shouldShow;
                })() && (
                  <div className="ai-analysis-section" onClick={(e) => e.stopPropagation()}>
                    <div className="analysis-header">
                      <h4>AI Analysis</h4>
                      <button className="close-analysis-btn" onClick={closeAnalysis}>×</button>
                    </div>
                    
                    {analyzing && !aiAnalysis ? (
                      <div className="analysis-loading" onClick={(e) => e.stopPropagation()}>
                        <div className="loading-spinner"></div>
                        <p>Analyzing news sentiment and market implications...</p>
                      </div>
                    ) : error ? (
                      <div className="analysis-error" onClick={(e) => e.stopPropagation()}>
                        <p>{error}</p>
                        <button 
                          className="retry-analysis-btn"
                          onClick={() => analyzeNews(newsItem)}
                          disabled={analyzing}
                        >
                          {analyzing ? 'Analyzing...' : 'Try Again'}
                        </button>
                      </div>
                    ) : aiAnalysis ? (
                      <div className="analysis-content" onClick={(e) => e.stopPropagation()}>
                        {console.log('🦊 React app - Rendering analysis content with aiAnalysis:', aiAnalysis)}
                        {console.log('🦊 React app - aiAnalysis.news_impact:', aiAnalysis.news_impact)}
                        {console.log('🦊 React app - aiAnalysis.trading_implications:', aiAnalysis.trading_implications)}
                        {console.log('🦊 React app - aiAnalysis.immediate_reaction:', aiAnalysis.immediate_reaction)}
                        {console.log('🦊 React app - aiAnalysis.confidence:', aiAnalysis.confidence)}
                        {/* Simplified Analysis Header */}
                        <div className="analysis-content-header">
                          <div className="sentiment-badge" style={{ backgroundColor: getSentimentColor(aiAnalysis.immediate_reaction?.replace('_', ' ') || 'neutral') }}>
                            {getSentimentIcon(aiAnalysis.immediate_reaction?.replace('_', ' ') || 'neutral')} {aiAnalysis.immediate_reaction?.replace('_', ' ').toUpperCase() || 'NEUTRAL'}
                          </div>
                          <div className={`confidence-score ${aiAnalysis.confidence > 80 ? 'high' : aiAnalysis.confidence > 60 ? 'medium' : 'low'}`}>
                            Confidence: {typeof aiAnalysis.confidence === 'string' ? aiAnalysis.confidence : `${aiAnalysis.confidence}%`}
                          </div>
                        </div>
                        
                        {/* News Impact Paragraph */}
                        <div className="news-impact">
                          <h5>Market Impact</h5>
                          <p>{aiAnalysis.news_impact || 'NO NEWS IMPACT DATA'}</p>
                        </div>
                        
                        {/* Trading Essentials */}
                        <div className="trading-essentials">
                          <div className="essentials-grid">
                            <div className="essential-item">
                              <span className="label">Immediate Reaction:</span>
                              <span className="value bold">{aiAnalysis.immediate_reaction?.replace('_', ' ').toUpperCase() || 'NEUTRAL'}</span>
                            </div>
                            <div className="essential-item">
                              <span className="label">Key Pairs:</span>
                              <span className="value">{aiAnalysis.key_pairs?.join(', ') || 'EUR/USD, USD/JPY'}</span>
                            </div>
                            <div className="essential-item">
                              <span className="label">Volatility:</span>
                              <span className="value">{aiAnalysis.volatility?.toUpperCase() || 'MEDIUM'}</span>
                            </div>
                            <div className="essential-item">
                              <span className="label">Timeframe:</span>
                              <span className="value">{aiAnalysis.timeframe || '1-24 hours'}</span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Trading Implications Paragraph */}
                        <div className="trading-implications">
                          <h5>Trading Implications</h5>
                          <p>{aiAnalysis.trading_implications || 'NO TRADING IMPLICATIONS DATA'}</p>
                        </div>
                        
                        {/* Risk Assessment */}
                        {aiAnalysis.risk_assessment && (
                          <div className="risk-assessment">
                            <h5>Risk Assessment</h5>
                            <div className="risk-grid">
                              <div className="risk-item">
                                <span className="risk-label">Market Volatility:</span>
                                <span className={`risk-value ${aiAnalysis.risk_assessment.market_volatility}`}>
                                  {aiAnalysis.risk_assessment.market_volatility?.toUpperCase() || 'MEDIUM'}
                                </span>
                              </div>
                              <div className="risk-item">
                                <span className="risk-label">Liquidity Impact:</span>
                                <span className={`risk-value ${aiAnalysis.risk_assessment.liquidity_impact}`}>
                                  {aiAnalysis.risk_assessment.liquidity_impact?.toUpperCase() || 'MEDIUM'}
                                </span>
                              </div>
                              <div className="risk-item">
                                <span className="risk-label">Correlation Risk:</span>
                                <span className={`risk-value ${aiAnalysis.risk_assessment.correlation_risk}`}>
                                  {aiAnalysis.risk_assessment.correlation_risk?.toUpperCase() || 'MEDIUM'}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* Market Context */}
                        {aiAnalysis.market_context && (
                          <div className="market-context">
                            <h5>Market Context</h5>
                            <div className="context-sections">
                              {aiAnalysis.market_context.economic_factors && (
                                <div className="context-section">
                                  <span className="context-label">Economic Factors:</span>
                                  <div className="context-items">
                                    {aiAnalysis.market_context.economic_factors.map((factor, index) => (
                                      <span key={index} className="context-item">{factor}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {aiAnalysis.market_context.technical_levels && (
                                <div className="context-section">
                                  <span className="context-label">Technical Levels:</span>
                                  <div className="context-items">
                                    {aiAnalysis.market_context.technical_levels.map((level, index) => (
                                      <span key={index} className="context-item">{level}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {aiAnalysis.market_context.sentiment_drivers && (
                                <div className="context-section">
                                  <span className="context-label">Sentiment Drivers:</span>
                                  <div className="context-items">
                                    {aiAnalysis.market_context.sentiment_drivers.map((driver, index) => (
                                      <span key={index} className="context-item">{driver}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        

                        

                        
                        <div className="analysis-meta">
                          <span className="analysis-time">Analyzed just now</span>
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveNewsFeed;
