import { useCallback, useEffect, useState } from 'react';
import { config } from '../config';

/**
 * Live spot quote for a Markets instrument — Binance BTCUSDT for BTCUSD.
 * Poll frequently; same venue as chart OHLC.
 */
export function useMarketQuote(marketId, { enabled = true, pollMs = 5_000 } = {}) {
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(Boolean(enabled && marketId));
  const [error, setError] = useState(null);

  const fetchQuote = useCallback(async () => {
    if (!marketId) return;
    try {
      const res = await fetch(config.endpoints.marketQuote(marketId));
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || body.detail || `Quote HTTP ${res.status}`);
      }
      const data = await res.json();
      setQuote(data);
      setError(null);
    } catch (e) {
      setError(e.message || 'Failed to load live quote');
    } finally {
      setLoading(false);
    }
  }, [marketId]);

  useEffect(() => {
    if (!enabled || !marketId) {
      setLoading(false);
      return undefined;
    }

    setLoading(true);
    fetchQuote();

    if (!pollMs || pollMs <= 0) return undefined;
    const id = window.setInterval(fetchQuote, pollMs);
    return () => window.clearInterval(id);
  }, [enabled, marketId, pollMs, fetchQuote]);

  return { quote, loading, error, refetch: fetchQuote };
}
