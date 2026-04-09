# Holistic Scan Quality Improvement Plan

## Scope
This document tracks known issues in the Economies `Holistic Scan` output and defines practical improvements.  
Goal: increase trustworthiness, interpretability, and consistency between model confidence and input quality.

---

## Current Problems (from recent UK scan review)

### 1) Confidence too high for stale inputs
- **Observed:** `90% confidence` while freshness shows about `21d` staleness.
- **Why this is a problem:** confidence should reflect uncertainty. Old data should reduce confidence.
- **Likely cause:** staleness penalty is too weak, or applied late after confidence is already clamped high.

### 2) Data quality label is too lenient
- **Observed:** quality shown as `FAIR` despite major staleness.
- **Why this is a problem:** users may underestimate model risk and over-trust old signals.
- **Likely cause:** quality grading prioritizes missing signals over recency.

### 3) Calendar stress can report 0 suspiciously often
- **Observed:** `Calendar stress: 0/100` for GBP in 14-day window.
- **Why this is a problem:** exact zero is possible but uncommon for major economies; may indicate filtering/parsing loss.
- **Likely cause:** currency mapping mismatch (`GBP` vs variants), impact field normalization, or date parsing window issues.

### 4) Freshness messaging is not source-specific
- **Observed:** output mentions `Live market inputs` and `Staleness: 21d` in same context.
- **Why this is a problem:** users may think yields are 21 days stale even if only macro indicators are stale.
- **Likely cause:** one staleness value is used for all input families.

### 5) Narrative can feel generic vs country-specific
- **Observed:** geopolitical block is broad and reusable.
- **Why this is a problem:** lower perceived relevance and weaker explanatory power for specific economy decisions.
- **Likely cause:** static overlay context dominates dynamic economy-linked narrative.

### 6) Bearish regime + hawkish repricing needs clearer causal bridge
- **Observed:** both are shown, but causal interpretation is not explicit.
- **Why this is a problem:** users can misread rising yields as always currency-bullish.
- **Likely cause:** output language does not clearly separate "policy tightening pressure" from "growth drag channel."

---

## Improvement Strategy

## Priority P0 (High impact, low complexity)

### A) Add hard confidence caps by staleness
- **Change:** impose max confidence when oldest core indicator is stale.
- **Suggested thresholds:**
  - `> 7d` -> max `80`
  - `> 14d` -> max `70`
  - `> 21d` -> max `60`
- **Reason:** confidence should never imply precision beyond data freshness.

### B) Upgrade quality grading logic
- **Change:** quality status should combine missing families + staleness.
- **Suggested policy:**
  - `GOOD`: staleness <= 7d and missing families = 0
  - `FAIR`: staleness <= 14d and missing families <= 1
  - `POOR`: staleness > 14d or missing families >= 2
- **Reason:** keeps quality label consistent with practical reliability.

### C) Separate freshness by input family in output
- **Change:** expose fields:
  - `indicator_staleness`
  - `yield_staleness`
  - `calendar_staleness`
- **Reason:** prevents confusion when one source is fresh and another is stale.

---

## Priority P1 (Important correctness hardening)

### D) Add calendar stress sanity checks
- **Change:** if major economy has zero high/medium events for 14 days, emit low-severity warning in metadata.
- **Reason:** catches silent data-shape regressions without blocking output.

### E) Add normalization audit logs (debug mode)
- **Change:** log counts before and after event filtering:
  - total events loaded
  - currency-matched events
  - impact-qualified events
  - date-window-qualified events
- **Reason:** makes it easy to diagnose why calendar stress collapses to zero.

### F) Improve narrative causality sentence
- **Change:** explicitly explain when hawkish repricing is FX-negative due to growth drag / financial-condition tightening.
- **Reason:** reduces interpretation errors for beginners.

---

## Priority P2 (Quality polish)

### G) Increase country specificity in geopolitical text
- **Change:** add economy-sensitive sentence templates (energy importer/exporter profile, CPI pass-through sensitivity, policy reaction bias).
- **Reason:** higher relevance and better educational value.

### H) Add reliability badge details in UI
- **Change:** show expandable "Why FAIR/POOR" details (staleness + missing families + low-event warning).
- **Reason:** transparent quality grading improves user trust.

---

## Implementation Plan (Suggested order)
1. Confidence caps + quality thresholds (P0 A/B).
2. Source-specific freshness fields in backend response and UI render (P0 C).
3. Calendar stress sanity checks + audit logging (P1 D/E).
4. Narrative bridge wording update (P1 F).
5. Country-specific geopolitical template enrichment (P2 G).
6. UI reliability detail panel (P2 H).

---

## Testing Plan

### Unit tests
- Confidence cap scenarios at staleness boundaries (7/14/21+ days).
- Quality status matrix tests (staleness x missing families).
- Calendar stress normalization tests using mixed date/impact/currency inputs.

### Integration tests
- End-to-end `/api/economy-scan/<country>` with:
  - fresh indicators
  - stale indicators
  - sparse events
  - empty events
- Assert confidence, quality label, and warnings are expected.

### UI checks
- Ensure new freshness fields render without layout regressions.
- Verify reliability explanation appears only when relevant.

---

## Acceptance Criteria
- Confidence cannot exceed cap for stale datasets.
- `FAIR/POOR` label changes in line with freshness thresholds.
- User can distinguish indicator vs yield vs calendar freshness.
- Calendar stress `0` includes explainable diagnostics.
- Narrative explicitly explains hawkish repricing + bearish FX cases.

