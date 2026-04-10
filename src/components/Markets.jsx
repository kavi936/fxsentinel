import React from 'react';
import './Markets.css';

/**
 * Markets tab — coming soon: focused market analysis (macro, fundamentals, intraday & longer horizon)
 * using FXSentinel data. Replace overlay when features ship.
 */
function Markets() {
  return (
    <div className="markets-tab">
      <div className="markets-coming-bg" aria-hidden="true">
        <div className="markets-coming-gradient" />
        <div className="markets-coming-orb markets-coming-orb--a" />
        <div className="markets-coming-orb markets-coming-orb--b" />
        <div className="markets-coming-orb markets-coming-orb--c" />
        <div className="markets-coming-grid" />
      </div>

      <div className="markets-coming-inner">
        <p className="markets-coming-badge">Coming soon</p>
        <h1 className="markets-coming-title">Markets</h1>
        <p className="markets-coming-lead">
          Deep, market-specific analysis powered by the same macro and fundamental data that drives
          FXSentinel — built for both intraday reactions and longer-term positioning.
        </p>
        <p className="markets-coming-sub">
          Expect targeted breakdowns that tie together economics, policy, and cross-asset context so
          you can see how the narrative lines up with price — not generic commentary.
        </p>
      </div>
    </div>
  );
}

export default Markets;
