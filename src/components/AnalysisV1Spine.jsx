import React from 'react';
import { sanitizeText } from '../utils/sanitize';
import './AnalysisV1Spine.css';

/**
 * Unified V1 “spine” block (see AI_ANALYSIS_V1_UNIFIED_SPEC.md).
 * Renders only when backend sends analysis_format_version + spine.
 */
function renderBoldSegments(raw) {
  const clean = sanitizeText(String(raw ?? ''));
  if (!clean) return null;
  const parts = clean.split('**');
  if (parts.length === 1) return clean;
  return parts.map((segment, i) =>
    i % 2 === 1 ? (
      <strong key={`b-${i}`} className="analysis-v1-spine__strong">
        {segment}
      </strong>
    ) : (
      <React.Fragment key={`t-${i}`}>{segment}</React.Fragment>
    )
  );
}

export default function AnalysisV1Spine({ spine, scenarioWarnings, className = '' }) {
  if (!spine || typeof spine !== 'object') return null;

  const bias = String(spine.bias || 'neutral').toLowerCase();
  const biasClass =
    bias === 'bullish' ? 'analysis-v1-spine__bias--bullish' : bias === 'bearish' ? 'analysis-v1-spine__bias--bearish' : 'analysis-v1-spine__bias--neutral';

  const instruments = Array.isArray(spine.primary_instruments) ? spine.primary_instruments : [];
  const warnings = Array.isArray(scenarioWarnings) ? scenarioWarnings : [];

  return (
    <section
      className={`analysis-v1-spine ${className}`.trim()}
      role="region"
      aria-label="Analysis summary"
      data-analysis-v1-spine
    >
      <div className="analysis-v1-spine__header">
        <span className="analysis-v1-spine__badge">Analysis brief</span>
      </div>
      <p className="analysis-v1-spine__summary">{renderBoldSegments(spine.summary_line)}</p>
      <div className="analysis-v1-spine__grid">
        <div className="analysis-v1-spine__cell">
          <span className="analysis-v1-spine__label">Bias</span>
          <span className={`analysis-v1-spine__bias ${biasClass}`}>{sanitizeText(String(spine.bias || 'neutral'))}</span>
          <span className="analysis-v1-spine__subject">{renderBoldSegments(spine.bias_subject)}</span>
        </div>
        <div className="analysis-v1-spine__cell">
          <span className="analysis-v1-spine__label">Horizon</span>
          <span className="analysis-v1-spine__value">{sanitizeText(String(spine.time_horizon || '—'))}</span>
        </div>
        <div className="analysis-v1-spine__cell">
          <span className="analysis-v1-spine__label">Confidence</span>
          <span className="analysis-v1-spine__value">
            {typeof spine.confidence === 'number' ? `${spine.confidence}%` : sanitizeText(String(spine.confidence ?? '—'))}
          </span>
          {spine.confidence_reason ? (
            <span className="analysis-v1-spine__reason">{renderBoldSegments(spine.confidence_reason)}</span>
          ) : null}
        </div>
        <div className="analysis-v1-spine__cell analysis-v1-spine__cell--wide">
          <span className="analysis-v1-spine__label">Invalidation</span>
          <span className="analysis-v1-spine__value analysis-v1-spine__value--multiline">
            {renderBoldSegments(spine.invalidation)}
          </span>
        </div>
        {instruments.length > 0 ? (
          <div className="analysis-v1-spine__cell analysis-v1-spine__cell--wide">
            <span className="analysis-v1-spine__label">Focus</span>
            <span className="analysis-v1-spine__instruments">{instruments.map((p) => sanitizeText(String(p))).join(' · ')}</span>
          </div>
        ) : null}
      </div>
      {warnings.length > 0 ? (
        <ul className="analysis-v1-spine__warnings">
          {warnings.map((w, idx) => (
            <li key={idx}>{sanitizeText(String(w))}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
