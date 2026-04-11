/**
 * Preset instruments for onboarding and profile: FX, commodities, indices, crypto.
 * FXSentinel is focused on macro and these markets — not individual stocks.
 * Format: BASE/QUOTE (e.g. EUR/USD, US500/USD). Custom entries must match backend validation.
 */
export const PRESET_MARKET_INSTRUMENTS = [
  // FX — majors
  'EUR/USD',
  'GBP/USD',
  'USD/JPY',
  'USD/CHF',
  'AUD/USD',
  'USD/CAD',
  'NZD/USD',
  // FX — common crosses
  'EUR/GBP',
  'EUR/JPY',
  'EUR/AUD',
  'EUR/NZD',
  'EUR/CAD',
  'EUR/CHF',
  'GBP/JPY',
  'GBP/AUD',
  'GBP/NZD',
  'AUD/JPY',
  'AUD/NZD',
  'AUD/CAD',
  'NZD/JPY',
  'CAD/JPY',
  'CHF/JPY',
  'USD/MXN',
  'USD/ZAR',
  // Commodities
  'XAU/USD',
  'XAG/USD',
  'XPT/USD',
  'XPD/USD',
  'WTI/USD',
  'BRENT/USD',
  'NATGAS/USD',
  // Indices (CFD-style BASE/QUOTE)
  'US30/USD',
  'US500/USD',
  'US100/USD',
  'UK100/GBP',
  'GER40/EUR',
  'FRA40/EUR',
  'EU50/EUR',
  'JP225/JPY',
  'AUS200/AUD',
  'HK50/HKD',
  'VIX/USD',
  // Crypto
  'BTC/USD',
  'ETH/USD',
];

/** @deprecated Use PRESET_MARKET_INSTRUMENTS — name kept for older imports */
export const COMMON_FOREX_PAIRS = PRESET_MARKET_INSTRUMENTS;
