import React from 'react';
import './MarketsSkeleton.css';

/**
 * Phase 0 chart placeholder — black canvas with mock level/range overlays.
 * Replaced by lightweight-charts + live OHLC in Phase 1.
 */
function MarketChartSkeleton({ levels = [], showCaption = true }) {
  const lineLevels = levels.filter((l) => l.kind === 'level' || l.kind === 'poi');
  const ranges = levels.filter((l) => l.kind === 'range');

  return (
    <div className="markets-chart-skeleton" aria-label="Chart placeholder">
      <div className="markets-chart-skeleton__toolbar" aria-hidden="true">
        <span>1H</span>
        <span className="is-active">4H</span>
        <span>1D</span>
        <span>1W</span>
      </div>
      <div className="markets-chart-skeleton__grid" aria-hidden="true" />
      {ranges.map((r) => (
        <div
          key={r.level_id}
          className="markets-chart-skeleton__range"
          title={r.label}
        >
          <span className="markets-chart-skeleton__range-label">{r.label}</span>
        </div>
      ))}
      {lineLevels.map((l, i) => (
        <div
          key={l.level_id}
          className={`markets-chart-skeleton__line markets-chart-skeleton__line--${i % 3}`}
          title={`${l.label} · ${l.price}`}
        >
          <span className="markets-chart-skeleton__line-label">{l.label}</span>
        </div>
      ))}
      <div className="markets-chart-skeleton__candles" aria-hidden="true">
        {Array.from({ length: 24 }).map((_, i) => (
          <div
            key={i}
            className="markets-chart-skeleton__bar"
            style={{ '--h': `${30 + ((i * 17) % 50)}%` }}
          />
        ))}
      </div>
      {showCaption && (
        <p className="markets-chart-skeleton__caption">Chart placeholder · live candles coming in Phase 1</p>
      )}
    </div>
  );
}

export default MarketChartSkeleton;
