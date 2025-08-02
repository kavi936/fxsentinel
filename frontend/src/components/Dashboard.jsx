import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { config } from '../config';
import './Dashboard.css';

function Dashboard() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNews, setSelectedNews] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  // Fetch news data on mount
  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const response = await axios.get(config.endpoints.news);
      setNews(response.data.news);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching news:', error);
      setLoading(false);
    }
  };

  const fetchAnalysis = async (newsId) => {
    try {
      const response = await axios.get(config.endpoints.analysis(newsId));
      setAnalysis(response.data);
    } catch (error) {
      console.error('Error fetching analysis:', error);
    }
  };

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem);
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

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading market news...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Dashboard Header */}
      <header className="dashboard-header">
        <div className="dashboard-nav">
          <Link to="/" className="back-link">
            ← Back to Home
          </Link>
          <div className="dashboard-title">
            <h1>🌐 FXSentinel Dashboard</h1>
            <p>AI-Powered Macro News Analysis</p>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="news-grid">
          <div className="news-list">
            <h2>📊 Upcoming Events</h2>
            {news.map((item) => (
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
                  <span className="time">{item.time}</span>
                  <span className="currency">{item.currency}</span>
                </div>
                <div className="pairs">
                  {item.pairs.map((pair, index) => (
                    <span key={index} className="pair-tag">{pair}</span>
                  ))}
                </div>
              </div>
            ))}
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

                {analysis && (
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
                )}
              </div>
            ) : (
              <div className="no-selection">
                <h2>🤖 AI Analysis</h2>
                <p>Select a news event to see AI-powered analysis and trading insights.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard; 