import React from 'react';
import { useForexPrices } from '../hooks/useForexPrices';

const ForexPriceDebug = () => {
  const { prices, loading, error, dataSource, clearCache } = useForexPrices();

  const handleClearCache = () => {
    clearCache();
  };

  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      right: '10px', 
      background: 'rgba(0,0,0,0.8)', 
      color: 'white', 
      padding: '10px', 
      borderRadius: '5px',
      fontSize: '12px',
      zIndex: 1000
    }}>
      <h4>Forex Price Debug</h4>
      <div>Loading: {loading ? 'Yes' : 'No'}</div>
      <div>Data Source: {dataSource}</div>
      <div>EUR/USD: {prices.EURUSD?.price?.toFixed(4)}</div>
      <div>USD/JPY: {prices.USDJPY?.price?.toFixed(2)}</div>
      <div>GBP/USD: {prices.GBPUSD?.price?.toFixed(4)}</div>
      <div>Last Update: {prices.GBPUSD?.lastUpdate?.toLocaleString()}</div>
      {error && <div style={{color: 'red'}}>Error: {error}</div>}
      <button 
        onClick={handleClearCache}
        style={{
          marginTop: '5px',
          padding: '2px 8px',
          background: '#ff4444',
          color: 'white',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer'
        }}
      >
        Clear Cache
      </button>
    </div>
  );
};

export default ForexPriceDebug; 