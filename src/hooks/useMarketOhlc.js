import { useCallback, useEffect, useRef, useState } from 'react';
import { config } from '../config';

/**
 * OHLC bars for Markets research chart — polls for live bar updates.
 */
export function useMarketOhlc(marketId, timeframe = '4H', { enabled = true, pollMs = 45_000, limit = 1000 } = {}) {
  const [bars, setBars] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(Boolean(enabled && marketId));
  const [error, setError] = useState(null);
  const lastFingerprint = useRef('');

  const fetchOhlc = useCallback(async () => {
    if (!marketId) return;
    try {
      const url = config.endpoints.marketOhlc(marketId, timeframe, limit);
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`OHLC HTTP ${res.status}`);
      }
      const data = await res.json();
      const nextBars = data.bars || [];
      const fp = `${nextBars.length}:${nextBars[nextBars.length - 1]?.time}:${nextBars[nextBars.length - 1]?.close}`;
      if (fp !== lastFingerprint.current) {
        lastFingerprint.current = fp;
        setBars(nextBars);
      }
      setMeta({
        as_of: data.as_of,
        source: data.source,
        timeframe: data.timeframe,
      });
      setError(null);
    } catch (e) {
      setError(e.message || 'Failed to load OHLC');
    } finally {
      setLoading(false);
    }
  }, [marketId, timeframe, limit]);

  useEffect(() => {
    if (!enabled || !marketId) {
      setLoading(false);
      return undefined;
    }

    setLoading(true);
    lastFingerprint.current = '';
    fetchOhlc();

    if (!pollMs || pollMs <= 0) return undefined;
    const id = window.setInterval(fetchOhlc, pollMs);
    return () => window.clearInterval(id);
  }, [enabled, marketId, timeframe, pollMs, limit, fetchOhlc]);

  return { bars, meta, loading, error, refetch: fetchOhlc };
}
