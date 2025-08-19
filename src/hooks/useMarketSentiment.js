import { useState, useEffect, useCallback } from 'react';
import { config } from '../config.js';

const fallbackSentiment = {
  timestamp: new Date().toISOString(),
  trading_day: new Date().toISOString().split('T')[0],
  market_conditions: [
    {
      name: 'Volatility Environment',
      value: 'medium',
      percentage: 50,
      detail: 'VIX: 15.0 (+0.0)',
      trend: 'stable'
    },
    {
      name: 'Risk Appetite',
      value: 'medium',
      percentage: 50,
      detail: 'Safe Havens: JPY, CHF',
      trend: 'stable'
    },
    {
      name: 'Market Correlation',
      value: 'medium',
      percentage: 50,
      detail: 'Pairs moving independently',
      trend: 'stable'
    }
  ],
  pairs_sentiment: [
    {
      pair: 'EURUSD',
      sentiment: 'neutral',
      percentage: 50,
      price_change: 0.0,
      rsi: 50.0,
      volatility: 10.0
    },
    {
      pair: 'GBPUSD',
      sentiment: 'neutral',
      percentage: 50,
      price_change: 0.0,
      rsi: 50.0,
      volatility: 10.0
    },
    {
      pair: 'USDJPY',
      sentiment: 'neutral',
      percentage: 50,
      price_change: 0.0,
      rsi: 50.0,
      volatility: 10.0
    },
    {
      pair: 'USDCHF',
      sentiment: 'neutral',
      percentage: 50,
      price_change: 0.0,
      rsi: 50.0,
      volatility: 10.0
    }
  ],
  market_drivers: [],
  market_outlook: 'Market sentiment analysis is currently updating. Please check back shortly.',
  confidence_score: 0.5,
  data_sources: ['Fallback']
};

export const useMarketSentiment = () => {
  const [sentiment, setSentiment] = useState(fallbackSentiment);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchSentiment = useCallback(async () => {
    try {
      console.log('🔍 Fetching market sentiment from:', `${config.endpoints.marketSentiment}`);
      
      const response = await fetch(`${config.endpoints.marketSentiment}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📊 Market sentiment data received:', data);
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setSentiment(data);
      setLastUpdate(new Date());
      setError(null);
      
      return data;
    } catch (error) {
      console.error('Failed to fetch market sentiment:', error.message);
      setError(error.message);
      return null;
    }
  }, []);

  const refreshSentiment = useCallback(async () => {
    try {
      setLoading(true);
      console.log('🔄 Manually refreshing market sentiment...');
      
      const response = await fetch(`${config.endpoints.sentimentRefresh}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('✅ Sentiment refresh result:', result);
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      // Fetch fresh data after refresh
      await fetchSentiment();
      
    } catch (error) {
      console.error('Failed to refresh sentiment:', error.message);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [fetchSentiment]);

  // Initial fetch
  useEffect(() => {
    fetchSentiment().finally(() => setLoading(false));
  }, [fetchSentiment]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      console.log('🔄 Auto-refreshing market sentiment...');
      fetchSentiment();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [fetchSentiment]);

  // Helper functions for frontend
  const getConditionValue = (conditionName) => {
    const condition = sentiment.market_conditions.find(c => c.name === conditionName);
    return condition ? condition.value : 'medium';
  };

  const getConditionPercentage = (conditionName) => {
    const condition = sentiment.market_conditions.find(c => c.name === conditionName);
    return condition ? condition.percentage : 50;
  };

  const getPairSentiment = (pair) => {
    return sentiment.pairs_sentiment.find(p => p.pair === pair) || null;
  };

  const getSentimentColor = (sentimentType) => {
    switch (sentimentType) {
      case 'bullish':
      case 'positive':
      case 'high':
        return '#00ff88';
      case 'bearish':
      case 'negative':
      case 'low':
        return '#ff4757';
      case 'neutral':
      case 'medium':
      default:
        return '#ffa500';
    }
  };

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown';
    
    const now = new Date();
    const updateTime = new Date(timestamp);
    const diffMs = now - updateTime;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return {
    sentiment,
    loading,
    error,
    lastUpdate,
    fetchSentiment,
    refreshSentiment,
    getConditionValue,
    getConditionPercentage,
    getPairSentiment,
    getSentimentColor,
    formatTimeAgo
  };
};
