import React from 'react';
import './Markets.css';

function Markets({ tradingData, aiInsights, getSentimentColor }) {
  return (
    <div className="markets-section">
      <div className="markets-overview">
        <h2>📈 Live Market Data</h2>
        <p>Real-time forex prices and market analysis</p>
      </div>
      
      <div className="markets-grid">
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
                <h4>📊 {insight.title}</h4>
                <p>{insight.description}</p>
                <div className="insight-meta">
                  <span className="confidence">Confidence: {insight.confidence}%</span>
                  <span className="timeframe">{insight.timeframe}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Markets;
