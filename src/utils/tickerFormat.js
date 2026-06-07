/**
 * Shared formatting for live ticker + Markets picker (same TradingView feed).
 */

export function formatTickerPrice(price, decimals = 4) {
  if (price == null || price === '') return Number(0).toFixed(decimals);
  const n = parseFloat(price);
  if (Number.isNaN(n)) return Number(0).toFixed(decimals);
  return n.toFixed(decimals);
}

export function formatTickerChange(change, decimals = 4) {
  const n = parseFloat(change);
  if (Number.isNaN(n)) return `+${Number(0).toFixed(decimals)}`;
  return (n >= 0 ? '+' : '') + n.toFixed(decimals);
}

export function formatTickerPercent(change, price, changePercent) {
  if (changePercent != null && !Number.isNaN(parseFloat(changePercent))) {
    const pct = parseFloat(changePercent);
    return (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
  }
  if (!change || !price) return '+0.00%';
  const num = parseFloat(change);
  const p = parseFloat(price);
  if (Number.isNaN(num) || Number.isNaN(p) || p === 0) return '+0.00%';
  const percent = (num / p) * 100;
  return (percent >= 0 ? '+' : '') + percent.toFixed(2) + '%';
}

export function isTickerChangePositive(change, changePercent) {
  if (changePercent != null && !Number.isNaN(parseFloat(changePercent))) {
    return parseFloat(changePercent) >= 0;
  }
  if (change == null) return true;
  const n = parseFloat(change);
  return Number.isNaN(n) ? true : n >= 0;
}
