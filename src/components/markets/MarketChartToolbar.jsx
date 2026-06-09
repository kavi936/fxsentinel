import React, { useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

function ChevronDownIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
      <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function LayersIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M12 2L2 7l10 5 10-5-10-5z" strokeLinejoin="round" />
      <path d="M2 17l10 5 10-5" strokeLinejoin="round" />
      <path d="M2 12l10 5 10-5" strokeLinejoin="round" />
    </svg>
  );
}

function useDismissMenu(open, onClose, controlsRef, overlayRef) {
  useEffect(() => {
    if (!open) return undefined;

    const onPointerDown = (event) => {
      if (controlsRef.current?.contains(event.target)) return;
      if (overlayRef.current?.contains(event.target)) return;
      onClose();
    };

    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };

    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open, onClose, controlsRef, overlayRef]);
}

/**
 * Compact chart controls — timeframe pill + layers icon; menus overlay the chart pane.
 */
function MarketChartToolbar({
  paneRef,
  timeframes,
  timeframe,
  onTimeframeChange,
  layers,
  layerOptions,
  onLayerToggle,
  liveQuote,
  quoteLoading,
  liveTone,
  quoteLabel,
  formatTickerPrice,
  formatTickerPercent,
}) {
  const wrapRef = useRef(null);
  const overlayRef = useRef(null);
  const [openMenu, setOpenMenu] = React.useState(null);

  const closeMenu = useCallback(() => setOpenMenu(null), []);
  useDismissMenu(Boolean(openMenu), closeMenu, wrapRef, overlayRef);

  const activeLayerCount = layerOptions.filter(({ id }) => layers[id]).length;
  const tfLabel = timeframes.find((tf) => tf.id === timeframe)?.label || timeframe;

  const overlayMenu =
    openMenu && paneRef?.current
      ? createPortal(
          <div
            ref={overlayRef}
            className="markets-research-chart__overlay-menu"
            role={openMenu === 'timeframe' ? 'listbox' : 'menu'}
            aria-label={openMenu === 'timeframe' ? 'Select timeframe' : 'Toggle chart overlays'}
          >
            {openMenu === 'timeframe'
              ? timeframes.map((tf) => (
                  <button
                    key={tf.id}
                    type="button"
                    role="option"
                    aria-selected={timeframe === tf.id}
                    className={`markets-research-chart__overlay-item ${
                      timeframe === tf.id ? 'is-selected' : ''
                    }`}
                    onClick={() => {
                      onTimeframeChange(tf.id);
                      closeMenu();
                    }}
                  >
                    {tf.label}
                  </button>
                ))
              : layerOptions.map(({ id, label }) => (
                  <label key={id} className="markets-research-chart__overlay-check" role="menuitemcheckbox">
                    <input
                      type="checkbox"
                      checked={Boolean(layers[id])}
                      onChange={() => onLayerToggle(id)}
                    />
                    <span>{label}</span>
                  </label>
                ))}
          </div>,
          paneRef.current
        )
      : null;

  return (
    <>
      <div className="markets-research-chart__toolbar" role="toolbar" aria-label="Chart controls">
        <div className="markets-research-chart__toolbar-controls" ref={wrapRef}>
          <button
            type="button"
            className={`markets-research-chart__menu-trigger ${openMenu === 'timeframe' ? 'is-open' : ''}`}
            aria-expanded={openMenu === 'timeframe'}
            aria-haspopup="listbox"
            aria-label={`Timeframe, ${tfLabel}`}
            onClick={() => setOpenMenu((prev) => (prev === 'timeframe' ? null : 'timeframe'))}
          >
            <span className="markets-research-chart__menu-trigger-label">{tfLabel}</span>
            <ChevronDownIcon />
          </button>

          <button
            type="button"
            className={`markets-research-chart__menu-trigger markets-research-chart__menu-trigger--icon ${
              openMenu === 'layers' ? 'is-open' : ''
            }`}
            aria-expanded={openMenu === 'layers'}
            aria-haspopup="menu"
            aria-label={`Chart overlays, ${activeLayerCount} of ${layerOptions.length} visible`}
            onClick={() => setOpenMenu((prev) => (prev === 'layers' ? null : 'layers'))}
          >
            <LayersIcon />
            {activeLayerCount < layerOptions.length ? (
              <span className="markets-research-chart__menu-badge" aria-hidden="true">
                {activeLayerCount}
              </span>
            ) : null}
          </button>
        </div>

        <div className="markets-research-chart__live-quote" aria-live="polite">
          {quoteLoading && !liveQuote?.price ? (
            <span className="markets-research-chart__live-quote-loading">Live…</span>
          ) : liveQuote?.price != null ? (
            <>
              <span className="markets-research-chart__live-quote-label">{quoteLabel}</span>
              <span className={`markets-research-chart__live-quote-price ${liveTone}`}>
                {formatTickerPrice(liveQuote.price, 2)}
              </span>
              <span className={`markets-research-chart__live-quote-pct ${liveTone}`}>
                {formatTickerPercent(liveQuote.change, liveQuote.price, liveQuote.changePercent)}
              </span>
            </>
          ) : null}
        </div>
      </div>
      {overlayMenu}
    </>
  );
}

export default MarketChartToolbar;
