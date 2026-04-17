/**
 * Major-pair daily % gauge: bar grows from center (50%) toward the bullish (right)
 * or bearish (left) edge. Must match GAUGE_CAP_PCT in market_sentiment_service.py.
 */
export const DAILY_CHANGE_GAUGE_CAP_PCT = 1.15;

/**
 * @param {number} changePercent — Daily % change (e.g. 0.25 for +0.25%)
 * @returns {{ leftPct: number, widthPct: number, t: number }}
 */
export function getDailyChangeGaugeLayout(changePercent) {
  const c = Number(changePercent);
  if (!Number.isFinite(c)) {
    return { leftPct: 50, widthPct: 0, t: 0 };
  }
  const t = Math.max(-1, Math.min(1, c / DAILY_CHANGE_GAUGE_CAP_PCT));
  const leftPct = 50 + Math.min(t, 0) * 50;
  let widthPct = Math.abs(t) * 50;
  if (Math.abs(c) > 1e-9 && widthPct > 0 && widthPct < 0.85) {
    widthPct = 0.85;
  }
  return { leftPct, widthPct, t };
}
