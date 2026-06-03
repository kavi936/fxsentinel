import React from 'react';

const EMPHASIS_RE = /\*\*(.+?)\*\*|\[\[([^\]]+)\]\]/g;
const EVIDENCE_CITE_RE = /(\[E\d+\])/gi;

/** Strip orphan ** when GPT or backend slicing leaves unbalanced markdown. */
function normalizeEmphasisInput(text) {
  const str = text == null ? '' : String(text);
  if (!str.includes('**')) return str;
  if (str.split('**').length % 2 === 0) {
    return str.replace(/\*\*/g, '');
  }
  return str;
}

function renderEmphasisSegment(str, { bracketEmphasis = true } = {}) {
  if (!str) return null;

  const nodes = [];
  let pos = 0;
  let key = 0;
  const re = bracketEmphasis ? EMPHASIS_RE : /\*\*(.+?)\*\*/g;

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

/**
 * Inline emphasis for trader analysis copy (calendar, live news, holistic scan).
 * - **double asterisks** → bold accent (.analysis-emphasis-bold)
 * - [[double brackets]] → secondary accent (.analysis-emphasis-bracket), optional
 * - [E1]…[En] → link to related coverage when evidenceMap is provided
 */
export function renderAnalysisEmphasis(text, { bracketEmphasis = true, evidenceMap = null } = {}) {
  const str = normalizeEmphasisInput(text);
  if (!str) return '';

  const hasEvidence =
    evidenceMap && typeof evidenceMap === 'object' && Object.keys(evidenceMap).length > 0;

  if (!hasEvidence) {
    return renderEmphasisSegment(str, { bracketEmphasis });
  }

  const parts = str.split(EVIDENCE_CITE_RE).filter((p) => p !== '');
  if (parts.length <= 1) {
    return renderEmphasisSegment(str, { bracketEmphasis });
  }

  return parts.map((part, i) => {
    const citeMatch = part.match(/^\[E(\d+)\]$/i);
    if (citeMatch) {
      const eid = `E${citeMatch[1]}`;
      const ev = evidenceMap[eid];
      const href = ev?.url || `#source-${eid}`;
      const title = ev?.headline ? `${ev.headline}${ev.publisher ? ` — ${ev.publisher}` : ''}` : eid;
      return (
        <a
          key={`cite-${i}-${eid}`}
          href={href}
          className="analysis-evidence-cite"
          title={title}
          {...(ev?.url
            ? { target: '_blank', rel: 'noopener noreferrer' }
            : {})}
        >
          [{eid}]
        </a>
      );
    }
    return <span key={`seg-${i}`}>{renderEmphasisSegment(part, { bracketEmphasis })}</span>;
  });
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
