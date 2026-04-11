/** Must match backend PRIMARY_GOALS in user_trader_profile.py */
export const PRIMARY_GOALS = [
  {
    value: 'stay_informed',
    label: 'Stay on top of news & calendar',
    hint: 'Headlines, events, and context in one place',
  },
  {
    value: 'analysis_workflow',
    label: 'Stronger analysis workflow',
    hint: 'Structure how I research before and after releases',
  },
  {
    value: 'alerts',
    label: 'Timely alerts',
    hint: 'Know when something important hits my markets',
  },
  {
    value: 'learning',
    label: 'Learn macro & context',
    hint: 'Deeper understanding, not just prices',
  },
  {
    value: 'other',
    label: 'Something else',
    hint: 'We will still personalize your workspace',
  },
];

/** Must match backend REFERRAL_SOURCES in user_trader_profile.py */
export const REFERRAL_SOURCES = [
  { value: 'search', label: 'Google / search' },
  { value: 'social_x', label: 'X (Twitter)' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'discord', label: 'Discord' },
  { value: 'reddit', label: 'Reddit' },
  { value: 'friend', label: 'Friend or colleague' },
  { value: 'blog_news', label: 'Blog or news site' },
  { value: 'podcast', label: 'Podcast' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_say', label: 'Prefer not to say' },
];

export function labelForPrimaryGoal(value) {
  return PRIMARY_GOALS.find((x) => x.value === value)?.label ?? value ?? '—';
}

export function labelForReferralSource(value) {
  return REFERRAL_SOURCES.find((x) => x.value === value)?.label ?? value ?? '—';
}
