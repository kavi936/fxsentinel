/**
 * Parses user-entered market symbols to match backend INSTRUMENT_PATTERN:
 * BASE/QUOTE with alphanumeric segments (e.g. EUR/USD, XAU/USD, US500/USD, GER40/EUR).
 */
export function parseInstrumentSymbol(raw) {
  const s = (raw || '').trim().toUpperCase().replace(/\s+/g, '');
  if (/^[A-Z0-9]{2,12}\/[A-Z0-9]{2,12}$/.test(s)) return s;
  return null;
}

/**
 * Whether a BASE/QUOTE symbol matches a free-text filter (substring; slash- and space-insensitive).
 * Lets users find "EUR/USD" by typing eurusd, EUR USD, or JPY for any *JPY* pair.
 */
export function instrumentSymbolMatchesSearch(pair, rawQuery) {
  const trimmed = (rawQuery || '').trim();
  if (!trimmed) return true;
  const upperPair = pair.toUpperCase();
  const qUpper = trimmed.toUpperCase();
  if (upperPair.includes(qUpper)) return true;
  const compactPair = upperPair.replace(/\//g, '');
  const compactQ = qUpper.replace(/[\s/]/g, '');
  if (!compactQ) return true;
  return compactPair.includes(compactQ);
}

export function filterInstrumentsBySearch(pairs, rawQuery) {
  return pairs.filter((p) => instrumentSymbolMatchesSearch(p, rawQuery));
}
