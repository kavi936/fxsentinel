/**
 * Shared chart path + normalization helpers (Economies tab parity).
 */

export function normalizeChartData(values) {
  if (!values || values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;
  if (range === 0) return values.map(() => 50);
  return values.map((val) => ((val - min) / range) * 80 + 10);
}

export function collapseSeries(chartData, chartDates, maxPoints = 8) {
  if (!Array.isArray(chartData) || chartData.length === 0) {
    return { data: [], dates: [] };
  }
  if (chartData.length <= maxPoints) {
    return { data: chartData, dates: chartDates || [] };
  }
  return {
    data: chartData.slice(-maxPoints),
    dates: (chartDates || []).slice(-maxPoints),
  };
}

export function generateLinePath(data) {
  if (!data.length) return '';
  if (data.length === 1) {
    return `M 0,${100 - data[0]}`;
  }

  const points = data.map((value, index) => ({
    x: (index / (data.length - 1)) * 100,
    y: 100 - value,
  }));

  const slopes = [];
  for (let i = 0; i < points.length - 1; i += 1) {
    const dx = points[i + 1].x - points[i].x;
    const dy = points[i + 1].y - points[i].y;
    slopes.push(dx !== 0 ? dy / dx : 0);
  }

  const tangents = points.map((_, i) => {
    if (i === 0) return slopes[0];
    if (i === points.length - 1) return slopes[slopes.length - 1];
    const s1 = slopes[i - 1];
    const s2 = slopes[i];
    if (s1 * s2 <= 0) return 0;
    return (s1 + s2) / 2;
  });

  let path = `M ${points[0].x},${points[0].y}`;
  for (let i = 0; i < points.length - 1; i += 1) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const delta = (p1.x - p0.x) / 3;
    const cp1x = p0.x + delta;
    const cp1y = p0.y + tangents[i] * delta;
    const cp2x = p1.x - delta;
    const cp2y = p1.y - tangents[i + 1] * delta;
    path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p1.x},${p1.y}`;
  }
  return path;
}

export function generateAreaPath(data) {
  if (!data.length) return '';
  const linePath = generateLinePath(data);
  if (!linePath) return '';
  return `${linePath} L 100,100 L 0,100 Z`;
}

export function getTargetLineY(originalData, targetValue) {
  if (!originalData?.length || targetValue == null) return null;
  const rawMin = Math.min(...originalData);
  const rawMax = Math.max(...originalData);
  const rawRange = rawMax - rawMin;
  if (rawRange === 0) return 50;
  const normalized = 10 + ((targetValue - rawMin) / rawRange) * 80;
  return 100 - normalized;
}

export function formatAxisValue(value, indicatorId) {
  if (indicatorId === 'nonfarm-payrolls') {
    return `${Math.round(value)}K`;
  }
  return `${Number(value).toFixed(1)}%`;
}

export function buildYAxisLabels(originalData, indicatorId) {
  if (!originalData?.length) return [];
  const rawMin = Math.min(...originalData);
  const rawMax = Math.max(...originalData);
  const rawRange = rawMax - rawMin;
  if (rawRange === 0) {
    return [{ position: 50, label: formatAxisValue(rawMin, indicatorId) }];
  }
  return [
    { position: 10, label: formatAxisValue(rawMax, indicatorId) },
    { position: 50, label: formatAxisValue(rawMin + rawRange / 2, indicatorId) },
    { position: 90, label: formatAxisValue(rawMin, indicatorId) },
  ];
}

export function valueAtIndex(originalData, index) {
  if (!originalData?.length) return null;
  const clamped = Math.max(0, Math.min(index, originalData.length - 1));
  return originalData[clamped];
}
