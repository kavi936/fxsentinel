import React, { useEffect } from 'react';
import { useForexPrices } from '../hooks/useForexPrices';
import './LiveTicker.css';

const LiveTicker = () => {
  const { prices, loading, error, dataSource, dataQuality } = useForexPrices();

  // Clear cache on component mount to ensure fresh data
  useEffect(() => {
    console.log('LiveTicker: Clearing cache and forcing refresh...');
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
      dataQuality,
      gbpPrice: prices.GBPUSD?.price,
      eurPrice: prices.EURUSD?.price,
      jpyPrice: prices.USDJPY?.price,
      isMarketClosed: dataQuality?.isMarketClosed,
      hasStaleData: dataQuality?.hasStaleData,
      hasModeratelyOldData: dataQuality?.hasModeratelyOldData
    });
  }, [prices, loading, error, dataSource, dataQuality]);

  const formatPrice = (price, decimals = 4) => {
    return price.toFixed(decimals);
  };

  const getDataQualityIndicator = () => {
    if (!dataQuality) return null;
    
    // If market is closed, don't show any indicator
    if (dataQuality.isMarketClosed) {
      return null;
    }
    
    // Show warning only for truly stale data (not just moderately old)
    if (dataQuality.hasStaleData) {
      return (
        <span className="ticker-warning" title={`Data may be stale (${dataQuality.averageAgeMinutes?.toFixed(1)} min old)`}>
          [STALE]
        </span>
      );
    }
    
    // Show info for moderately old data during market hours
    if (dataQuality.hasModeratelyOldData && !dataQuality.isMarketClosed) {
      return (
        <span className="ticker-info" title={`Data age: ${dataQuality.averageAgeMinutes?.toFixed(1)} minutes`}>
          [OLD]
        </span>
      );
    }
    
    return null;
  };

  const getDataSourceInfo = () => {
    if (!dataSource) return null;
    
    if (dataSource.includes('TradingView')) {
      return (
        <span className="ticker-source" title="Real-time forex market data from TradingView">
          [TV]
        </span>
      );
    }
    
    if (dataSource.includes('AlphaVantage')) {
      return (
        <span className="ticker-source" title="Data from Alpha Vantage (Professional forex data)">
          [AV]
        </span>
      );
    }
    
    if (dataSource.includes('UniRateAPI')) {
      return (
        <span className="ticker-source" title="Data from UniRateAPI">
          [UR]
        </span>
      );
    }
    
    if (dataSource.includes('fallback')) {
      return (
        <span className="ticker-source" title="Using fallback data - API rate limit exceeded">
          [FB]
        </span>
      );
    }
    
    return null;
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
            [ERROR]
          </span>
        )}
        
        {/* Show data quality indicator */}
        {getDataQualityIndicator()}
      </div>
    </div>
  );
};

export default LiveTicker; 