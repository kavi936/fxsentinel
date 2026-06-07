import React, { useState } from 'react';

/**
 * Market mark for the picker chip.
 * Priority: `iconLegs` (FX pair from currency PNGs) → single `src` → built-in `type` fallback.
 */
function MarketSymbolIcon({ type, src, iconLegs, alt = '', className = '' }) {
  const [singleFailed, setSingleFailed] = useState(false);
  const cn = `markets-symbol-icon markets-symbol-icon--${type} ${className}`.trim();

  if (Array.isArray(iconLegs) && iconLegs.length >= 2) {
    return <PairIcon legs={iconLegs} alt={alt} className={`${cn} markets-symbol-icon--pair`} type={type} />;
  }

  const useImage = Boolean(src) && !singleFailed;
  if (useImage) {
    return (
      <span className={cn}>
        <img
          className="markets-symbol-icon__img"
          src={src}
          alt={alt}
          decoding="async"
          onError={() => setSingleFailed(true)}
        />
      </span>
    );
  }

  if (src && singleFailed) {
    return <BuiltInIcon type={type} className={cn} />;
  }

  return <BuiltInIcon type={type} className={cn} />;
}

function PairIcon({ legs, alt, className, type }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return <BuiltInIcon type={type} className={className.replace('markets-symbol-icon--pair', '').trim()} />;
  }

  return (
    <span className={className} role="img" aria-label={alt || 'Currency pair'}>
      {legs.slice(0, 2).map((legSrc, index) => (
        <img
          key={legSrc}
          className={`markets-symbol-icon__leg markets-symbol-icon__leg--${index === 0 ? 'base' : 'quote'}`}
          src={legSrc}
          alt=""
          decoding="async"
          onError={() => setFailed(true)}
        />
      ))}
    </span>
  );
}

function BuiltInIcon({ type, className }) {
  switch (type) {
    case 'btc':
      return (
        <span className={className} aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="16" fill="#F7931A" />
            <path
              d="M17.8 14.2c.9-.6 1.5-1.5 1.3-3.1-.2-1.8-1.5-2.5-3.2-2.6v-2.5h-1.3v2.4h-1.1v-2.4H12v2.5c-.3 0-.6.1-.9.1v.1l1.3.3c.7.2 1 .5 1.1 1.1v4.8c-.1.1-.2.1-.4.2-1 .3-1.4.9-1.3 2 .1 1.7 1.4 2.2 3.1 2.4v2.5h1.3v-2.5c.4 0 .8-.1 1.2-.1v2.6h1.3v-2.5c2.4-.4 4-1.5 3.8-3.8-.2-1.6-1.2-2.3-2.9-2.7zm-2.2-5.4c1.2.1 2.3.5 2.2 2-.1 1.3-1.1 1.7-2.2 1.8v-3.8zm-1.3 9.2v-4c1.4-.1 2.9-.5 2.9 2s-1.5 2-2.9 2z"
              fill="#fff"
            />
          </svg>
        </span>
      );

    case 'gold':
      return (
        <span className={className} aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="16" fill="#3d3520" />
            <rect x="9" y="13" width="14" height="8" rx="1.5" fill="url(#goldBarFallback)" />
            <path d="M11 13 L16 9 L21 13 Z" fill="#E8C547" />
            <defs>
              <linearGradient id="goldBarFallback" x1="9" y1="13" x2="23" y2="21">
                <stop stopColor="#F5D76E" />
                <stop offset="1" stopColor="#C9A227" />
              </linearGradient>
            </defs>
          </svg>
        </span>
      );

    case 'eurusd':
      return (
        <span className={className} aria-hidden="true">
          <span className="markets-symbol-icon__flags">
            <span className="markets-symbol-icon__flag">🇪🇺</span>
            <span className="markets-symbol-icon__flag">🇺🇸</span>
          </span>
        </span>
      );

    case 'usdjpy':
      return (
        <span className={className} aria-hidden="true">
          <span className="markets-symbol-icon__flags">
            <span className="markets-symbol-icon__flag">🇺🇸</span>
            <span className="markets-symbol-icon__flag">🇯🇵</span>
          </span>
        </span>
      );

    default:
      return (
        <span className={className} aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="16" fill="#2a2a2a" />
            <circle cx="16" cy="16" r="6" stroke="#666" strokeWidth="2" />
          </svg>
        </span>
      );
  }
}

export default MarketSymbolIcon;
