import React from 'react';

/**
 * Split plain headline on emphasis phrases (longest first) for red highlights.
 */
function buildHeadlineParts(headline, emphasisPhrases) {
  if (!headline) return [];
  const phrases = (emphasisPhrases || [])
    .filter(Boolean)
    .sort((a, b) => b.length - a.length);

  if (phrases.length === 0) {
    return [{ text: headline, emphasis: false }];
  }

  let parts = [{ text: headline, emphasis: false }];

  for (const phrase of phrases) {
    const next = [];
    const needle = phrase.toLowerCase();

    for (const part of parts) {
      if (part.emphasis) {
        next.push(part);
        continue;
      }

      const source = part.text;
      const lower = source.toLowerCase();
      let cursor = 0;
      let idx = lower.indexOf(needle, cursor);

      if (idx === -1) {
        next.push(part);
        continue;
      }

      while (idx !== -1) {
        if (idx > cursor) {
          next.push({ text: source.slice(cursor, idx), emphasis: false });
        }
        next.push({
          text: source.slice(idx, idx + phrase.length),
          emphasis: true,
        });
        cursor = idx + phrase.length;
        idx = lower.indexOf(needle, cursor);
      }

      if (cursor < source.length) {
        next.push({ text: source.slice(cursor), emphasis: false });
      }
    }

    parts = next;
  }

  return parts;
}

/**
 * One-line market headline — Sen/header typography, red emphasis on key phrases.
 */
function MarketHeadline({ headline, emphasis = [], segments = null, id = 'markets-headline' }) {
  if (!headline && !segments?.length) return null;

  if (Array.isArray(segments) && segments.length > 0) {
    return (
      <h2 id={id} className="markets-headline">
        {segments.map((seg, i) =>
          seg.emphasis ? (
            <span key={i} className="markets-headline__emphasis">
              {seg.text ?? seg.t}
            </span>
          ) : (
            <span key={i}>{seg.text ?? seg.t}</span>
          )
        )}
      </h2>
    );
  }

  const parts = buildHeadlineParts(headline, emphasis);

  return (
    <h2 id={id} className="markets-headline">
      {parts.map((part, i) =>
        part.emphasis ? (
          <span key={i} className="markets-headline__emphasis">
            {part.text}
          </span>
        ) : (
          <span key={i}>{part.text}</span>
        )
      )}
    </h2>
  );
}

export default MarketHeadline;
