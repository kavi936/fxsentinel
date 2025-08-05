import { useState, useEffect } from 'react';
import { config } from '../config';

// Fallback data in case API fails
const fallbackPrices = {
  EURUSD: { price: 1.0854, change: 0.0012, lastUpdate: new Date() },
  USDJPY: { price: 148.23, change: -0.08, lastUpdate: new Date() },
  GBPUSD: { price: 1.2650, change: -0.0020, lastUpdate: new Date() } // Replaced Gold with GBP/USD
};

export const useForexPrices = () => {
  const [prices, setPrices] = useState(fallbackPrices);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('fallback'); // 'API' or 'fallback'

  const fetchForexPrices = async () => {
    try {
      const response = await fetch(config.endpoints.forexPrices);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      return data.prices;
    } catch (error) {
      console.warn('Failed to fetch forex prices:', error.message);
      return null;
    }
  };

  const fetchAllPrices = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Check if we should use cached data (API calls are expensive)
      const lastFetch = localStorage.getItem('lastForexFetch');
      const cacheTime = 5 * 60 * 1000; // 5 minutes
      
      if (lastFetch && (Date.now() - parseInt(lastFetch)) < cacheTime) {
        const cachedData = localStorage.getItem('forexPrices');
        if (cachedData) {
          setPrices(JSON.parse(cachedData));
          setDataSource('API (cached)');
          setLoading(false);
          return;
        }
      }
      
      // Fetch all prices from backend
      const apiPrices = await fetchForexPrices();
      
      if (apiPrices) {
        setPrices(apiPrices);
        setDataSource('API');
        // Cache the data
        localStorage.setItem('forexPrices', JSON.stringify(apiPrices));
        localStorage.setItem('lastForexFetch', Date.now().toString());
      } else {
        setPrices(fallbackPrices);
        setDataSource('fallback');
        setError('Using fallback data - API unavailable');
      }
      
    } catch (error) {
      console.error('Error fetching forex prices:', error);
      setError('Failed to fetch live data');
      setDataSource('fallback');
      setPrices(fallbackPrices);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllPrices();
    
    // Refresh prices every 5 minutes
    const interval = setInterval(fetchAllPrices, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  const clearCache = () => {
    localStorage.removeItem('forexPrices');
    localStorage.removeItem('lastForexFetch');
    fetchAllPrices(); // Refresh immediately
  };

  return {
    prices,
    loading,
    error,
    dataSource,
    refreshPrices: fetchAllPrices,
    clearCache
  };
}; 