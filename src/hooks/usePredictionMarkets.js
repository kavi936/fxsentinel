import { useState, useEffect, useCallback } from 'react';
import { config } from '../config.js';

const fallbackMarkets = {
  markets: [],
  summary: {
    total_markets: 0,
    platforms: [],
    last_updated: null
  }
};

export const usePredictionMarkets = () => {
  const [markets, setMarkets] = useState(fallbackMarkets);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchMarkets = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const url = forceRefresh 
        ? `${config.endpoints.predictionMarkets}?refresh=true`
        : config.endpoints.predictionMarkets;
      
      console.log('🔍 Fetching prediction markets from:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success' && data.data) {
        setMarkets(data.data);
        setLastUpdate(new Date());
        console.log('✅ Prediction markets data received:', data.data.summary);
      } else {
        throw new Error(data.error || 'Failed to fetch prediction markets');
      }
      
    } catch (err) {
      console.error('❌ Error fetching prediction markets:', err);
      setError(err.message);
      // Use functional update to avoid stale closure
      setMarkets(prevMarkets => {
        // Keep existing data on error (don't clear on transient errors)
        if (!prevMarkets.markets || prevMarkets.markets.length === 0) {
          return fallbackMarkets;
        }
        return prevMarkets;
      });
    } finally {
      setLoading(false);
    }
  }, []); // Empty deps is fine now since we use functional updates

  useEffect(() => {
    fetchMarkets();
  }, [fetchMarkets]);

  return {
    markets: markets.markets || [],
    summary: markets.summary || {},
    loading,
    error,
    lastUpdate,
    refresh: () => fetchMarkets(true)
  };
};

