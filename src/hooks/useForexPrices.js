import { useState, useEffect } from 'react';
import { config } from '../config';

// Fallback data in case API fails
const fallbackPrices = {
  EURUSD: { price: 1.0923, change: 0.0012, lastUpdate: new Date() },
  GBPUSD: { price: 1.2712, change: -0.0020, lastUpdate: new Date() },
  USDJPY: { price: 147.85, change: -0.08, lastUpdate: new Date() },
  USDCHF: { price: 0.8845, change: 0.0015, lastUpdate: new Date() },
  AUDUSD: { price: 0.6623, change: -0.0018, lastUpdate: new Date() },
  USDCAD: { price: 1.3542, change: 0.0021, lastUpdate: new Date() },
  NZDUSD: { price: 0.6128, change: -0.0012, lastUpdate: new Date() },
  EURGBP: { price: 0.8598, change: 0.0015, lastUpdate: new Date() },
  EURJPY: { price: 161.45, change: -0.12, lastUpdate: new Date() },
  GBPJPY: { price: 187.82, change: -0.25, lastUpdate: new Date() },
  USDSEK: { price: 10.456, change: 0.023, lastUpdate: new Date() },
  USDNOK: { price: 10.823, change: 0.031, lastUpdate: new Date() },
  USDHKD: { price: 7.8234, change: 0.015, lastUpdate: new Date() },
  EURCHF: { price: 0.9665, change: 0.0028, lastUpdate: new Date() },
  GBPCHF: { price: 1.1234, change: 0.0019, lastUpdate: new Date() },
  BTCUSDT: { price: 98000, change: 120, lastUpdate: new Date(), decimals: 2, category: 'crypto' },
  ETHUSDT: { price: 3500, change: -15, lastUpdate: new Date(), decimals: 2, category: 'crypto' },
  GOLD: { price: 2650, change: 4.2, lastUpdate: new Date(), decimals: 2, category: 'commodities' },
  SILVER: { price: 31.2, change: -0.08, lastUpdate: new Date(), decimals: 3, category: 'commodities' },
  USOIL: { price: 72.5, change: -0.35, lastUpdate: new Date(), decimals: 2, category: 'commodities' },
  SPX: { price: 6500, change: -100, lastUpdate: new Date(), decimals: 2, category: 'indices' },
  DJI: { price: 45000, change: -120, lastUpdate: new Date(), decimals: 2, category: 'indices' },
  IXIC: { price: 19500, change: -80, lastUpdate: new Date(), decimals: 2, category: 'indices' },
  VIX: { price: 18.5, change: 0.4, lastUpdate: new Date(), decimals: 2, category: 'indices' },
  US02Y: { price: 3.91, change: 0.01, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  US10Y: { price: 4.38, change: 0.02, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  US30Y: { price: 4.95, change: 0.01, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  DE10Y: { price: 3.05, change: 0.01, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  GB10Y: { price: 5.0, change: -0.02, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  JP10Y: { price: 2.26, change: 0.0, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  EU10Y: { price: 3.05, change: 0.01, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  AU10Y: { price: 5.07, change: -0.01, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  CA10Y: { price: 3.56, change: 0.01, lastUpdate: new Date(), decimals: 3, category: 'bonds' },
  IT10Y: { price: 3.96, change: 0.02, lastUpdate: new Date(), decimals: 3, category: 'bonds' }
};

export const useForexPrices = () => {
  const [prices, setPrices] = useState(fallbackPrices);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('fallback'); // 'API' or 'fallback'
  const [dataQuality, setDataQuality] = useState(null);
  /** @type {[Array<{id: string, label: string, category: string, decimals: number}> | null, function]} */
  const [instruments, setInstruments] = useState(null);

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
        dataQuality: data.dataQuality,
        instruments: data.instruments || null
      };
    } catch (error) {
      console.error('Failed to fetch forex prices:', error.message);
      return null;
    }
  };

  const fetchAllPrices = async (isInitialLoad = false) => {
    // Only show loading state on initial load, not on background refreshes
    if (isInitialLoad) {
      setLoading(true);
    }
    setError(null);
    
    try {
      // Check if we should use cached data (very short cache for live updates)
      const lastFetch = localStorage.getItem('lastForexFetch');
      const cacheTime = 3 * 1000; // 3 seconds - very short cache to allow frequent updates
      
      if (lastFetch && (Date.now() - parseInt(lastFetch)) < cacheTime) {
        const cachedData = localStorage.getItem('forexPrices');
        if (cachedData) {
          // Use cached data immediately for instant display
          const parsedData = JSON.parse(cachedData);
          setPrices(parsedData.prices || parsedData);
          setDataSource(parsedData.dataSource || 'API (cached)');
          setDataQuality(parsedData.dataQuality || null);
          setInstruments(parsedData.instruments || null);
          if (isInitialLoad) {
            setLoading(false);
          }
          // Continue to fetch fresh data in background even if cache is valid
        }
      }
      
      // Fetch fresh data from backend
      const apiData = await fetchForexPrices();
      
      if (apiData) {
        // Update prices with fresh data
        setPrices(apiData.prices);
        setDataSource(apiData.dataSource);
        setDataQuality(apiData.dataQuality);
        setInstruments(apiData.instruments || null);
        // Cache the data
        localStorage.setItem('forexPrices', JSON.stringify({
          prices: apiData.prices,
          dataSource: apiData.dataSource,
          dataQuality: apiData.dataQuality,
          instruments: apiData.instruments
        }));
        localStorage.setItem('lastForexFetch', Date.now().toString());
      } else {
        // Only show error if we don't have cached data
        const cachedData = localStorage.getItem('forexPrices');
        if (!cachedData) {
          setPrices(fallbackPrices);
          setDataSource('fallback');
          setDataQuality(null);
          setInstruments(null);
          setError('Using fallback data - API unavailable');
        }
      }
      
    } catch (error) {
      console.error('Error fetching forex prices:', error);
      // Only update error state if we don't have cached data
      const cachedData = localStorage.getItem('forexPrices');
      if (!cachedData) {
        setError('Failed to fetch live data');
        setDataSource('fallback');
        setDataQuality(null);
        setInstruments(null);
        setPrices(fallbackPrices);
      }
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    // Initial load with loading state
    fetchAllPrices(true);
    
    // Refresh prices every 5 seconds for live updates
    const interval = setInterval(() => {
      fetchAllPrices(false); // Background refresh without loading state
    }, 5 * 1000); // 5 seconds - frequent updates for live ticker
    
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
    instruments,
    clearCache
  };
}; 