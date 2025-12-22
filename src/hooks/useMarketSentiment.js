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
  data_sources: ['Fallback'],
  is_market_closed: false,
  market_status: 'open'
};

export const useMarketSentiment = () => {
  const [sentiment, setSentiment] = useState(fallbackSentiment);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchSentiment = useCallback(async () => {
    try {
      setLoading(true);
      console.log('🔍 Fetching market sentiment from:', `${config.endpoints.marketSentiment}`);
      
      const response = await fetch(`${config.endpoints.marketSentiment}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ HTTP error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('📊 Market sentiment data received:', data);
      console.log('📊 Pairs sentiment:', data.pairs_sentiment);
      
      // Check if we received default/fallback values
      if (data.pairs_sentiment && data.pairs_sentiment.length > 0) {
        const firstPair = data.pairs_sentiment[0];
        const isAllDefaults = data.pairs_sentiment.every(p => 
          p.price_change === 0.0 && 
          p.rsi === 50.0 && 
          p.volatility === 10.0
        );
        if (isAllDefaults) {
          console.warn('⚠️ WARNING: All pairs have default values - TradingView API may have failed');
          console.warn('⚠️ This suggests the backend could not fetch real forex data');
        }
      }
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Verify pairs_sentiment exists and has data
      if (!data.pairs_sentiment || !Array.isArray(data.pairs_sentiment) || data.pairs_sentiment.length === 0) {
        console.warn('⚠️ No pairs_sentiment data in API response, using fallback');
        console.warn('⚠️ API response keys:', Object.keys(data));
        // Don't set error, just log warning - might be valid empty state
      } else {
        console.log(`✅ Received ${data.pairs_sentiment.length} pairs sentiment items`);
        // Log first pair for debugging
        if (data.pairs_sentiment[0]) {
          const firstPair = data.pairs_sentiment[0];
          console.log('📊 First pair sample:', {
            pair: firstPair.pair,
            sentiment: firstPair.sentiment,
            percentage: firstPair.percentage,
            price_change: firstPair.price_change,
            rsi: firstPair.rsi,
            volatility: firstPair.volatility
          });
          
          // Check if it's default values
          const isDefault = (firstPair.price_change === 0.0 && 
                           firstPair.rsi === 50.0 && 
                           firstPair.volatility === 10.0);
          if (isDefault) {
            console.warn('⚠️ WARNING: First pair has default values (0.0, 50.0, 10.0) - backend may be returning defaults');
          } else {
            console.log('✅ First pair has calculated values (not defaults)');
          }
        }
      }
      
      // Verify data structure before setting
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid data format received from API');
      }
      
      // Check if pairs_sentiment exists and is valid
      if (!data.pairs_sentiment || !Array.isArray(data.pairs_sentiment)) {
        console.warn('⚠️ API response missing pairs_sentiment array, checking structure:', Object.keys(data));
        // Try to continue with what we have, but log the issue
      }
      
      setSentiment(data);
      setLastUpdate(new Date());
      setError(null);
      setLoading(false);
      
      return data;
    } catch (error) {
      console.error('❌ Failed to fetch market sentiment:', error.message);
      console.error('❌ Error details:', error);
      console.error('❌ Error stack:', error.stack);
      
      // Check if it's a network error
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        setError('Network error: Could not connect to backend. Please check if the backend server is running.');
      } else {
        setError(`Failed to fetch: ${error.message}`);
      }
      setLoading(false);
      
      // Don't reset to fallback on error - keep existing data
      // This prevents clearing good data if there's a temporary network issue
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
