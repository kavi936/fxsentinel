/**
 * Markets tab instrument list — order is display order in the horizontal picker.
 *
 * Icons (pick one per market):
 * - `iconPath`: single logo served from public/markets/ e.g. '/markets/bitcoin.png'
 * - `iconLegs`: FX pair from currency logos e.g. ['EUR', 'USD'] → marketCurrencyAssets.js
 * - `icon`: built-in inline SVG fallback if the file 404s
 */
export const MARKET_CATALOG = [
  {
    id: 'BTCUSD',
    label: 'BTC/USD',
    shortLabel: 'BTC',
    enabled: true,
    icon: 'btc',
    iconPath: '/markets/bitcoin.png',
    quoteInstrumentId: 'BTCUSDT',
  },
  {
    id: 'GOLD',
    label: 'XAUUSD',
    shortLabel: 'XAU',
    enabled: false,
    icon: 'gold',
    iconPath: '/markets/gold.png',
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
