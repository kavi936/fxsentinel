/** Keywords aligned with backend/services/market_research_profiles/BTCUSD.json */
const BTC_NEWS_KEYWORDS = [
  'bitcoin',
  'btc',
  'crypto',
  'cryptocurrency',
  'ethereum',
  'etf',
  'sec',
  'binance',
  'regulation',
];

export function isBtcMarketNews(item) {
  const text = `${item?.title || ''} ${item?.summary || ''}`.toLowerCase();
  return BTC_NEWS_KEYWORDS.some((kw) => text.includes(kw));
}

export function filterBtcMarketNews(items, maxItems = 5) {
  if (!Array.isArray(items)) return [];
  return items.filter(isBtcMarketNews).slice(0, maxItems);
}
