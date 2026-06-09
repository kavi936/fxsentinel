/**
 * Chart timeframe options — label shown in toolbar, apiTf sent to GET /ohlc?tf=…
 */
export const MARKET_CHART_TIMEFRAMES = [
  { id: '15M', label: '15m', apiTf: '15M' },
  { id: '30M', label: '30m', apiTf: '30M' },
  { id: '1H', label: '1H', apiTf: '1H' },
  { id: '2H', label: '2H', apiTf: '2H' },
  { id: '4H', label: '4H', apiTf: '4H' },
  { id: '1D', label: '1D', apiTf: '1D' },
  { id: '1W', label: '1W', apiTf: '1W' },
];

/** Binance klines max per request — keep in sync with backend OHLC_MAX_BARS */
export const MARKET_OHLC_BAR_LIMIT = 1000;
