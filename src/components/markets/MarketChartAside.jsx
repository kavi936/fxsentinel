import React, { useState } from 'react';

function formatAsOf(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

function biasClass(displayBias) {
  const t = (displayBias || '').toLowerCase();
  if (t.includes('bearish')) return 'markets-bias--bearish';
  if (t.includes('bullish')) return 'markets-bias--bullish';
  return 'markets-bias--neutral';
}

/**
 * Right column — Analysis (bias + narrative) or filtered live news.
 */
function MarketChartAside({
  className = '',
  verdict,
  thesis,
  fallbackNews = [],
  liveNews = [],
  newsLoading,
  newsError,
}) {
  const [panel, setPanel] = useState('analysis');
  const newsItems = liveNews.length > 0 ? liveNews : fallbackNews;

  return (
    <aside
      className={['markets-chart-aside', className].filter(Boolean).join(' ')}
      aria-label="Market context"
    >
      <div className="markets-chart-aside__tabs" role="tablist" aria-label="Context panel">
        <button
          type="button"
          role="tab"
          aria-selected={panel === 'analysis'}
          className={panel === 'analysis' ? 'is-active' : ''}
          onClick={() => setPanel('analysis')}
        >
          Analysis
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={panel === 'news'}
          className={panel === 'news' ? 'is-active' : ''}
          onClick={() => setPanel('news')}
        >
          Live news
        </button>
      </div>

      {panel === 'analysis' ? (
        <div className="markets-chart-aside__panel" role="tabpanel">
          {verdict?.display_bias && (
            <span className={`markets-bias ${biasClass(verdict.display_bias)}`}>{verdict.display_bias}</span>
          )}
          {verdict?.conviction && (
            <p className="markets-chart-aside__meta">Conviction · {verdict.conviction}</p>
          )}
          {thesis?.headline && <p className="markets-chart-aside__subhead">{thesis.headline}</p>}
          {verdict?.day_summary && <p className="markets-chart-aside__body">{verdict.day_summary}</p>}
          {thesis?.body && <p className="markets-chart-aside__body markets-chart-aside__body--muted">{thesis.body}</p>}
        </div>
      ) : (
        <div className="markets-chart-aside__panel" role="tabpanel">
          {newsLoading && <p className="markets-chart-aside__status">Loading headlines…</p>}
          {!newsLoading && newsError && (
            <p className="markets-chart-aside__status">Showing cached headlines · {newsError}</p>
          )}
          {!newsLoading && newsItems.length === 0 && (
            <p className="markets-chart-aside__status">No BTC-related headlines right now.</p>
          )}
          <ul className="markets-chart-aside__news">
            {newsItems.map((n, i) => (
              <li key={n.id || i} className="markets-chart-aside__news-item">
                <span className="markets-chart-aside__news-title">{n.title}</span>
                {(n.source || n.published_at) && (
                  <span className="markets-chart-aside__news-meta">
                    {[n.source, n.published_at ? formatAsOf(n.published_at) : null].filter(Boolean).join(' · ')}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}

export default MarketChartAside;
