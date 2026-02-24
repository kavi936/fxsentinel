import { useState, useEffect, useCallback, useRef } from 'react';
import { config } from '../config.js';

const fallbackMarkets = {
  markets: [],
  summary: {
    total_markets: 0,
    platforms: [],
    last_updated: null
  }
};

const AUTO_REFRESH_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes

export const usePredictionMarkets = (options = {}) => {
  const { onDataRefresh } = options;
  const onDataRefreshRef = useRef(onDataRefresh);
  onDataRefreshRef.current = onDataRefresh;

  const [markets, setMarkets] = useState(fallbackMarkets);
  const [loading, setLoading] = useState(true);
  const [backgroundRefreshing, setBackgroundRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchMarkets = useCallback(async (forceRefresh = false, { background = false } = {}) => {
    try {
      if (background) {
        setBackgroundRefreshing(true);
      } else {
        setLoading(true);
      }
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
        onDataRefreshRef.current?.();
      } else {
        throw new Error(data.error || 'Failed to fetch prediction markets');
      }
    } catch (err) {
      console.error('❌ Error fetching prediction markets:', err);
      setError(err.message);
      setMarkets(prevMarkets => {
        if (!prevMarkets.markets || prevMarkets.markets.length === 0) {
          return fallbackMarkets;
        }
        return prevMarkets;
      });
    } finally {
      setLoading(false);
      setBackgroundRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchMarkets();
  }, [fetchMarkets]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchMarkets(true, { background: true });
    }, AUTO_REFRESH_INTERVAL_MS);
    return () => clearInterval(intervalId);
  }, [fetchMarkets]);

  return {
    markets: markets.markets || [],
    summary: markets.summary || {},
    loading,
    backgroundRefreshing,
    error,
    lastUpdate,
    refresh: () => fetchMarkets(true)
  };
};

