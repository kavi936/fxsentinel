/**
 * Shared rules for email/password accounts. Signup enforces these client-side;
 * Firebase also applies its own minimum (6) — we stay stricter for UX consistency.
 */
export const PASSWORD_MIN_LENGTH = 12;

/** Characters we accept as "special" for password rules (common keyboard symbols). */
const SPECIAL_RE = /[!@#$%^&*()_+\-=[\]{}|;:,.<>?/\\`~'"]/;

/**
 * @returns {Record<string, boolean>}
 */
export function getPasswordRuleStatus(password) {
  return {
    minLength: password.length >= PASSWORD_MIN_LENGTH,
    hasUpper: /[A-Z]/.test(password),
    hasLower: /[a-z]/.test(password),
    hasDigit: /\d/.test(password),
    hasSpecial: SPECIAL_RE.test(password),
  };
}

export function isPasswordCompliant(password) {
  const s = getPasswordRuleStatus(password);
  return Object.values(s).every(Boolean);
}

/** For the strength banner: weak / medium / strong based on how many rules pass. */
export function getPasswordStrengthTier(password) {
  if (!password) return '';
  const s = getPasswordRuleStatus(password);
  const passed = Object.values(s).filter(Boolean).length;
  if (passed <= 2) return 'weak';
  if (passed < 5) return 'medium';
  return 'strong';
}
