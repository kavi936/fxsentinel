import React from 'react';
import { relationshipDisplayLabel } from '../utils/liveNewsGrounding';

/**
 * Sources footer from related_evidence pack (deterministic — not GPT prose).
 * Uses the same lna-section / inner-card patterns as Market Impact, Risk assessment, etc.
 */
export default function RelatedCoverageSection({ relatedEvidence }) {
  const pack = relatedEvidence;
  if (!pack) return null;

  const status = pack?.quality?.status;
  if (!status || status === 'skipped') return null;

  const evidence = pack.evidence || [];

  if (evidence.length === 0 && status === 'failed') {
    return (
      <div className="lna-section lna-related-coverage lna-related-coverage--empty">
        <h5>Related coverage</h5>
        <p className="lna-related-coverage-note">
          Web search was unavailable for this analysis. Claims are based on the headline and live
          market data only.
        </p>
      </div>
    );
  }

  if (evidence.length === 0) return null;

  const searchCount = pack?.quality?.search_query_count;

  return (
    <div className="lna-section lna-related-coverage">
      <h5>Related coverage</h5>
      <p className="lna-related-coverage-note">
        Sources found via web search before analysis
        {searchCount ? ` (${searchCount} search${searchCount === 1 ? '' : 'es'})` : ''}.
        Cited in the text above as [E1], [E2], …
        {evidence.length > 3 ? ' Scroll the list below for all sources.' : ''}
      </p>
      <div className="lna-related-coverage-scroll" role="region" aria-label="Related coverage sources">
        <ul className="lna-related-coverage-list">
        {evidence.map((ev) => {
          const eid = ev.id || '';
          const headline = ev.headline || ev.publisher || 'Related article';
          const publisher = ev.publisher || ev.source || '';
          const url = ev.url || '';
          const relKey = (ev.relationship || 'background').toLowerCase();
          const rel = relationshipDisplayLabel(ev.relationship);
          const recency =
            ev.recency_bucket && ev.recency_bucket !== 'unknown'
              ? ev.recency_bucket.replace(/_/g, ' ')
              : null;

          return (
            <li key={eid} id={`source-${eid}`} className="lna-related-coverage-card">
              <div className="lna-related-coverage-card-top">
                <span className="lna-related-coverage-id">[{eid}]</span>
                {url ? (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="lna-related-coverage-headline lna-related-coverage-headline--link"
                  >
                    {headline}
                  </a>
                ) : (
                  <span className="lna-related-coverage-headline">{headline}</span>
                )}
              </div>
              <div className="lna-related-coverage-card-foot">
                {publisher ? (
                  <span className="lna-related-coverage-publisher">{publisher}</span>
                ) : null}
                <span className={`lna-related-coverage-rel lna-rel-${relKey}`}>{rel}</span>
                {recency ? (
                  <span className="lna-related-coverage-recency">{recency}</span>
                ) : null}
              </div>
            </li>
          );
        })}
        </ul>
      </div>
    </div>
  );
}
