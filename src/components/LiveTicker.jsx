import React, { useEffect } from 'react';
import { useForexPrices } from '../hooks/useForexPrices';
import './LiveTicker.css';

const LiveTicker = () => {
  const { prices, loading, error, dataSource, clearCache } = useForexPrices();

  // Clear cache on component mount to ensure fresh data
  useEffect(() => {
    localStorage.removeItem('forexPrices');
    localStorage.removeItem('lastForexFetch');
  }, []);

  // Debug logging
  useEffect(() => {
    console.log('LiveTicker Debug:', {
      prices,
      loading,
      error,
      dataSource,
      gbpPrice: prices.GBPUSD?.price,
      eurPrice: prices.EURUSD?.price,
      jpyPrice: prices.USDJPY?.price
    });
  }, [prices, loading, error, dataSource]);

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
        
        {error && (
          <span className="ticker-error" title={error}>
            ⚠️
          </span>
        )}
      </div>
    </div>
  );
};

export default LiveTicker; 