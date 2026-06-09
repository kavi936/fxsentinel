import React, { useMemo, useState } from 'react';
import { useForexPrices } from '../../hooks/useForexPrices';
import { useMarketQuote } from '../../hooks/useMarketQuote';
import { useMarketResearch } from '../../hooks/useMarketResearch';
import { getMarketById } from './marketCatalog';
import MarketPicker from './MarketPicker';
import MarketResearch from './MarketResearch';
import MarketChartSection from './MarketChartSection';
import './MarketsLayout.css';

/** Full layout preview (chart + verdict + panels). Set true to re-enable inspiration skeleton. */
const SHOW_LAYOUT_SKELETON = false;

function formatLastUpdated(isoOrDate) {
  const date = isoOrDate instanceof Date ? isoOrDate : isoOrDate ? new Date(isoOrDate) : null;
  if (!date || Number.isNaN(date.getTime())) return '—';
  try {
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
}

/**
 * Markets tab — research chart + API-driven levels and verdict.
 */
function MarketsHub() {
  const [selectedId, setSelectedId] = useState('BTCUSD');
  const selected = getMarketById(selectedId);
  const { prices, loading: pricesLoading, instruments } = useForexPrices();

  const { research, loading: researchLoading } = useMarketResearch(selectedId, {
    enabled: Boolean(selected?.enabled),
  });

  const { quote: liveQuote, loading: quoteLoading } = useMarketQuote(selectedId, {
    enabled: Boolean(selected?.enabled),
    pollMs: 5_000,
  });

  const pickerPrices = useMemo(() => {
    const quoteId = selected?.quoteInstrumentId;
    if (!liveQuote?.price || !quoteId) return prices;
    return {
      ...prices,
      [quoteId]: {
        ...(prices?.[quoteId] || {}),
        price: liveQuote.price,
        change: liveQuote.change,
        changePercent: liveQuote.changePercent,
        lastUpdate: liveQuote.as_of,
        source: liveQuote.source || 'binance',
      },
    };
  }, [prices, liveQuote, selected?.quoteInstrumentId]);

  const lastUpdatedLabel = research?.as_of ?? new Date();

  const showSkeleton = SHOW_LAYOUT_SKELETON && selected?.enabled && research;
  const showChartSection = !SHOW_LAYOUT_SKELETON && selected?.enabled;

  return (
    <div className="markets-tab">
      <div className="markets-content--canvas">
        <header className="markets-top-bar">
          <div className="markets-top-bar__picker-wrap">
            <MarketPicker
              selectedId={selectedId}
              onSelect={setSelectedId}
              prices={pickerPrices}
              instruments={instruments}
              pricesLoading={pricesLoading && !liveQuote?.price}
            />
          </div>
          <div className="markets-top-bar__meta">
            <span className="markets-last-updated" title="Analysis snapshot time">
              Updated · {formatLastUpdated(lastUpdatedLabel)}
              {researchLoading && !research ? ' · loading…' : ''}
            </span>
          </div>
        </header>

        {showSkeleton ? (
          <div className="markets-body">
            <MarketResearch data={research} />
          </div>
        ) : showChartSection ? (
          <div className="markets-body markets-body--chart">
            <MarketChartSection
              research={research}
              marketId={selectedId}
              researchLoading={researchLoading}
              liveQuote={liveQuote}
              quoteLoading={quoteLoading}
            />
          </div>
        ) : (
          <div className="markets-canvas" aria-label="Markets workspace">
            {!selected?.enabled && (
              <p className="markets-canvas__hint">{selected?.label} — coming later</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default MarketsHub;
