import { useEffect, useState } from 'react';
import { config } from '../config';
import { filterBtcMarketNews } from '../components/markets/marketNewsFilter';

/**
 * Market-filtered news strip for Markets tab (minimal fetch, no full LiveNewsFeed UI).
 */
export function useMarketNews({ enabled = true, marketId = 'BTCUSD', maxItems = 5 } = {}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!enabled || marketId !== 'BTCUSD') {
      setItems([]);
      setLoading(false);
      return undefined;
    }

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);
        const res = await fetch(config.endpoints.news, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (!res.ok) throw new Error(`News ${res.status}`);
        const data = await res.json();
        if (cancelled) return;
        const filtered = filterBtcMarketNews(data.news, maxItems);
        setItems(filtered);
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load news');
          setItems([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [enabled, marketId, maxItems]);

  return { items, loading, error };
}
