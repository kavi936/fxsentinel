import { ColorType, CrosshairMode } from 'lightweight-charts';

/** FXSentinel dark research chart — TV-like grid, no drawing tools. */
export function createChartOptions(width, height) {
  return {
    width,
    height,
    layout: {
      background: { type: ColorType.Solid, color: '#000000' },
      textColor: 'rgba(255, 255, 255, 0.55)',
      fontFamily: "'Sen', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    },
    grid: {
      vertLines: { color: 'rgba(255, 255, 255, 0.06)' },
      horzLines: { color: 'rgba(255, 255, 255, 0.06)' },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: { color: 'rgba(255, 68, 68, 0.45)', labelBackgroundColor: '#1a1a1a' },
      horzLine: { color: 'rgba(255, 68, 68, 0.45)', labelBackgroundColor: '#1a1a1a' },
    },
    rightPriceScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
      scaleMargins: { top: 0.08, bottom: 0.12 },
    },
    timeScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
      timeVisible: true,
      secondsVisible: false,
    },
    handleScroll: { vertTouchDrag: false },
  };
}

export const CANDLE_SERIES_OPTIONS = {
  upColor: '#3d9a76',
  downColor: '#c75c5c',
  borderVisible: false,
  wickUpColor: '#3d9a76',
  wickDownColor: '#c75c5c',
};
