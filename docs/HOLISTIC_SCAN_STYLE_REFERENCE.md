# Holistic Scan Style Reference (for Overview Transfer)

## Purpose
Manual reference for transferring the Holistic Scan visual language from `Economies` to `Overview` (`ai-analysis-content`) without breaking behavior.

This captures:
- visual tokens (color, borders, spacing)
- typography hierarchy
- emphasis rules (red-based importance)
- reusable UI patterns

---

## Source of Truth
- Component markup: `src/components/Economies.jsx` (Holistic Scan ready-state block)
- Styling: `src/components/Economies.css` (`scan-*` and `holistic-*` classes)

---

## Brand Direction (Current)
- Primary brand accent: red (`#da0012` family)
- Important/subtitle cues: red-pink (`#ff6b74`, `#ff7d85`)
- Surface palette: black/charcoal base with subtle white overlays
- Border language: red-tinted translucent borders (not neutral gray)

---

## Core Container + Scroll Pattern

### Fixed-height scan viewport
- Class: `.holistic-scan-scroll-shell`
- Intent:
  - fixed-height analysis panel
  - left-side scrollbar
  - always-scroll affordance
  - bottom fog cue for overflow awareness

### Key behavior
- `overflow-y: scroll`
- `direction: rtl` on shell, `direction: ltr` on inner content
- rounded corners (`border-radius: 12px`)
- custom scrollbar track/thumb (red thumb)

### Overflow cue (fog)
- Class: `.holistic-scan-scroll-shell::after`
- Dark gray bottom gradient signaling more content below

---

## Typography System (Holistic Scan)

### Top headings
- `.analysis-title`
  - uppercase
  - compact tracking
  - neutral light color

### Section headers (important)
- `.scan-section-title`
  - uppercase
  - red title color (`#ff6b74`)
  - thin red divider line below

### Sub-labels (important metadata labels)
- `.scan-card-label`
- `.scan-yield-label`
- `.scan-regime-metric-label`
  - all red-pink label color (`#ff7d85`)
  - uppercase, small text, wider tracking

### Body/meta
- `.scan-meta-large` (main descriptive text block)
- `.scan-meta`, `.scan-paragraph`, `.scan-paragraph-metadata` (supporting text)

---

## Emphasis Rules (Important)

Current direction: important text is signaled by color, not only bold.

### Inline emphasis from content parser
- `.scan-text-strong`
  - red emphasis color (`#ff6b74`)
  - medium-bold weight (not too heavy)
- `.scan-inline-emphasis`
  - lighter red tone (`#ff848c`)

### Context-specific strong overrides
- `.scan-paragraph .scan-text-strong`
- `.scan-highlight-detail .scan-text-strong`
- `.scan-meta-large .scan-text-strong`
- `.scan-driver-row .scan-text-strong`
  - unified red emphasis shades

### Regime line value emphasis
- `.scan-regime-inline-value`
  - stronger red + heavier weight
  - used for numeric values (score, confidence)

---

## Card + Border Language

Use consistent red-tinted borders across analysis cards:
- `.scan-card`
- `.scan-section`
- `.scan-yield-item`
- `.scan-pair-chip`
- `.scan-regime-pill`
- `.scan-regime-core-metrics`
- `.scan-trader-warning` (with subtle red background)

Target feel: one coherent card system instead of mixed neutral/red borders.

---

## Reusable UI Patterns to Port to Overview

### 1) Summary chips row
- `scan-overview-bar` + `scan-overview-item`
- Lightweight pill metadata cluster

### 2) Regime strip composition
- summary pills
- metric row
- warning callouts

### 3) Two-column analysis cards
- `scan-grid` + `scan-card`
- consistent label/value/meta structure

### 4) Narrative sections
- `scan-section` + `scan-section-title` + paragraph classes

### 5) Reliability/details area
- section with metadata separators and chip-like missing-signal items

---

## Overview Transfer Mapping (Manual)

Apply the style language to `Overview` `ai-analysis-content` in this order:

1. **Container layer**
   - replicate fixed-height shell + fog cue only if desired in Overview card context
2. **Heading + subtitle layer**
   - align `section-header`, `analysis-badge`, sublabels to red emphasis hierarchy
3. **Card and section chrome**
   - unify borders/background/radius to red-tinted system
4. **Inline emphasis parser output**
   - ensure strong/important text maps to red emphasis classes
5. **Metadata chips and warnings**
   - adopt scan chip/callout pattern for quick scanability

---

## Guardrails
- Do not change API payload handling while migrating styles.
- Keep existing Overview layout logic first; style parity before structural refactor.
- Migrate class-by-class in small passes (header -> chips -> cards -> text emphasis).
- Preserve readability: red for important cues, neutral for body copy.

---

## Quick QA Checklist
- Important values are visibly red in both tabs.
- Section headers have consistent size, tracking, and divider treatment.
- Borders are consistently red-tinted (no accidental gray variants).
- Body text remains legible; red is used for priority, not everything.
- Scroll/fog cue (if used) is visible but not distracting.

