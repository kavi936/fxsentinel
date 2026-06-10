import React from 'react';
import { useMarketNews } from '../../hooks/useMarketNews';
import { useMarketsChartSplitResize } from '../../hooks/useMarketsChartSplitResize';
import MarketChart from './MarketChart';
import MarketHeadline from './MarketHeadline';
import MarketChartAside from './MarketChartAside';
import MarketContextPanel from './MarketContextPanel';
import './MarketsChart.css';

/**
 * Chart block: headline + chart (left), structure aside (right), platform context below.
 */
function MarketChartSection({
  research,
  marketId = 'BTCUSD',
  researchLoading = false,
  liveQuote = null,
  quoteLoading = false,
}) {
  const headline = research?.headline || research?.thesis?.headline || '';

  const { items: liveNews, loading: newsLoading, error: newsError } = useMarketNews({
    enabled: marketId === 'BTCUSD',
    marketId,
    maxItems: 6,
  });

  const { containerRef, isDragging, onHandlePointerDown, leftWidthPercent } =
    useMarketsChartSplitResize({ enabled: true });

  return (
    <section
      className="markets-chart-block"
      aria-labelledby={headline ? 'markets-headline-label' : undefined}
    >
      <div
        ref={containerRef}
        className={`markets-chart-split ${isDragging ? 'is-resizing' : ''}`}
        style={{ '--markets-split-left': leftWidthPercent }}
      >
        <div className="markets-chart-split__main">
          <MarketHeadline
            headline={
              headline ||
              (researchLoading ? 'Loading market structure and bias…' : 'Market research unavailable.')
            }
            emphasis={research?.headline_emphasis}
            segments={research?.headline_segments}
          />
          <div className="markets-chart-split__chart">
            <MarketChart
              marketId={marketId}
              structuredLevels={research?.structured_levels}
              liveQuote={liveQuote}
              quoteLoading={quoteLoading}
            />
          </div>
        </div>

        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize chart and structure panels"
          className={`markets-chart-resize-handle vertical ${isDragging ? 'active' : ''}`}
          onMouseDown={onHandlePointerDown}
          onTouchStart={onHandlePointerDown}
        />

        <div className="markets-chart-split__aside-wrap">
          <MarketChartAside
            className="markets-chart-split__aside"
            verdict={research?.verdict}
            structuredLevels={research?.structured_levels}
            invalidation={research?.invalidation}
            crossAssets={research?.cross_assets}
          />
        </div>
      </div>

      <MarketContextPanel
        catalysts={research?.catalysts}
        macroContext={research?.macro_context}
        sentiment={research?.sentiment}
        fallbackNews={research?.news}
        liveNews={liveNews}
        newsLoading={newsLoading}
        newsError={newsError}
        showNews={marketId === 'BTCUSD'}
      />
    </section>
  );
}

export default MarketChartSection;
