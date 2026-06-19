import React from 'react';
import {
  cleanNewsTitle,
  formatMarketNewsTime,
  getImpactLabel,
  getMarketNewsImpact,
  truncateSummary,
} from '../../utils/marketNewsUtils';
import { sanitizeURL } from '../../utils/sanitize';

function NewsSkeleton() {
  return (
    <div className="markets-live-news__skeleton" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <div key={i} className="markets-live-news__skeleton-item">
          <div className="markets-live-news__skeleton-line markets-live-news__skeleton-line--short" />
          <div className="markets-live-news__skeleton-line" />
          <div className="markets-live-news__skeleton-line markets-live-news__skeleton-line--medium" />
        </div>
      ))}
    </div>
  );
}

function ImpactBadge({ impact }) {
  const level = impact || 'low';
  return (
    <div className={`markets-live-news__impact impact-${level}`} aria-label={`Impact ${getImpactLabel(level)}`}>
      <span className="markets-live-news__impact-label">{getImpactLabel(level)}</span>
      <div className="markets-live-news__impact-bars">
        <span className="markets-live-news__impact-bar" />
        <span className="markets-live-news__impact-bar" />
        <span className="markets-live-news__impact-bar" />
      </div>
    </div>
  );
}

function MarketNewsItem({ item, onOpen }) {
  const impact = getMarketNewsImpact(item);
  const title = cleanNewsTitle(item.title);
  const summary = truncateSummary(item.summary);
  const timeLabel = formatMarketNewsTime(item.added_to_feed_at || item.published_at);
  const safeUrl = item.url ? sanitizeURL(item.url) : null;
  const isLink = safeUrl && safeUrl !== '#';

  const handleClick = () => {
    if (isLink) {
      window.open(safeUrl, '_blank', 'noopener,noreferrer');
      return;
    }
    onOpen?.(item);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  };

  return (
    <article
      className={`markets-live-news__item${isLink ? ' is-clickable' : ''}`}
      onClick={isLink ? handleClick : undefined}
      onKeyDown={isLink ? handleKeyDown : undefined}
      role={isLink ? 'link' : undefined}
      tabIndex={isLink ? 0 : undefined}
    >
      <div className="markets-live-news__item-head">
        <div className="markets-live-news__source-block">
          {item.source && <span className="markets-live-news__source">{item.source}</span>}
          <span className="markets-live-news__time">{timeLabel}</span>
        </div>
        <ImpactBadge impact={impact} />
      </div>
      <h3 className="markets-live-news__title">{title}</h3>
      {summary && <p className="markets-live-news__summary">{summary}</p>}
    </article>
  );
}

/**
 * Compact live news strip for Markets — Overview visual language, market-filtered.
 */
function MarketLiveNews({
  items = [],
  loading = false,
  error = null,
  marketLabel = 'Market',
  onRefresh,
  refreshing = false,
  usingFallback = false,
  className = '',
}) {
  const showSkeleton = loading && items.length === 0;
  const isEmpty = !loading && !error && items.length === 0;

  return (
    <div className={['markets-live-news', className].filter(Boolean).join(' ')}>
      <header className="markets-live-news__header">
        <div className="markets-live-news__header-main">
          <h2 className="markets-live-news__heading">Live news</h2>
          <span className="markets-live-news__filter-badge">{marketLabel}</span>
        </div>
        <div className="markets-live-news__controls">
          {refreshing && items.length > 0 && (
            <span className="markets-live-news__refresh-label" aria-live="polite">
              Refreshing…
            </span>
          )}
          {onRefresh && (
            <button
              type="button"
              className="markets-live-news__refresh-btn"
              onClick={onRefresh}
              disabled={loading || refreshing}
              title="Refresh headlines"
              aria-label="Refresh headlines"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16" />
              </svg>
            </button>
          )}
        </div>
      </header>

      <div className="markets-live-news__body">
        {showSkeleton && <NewsSkeleton />}

        {!showSkeleton && error && items.length === 0 && (
          <div className="markets-live-news__empty">
            <p className="markets-live-news__empty-title">Headlines unavailable</p>
            <p className="markets-live-news__empty-sub">{error}</p>
            {onRefresh && (
              <button type="button" className="markets-live-news__retry-btn" onClick={onRefresh}>
                Try again
              </button>
            )}
          </div>
        )}

        {isEmpty && (
          <div className="markets-live-news__empty">
            <p className="markets-live-news__empty-title">No matching headlines</p>
            <p className="markets-live-news__empty-sub">
              Nothing in the feed matches {marketLabel} right now. Broader FX headlines still appear on Overview.
            </p>
          </div>
        )}

        {usingFallback && items.length > 0 && (
          <p className="markets-live-news__status markets-live-news__status--muted">
            Showing cached headlines from research snapshot
          </p>
        )}

        {items.length > 0 && (
          <div className="markets-live-news__list">
            {items.map((item, index) => (
              <MarketNewsItem key={item.id || `${item.title}-${index}`} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default MarketLiveNews;
