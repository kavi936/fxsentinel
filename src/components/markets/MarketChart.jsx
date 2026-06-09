import React, { useEffect, useMemo, useRef, useState } from 'react';
import { CandlestickSeries, createChart } from 'lightweight-charts';
import { useMarketOhlc } from '../../hooks/useMarketOhlc';
import { applyStructuredLevels, clearPriceLines, filterLevelsByLayer } from './marketChartOverlays';
import { applyRangeBands, removeRangeBands, updateRangeBands } from './marketChartRangeBands';
import { MARKET_CHART_TIMEFRAMES, MARKET_OHLC_BAR_LIMIT } from './marketChartTimeframes';
import { CANDLE_SERIES_OPTIONS, createChartOptions } from './marketChartTheme';
import MarketChartToolbar from './MarketChartToolbar';
import {
  formatTickerPercent,
  formatTickerPrice,
  isTickerChangePositive,
} from '../../utils/tickerFormat';
import './MarketsChart.css';

const TIMEFRAMES = MARKET_CHART_TIMEFRAMES;

function formatSourceFooter(meta) {
  if (!meta) return 'Loading OHLC…';
  const src = meta.source === 'binance' ? 'Binance' : meta.source || 'FXSentinel';
  const asOf = meta.as_of
    ? new Date(meta.as_of).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    : '—';
  return `${src} · ${meta.timeframe || '4H'} · updated ${asOf}`;
}

function toCandleData(bars) {
  return bars.map((b) => ({
    time: b.time,
    open: b.open,
    high: b.high,
    low: b.low,
    close: b.close,
  }));
}

/**
 * FXSentinel research chart — our OHLC + system level overlays (read-only).
 */
const LAYER_TOGGLES = [
  { id: 'levels', label: 'Levels' },
  { id: 'poi', label: 'POI' },
  { id: 'ranges', label: 'Ranges' },
];

function MarketChart({
  marketId = 'BTCUSD',
  structuredLevels = [],
  liveQuote = null,
  quoteLoading = false,
}) {
  const containerRef = useRef(null);
  const paneRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const bandSeriesRef = useRef([]);
  const priceLinesRef = useRef([]);
  const prevBarsLenRef = useRef(0);
  const prevOverlayKeyRef = useRef('');

  const [timeframe, setTimeframe] = useState('4H');
  const [layers, setLayers] = useState({ levels: true, poi: true, ranges: true });
  const tfConfig = TIMEFRAMES.find((t) => t.id === timeframe) || TIMEFRAMES[1];

  const visibleLevels = useMemo(
    () => filterLevelsByLayer(structuredLevels, layers),
    [structuredLevels, layers]
  );

  const overlayKey = useMemo(
    () =>
      [
        layers.levels,
        layers.poi,
        layers.ranges,
        structuredLevels.map((l) => l.level_id).join(','),
      ].join(';'),
    [layers, structuredLevels]
  );

  const rangeLevels = useMemo(
    () => visibleLevels.filter((l) => l.kind === 'range'),
    [visibleLevels]
  );

  const { bars, meta, loading, error } = useMarketOhlc(marketId, tfConfig.apiTf, {
    enabled: Boolean(marketId),
    pollMs: 30_000,
    limit: MARKET_OHLC_BAR_LIMIT,
  });

  const liveTone = liveQuote ? (isTickerChangePositive(liveQuote.change, liveQuote.changePercent) ? 'up' : 'down') : '';
  const quoteLabel = liveQuote?.instrument_id || liveQuote?.symbol || '—';

  /* Chart shell */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const chart = createChart(el, createChartOptions(el.clientWidth, el.clientHeight || 320));
    chartRef.current = chart;

    const ro = new ResizeObserver(() => {
      const { clientWidth, clientHeight } = el;
      if (clientWidth > 0 && clientHeight > 0) {
        chart.applyOptions({ width: clientWidth, height: clientHeight });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      removeRangeBands(chart, bandSeriesRef.current);
      bandSeriesRef.current = [];
      if (seriesRef.current) {
        clearPriceLines(seriesRef.current, priceLinesRef.current);
        priceLinesRef.current = [];
        try {
          chart.removeSeries(seriesRef.current);
        } catch {
          /* ignore */
        }
        seriesRef.current = null;
      }
      chart.remove();
      chartRef.current = null;
      prevBarsLenRef.current = 0;
      prevOverlayKeyRef.current = '';
    };
  }, []);

  /* Candles, range fills, and price lines */
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !bars.length) return;

    const candleData = toCandleData(bars);
    const fullRebuild =
      bars.length !== prevBarsLenRef.current || overlayKey !== prevOverlayKeyRef.current;

    if (fullRebuild) {
      if (seriesRef.current) {
        clearPriceLines(seriesRef.current, priceLinesRef.current);
        priceLinesRef.current = [];
        chart.removeSeries(seriesRef.current);
        seriesRef.current = null;
      }
      removeRangeBands(chart, bandSeriesRef.current);
      bandSeriesRef.current = applyRangeBands(chart, rangeLevels, bars);

      const series = chart.addSeries(CandlestickSeries, CANDLE_SERIES_OPTIONS);
      seriesRef.current = series;
      series.setData(candleData);
      chart.timeScale().fitContent();

      priceLinesRef.current = applyStructuredLevels(series, visibleLevels);

      prevBarsLenRef.current = bars.length;
      prevOverlayKeyRef.current = overlayKey;
      return;
    }

    const series = seriesRef.current;
    if (series) {
      series.update(candleData[candleData.length - 1]);
    }
    updateRangeBands(bandSeriesRef.current, bars, rangeLevels);
  }, [bars, overlayKey, rangeLevels, visibleLevels]);

  return (
    <div className="markets-research-chart" aria-label={`${marketId} research chart`}>
      <MarketChartToolbar
        paneRef={paneRef}
        timeframes={TIMEFRAMES}
        timeframe={timeframe}
        onTimeframeChange={(id) => {
          setTimeframe(id);
          prevBarsLenRef.current = 0;
          prevOverlayKeyRef.current = '';
        }}
        layers={layers}
        layerOptions={LAYER_TOGGLES}
        onLayerToggle={(id) => setLayers((prev) => ({ ...prev, [id]: !prev[id] }))}
        liveQuote={liveQuote}
        quoteLoading={quoteLoading}
        liveTone={liveTone}
        quoteLabel={quoteLabel}
        formatTickerPrice={formatTickerPrice}
        formatTickerPercent={formatTickerPercent}
      />

      <div className="markets-research-chart__pane" ref={paneRef}>
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
        {visibleLevels.length > 0 && (
          <span className="markets-research-chart__footer-levels">
            {visibleLevels.length} overlays visible
          </span>
        )}
      </footer>
    </div>
  );
}

export default MarketChart;
