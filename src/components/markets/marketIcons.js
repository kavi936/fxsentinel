/**
 * Bundled market icons (Vite imports from src/assets/markets/).
 *
 * 1. Add e.g. src/assets/markets/btcusd.svg
 * 2. Uncomment the import below and add to BUNDLED_MARKET_ICONS
 *
 * Drop-in without imports: use iconPath in marketCatalog.js → public/markets/
 */

// import btcusdIcon from '../../assets/markets/btcusd.svg';
// import goldIcon from '../../assets/markets/gold.svg';
// import eurusdIcon from '../../assets/markets/eurusd.svg';
// import usdjpyIcon from '../../assets/markets/usdjpy.svg';

/** @type {Record<string, string>} market_id → resolved URL */
export const BUNDLED_MARKET_ICONS = {
  // BTCUSD: btcusdIcon,
  // GOLD: goldIcon,
  // EURUSD: eurusdIcon,
  // USDJPY: usdjpyIcon,
};

export function getBundledMarketIcon(marketId) {
  return BUNDLED_MARKET_ICONS[marketId] || null;
}
