/** Helpers for live-news Gemini grounding UX (loading + sources footer). */

export const LIVE_NEWS_LOADING_STEPS = {
  grounding: [
    'Searching the web for related coverage…',
    'Checking credible publishers for corroboration…',
    'Building a related-headlines summary…',
  ],
  analyzing: [
    'Loading live market context…',
    'Applying your trading profile…',
    'Writing trader-facing analysis…',
  ],
  skipped: [
    'Preparing headline and market context…',
    'Writing trader-facing analysis…',
  ],
};

export function groundingStatusLabel(pack) {
  const status = pack?.quality?.status;
  if (!status || status === 'skipped') return null;
  if (status === 'failed') return 'Web search unavailable — continuing with headline only';
  const count = pack?.quality?.evidence_count ?? 0;
  if (count === 0) return 'No extra related coverage found';
  return `${count} related source${count === 1 ? '' : 's'} found`;
}

export function hasDisplayableGrounding(pack) {
  const status = pack?.quality?.status;
  if (!status || status === 'skipped' || status === 'failed') return false;
  const bullets = pack?.synthesis_bullets || [];
  const evidence = pack?.evidence || [];
  return bullets.length > 0 || evidence.length > 0;
}

export function buildEvidenceCitationMap(pack) {
  const map = {};
  if (!pack?.evidence) return map;
  for (const ev of pack.evidence) {
    const id = ev?.id;
    if (!id || typeof id !== 'string') continue;
    map[id.toUpperCase()] = {
      headline: ev.headline || ev.publisher || id,
      publisher: ev.publisher || ev.source || '',
      url: ev.url || '',
      relationship: ev.relationship || 'background',
    };
  }
  return map;
}

export function relationshipDisplayLabel(rel) {
  const labels = {
    corroborates: 'Corroborates',
    contradicts: 'Contradicts',
    background: 'Background',
    market_reaction: 'Market reaction',
  };
  return labels[rel] || rel || 'Background';
}
