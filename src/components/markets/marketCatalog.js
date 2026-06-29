/**
 * Markets tab instrument list — order is display order in the horizontal picker.
 *
 * Icons (pick one per market):
 * - Bundled SVG import → marketIcons.js (preferred in production)
 * - `iconLegs`: FX pair from currency SVGs e.g. ['EUR', 'USD']
 * - `icon`: built-in SVG fallback if bundled assets missing
 */
export const MARKET_CATALOG = [
  {
    id: 'BTCUSD',
    label: 'BTC/USD',
    shortLabel: 'BTC',
    enabled: true,
    icon: 'btc',
    quoteInstrumentId: 'BTCUSDT',
  },
  {
    id: 'GOLD',
    label: 'XAUUSD',
    shortLabel: 'XAU',
    enabled: false,
    icon: 'gold',
    quoteInstrumentId: 'GOLD',
  },
  {
    id: 'EURUSD',
    label: 'EUR/USD',
    shortLabel: 'EUR',
    enabled: false,
    icon: 'eurusd',
    iconPath: null,
    iconLegs: ['EUR', 'USD'],
    quoteInstrumentId: 'EURUSD',
  },
  {
    id: 'USDJPY',
    label: 'USD/JPY',
    shortLabel: 'JPY',
    enabled: false,
    icon: 'usdjpy',
    iconPath: null,
    iconLegs: ['USD', 'JPY'],
    quoteInstrumentId: 'USDJPY',
  },
];

/** Resolve live quote row from useForexPrices (same ids as Overview ticker). */
export function getMarketQuote(market, prices, instruments) {
  const quoteId = market?.quoteInstrumentId;
  if (!quoteId) return null;
  const row = prices?.[quoteId];
  if (!row) return null;
  const inst = instruments?.find((i) => i.id === quoteId);
  return {
    price: row.price,
    change: row.change,
    changePercent: row.changePercent,
    decimals: row.decimals ?? inst?.decimals ?? 4,
  };
}

export function getMarketById(id) {
  return MARKET_CATALOG.find((m) => m.id === id);
}
