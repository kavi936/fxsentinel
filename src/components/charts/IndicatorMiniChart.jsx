import React, { useMemo, useState } from 'react';
import {
  buildYAxisLabels,
  collapseSeries,
  generateAreaPath,
  generateLinePath,
  getTargetLineY,
  normalizeChartData,
  valueAtIndex,
} from './indicatorChartUtils';
import './IndicatorChart.css';

export default function IndicatorMiniChart({
  chartId = 'chart',
  chartData = [],
  chartDates = [],
  showTargetLine = false,
  targetValue = 2,
  variant = 'analysis-compact',
  indicatorId = '',
}) {
  const [hoverIndex, setHoverIndex] = useState(null);

  const { normalized, original, dates } = useMemo(() => {
    const collapsed = collapseSeries(chartData, chartDates, 8);
    return {
      normalized: normalizeChartData(collapsed.data),
      original: collapsed.data,
      dates: collapsed.dates,
    };
  }, [chartData, chartDates]);

  const linePath = useMemo(() => generateLinePath(normalized), [normalized]);
  const areaPath = useMemo(() => generateAreaPath(normalized), [normalized]);
  const yAxisLabels = useMemo(
    () => buildYAxisLabels(original, indicatorId),
    [original, indicatorId]
  );
  const targetLineY = useMemo(
    () => (showTargetLine ? getTargetLineY(original, targetValue) : null),
    [showTargetLine, original, targetValue]
  );

  const handleMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
    const index = Math.round(ratio * (normalized.length - 1));
    setHoverIndex(index);
  };

  const hoverValue = hoverIndex != null ? valueAtIndex(original, hoverIndex) : null;
  const hoverDate = hoverIndex != null ? dates[hoverIndex] : null;

  return (
    <div className={`indicator-mini-chart indicator-mini-chart--${variant}`}>
      <div
        className={`mini-chart${hoverIndex != null ? ' chart-hover' : ''}`}
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverIndex(null)}
      >
        <div className="chart-y-axis" aria-hidden="true">
          {yAxisLabels.map((label) => (
            <span key={`${label.position}-${label.label}`} style={{ top: `${label.position}%` }}>
              {label.label}
            </span>
          ))}
        </div>
        <svg className="chart-line" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id={`chart-gradient-${chartId}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="rgba(255, 59, 48, 0.4)" />
              <stop offset="100%" stopColor="rgba(255, 59, 48, 0)" />
            </linearGradient>
          </defs>
          {[0, 25, 50, 75, 100].map((x) => (
            <line key={`v-${x}`} x1={x} y1="0" x2={x} y2="100" className="chart-grid-line" />
          ))}
          {yAxisLabels.map((label) => (
            <line
              key={`h-${label.position}`}
              x1="0"
              y1={label.position}
              x2="100"
              y2={label.position}
              className="chart-grid-line"
            />
          ))}
          <path className="chart-area" d={areaPath} fill={`url(#chart-gradient-${chartId})`} />
          {targetLineY != null && (
            <line x1="0" y1={targetLineY} x2="100" y2={targetLineY} className="chart-target-line" />
          )}
          <path className="chart-path-glow" d={linePath} />
          <path className="chart-path" d={linePath} />
        </svg>
        {hoverValue != null && (
          <div className="chart-hover-tooltip">
            <span>{hoverValue}{indicatorId === 'nonfarm-payrolls' ? 'K' : '%'}</span>
            {hoverDate && <span className="chart-hover-date">{hoverDate}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
