import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CandlestickSeries, createChart } from 'lightweight-charts';
import { useMarketOhlc } from '../../hooks/useMarketOhlc';
import { applyStructuredLevels, clearPriceLines, filterLevelsByLayer } from './marketChartOverlays';
import { applyRangeBands, removeRangeBands, updateRangeBands } from './marketChartRangeBands';
import { MARKET_CHART_TIMEFRAMES, MARKET_OHLC_BAR_LIMIT } from './marketChartTimeframes';
import { CANDLE_SERIES_OPTIONS, createChartOptions } from './marketChartTheme';
import { captureChartViewport, fitChartContent, restoreChartViewport } from './marketChartViewport';
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

function barsSeriesKey(timeframe, bars) {
  if (!bars.length) return `${timeframe}:empty`;
  return `${timeframe}:${bars.length}:${bars[0].time}:${bars[bars.length - 1].time}`;
}

function ohlcMatchesTimeframe(meta, apiTf) {
  if (!meta?.timeframe || !apiTf) return false;
  return String(meta.timeframe).toUpperCase() === String(apiTf).toUpperCase();
}

/**
 * FXSentinel research chart — our OHLC + system level overlays (read-only).
 */
const LAYER_TOGGLES = [
  { id: 'levels', label: 'Structure' },
  { id: 'volume', label: 'Volume' },
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
  const prevBarsKeyRef = useRef('');
  const prevLevelsKeyRef = useRef('');
  const viewportByTfRef = useRef({});
  const pendingTimeRangeRef = useRef(null);
  const timeframeRef = useRef('4H');
  const isRestoringViewportRef = useRef(false);
  const hasInitialFitRef = useRef(false);

  const [timeframe, setTimeframe] = useState('4H');
  const [layers, setLayers] = useState({ levels: true, volume: true, poi: false, ranges: false });
  const tfConfig = TIMEFRAMES.find((t) => t.id === timeframe) || TIMEFRAMES[1];

  timeframeRef.current = timeframe;

  const visibleLevels = useMemo(
    () => filterLevelsByLayer(structuredLevels, layers),
    [structuredLevels, layers]
  );

  const levelsKey = useMemo(
    () =>
      [
        layers.levels,
        layers.volume,
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

  const barsReady = bars.length > 0 && ohlcMatchesTimeframe(meta, tfConfig.apiTf);

  const liveTone = liveQuote ? (isTickerChangePositive(liveQuote.change, liveQuote.changePercent) ? 'up' : 'down') : '';
  const quoteLabel = liveQuote?.instrument_id || liveQuote?.symbol || '—';

  const persistViewport = useCallback(() => {
    if (isRestoringViewportRef.current) return;
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart) return;
    const snap = captureChartViewport(chart, series);
    if (snap?.timeRange) {
      viewportByTfRef.current[timeframeRef.current] = snap;
    }
  }, []);

  const handleResetView = useCallback(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart) return;

    isRestoringViewportRef.current = true;
    fitChartContent(chart, series);
    requestAnimationFrame(() => {
      persistViewport();
      isRestoringViewportRef.current = false;
    });
  }, [persistViewport]);

  const applyViewportAfterSeriesChange = useCallback(
    (chart, series, barCount) => {
      const tf = timeframeRef.current;
      const saved = viewportByTfRef.current[tf];
      const pending = pendingTimeRangeRef.current;

      isRestoringViewportRef.current = true;

      const finish = () => {
        requestAnimationFrame(() => {
          persistViewport();
          isRestoringViewportRef.current = false;
        });
      };

      if (saved?.timeRange) {
        pendingTimeRangeRef.current = null;
        restoreChartViewport(chart, series, saved, {
          barCount,
          restorePrice: false,
          onDone: finish,
        });
        return;
      }

      if (pending?.from != null && pending?.to != null) {
        pendingTimeRangeRef.current = null;
        restoreChartViewport(chart, series, { timeRange: pending }, {
          barCount,
          restorePrice: false,
          onDone: finish,
        });
        return;
      }

      fitChartContent(chart, series);
      hasInitialFitRef.current = true;
      finish();
    },
    [persistViewport]
  );

  /* Chart shell */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const chart = createChart(el, createChartOptions(el.clientWidth, el.clientHeight || 320));
    chartRef.current = chart;

    const onVisibleRangeChange = () => {
      persistViewport();
    };
    chart.timeScale().subscribeVisibleLogicalRangeChange(onVisibleRangeChange);

    const ro = new ResizeObserver(() => {
      const { clientWidth, clientHeight } = el;
      if (clientWidth > 0 && clientHeight > 0) {
        chart.applyOptions({ width: clientWidth, height: clientHeight });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(onVisibleRangeChange);
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
      prevBarsKeyRef.current = '';
      prevLevelsKeyRef.current = '';
      hasInitialFitRef.current = false;
    };
  }, [persistViewport]);

  /* Double-click chart pane → fit all candles */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const onDoubleClick = (event) => {
      event.preventDefault();
      handleResetView();
    };
    el.addEventListener('dblclick', onDoubleClick);
    return () => el.removeEventListener('dblclick', onDoubleClick);
  }, [handleResetView]);

  /* Candle series — rebuild only when OHLC series identity changes (timeframe / market / full reload) */
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !barsReady) return;

    const barsKey = barsSeriesKey(timeframe, bars);
    const candleData = toCandleData(bars);

    if (barsKey === prevBarsKeyRef.current && seriesRef.current) {
      seriesRef.current.update(candleData[candleData.length - 1]);
      updateRangeBands(bandSeriesRef.current, bars, rangeLevels);
      return;
    }

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

    const series = chart.addSeries(CandlestickSeries, CANDLE_SERIES_OPTIONS);
    seriesRef.current = series;
    series.setData(candleData);

    applyViewportAfterSeriesChange(chart, series, candleData.length);

    prevBarsKeyRef.current = barsKey;
    prevLevelsKeyRef.current = '';
  }, [bars, barsReady, timeframe, rangeLevels, applyViewportAfterSeriesChange]);

  /* Overlays — layer toggles update price lines / bands only (no candle tear-down) */
  useEffect(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series || !barsReady) return;

    if (levelsKey === prevLevelsKeyRef.current) return;

    clearPriceLines(series, priceLinesRef.current);
    priceLinesRef.current = applyStructuredLevels(series, visibleLevels);

    removeRangeBands(chart, bandSeriesRef.current);
    bandSeriesRef.current = applyRangeBands(chart, rangeLevels, bars);

    prevLevelsKeyRef.current = levelsKey;
  }, [levelsKey, visibleLevels, rangeLevels, bars, barsReady]);

  const handleTimeframeChange = (id) => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (chart && series) {
      const snap = captureChartViewport(chart, series);
      if (snap) {
        viewportByTfRef.current[timeframe] = snap;
        if (snap.timeRange) {
          pendingTimeRangeRef.current = snap.timeRange;
        }
      }
    }
    setTimeframe(id);
    prevBarsKeyRef.current = '';
    prevLevelsKeyRef.current = '';
  };

  const handleLayerToggle = (id) => {
    setLayers((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="markets-research-chart" aria-label={`${marketId} research chart`}>
      <MarketChartToolbar
        paneRef={paneRef}
        timeframes={TIMEFRAMES}
        timeframe={timeframe}
        onTimeframeChange={handleTimeframeChange}
        layers={layers}
        layerOptions={LAYER_TOGGLES}
        onLayerToggle={handleLayerToggle}
        onResetView={handleResetView}
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
        <div
          ref={containerRef}
          className="markets-research-chart__canvas"
          title="Double-click to reset view"
        />
      </div>

      <footer className="markets-research-chart__footer">
        <span>{formatSourceFooter(meta)}</span>
        <span className="markets-research-chart__footer-hint">Double-click chart to reset view</span>
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
