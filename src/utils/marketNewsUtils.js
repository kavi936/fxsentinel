import { formatNewsTime, getUserTimezone } from './timezoneUtils';

const HIGH_IMPACT_HINTS = [
  'breaking',
  'etf',
  'sec ',
  'fed ',
  'rate cut',
  'rate hike',
  'halving',
  'liquidation',
  'crash',
  'surge',
  'record',
];

export function normalizeImpactLevel(impact) {
  const value = String(impact || '').toLowerCase().trim();
  if (!value) return null;
  if (value.includes('high') || value === 'critical' || value === 'h') return 'high';
  if (value.includes('medium') || value === 'med' || value === 'm') return 'medium';
  if (value.includes('low') || value === 'l') return 'low';
  return null;
}

export function getMarketNewsImpact(item) {
  const explicit =
    normalizeImpactLevel(item?.impact) ||
    normalizeImpactLevel(item?.impact_level) ||
    normalizeImpactLevel(item?.analysis_summary?.impact);

  if (explicit) return explicit;

  const text = `${item?.title || ''} ${item?.summary || ''}`.toLowerCase();
  if (HIGH_IMPACT_HINTS.some((hint) => text.includes(hint))) return 'high';
  return 'medium';
}

export function getImpactLabel(impact) {
  switch (String(impact || '').toLowerCase()) {
    case 'high':
      return 'High';
    case 'medium':
      return 'Medium';
    case 'low':
      return 'Low';
    default:
      return 'Low';
  }
}

const TITLE_PREFIXES = [
  '**JUST IN:**',
  '**BREAKING:**',
  '**UPDATE:**',
  '**LIVE:**',
  '**URGENT:**',
  'JUST IN:',
  'BREAKING:',
  'UPDATE:',
  'LIVE:',
  'URGENT:',
];

export function cleanNewsTitle(title) {
  if (!title) return '';
  let cleaned = title.trim();
  for (const prefix of TITLE_PREFIXES) {
    if (cleaned.toUpperCase().startsWith(prefix.replace(/\*/g, ''))) {
      cleaned = cleaned.slice(prefix.replace(/\*/g, '').length).trim();
    }
    if (cleaned.startsWith(prefix)) {
      cleaned = cleaned.slice(prefix.length).trim();
    }
  }
  return cleaned;
}

export function formatMarketNewsTime(timestamp) {
  if (!timestamp) return 'Recently';
  return formatNewsTime(timestamp, getUserTimezone());
}

export function truncateSummary(text, maxLen = 120) {
  if (!text) return '';
  const trimmed = text.trim();
  if (trimmed.length <= maxLen) return trimmed;
  return `${trimmed.slice(0, maxLen).trim()}…`;
}
