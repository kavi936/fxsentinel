import React, { useState } from 'react';
import { useForexPrices } from '../hooks/useForexPrices';
import './Overview.css';

const Overview = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [selectedPairs, setSelectedPairs] = useState(['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']);
  const { prices, loading, error } = useForexPrices();

  // All available forex pairs
  const allPairs = [
    { key: 'EURUSD', label: 'EUR/USD' },
    { key: 'GBPUSD', label: 'GBP/USD' },
    { key: 'USDJPY', label: 'USD/JPY' },
    { key: 'USDCHF', label: 'USD/CHF' },
    { key: 'AUDUSD', label: 'AUD/USD' },
    { key: 'USDCAD', label: 'USD/CAD' },
    { key: 'NZDUSD', label: 'NZD/USD' },
    { key: 'EURGBP', label: 'EUR/GBP' },
    { key: 'EURJPY', label: 'EUR/JPY' },
    { key: 'GBPJPY', label: 'GBP/JPY' },
    { key: 'USDSEK', label: 'USD/SEK' },
    { key: 'USDNOK', label: 'USD/NOK' },
    { key: 'USDHKD', label: 'USD/HKD' },
    { key: 'EURCHF', label: 'EUR/CHF' },
    { key: 'GBPCHF', label: 'GBP/CHF' }
  ];

  // Currently displayed pairs (max 5)
  const currencyPairs = allPairs.filter(pair => selectedPairs.includes(pair.key));

  const handleEditClick = () => {
    setIsEditing(true);
  };

  const handleCloseModal = () => {
    setIsEditing(false);
  };

  const handlePairToggle = (pairKey) => {
    setSelectedPairs(prev => {
      if (prev.includes(pairKey)) {
        // Remove pair
        return prev.filter(key => key !== pairKey);
      } else {
        // Add pair (max 5)
        if (prev.length < 5) {
          return [...prev, pairKey];
        }
        return prev; // Don't add if already at max
      }
    });
  };

  const handleSaveChanges = () => {
    setIsEditing(false);
    // Here you could save to localStorage or backend
  };

  // Helper functions for formatting
  const formatPrice = (price) => {
    if (!price) return '0.0000';
    return parseFloat(price).toFixed(4);
  };

  const formatChange = (change) => {
    if (!change) return '+0.0000';
    const num = parseFloat(change);
    return (num >= 0 ? '+' : '') + num.toFixed(4);
  };

  const formatPercentage = (change, price) => {
    if (!change || !price) return '+0.00%';
    const num = parseFloat(change);
    const percent = (num / parseFloat(price)) * 100;
    return (percent >= 0 ? '+' : '') + percent.toFixed(2) + '%';
  };

  const getChangeColor = (change) => {
    if (!change) return '#666';
    return parseFloat(change) >= 0 ? '#00ff88' : '#ff4757';
  };

  return (
    <div className="overview-tab">
      {/* Market Ticker - Full width, top of overview */}
      <div className="market-ticker-container">
        <div className="market-ticker">
          {/* Edit Button */}
          <button className="ticker-edit-btn" onClick={handleEditClick}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>

          {/* Currency Pairs - Inline Format */}
          <div className="ticker-pairs-inline">
            {currencyPairs.map((pair, index) => {
              const priceData = prices[pair.key];
              const price = priceData?.price || '0.0000';
              const change = priceData?.change || '0.0000';
              const changeColor = getChangeColor(change);

              return (
                <span key={pair.key} className="ticker-pair-inline">
                  <span className="pair-label-inline">{pair.label}</span>
                  <span className="pair-rate-inline" style={{ color: changeColor }}>
                    {formatPrice(price)}
                  </span>
                  <span className="pair-change-inline" style={{ color: changeColor }}>
                    {formatChange(change)}
                  </span>
                  <span className="pair-percentage-inline" style={{ color: changeColor }}>
                    {formatPercentage(change, price)}
                  </span>
                  
                  {/* Separator between pairs */}
                  {index < currencyPairs.length - 1 && (
                    <span className="pair-separator-inline"> | </span>
                  )}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* Rest of Overview Content */}
      <div className="overview-content">
        {loading && <div className="loading-indicator">Loading market data...</div>}
        {error && <div className="error-indicator">Error: {error}</div>}
        
        {/* Additional overview content can go here */}
        <div className="overview-content-main">
          {/* Content will be added here */}
        </div>
      </div>

      {/* Forex Pairs Selection Modal */}
      {isEditing && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="modal-header">
              <h2>Select Forex Pairs</h2>
              <button className="modal-close-btn" onClick={handleCloseModal}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* Modal Instructions */}
            <div className="modal-instructions">
              <p>Choose which forex pairs to display on your dashboard (max 5 pairs). The order you select them will be the order they appear in the ticker.</p>
            </div>

            {/* Forex Pairs Grid */}
            <div className="pairs-grid">
              {allPairs.map((pair) => {
                const isSelected = selectedPairs.includes(pair.key);
                return (
                  <div
                    key={pair.key}
                    className={`pair-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => handlePairToggle(pair.key)}
                  >
                    <div className="pair-checkbox">
                      {isSelected && (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M20 6L9 17L4 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                    <span className="pair-label">{pair.label}</span>
                    {isSelected && (
                      <button 
                        className="pair-remove-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePairToggle(pair.key);
                        }}
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M18 6L6 18M6 6L18 18" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Modal Actions */}
            <div className="modal-actions">
              <button className="btn-cancel" onClick={handleCloseModal}>
                Cancel
              </button>
              <button className="btn-save" onClick={handleSaveChanges}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Overview;
