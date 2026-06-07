import React, { useState } from 'react';
import MarketChartSkeleton from './MarketChartSkeleton';
import './MarketsLayout.css';
import './MarketsSkeleton.css';

function formatPrice(n) {
  if (n == null || Number.isNaN(n)) return '—';
  return n >= 1000 ? n.toLocaleString(undefined, { maximumFractionDigits: 1 }) : String(n);
}

function formatPct(n) {
  if (n == null || Number.isNaN(n)) return '—';
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}%`;
}

function formatAsOf(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function biasClass(displayBias) {
  const t = (displayBias || '').toLowerCase();
  if (t.includes('bearish')) return 'markets-bias--bearish';
  if (t.includes('bullish')) return 'markets-bias--bullish';
  return 'markets-bias--neutral';
}

/**
 * BTCUSD research layout skeleton — chart-first, black canvas.
 * Data: mock JSON until API is wired (Phase 1).
 */
function MarketResearch({ data }) {
  const [horizon, setHorizon] = useState('day');

  if (!data) {
    return (
      <div className="markets-research markets-research--empty">
        <p>No market data loaded.</p>
      </div>
    );
  }

  const { quote, verdict, structured_levels, cross_assets, catalysts, news, thesis, invalidation, latest_run } =
    data;
  const summary = horizon === 'swing' ? verdict.swing_summary : verdict.day_summary;

  return (
    <div className="markets-research">
      <p className="markets-research__preview-badge" aria-hidden="true">
        Layout preview
      </p>
      <section className="markets-section markets-chart-section" aria-labelledby="markets-chart-heading">
        <h2 id="markets-chart-heading" className="markets-sr-only">
          {data.display_label} chart
        </h2>
        <MarketChartSkeleton levels={structured_levels} />
      </section>

      <section className="markets-verdict-bar" aria-label="Market verdict">
        <div className="markets-verdict-bar__primary">
          <span className={`markets-bias ${biasClass(verdict.display_bias)}`}>{verdict.display_bias}</span>
          <span className="markets-verdict-bar__conviction">Conviction · {verdict.conviction}</span>
          {latest_run?.label_short && (
            <span className="markets-verdict-bar__run" title={latest_run.created_at}>
              Last run · {latest_run.label_short}
            </span>
          )}
        </div>
        <div className="markets-verdict-bar__quote">
          <span className="markets-verdict-bar__price">${formatPrice(quote.price)}</span>
          <span
            className={
              quote.changePercent >= 0 ? 'markets-change markets-change--up' : 'markets-change markets-change--down'
            }
          >
            {formatPct(quote.changePercent)}
          </span>
        </div>
        <div className="markets-horizon-toggle" role="tablist" aria-label="Bias horizon">
          <button
            type="button"
            role="tab"
            aria-selected={horizon === 'day'}
            className={horizon === 'day' ? 'is-active' : ''}
            onClick={() => setHorizon('day')}
          >
            Day
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={horizon === 'swing'}
            className={horizon === 'swing' ? 'is-active' : ''}
            onClick={() => setHorizon('swing')}
          >
            Swing
          </button>
        </div>
        <p className="markets-verdict-bar__summary">{summary}</p>
      </section>

      <div className="markets-columns">
        <div className="markets-columns__main">
          <section className="markets-section markets-panel" aria-labelledby="markets-thesis-heading">
            <h3 id="markets-thesis-heading" className="markets-section__title">
              Thesis
            </h3>
            <p className="markets-thesis__headline">{thesis.headline}</p>
            <p className="markets-thesis__body">{thesis.body}</p>
          </section>

          <section className="markets-section markets-panel" aria-labelledby="markets-levels-heading">
            <h3 id="markets-levels-heading" className="markets-section__title">
              Structure
            </h3>
            <ul className="markets-levels-list">
              {structured_levels.map((l) => (
                <li key={l.level_id} className={`markets-levels-list__item markets-levels-list__item--${l.kind}`}>
                  <span className="markets-levels-list__kind">{l.kind}</span>
                  <span className="markets-levels-list__label">{l.label}</span>
                  <span className="markets-levels-list__price">
                    {l.kind === 'range'
                      ? `${formatPrice(l.price_low)} – ${formatPrice(l.price_high)}`
                      : formatPrice(l.price)}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="markets-section markets-panel" aria-labelledby="markets-invalidation-heading">
            <h3 id="markets-invalidation-heading" className="markets-section__title">
              Invalidation
            </h3>
            <ul className="markets-invalidation-list">
              {invalidation.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </section>
        </div>

        <aside className="markets-columns__aside">
          <section className="markets-section markets-panel" aria-labelledby="markets-cross-heading">
            <h3 id="markets-cross-heading" className="markets-section__title">
              Cross-asset
            </h3>
            <ul className="markets-cross-strip">
              {cross_assets.map((a) => (
                <li key={a.id} className="markets-cross-strip__item">
                  <span className="markets-cross-strip__label">{a.label}</span>
                  <span
                    className={
                      a.changePercent >= 0 ? 'markets-change markets-change--up' : 'markets-change markets-change--down'
                    }
                  >
                    {formatPct(a.changePercent)}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="markets-section markets-panel" aria-labelledby="markets-news-heading">
            <h3 id="markets-news-heading" className="markets-section__title">
              Live news
            </h3>
            <ul className="markets-news-strip">
              {news.map((n, i) => (
                <li key={i} className="markets-news-strip__item">
                  <span className="markets-news-strip__title">{n.title}</span>
                  <span className="markets-news-strip__meta">
                    {n.source} · {formatAsOf(n.published_at)}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="markets-section markets-panel" aria-labelledby="markets-catalysts-heading">
            <h3 id="markets-catalysts-heading" className="markets-section__title">
              Catalysts
            </h3>
            <ul className="markets-catalysts-list">
              {catalysts.map((c, i) => (
                <li key={i} className="markets-catalysts-list__item">
                  <span className={`markets-catalysts-list__impact markets-catalysts-list__impact--${c.impact}`}>
                    {c.impact}
                  </span>
                  <span className="markets-catalysts-list__title">{c.title}</span>
                  <span className="markets-catalysts-list__when">
                    {c.date} {c.time_utc} UTC
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>

      {data.data_quality?.note && (
        <p className="markets-footer-note">{data.data_quality.note}</p>
      )}
    </div>
  );
}

export default MarketResearch;
