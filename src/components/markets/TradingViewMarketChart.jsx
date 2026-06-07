import React, { useEffect, useRef, memo } from 'react';

const WIDGET_SCRIPT = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
/** Space for the in-flow copyright row (TradingView embed uses ~32px). */
const COPYRIGHT_HEIGHT_PX = 32;

/**
 * TradingView advanced chart — height follows the official embed pattern:
 * - Parent chain must supply a real height (flex column or min-height on chart area).
 * - Container: height 100%
 * - Widget host: calc(100% - COPYRIGHT) — autosize reads this element.
 */
function TradingViewMarketChart({ symbol, interval = '240' }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !symbol) return undefined;

    container.querySelectorAll('script[src*="tradingview.com"]').forEach((el) => el.remove());

    const script = document.createElement('script');
    script.src = WIDGET_SCRIPT;
    script.type = 'text/javascript';
    script.async = true;
    script.innerHTML = JSON.stringify({
      allow_symbol_change: false,
      calendar: false,
      details: false,
      hide_side_toolbar: true,
      hide_top_toolbar: false,
      hide_legend: true,
      hide_volume: false,
      hotlist: false,
      interval,
      locale: 'en',
      save_image: false,
      style: '1',
      symbol,
      theme: 'dark',
      timezone: 'Etc/UTC',
      backgroundColor: '#000000',
      gridColor: 'rgba(255, 255, 255, 0.06)',
      watchlist: [],
      withdateranges: true,
      compareSymbols: [],
      show_popup_button: true,
      popup_height: '650',
      popup_width: '1000',
      studies: [],
      autosize: true,
    });

    container.appendChild(script);

    return () => {
      script.remove();
    };
  }, [symbol, interval]);

  if (!symbol) {
    return (
      <div className="markets-tv-chart markets-tv-chart--empty" aria-label="Chart unavailable">
        <p>Chart symbol not configured.</p>
      </div>
    );
  }

  const symbolPath = symbol.replace(':', '-');
  const widgetHeight = `calc(100% - ${COPYRIGHT_HEIGHT_PX}px)`;

  return (
    <div
      className="markets-tv-chart tradingview-widget-container"
      ref={containerRef}
      style={{ height: '100%', width: '100%' }}
      aria-label={`${symbol} TradingView chart`}
    >
      <div
        className="tradingview-widget-container__widget"
        style={{ height: widgetHeight, width: '100%' }}
      />
      <div className="tradingview-widget-copyright markets-tv-chart__copyright">
        <a
          href={`https://www.tradingview.com/symbols/${symbolPath}/`}
          rel="noopener nofollow"
          target="_blank"
        >
          <span className="blue-text">{symbol}</span>
        </a>
        <span className="trademark"> · TradingView</span>
      </div>
    </div>
  );
}

export default memo(TradingViewMarketChart);
