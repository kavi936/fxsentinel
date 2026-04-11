/**
 * Parses user-entered market symbols to match backend INSTRUMENT_PATTERN:
 * BASE/QUOTE with alphanumeric segments (e.g. EUR/USD, XAU/USD, US500/USD, GER40/EUR).
 */
export function parseInstrumentSymbol(raw) {
  const s = (raw || '').trim().toUpperCase().replace(/\s+/g, '');
  if (/^[A-Z0-9]{2,12}\/[A-Z0-9]{2,12}$/.test(s)) return s;
  return null;
}
