import React from 'react';

const EMPHASIS_RE = /\*\*(.+?)\*\*|\[\[([^\]]+)\]\]/g;

/**
 * Inline emphasis for trader analysis copy (calendar, live news, holistic scan).
 * - **double asterisks** → bold accent (.analysis-emphasis-bold)
 * - [[double brackets]] → secondary accent (.analysis-emphasis-bracket), optional
 */
export function renderAnalysisEmphasis(text, { bracketEmphasis = true } = {}) {
  const str = text == null ? '' : String(text);
  if (!str) return '';

  const nodes = [];
  let pos = 0;
  let key = 0;
  const re = bracketEmphasis
    ? EMPHASIS_RE
    : /\*\*(.+?)\*\*/g;

  let m;
  while ((m = re.exec(str)) !== null) {
    if (m.index > pos) {
      nodes.push(<span key={`t-${key++}`}>{str.slice(pos, m.index)}</span>);
    }
    if (m[1] !== undefined) {
      nodes.push(
        <strong key={`b-${key++}`} className="analysis-emphasis-bold">
          {m[1]}
        </strong>
      );
    } else if (bracketEmphasis && m[2] !== undefined) {
      nodes.push(
        <span key={`e-${key++}`} className="analysis-emphasis-bracket">
          {m[2]}
        </span>
      );
    }
    pos = m.index + m[0].length;
  }

  if (pos < str.length) {
    nodes.push(<span key={`t-${key++}`}>{str.slice(pos)}</span>);
  }

  return nodes.length > 0 ? nodes : str;
}

export function renderAnalysisEmphasisLines(text, options) {
  const lines = String(text ?? '').split('\n');
  return lines.flatMap((line, i) => {
    const n = renderAnalysisEmphasis(line, options);
    if (i === 0) return [n];
    return [<br key={`nl-${i}`} />, n];
  });
}

export function FormattedAnalysisParagraph({ text, className, options }) {
  const raw = String(text ?? '');
  if (!raw.trim()) return null;
  const blocks = raw.split(/\n\n+/).filter((b) => b.trim());
  if (blocks.length === 0) return null;
  return (
    <>
      {blocks.map((block, i) => (
        <p key={i} className={className}>
          {renderAnalysisEmphasisLines(block, options)}
        </p>
      ))}
    </>
  );
}

export function FormattedAnalysisBlock({ text, className, as: Component = 'div', options }) {
  const raw = String(text ?? '');
  if (!raw.trim()) return null;
  const blocks = raw.split(/\n\n+/).filter((b) => b.trim());
  if (blocks.length === 0) return null;
  return (
    <>
      {blocks.map((block, i) => (
        <Component key={i} className={className}>
          {renderAnalysisEmphasisLines(block, options)}
        </Component>
      ))}
    </>
  );
}

/** @deprecated Use renderAnalysisEmphasis — kept for Economies import alias */
export const renderInlineScanFormatting = renderAnalysisEmphasis;

/** @deprecated Use FormattedAnalysisParagraph */
export const FormattedScanParagraph = FormattedAnalysisParagraph;

/** @deprecated Use FormattedAnalysisBlock */
export const FormattedScanBlock = FormattedAnalysisBlock;
