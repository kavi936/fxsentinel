import { getBundledCurrencyIcon } from './marketIcons';

/**
 * Per-currency icons bundled via Vite — combined into FX pair chips.
 */

/**
 * @param {string[] | undefined} legs e.g. ['EUR', 'USD'] for EUR/USD (base → quote)
 * @returns {string[] | null} resolved bundled URLs
 */
export function resolveCurrencyIconLegs(legs) {
  if (!Array.isArray(legs) || legs.length === 0) return null;
  const paths = legs
    .map((code) => getBundledCurrencyIcon(code))
    .filter(Boolean);
  return paths.length === legs.length ? paths : null;
}
