import React, { useEffect, useRef, useState } from 'react';
import { CandlestickSeries, createChart } from 'lightweight-charts';
import { useMarketOhlc } from '../../hooks/useMarketOhlc';
import { applyStructuredLevels, clearPriceLines } from './marketChartOverlays';
import { CANDLE_SERIES_OPTIONS, createChartOptions } from './marketChartTheme';
import './MarketsChart.css';

const TIMEFRAMES = [
  { id: '1H', label: '1H', apiTf: '1H', resolution: '60' },
  { id: '4H', label: '4H', apiTf: '4H', resolution: '240' },
  { id: '1D', label: '1D', apiTf: '1D', resolution: 'D' },
];

function formatSourceFooter(meta) {
  if (!meta) return 'Loading OHLC…';
  const src = meta.source === 'binance' ? 'Binance' : meta.source || 'FXSentinel';
  const asOf = meta.as_of
    ? new Date(meta.as_of).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    : '—';
  return `${src} · ${meta.timeframe || '4H'} · updated ${asOf}`;
}

/**
 * FXSentinel research chart — our OHLC + system level overlays (read-only).
 */
function MarketChart({ marketId = 'BTCUSD', structuredLevels = [], showLevels = true }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const priceLinesRef = useRef([]);
  const prevBarsLenRef = useRef(0);

  const [timeframe, setTimeframe] = useState('4H');
  const tfConfig = TIMEFRAMES.find((t) => t.id === timeframe) || TIMEFRAMES[1];

  const { bars, meta, loading, error } = useMarketOhlc(marketId, tfConfig.apiTf, {
    enabled: Boolean(marketId),
    pollMs: 45_000,
    limit: 200,
  });

  /* Chart lifecycle */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const chart = createChart(el, createChartOptions(el.clientWidth, el.clientHeight || 320));
    const series = chart.addSeries(CandlestickSeries, CANDLE_SERIES_OPTIONS);

    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver(() => {
      const { clientWidth, clientHeight } = el;
      if (clientWidth > 0 && clientHeight > 0) {
        chart.applyOptions({ width: clientWidth, height: clientHeight });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      clearPriceLines(series, priceLinesRef.current);
      priceLinesRef.current = [];
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  /* Candles — setData on length change, update last bar on poll */
  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !bars.length) return;

    const candleData = bars.map((b) => ({
      time: b.time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));

    if (bars.length !== prevBarsLenRef.current) {
      series.setData(candleData);
      prevBarsLenRef.current = bars.length;
      chart.timeScale().fitContent();
    } else {
      const last = candleData[candleData.length - 1];
      series.update(last);
    }
  }, [bars]);

  /* System overlays */
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    clearPriceLines(series, priceLinesRef.current);
    priceLinesRef.current = [];

    if (showLevels && structuredLevels?.length) {
      priceLinesRef.current = applyStructuredLevels(series, structuredLevels);
    }
  }, [structuredLevels, showLevels, bars.length]);

  return (
    <div className="markets-research-chart" aria-label={`${marketId} research chart`}>
      <div className="markets-research-chart__toolbar" role="toolbar" aria-label="Chart timeframe">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf.id}
            type="button"
            className={timeframe === tf.id ? 'is-active' : ''}
            onClick={() => {
              setTimeframe(tf.id);
              prevBarsLenRef.current = 0;
            }}
          >
            {tf.label}
          </button>
        ))}
      </div>

      <div className="markets-research-chart__pane">
        {loading && !bars.length && (
          <div className="markets-research-chart__status">Loading chart data…</div>
        )}
        {error && !bars.length && (
          <div className="markets-research-chart__status markets-research-chart__status--error">
            {error}
          </div>
        )}
        <div ref={containerRef} className="markets-research-chart__canvas" />
      </div>

      <footer className="markets-research-chart__footer">
        <span>{formatSourceFooter(meta)}</span>
        {showLevels && structuredLevels?.length > 0 && (
          <span className="markets-research-chart__footer-levels">
            {structuredLevels.length} system levels
          </span>
        )}
      </footer>
    </div>
  );
}

export default MarketChart;
