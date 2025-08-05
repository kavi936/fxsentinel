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

  const fetchForexPrice = async (fromCurrency, toCurrency, pairName) => {
    try {
      const response = await fetch(config.endpoints.forexPrice(fromCurrency, toCurrency));
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data['Error Message']) {
        throw new Error(data['Error Message']);
      }
      
      if (data['Note']) {
        throw new Error('API rate limit exceeded');
      }
      
      const exchangeRate = data['Realtime Currency Exchange Rate'];
      if (exchangeRate) {
        const price = parseFloat(exchangeRate['5. Exchange Rate']);
        const lastUpdate = new Date(exchangeRate['6. Last Refreshed']);
        
        return {
          price: price,
          change: 0, // Alpha Vantage doesn't provide change in this endpoint
          lastUpdate: lastUpdate
        };
      }
      
      throw new Error('No exchange rate data found');
    } catch (error) {
      console.warn(`Failed to fetch ${pairName}:`, error.message);
      return null;
    }
  };

  const fetchGBPUSDPrice = async () => {
    try {
      const response = await fetch(config.endpoints.forexPrice('GBP', 'USD'));
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data['Error Message']) {
        throw new Error(data['Error Message']);
      }
      
      if (data['Note']) {
        throw new Error('API rate limit exceeded');
      }
      
      const exchangeRate = data['Realtime Currency Exchange Rate'];
      if (exchangeRate) {
        const price = parseFloat(exchangeRate['5. Exchange Rate']);
        const lastUpdate = new Date(exchangeRate['6. Last Refreshed']);
        
        return {
          price: price,
          change: 0,
          lastUpdate: lastUpdate
        };
      }
      
      throw new Error('No GBP/USD exchange rate data found');
    } catch (error) {
      console.warn('Failed to fetch GBP/USD price:', error.message);
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
      
      // Fetch all prices concurrently
      const [eurUsdData, usdJpyData, gbpUsdData] = await Promise.allSettled([
        fetchForexPrice('EUR', 'USD', 'EUR/USD'),
        fetchForexPrice('USD', 'JPY', 'USD/JPY'),
        fetchGBPUSDPrice()
      ]);
      
      const newPrices = { ...fallbackPrices };
      let apiDataCount = 0;
      
      // Update with API data if available
      if (eurUsdData.status === 'fulfilled' && eurUsdData.value) {
        newPrices.EURUSD = eurUsdData.value;
        apiDataCount++;
      }
      
      if (usdJpyData.status === 'fulfilled' && usdJpyData.value) {
        newPrices.USDJPY = usdJpyData.value;
        apiDataCount++;
      }
      
      if (gbpUsdData.status === 'fulfilled' && gbpUsdData.value) {
        newPrices.GBPUSD = gbpUsdData.value;
        apiDataCount++;
      }
      
      setPrices(newPrices);
      
      // Determine data source
      if (apiDataCount > 0) {
        setDataSource('API');
        // Cache the data
        localStorage.setItem('forexPrices', JSON.stringify(newPrices));
        localStorage.setItem('lastForexFetch', Date.now().toString());
      } else {
        setDataSource('fallback');
        setError('Using fallback data - API unavailable');
      }
      
    } catch (error) {
      console.error('Error fetching forex prices:', error);
      setError('Failed to fetch live data');
      setDataSource('fallback');
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