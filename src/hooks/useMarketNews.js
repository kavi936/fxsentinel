import { useCallback, useEffect, useRef, useState } from 'react';
import { config } from '../config';
import { filterMarketNews, getMarketNewsConfig } from '../components/markets/marketNewsFilter';
import { sanitizeNewsItem } from '../utils/sanitize';

const POLL_MS = 2 * 60 * 1000;

/**
 * Market-filtered live news for Markets tab — compact fetch, Overview-compatible fields.
 */
export function useMarketNews({ enabled = true, marketId = 'BTCUSD', maxItems = 6 } = {}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastFetchedAt, setLastFetchedAt] = useState(null);
  const forceRefreshRef = useRef(false);

  const newsConfig = getMarketNewsConfig(marketId);
  const isEnabled = enabled && Boolean(newsConfig?.enabled);

  const fetchNews = useCallback(async (forceRefresh = false) => {
    if (!isEnabled) {
      setItems([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    if (forceRefresh) forceRefreshRef.current = true;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000);
      const url = forceRefresh
        ? `${config.endpoints.news}?force_refresh=true&wait_fresh=true`
        : config.endpoints.news;
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!res.ok) throw new Error(`News ${res.status}`);

      const data = await res.json();
      const sanitized = (data.news || [])
        .map((item) => sanitizeNewsItem({ ...item, id: String(item.id ?? item.url ?? item.title) }))
        .filter(Boolean);
      const filtered = filterMarketNews(sanitized, marketId, maxItems);

      setItems(filtered);
      setError(null);
      setLastFetchedAt(Date.now());
    } catch (err) {
      setError(err.message || 'Failed to load news');
    } finally {
      setLoading(false);
      forceRefreshRef.current = false;
    }
  }, [isEnabled, marketId, maxItems]);

  useEffect(() => {
    if (!isEnabled) {
      setItems([]);
      setLoading(false);
      setError(null);
      return undefined;
    }

    fetchNews();

    const intervalId = setInterval(() => fetchNews(), POLL_MS);

    const onVisibility = () => {
      if (document.visibilityState === 'visible') fetchNews();
    };
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      clearInterval(intervalId);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [fetchNews, isEnabled]);

  const refresh = useCallback(() => fetchNews(true), [fetchNews]);

  return {
    items,
    loading,
    error,
    refresh,
    lastFetchedAt,
    isEnabled,
    marketLabel: newsConfig?.label || marketId,
  };
}
