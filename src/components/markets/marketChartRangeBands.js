import { BaselineSeries } from 'lightweight-charts';

const RANGE_FILL = {
  session_value_zone_4h: 'rgba(255, 68, 68, 0.12)',
  value_area_4h_5d: 'rgba(251, 191, 36, 0.14)',
  target_range: 'rgba(255, 68, 68, 0.12)',
  default: 'rgba(255, 68, 68, 0.1)',
};

function fillFor(level) {
  return RANGE_FILL[level.basis] || RANGE_FILL.default;
}

function bandData(bars, priceHigh) {
  const high = Number(priceHigh);
  return bars.map((b) => ({ time: b.time, value: high }));
}

/**
 * Semi-transparent fill between price_low and price_high (rendered behind candles).
 * @param {import('lightweight-charts').IChartApi} chart
 * @param {Array} rangeLevels — structured_levels where kind === 'range'
 * @param {Array} bars — OHLC bars for time axis alignment
 */
export function applyRangeBands(chart, rangeLevels = [], bars = []) {
  if (!chart || !bars.length || !rangeLevels.length) return [];

  const created = [];

  for (const level of rangeLevels) {
    const low = Number(level.price_low);
    const high = Number(level.price_high);
    if (!Number.isFinite(low) || !Number.isFinite(high) || high <= low) continue;

    const fill = fillFor(level);
    const series = chart.addSeries(BaselineSeries, {
      baseValue: { type: 'price', price: low },
      topFillColor1: fill,
      topFillColor2: fill,
      bottomFillColor1: 'transparent',
      bottomFillColor2: 'transparent',
      lineVisible: false,
      lastValueVisible: false,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      priceScaleId: 'right',
    });
    series.setData(bandData(bars, high));
    created.push(series);
  }

  return created;
}

export function updateRangeBands(bandSeries = [], bars = [], rangeLevels = []) {
  if (!bars.length) return;
  for (let i = 0; i < bandSeries.length; i += 1) {
    const level = rangeLevels[i];
    const series = bandSeries[i];
    if (!level || !series) continue;
    const data = bandData(bars, level.price_high);
    const last = data[data.length - 1];
    if (data.length <= 1) {
      series.setData(data);
    } else {
      series.update(last);
    }
  }
}

export function removeRangeBands(chart, bandSeries = []) {
  if (!chart) return;
  for (const series of bandSeries) {
    try {
      chart.removeSeries(series);
    } catch {
      /* ignore */
    }
  }
}
