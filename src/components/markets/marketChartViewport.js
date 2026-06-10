/**
 * Save / restore chart zoom & pan.
 *
 * Timeframe switches use **unix time ranges** (same calendar window), not logical
 * bar indices — indices mean different spans on 15m vs 1D and cause stretch.
 * Price scale is never restored on TF change (always autoScale).
 */

/**
 * @param {import('lightweight-charts').IChartApi | null} chart
 * @param {import('lightweight-charts').ISeriesApi | null} [series]
 * @param {{ includePrice?: boolean }} [options]
 */
export function captureChartViewport(chart, series, options = {}) {
  if (!chart) return null;

  let timeRange = null;
  try {
    timeRange = chart.timeScale().getVisibleRange();
  } catch {
    timeRange = null;
  }

  let price = null;
  if (options.includePrice && series) {
    try {
      price = series.priceScale().getVisibleRange();
    } catch {
      price = null;
    }
  }

  if (!timeRange && !price) return null;
  return { timeRange, price };
}

/**
 * @param {import('lightweight-charts').LogicalRange} logical
 * @param {number} barCount
 */
export function clampLogicalRange(logical, barCount) {
  if (!logical || barCount < 1) return null;
  const maxIdx = Math.max(0, barCount - 1);
  let from = Number(logical.from);
  let to = Number(logical.to);
  if (!Number.isFinite(from) || !Number.isFinite(to)) return null;

  if (to < from) [from, to] = [to, from];

  const minWidth = Math.min(12, barCount);
  if (to - from < minWidth) {
    const mid = (from + to) / 2;
    from = mid - minWidth / 2;
    to = mid + minWidth / 2;
  }

  from = Math.max(0, from);
  to = Math.min(barCount, to);
  if (to - from < 2) {
    to = Math.min(barCount, from + minWidth);
  }

  return { from, to };
}

/**
 * @param {import('lightweight-charts').IChartApi} chart
 * @param {import('lightweight-charts').ISeriesApi | null} series
 * @param {{ timeRange?: { from: number, to: number } | null, logical?: import('lightweight-charts').LogicalRange | null, price?: import('lightweight-charts').PriceRange | null } | null | undefined} viewport
 * @param {{ barCount?: number, restorePrice?: boolean, onDone?: () => void }} [options]
 * @returns {boolean}
 */
export function restoreChartViewport(chart, series, viewport, options = {}) {
  const { barCount = 0, restorePrice = false, onDone } = options;
  if (!viewport) return false;

  const apply = () => {
    let applied = false;

    if (viewport.timeRange?.from != null && viewport.timeRange?.to != null) {
      try {
        chart.timeScale().setVisibleRange({
          from: viewport.timeRange.from,
          to: viewport.timeRange.to,
        });
        applied = true;
      } catch {
        /* fall through */
      }
    }

    if (!applied && viewport.logical && barCount > 0) {
      const clamped = clampLogicalRange(viewport.logical, barCount);
      if (clamped) {
        try {
          chart.timeScale().setVisibleLogicalRange(clamped);
          applied = true;
        } catch {
          /* ignore */
        }
      }
    }

    if (series) {
      try {
        if (restorePrice && viewport.price) {
          series.priceScale().setVisibleRange(viewport.price);
        } else {
          series.priceScale().applyOptions({ autoScale: true });
        }
      } catch {
        /* ignore */
      }
    }

    onDone?.();
    return applied;
  };

  requestAnimationFrame(apply);
  return Boolean(viewport.timeRange || viewport.logical);
}

/**
 * Fit all candles in view and re-enable price auto-scale.
 * @param {import('lightweight-charts').IChartApi | null} chart
 * @param {import('lightweight-charts').ISeriesApi | null} series
 */
export function fitChartContent(chart, series) {
  if (!chart) return;
  chart.timeScale().fitContent();
  if (series) {
    try {
      series.priceScale().applyOptions({ autoScale: true });
    } catch {
      /* ignore */
    }
  }
}
