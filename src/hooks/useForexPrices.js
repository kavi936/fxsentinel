import { useState, useEffect } from 'react';
import { config } from '../config';

// Fallback data in case API fails
const fallbackPrices = {
  EURUSD: { price: 1.0923, change: 0.0012, lastUpdate: new Date() },
  USDJPY: { price: 147.85, change: -0.08, lastUpdate: new Date() },
  GBPUSD: { price: 1.2712, change: -0.0020, lastUpdate: new Date() } // Replaced Gold with GBP/USD
};

export const useForexPrices = () => {
  const [prices, setPrices] = useState(fallbackPrices);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('fallback'); // 'API' or 'fallback'
  const [dataQuality, setDataQuality] = useState(null);

  const fetchForexPrices = async () => {
    try {
      console.log('🔍 Fetching from:', config.endpoints.forexPrices);
      const response = await fetch(config.endpoints.forexPrices);
      
      console.log('📡 Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📊 API Response data:', data);
      console.log('💰 Prices received:', data.prices);
      console.log('📈 Data quality:', data.dataQuality);
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      return {
        prices: data.prices,
        dataSource: data.dataSource,
        dataQuality: data.dataQuality
      };
    } catch (error) {
      console.error('Failed to fetch forex prices:', error.message);
      return null;
    }
  };

  const fetchAllPrices = async () => {
    setLoading(true);
    setError(null);
    
    console.log('Starting fetchAllPrices...');
    
    try {
      // Check if we should use cached data (API calls are expensive)
      const lastFetch = localStorage.getItem('lastForexFetch');
      const cacheTime = 5 * 60 * 1000; // 5 minutes
      
      console.log('Last fetch:', lastFetch);
      console.log('Cache time check:', lastFetch && (Date.now() - parseInt(lastFetch)) < cacheTime);
      
      if (lastFetch && (Date.now() - parseInt(lastFetch)) < cacheTime) {
        const cachedData = localStorage.getItem('forexPrices');
        if (cachedData) {
          console.log('Using cached data');
          const parsedData = JSON.parse(cachedData);
          setPrices(parsedData.prices || parsedData);
          setDataSource(parsedData.dataSource || 'API (cached)');
          setDataQuality(parsedData.dataQuality || null);
          setLoading(false);
          return;
        }
      }
      
      console.log('Fetching fresh data from API...');
      // Fetch all prices from backend
      const apiData = await fetchForexPrices();
      
      if (apiData) {
        console.log('API data received:', apiData);
        setPrices(apiData.prices);
        setDataSource(apiData.dataSource);
        setDataQuality(apiData.dataQuality);
        // Cache the data
        localStorage.setItem('forexPrices', JSON.stringify(apiData));
        localStorage.setItem('lastForexFetch', Date.now().toString());
      } else {
        console.log('API failed, using fallback data');
        setPrices(fallbackPrices);
        setDataSource('fallback');
        setDataQuality(null);
        setError('Using fallback data - API unavailable');
      }
      
    } catch (error) {
      console.error('Error fetching forex prices:', error);
      setError('Failed to fetch live data');
      setDataSource('fallback');
      setDataQuality(null);
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
    fetchAllPrices();
  };

  return {
    prices,
    loading,
    error,
    dataSource,
    dataQuality,
    clearCache
  };
}; 