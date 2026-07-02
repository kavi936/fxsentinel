/**
 * Per-currency logos served from public/markets/ — combined into FX pair chips.
 * Add a key here when you drop a new file (e.g. GBP.png in public/markets/).
 */
export const CURRENCY_ICON_PATHS = {
  EUR: '/markets/EUR.png',
  USD: '/markets/US.png',
  JPY: '/markets/JPY.png',
  DXY: '/markets/DXY.png',
};

/**
 * @param {string[] | undefined} legs e.g. ['EUR', 'USD'] for EUR/USD (base → quote)
 * @returns {string[] | null} resolved public URLs
 */
export function resolveCurrencyIconLegs(legs) {
  if (!Array.isArray(legs) || legs.length === 0) return null;
  const paths = legs.map((code) => CURRENCY_ICON_PATHS[String(code).toUpperCase()]).filter(Boolean);
  return paths.length === legs.length ? paths : null;
}
