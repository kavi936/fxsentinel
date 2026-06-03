import React, { useEffect, useState, useRef } from 'react';
import {
  LIVE_NEWS_LOADING_STEPS,
  groundingStatusLabel,
  hasDisplayableGrounding,
} from '../utils/liveNewsGrounding';

/**
 * Staged loading for live-news analysis: grounding preview then GPT phase.
 * @param {'grounding'|'analyzing'} phase
 * @param {object|null} groundingPreview - related_evidence pack from step 1
 */
export default function LiveNewsAnalysisLoading({ phase, groundingPreview }) {
  const [fakeProgress, setFakeProgress] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);
  const progressRef = useRef(null);
  const stepRef = useRef(null);

  const groundingSkipped =
    !groundingPreview ||
    groundingPreview?.quality?.status === 'skipped' ||
    groundingPreview?.quality?.status === 'failed';

  const steps =
    phase === 'grounding' && groundingSkipped
      ? LIVE_NEWS_LOADING_STEPS.skipped
      : LIVE_NEWS_LOADING_STEPS[phase] || LIVE_NEWS_LOADING_STEPS.analyzing;

  const showPreview = hasDisplayableGrounding(groundingPreview);

  useEffect(() => {
    setFakeProgress(0);
    setStepIndex(0);
    if (stepRef.current) clearInterval(stepRef.current);
    if (progressRef.current) clearInterval(progressRef.current);

    stepRef.current = setInterval(() => {
      setStepIndex((i) => (i + 1) % steps.length);
    }, 2800);

    progressRef.current = setInterval(() => {
      setFakeProgress((prev) => {
        if (prev >= 96) return prev;
        const delta = prev < 50 ? Math.random() * 6 + 2 : Math.random() * 2 + 0.5;
        return Math.min(96, +(prev + delta).toFixed(1));
      });
    }, 650);

    return () => {
      if (stepRef.current) clearInterval(stepRef.current);
      if (progressRef.current) clearInterval(progressRef.current);
    };
  }, [phase, steps.length]);

  const statusLabel = groundingStatusLabel(groundingPreview);
  const arc = groundingPreview?.story_context?.story_arc;
  const bullets = (groundingPreview?.synthesis_bullets || []).slice(0, 3);
  const queries = groundingPreview?.query?.search_queries_used || [];

  return (
    <div className="lna-loading" onClick={(e) => e.stopPropagation()}>
      <div className="lna-loading-spinner" aria-hidden="true" />
      <p className="lna-loading-phase-label">
        {phase === 'grounding' ? 'Step 1 of 2 — Related coverage' : 'Step 2 of 2 — AI analysis'}
      </p>
      <p className="lna-loading-step">{steps[stepIndex]}</p>
      <p className="lna-loading-hint">Typically 25–45 seconds for a full analysis.</p>

      <div className="lna-loading-progress-wrap">
        <div
          className="lna-loading-progress-track"
          role="progressbar"
          aria-valuenow={Math.round(fakeProgress)}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div className="lna-loading-progress-fill" style={{ width: `${fakeProgress}%` }} />
        </div>
        <span className="lna-loading-progress-label">{Math.round(fakeProgress)}%</span>
      </div>

      {phase === 'grounding' && queries.length > 0 && (
        <p className="lna-loading-search-query" title={queries.join('; ')}>
          Search: {queries[0]}
          {queries.length > 1 ? ` (+${queries.length - 1} more)` : ''}
        </p>
      )}

      {showPreview && (
        <div className="lna-grounding-preview">
          <p className="lna-grounding-preview-title">
            {statusLabel}
            {arc && arc !== 'unclear' ? ` · ${arc.replace(/_/g, ' ')}` : ''}
          </p>
          <ul className="lna-grounding-preview-bullets">
            {bullets.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}

      {phase === 'grounding' && groundingPreview?.quality?.status === 'failed' && (
        <p className="lna-loading-fallback-note">{statusLabel}</p>
      )}
    </div>
  );
}
