/**
 * V1 analysis brief (spine) UI — default off to match legacy product experience.
 * Set VITE_ANALYSIS_V1_ENABLED=true in .env when reviewing spine work.
 */
const truthy = (value) => ['1', 'true', 'yes', 'on'].includes(String(value ?? '').trim().toLowerCase());

export const isAnalysisV1UiEnabled = () => truthy(import.meta.env.VITE_ANALYSIS_V1_ENABLED);
