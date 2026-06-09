import { ColorType, CrosshairMode } from 'lightweight-charts';

/** FXSentinel research chart palette — warm red-black, not flat #000. */
export const MARKET_CHART_THEME = {
  background: '#120809',
  surface: '#1a0f10',
  grid: 'rgba(255, 68, 68, 0.07)',
  border: 'rgba(255, 68, 68, 0.2)',
  text: 'rgba(255, 255, 255, 0.58)',
  accent: '#ff4444',
  crosshair: 'rgba(255, 68, 68, 0.52)',
  crosshairLabel: '#1a0f10',
};

/** FXSentinel dark research chart — branded grid, no drawing tools. */
export function createChartOptions(width, height) {
  return {
    width,
    height,
    layout: {
      background: { type: ColorType.Solid, color: MARKET_CHART_THEME.background },
      textColor: MARKET_CHART_THEME.text,
      fontFamily: "'Sen', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    },
    grid: {
      vertLines: { color: MARKET_CHART_THEME.grid },
      horzLines: { color: MARKET_CHART_THEME.grid },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: {
        color: MARKET_CHART_THEME.crosshair,
        labelBackgroundColor: MARKET_CHART_THEME.crosshairLabel,
      },
      horzLine: {
        color: MARKET_CHART_THEME.crosshair,
        labelBackgroundColor: MARKET_CHART_THEME.crosshairLabel,
      },
    },
    rightPriceScale: {
      borderColor: MARKET_CHART_THEME.border,
      scaleMargins: { top: 0.08, bottom: 0.12 },
    },
    timeScale: {
      borderColor: MARKET_CHART_THEME.border,
      timeVisible: true,
      secondsVisible: false,
    },
    handleScroll: { vertTouchDrag: false },
  };
}

export const CANDLE_SERIES_OPTIONS = {
  upColor: '#3d9a76',
  downColor: '#e05555',
  borderVisible: false,
  wickUpColor: '#3d9a76',
  wickDownColor: '#e05555',
};
