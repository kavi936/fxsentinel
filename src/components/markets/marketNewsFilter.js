/** Keywords aligned with backend market profile news_filter (BTCUSD). */
export const MARKET_NEWS_CONFIG = {
  BTCUSD: {
    label: 'BTC / Crypto',
    keywords: [
      'bitcoin',
      'btc',
      'crypto',
      'cryptocurrency',
      'ethereum',
      'etf',
      'sec',
      'binance',
      'regulation',
    ],
    enabled: true,
  },
};

export function getMarketNewsConfig(marketId) {
  return MARKET_NEWS_CONFIG[(marketId || '').toUpperCase()] || null;
}

export function isMarketNewsItem(item, keywords) {
  if (!keywords?.length) return false;
  const text = `${item?.title || ''} ${item?.summary || ''}`.toLowerCase();
  return keywords.some((kw) => text.includes(kw));
}

export function normalizeMarketNewsItem(item) {
  if (!item || typeof item !== 'object') return null;
  const title = item.title || '';
  if (!title.trim()) return null;

  return {
    id: item.id || item.url || item.link || title,
    title,
    summary: item.summary || '',
    source: item.source || item.publisher || '',
    published_at: item.published_at || item.date || item.timestamp || null,
    added_to_feed_at: item.added_to_feed_at || null,
    url: item.url || item.link || null,
    impact: item.impact || item.impact_level || item.analysis_summary?.impact || null,
  };
}

export function filterMarketNews(items, marketId, maxItems = 6) {
  const config = getMarketNewsConfig(marketId);
  if (!config?.enabled || !Array.isArray(items)) return [];

  const out = [];
  for (const raw of items) {
    if (!isMarketNewsItem(raw, config.keywords)) continue;
    const normalized = normalizeMarketNewsItem(raw);
    if (normalized) out.push(normalized);
    if (out.length >= maxItems) break;
  }
  return out;
}

/** Prefer live fetch; fill gaps from research snapshot without duplicates. */
export function mergeMarketNews(liveItems = [], fallbackItems = [], maxItems = 6) {
  const seen = new Set();
  const merged = [];

  for (const raw of [...liveItems, ...fallbackItems]) {
    const item = normalizeMarketNewsItem(raw);
    if (!item) continue;
    const key = String(item.id || item.url || item.title).toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    merged.push(item);
    if (merged.length >= maxItems) break;
  }

  return merged;
}

/** @deprecated use filterMarketNews */
export function isBtcMarketNews(item) {
  return isMarketNewsItem(item, MARKET_NEWS_CONFIG.BTCUSD.keywords);
}

/** @deprecated use filterMarketNews */
export function filterBtcMarketNews(items, maxItems = 5) {
  return filterMarketNews(items, 'BTCUSD', maxItems);
}
