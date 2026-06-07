import { useCallback, useEffect, useState } from 'react';
import { config } from '../config';

/**
 * Fetch Markets research payload (levels, verdict, headline, quote).
 */
export function useMarketResearch(marketId, { enabled = true, pollMs = 90_000 } = {}) {
  const [research, setResearch] = useState(null);
  const [loading, setLoading] = useState(Boolean(enabled && marketId));
  const [error, setError] = useState(null);

  const fetchResearch = useCallback(async (refreshOhlc = false) => {
    if (!marketId) return;
    try {
      const url = `${config.endpoints.marketResearch(marketId)}?refresh=${refreshOhlc ? 'true' : 'false'}`;
      const res = await fetch(url);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Research HTTP ${res.status}`);
      }
      const data = await res.json();
      setResearch(data);
      setError(null);
    } catch (e) {
      setError(e.message || 'Failed to load research');
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
    fetchResearch(true);

    if (!pollMs || pollMs <= 0) return undefined;
    const id = window.setInterval(() => fetchResearch(false), pollMs);
    return () => window.clearInterval(id);
  }, [enabled, marketId, pollMs, fetchResearch]);

  return { research, loading, error, refetch: fetchResearch };
}
