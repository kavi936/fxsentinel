import React, { useMemo } from 'react';
import { useMarketsContextSplitResize } from '../../hooks/useMarketsContextSplitResize';
import { mergeMarketNews } from './marketNewsFilter';
import MarketLiveNews from './MarketLiveNews';

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

function impactClass(impact) {
  const t = (impact || 'medium').toLowerCase();
  if (t === 'high' || t === 'critical') return 'markets-catalyst__impact--high';
  if (t === 'low') return 'markets-catalyst__impact--low';
  return 'markets-catalyst__impact--medium';
}

function formatCatalystWhen(date, time) {
  const parts = [date, time].filter(Boolean);
  return parts.join(' · ') || 'TBD';
}

function formatRiskRegime(regime) {
  if (!regime) return '—';
  return String(regime).replace(/_/g, ' ');
}

/**
 * Below chart — platform context (left) + live news (right), resizable split.
 */
function MarketContextPanel({
  catalysts = [],
  macroContext = null,
  sentiment = null,
  fallbackNews = [],
  liveNews = [],
  newsLoading = false,
  newsError = null,
  newsRefreshing = false,
  onNewsRefresh,
  marketLabel = 'Market',
  showNews = true,
  maxNewsItems = 12,
}) {
  const hasSentiment = sentiment?.risk_regime || sentiment?.fear_greed?.value != null || sentiment?.volatility;
  const hasMacro = macroContext?.us_scan_summary || macroContext?.short_term_bias;
  const hasCatalysts = catalysts.length > 0;
  const hasContext = hasSentiment || hasMacro || hasCatalysts;

  const newsItems = useMemo(
    () => mergeMarketNews(liveNews, fallbackNews, maxNewsItems),
    [liveNews, fallbackNews, maxNewsItems],
  );
  const usingFallback = liveNews.length === 0 && fallbackNews.length > 0 && newsItems.length > 0;

  const { containerRef, isDragging, onHandlePointerDown, leftWidthPercent } = useMarketsContextSplitResize({
    enabled: showNews,
  });

  if (!showNews) {
    return (
      <section className="markets-context-panel" aria-label="Market context">
        <div className="markets-context-panel__container markets-context-panel__container--solo">
          <p className="markets-context-panel__heading">Platform context</p>
          <div className="markets-context-panel__body">
            {!hasContext ? (
              <p className="markets-context-panel__empty">Context loads with the research snapshot.</p>
            ) : (
              <ContextGrid
                hasSentiment={hasSentiment}
                sentiment={sentiment}
                hasMacro={hasMacro}
                macroContext={macroContext}
                hasCatalysts={hasCatalysts}
                catalysts={catalysts}
              />
            )}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="markets-context-panel" aria-label="Market context and news">
      <div
        ref={containerRef}
        className={`markets-context-split ${isDragging ? 'is-resizing' : ''}`}
        style={{ '--markets-context-split-left': leftWidthPercent }}
      >
        <div className="markets-context-split__context">
          <div className="markets-context-panel__container">
            <p className="markets-context-panel__heading">Platform context</p>
            <div className="markets-context-panel__body">
              {!hasContext ? (
                <p className="markets-context-panel__empty">Context loads with the research snapshot.</p>
              ) : (
                <ContextGrid
                  hasSentiment={hasSentiment}
                  sentiment={sentiment}
                  hasMacro={hasMacro}
                  macroContext={macroContext}
                  hasCatalysts={hasCatalysts}
                  catalysts={catalysts}
                />
              )}
            </div>
          </div>
        </div>

        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize context and news panels"
          className={`markets-chart-resize-handle vertical ${isDragging ? 'active' : ''}`}
          onMouseDown={onHandlePointerDown}
          onTouchStart={onHandlePointerDown}
        />

        <div className="markets-context-split__news-wrap">
          <div className="markets-context-panel__container markets-context-panel__container--news">
            <MarketLiveNews
              items={newsItems}
              loading={newsLoading}
              error={newsError}
              marketLabel={marketLabel}
              onRefresh={onNewsRefresh}
              refreshing={newsRefreshing}
              usingFallback={usingFallback}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function ContextGrid({ hasSentiment, sentiment, hasMacro, macroContext, hasCatalysts, catalysts }) {
  return (
    <div className="markets-context-panel__context-grid">
      {hasSentiment && (
        <div className="markets-context-panel__card">
          <h4 className="markets-context-panel__title">Risk backdrop</h4>
          <dl className="markets-context-panel__metrics">
            {sentiment?.risk_regime && (
              <div>
                <dt>Regime</dt>
                <dd>{formatRiskRegime(sentiment.risk_regime)}</dd>
              </div>
            )}
            {sentiment?.fear_greed?.value != null && (
              <div>
                <dt>Fear &amp; Greed</dt>
                <dd>
                  {sentiment.fear_greed.value}
                  {sentiment.fear_greed.classification ? ` · ${sentiment.fear_greed.classification}` : ''}
                </dd>
              </div>
            )}
            {sentiment?.volatility && (
              <div>
                <dt>Volatility</dt>
                <dd>{sentiment.volatility}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {hasMacro && (
        <div className="markets-context-panel__card markets-context-panel__card--macro">
          <h4 className="markets-context-panel__title">US macro</h4>
          {macroContext?.short_term_bias && (
            <p className="markets-context-panel__bias">Short-term · {macroContext.short_term_bias}</p>
          )}
          {macroContext?.us_scan_summary && (
            <p className="markets-context-panel__digest">{macroContext.us_scan_summary}</p>
          )}
          {macroContext?.us_scan_as_of && (
            <p className="markets-context-panel__meta">As of {formatAsOf(macroContext.us_scan_as_of)}</p>
          )}
        </div>
      )}

      <div className="markets-context-panel__card markets-context-panel__card--catalysts">
        <h4 className="markets-context-panel__title">Upcoming catalysts</h4>
        {!hasCatalysts && (
          <p className="markets-context-panel__meta">No high-impact USD events in the next 7 days.</p>
        )}
        {hasCatalysts && (
          <ul className="markets-context-panel__catalyst-list">
            {catalysts.map((c) => (
              <li key={c.id || `${c.title}-${c.date}`} className="markets-catalyst">
                <div className="markets-catalyst__head">
                  <span className={`markets-catalyst__impact ${impactClass(c.impact)}`}>{c.impact || 'medium'}</span>
                  {c.currency && <span className="markets-catalyst__currency">{c.currency}</span>}
                </div>
                <span className="markets-catalyst__title">{c.title}</span>
                <span className="markets-catalyst__when">{formatCatalystWhen(c.date, c.time)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default MarketContextPanel;
