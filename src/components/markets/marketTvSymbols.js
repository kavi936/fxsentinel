/**
 * TradingView advanced-chart symbols per Markets tab id.
 * Aligns with backend/services/tradingview_instruments.py + BTCUSD.json symbol_map.
 */
export const MARKET_TV_SYMBOLS = {
  BTCUSD: 'BINANCE:BTCUSDT',
  GOLD: 'COMEX:GC1!',
  EURUSD: 'FX:EURUSD',
  USDJPY: 'FX:USDJPY',
};

export function getTradingViewSymbol(marketId) {
  return MARKET_TV_SYMBOLS[marketId] || null;
}
