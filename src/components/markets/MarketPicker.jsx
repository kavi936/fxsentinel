import React, { useRef, useEffect } from 'react';
import { MARKET_CATALOG, getMarketQuote } from './marketCatalog';
import { resolveCurrencyIconLegs } from './marketCurrencyAssets';
import { getBundledMarketIcon } from './marketIcons';
import MarketSymbolIcon from './MarketSymbolIcon';
import {
  formatTickerPrice,
  formatTickerPercent,
  isTickerChangePositive,
} from '../../utils/tickerFormat';

/**
 * Horizontal scroll market selector — single line: icon · label · price · daily %
 */
function MarketPicker({ selectedId, onSelect, prices = {}, instruments = null, pricesLoading = false }) {
  const scrollRef = useRef(null);
  const chipRefs = useRef({});

  useEffect(() => {
    const el = chipRefs.current[selectedId];
    if (el && scrollRef.current) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }, [selectedId]);

  return (
    <nav className="markets-picker" aria-label="Select market">
      <div className="markets-picker__scroll" ref={scrollRef}>
        <div className="markets-picker__track" role="tablist">
          {MARKET_CATALOG.map((market) => {
            const isSelected = market.id === selectedId;
            const isDisabled = !market.enabled;
            const quote = getMarketQuote(market, prices, instruments);
            const isUp = quote ? isTickerChangePositive(quote.change, quote.changePercent) : true;
            const priceText = pricesLoading
              ? '…'
              : quote
                ? formatTickerPrice(quote.price, quote.decimals)
                : '—';
            const pctText = quote && !pricesLoading ? formatTickerPercent(quote.change, quote.price, quote.changePercent) : '';
            const toneClass = quote && !pricesLoading ? (isUp ? 'positive' : 'negative') : '';

            return (
              <button
                key={market.id}
                type="button"
                role="tab"
                ref={(node) => {
                  if (node) chipRefs.current[market.id] = node;
                }}
                aria-selected={isSelected}
                aria-disabled={isDisabled}
                aria-label={
                  quote && !pricesLoading
                    ? `${market.label}, ${priceText}, ${pctText}${isDisabled ? ', coming soon' : ''}`
                    : isDisabled
                      ? `${market.label}, coming soon`
                      : market.label
                }
                disabled={isDisabled}
                className={[
                  'markets-picker__chip',
                  isSelected ? 'markets-picker__chip--active' : '',
                  isDisabled ? 'markets-picker__chip--disabled' : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
                onClick={() => {
                  if (market.enabled) onSelect(market.id);
                }}
              >
                <MarketSymbolIcon
                  type={market.icon}
                  iconLegs={resolveCurrencyIconLegs(market.iconLegs)}
                  src={
                    market.iconLegs?.length
                      ? null
                      : getBundledMarketIcon(market.id) || market.iconPath || null
                  }
                  alt=""
                  className="markets-picker__icon"
                />
                <span className="markets-picker__label">{market.label}</span>
                <span className="markets-picker__sep" aria-hidden="true">
                  ·
                </span>
                <span className={`markets-picker__price ${toneClass}`}>{priceText}</span>
                {pctText && (
                  <>
                    <span className="markets-picker__sep" aria-hidden="true">
                      ·
                    </span>
                    <span className={`markets-picker__pct ${toneClass}`}>{pctText}</span>
                  </>
                )}
                {isDisabled && (
                  <>
                    <span className="markets-picker__sep" aria-hidden="true">
                      ·
                    </span>
                    <span className="markets-picker__soon">soon</span>
                  </>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

export default MarketPicker;
