import React, { useEffect } from 'react';
import { useForexPrices } from '../hooks/useForexPrices';
import './LiveTicker.css';

const LiveTicker = () => {
  const { prices, loading, error } = useForexPrices();

  // Clear cache on component mount to ensure fresh data
  useEffect(() => {
    console.log('LiveTicker: Clearing cache and forcing refresh...');
    localStorage.removeItem('forexPrices');
    localStorage.removeItem('lastForexFetch');
  }, []);

  const formatPrice = (price, decimals = 4) => {
    return price.toFixed(decimals);
  };

  return (
    <div className="live-ticker-container">
      <div className="live-ticker">
        <span className="ticker-label">
          Live
        </span>
        
        {loading ? (
          <span className="ticker-loading">Loading...</span>
        ) : (
          <>
            <span className="ticker-item">
              EUR/USD {formatPrice(prices.EURUSD.price)}
            </span>
            <span className="ticker-separator">•</span>
            <span className="ticker-item">
              USD/JPY {formatPrice(prices.USDJPY.price, 2)}
            </span>
            <span className="ticker-separator">•</span>
            <span className="ticker-item">
              GBP/USD {formatPrice(prices.GBPUSD.price)}
            </span>
          </>
        )}
      </div>
    </div>
  );
};

export default LiveTicker; 