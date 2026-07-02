/**
 * Optional bundled market icons (Vite imports from src/assets/markets/).
 *
 * Market logos are served as real files from `public/markets/` (see marketCatalog.js
 * `iconPath` and marketCurrencyAssets.js). These stubs return null so those public
 * paths win; add a bundled import here only if you want a hashed-asset override.
 */

/** @type {Record<string, string>} market_id → resolved URL */
export const BUNDLED_MARKET_ICONS = {};

/** @type {Record<string, string>} currency code → resolved URL */
export const BUNDLED_CURRENCY_ICONS = {};

export function getBundledMarketIcon(marketId) {
  return BUNDLED_MARKET_ICONS[marketId] || null;
}

export function getBundledCurrencyIcon(code) {
  return BUNDLED_CURRENCY_ICONS[String(code || '').toUpperCase()] || null;
}
