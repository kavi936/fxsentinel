/**
 * Bundled market icons (Vite imports — hashed URLs in production, no 404s).
 */
import btcusdIcon from '../../assets/markets/btcusd.svg';
import goldIcon from '../../assets/markets/gold.svg';
import eurIcon from '../../assets/markets/eur.svg';
import usIcon from '../../assets/markets/us.svg';
import jpyIcon from '../../assets/markets/jpy.svg';

/** @type {Record<string, string>} market_id → resolved URL */
export const BUNDLED_MARKET_ICONS = {
  BTCUSD: btcusdIcon,
  GOLD: goldIcon,
};

/** @type {Record<string, string>} currency code → resolved URL */
export const BUNDLED_CURRENCY_ICONS = {
  EUR: eurIcon,
  USD: usIcon,
  JPY: jpyIcon,
  US: usIcon,
};

export function getBundledMarketIcon(marketId) {
  return BUNDLED_MARKET_ICONS[marketId] || null;
}

export function getBundledCurrencyIcon(code) {
  return BUNDLED_CURRENCY_ICONS[String(code || '').toUpperCase()] || null;
}
