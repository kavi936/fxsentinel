/** Apply system levels / POI / ranges — read-only, data-driven overlays. */

const BASIS_STYLE = {
  prior_day_high: { color: 'rgba(255, 68, 68, 0.85)', lineStyle: 0, lineWidth: 1 },
  prior_day_low: { color: 'rgba(72, 187, 220, 0.85)', lineStyle: 0, lineWidth: 1 },
  prior_day_close: { color: 'rgba(255, 255, 255, 0.45)', lineStyle: 2, lineWidth: 1 },
  weekly_high: { color: 'rgba(255, 120, 80, 0.55)', lineStyle: 2, lineWidth: 1 },
  weekly_low: { color: 'rgba(80, 180, 255, 0.55)', lineStyle: 2, lineWidth: 1 },
  swing_high_4h: { color: 'rgba(255, 200, 80, 0.65)', lineStyle: 2, lineWidth: 1 },
  swing_low_4h: { color: 'rgba(255, 200, 80, 0.65)', lineStyle: 2, lineWidth: 1 },
  poi_confluence: { color: '#ff4444', lineStyle: 0, lineWidth: 2 },
  session_value_zone_4h: { color: 'rgba(255, 100, 100, 0.75)', lineStyle: 2, lineWidth: 1 },
};

const DEFAULT_STYLE = { color: 'rgba(255, 255, 255, 0.35)', lineStyle: 2, lineWidth: 1 };

function styleFor(level) {
  return BASIS_STYLE[level.basis] || DEFAULT_STYLE;
}

/**
 * @param {import('lightweight-charts').ISeriesApi<'Candlestick'>} series
 * @param {Array} structuredLevels
 * @returns {import('lightweight-charts').IPriceLine[]}
 */
/** Filter overlays by layer toggles (levels / poi / ranges). */
export function filterLevelsByLayer(structuredLevels = [], layers = {}) {
  const showLevels = layers.levels !== false;
  const showPoi = layers.poi !== false;
  const showRanges = layers.ranges !== false;

  return (structuredLevels || []).filter((level) => {
    if (level.kind === 'poi') return showPoi;
    if (level.kind === 'range') return showRanges;
    return showLevels;
  });
}

export function applyStructuredLevels(series, structuredLevels = []) {
  if (!series) return [];

  const lines = [];

  for (const level of structuredLevels) {
    if (level.kind === 'range') {
      const st = styleFor(level);
      const hi = series.createPriceLine({
        price: Number(level.price_high),
        color: st.color,
        lineWidth: st.lineWidth,
        lineStyle: st.lineStyle,
        axisLabelVisible: true,
        title: `${level.label || 'Range'} ↑`,
      });
      const lo = series.createPriceLine({
        price: Number(level.price_low),
        color: st.color,
        lineWidth: st.lineWidth,
        lineStyle: st.lineStyle,
        axisLabelVisible: true,
        title: `${level.label || 'Range'} ↓`,
      });
      lines.push(hi, lo);
      continue;
    }

    if (level.price == null) continue;

    const st = styleFor(level);
    const title = level.kind === 'poi' ? level.label || 'POI' : level.label || level.basis;
    const line = series.createPriceLine({
      price: Number(level.price),
      color: st.color,
      lineWidth: st.lineWidth,
      lineStyle: st.lineStyle,
      axisLabelVisible: true,
      title,
    });
    lines.push(line);
  }

  return lines;
}

export function clearPriceLines(series, priceLines = []) {
  for (const line of priceLines) {
    try {
      series.removePriceLine(line);
    } catch {
      /* ignore */
    }
  }
}
