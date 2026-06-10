import React from 'react';

function biasClass(displayBias) {
  const t = (displayBias || '').toLowerCase();
  if (t.includes('bearish')) return 'markets-bias--bearish';
  if (t.includes('bullish')) return 'markets-bias--bullish';
  return 'markets-bias--neutral';
}

function formatLevelPrice(level) {
  if (level?.kind === 'range') {
    return `${Number(level.price_low).toLocaleString()} – ${Number(level.price_high).toLocaleString()}`;
  }
  if (level?.price != null) return Number(level.price).toLocaleString();
  return '—';
}

const VOLUME_BASES = new Set(['volume_poc', 'value_area_4h_5d']);
const STRUCTURE_BASES = new Set([
  'prior_day_high',
  'prior_day_low',
  'prior_day_close',
  'weekly_high',
  'weekly_low',
  'swing_high_4h',
  'swing_low_4h',
  'session_value_zone_4h',
]);

function groupLevels(levels = []) {
  const structure = [];
  const volume = [];
  const other = [];

  for (const level of levels) {
    if (VOLUME_BASES.has(level.basis)) {
      volume.push(level);
    } else if (STRUCTURE_BASES.has(level.basis) || level.kind === 'level' || level.kind === 'range') {
      structure.push(level);
    } else {
      other.push(level);
    }
  }

  return { structure, volume, other };
}

/**
 * Right column — chart-linked structure only (levels, invalidation, cross-asset).
 */
function MarketChartAside({
  className = '',
  verdict,
  structuredLevels = [],
  invalidation = [],
  crossAssets = [],
}) {
  const { structure, volume, other } = groupLevels(structuredLevels);

  const renderLevelList = (items, limit = 8) => {
    if (!items.length) return null;
    return (
      <ul>
        {items.slice(0, limit).map((level) => (
          <li key={level.level_id}>
            <span className="markets-chart-aside__level-label">{level.label}</span>
            <span className="markets-chart-aside__level-price">{formatLevelPrice(level)}</span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <aside
      className={['markets-chart-aside', className].filter(Boolean).join(' ')}
      aria-label="Market structure"
    >
      <p className="markets-chart-aside__heading">Structure</p>

      <div className="markets-chart-aside__panel">
        {verdict?.display_bias && (
          <span className={`markets-bias ${biasClass(verdict.display_bias)}`}>{verdict.display_bias}</span>
        )}
        {verdict?.day_summary && (
          <p className="markets-chart-aside__body markets-chart-aside__body--muted">{verdict.day_summary}</p>
        )}

        {structure.length > 0 && (
          <div className="markets-chart-aside__levels">
            <p className="markets-chart-aside__levels-title">Key levels</p>
            {renderLevelList(structure)}
          </div>
        )}

        {volume.length > 0 && (
          <div className="markets-chart-aside__levels">
            <p className="markets-chart-aside__levels-title">Volume zones</p>
            {renderLevelList(volume)}
          </div>
        )}

        {other.length > 0 && (
          <div className="markets-chart-aside__levels">
            <p className="markets-chart-aside__levels-title">POI</p>
            {renderLevelList(other)}
          </div>
        )}

        {invalidation.length > 0 && (
          <div className="markets-chart-aside__invalidation">
            <p className="markets-chart-aside__levels-title">Invalidation</p>
            <ul>
              {invalidation.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </div>
        )}

        {crossAssets.length > 0 && (
          <div className="markets-chart-aside__cross">
            <p className="markets-chart-aside__levels-title">Cross-asset</p>
            <ul className="markets-chart-aside__cross-list">
              {crossAssets.map((a) => (
                <li key={a.id}>
                  <span>{a.label}</span>
                  <span
                    className={
                      a.changePercent > 0
                        ? 'markets-chart-aside__cross-up'
                        : a.changePercent < 0
                          ? 'markets-chart-aside__cross-down'
                          : ''
                    }
                  >
                    {a.changePercent != null ? `${a.changePercent > 0 ? '+' : ''}${Number(a.changePercent).toFixed(2)}%` : '—'}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  );
}

export default MarketChartAside;
