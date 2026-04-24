# Overview + Economies UI Baseline

## Purpose
This baseline defines what "current correct behavior" looks like for the `overview` and `economies` dashboard tabs before any structural refactor or redesign work starts.

Why this exists:
- Prevent accidental regressions during UI/CSS refactor phases.
- Make review objective (compare expected behavior, not memory).
- Keep behavior stable while implementation structure changes.

## Scope
- Dashboard tabs:
  - `overview`
  - `economies`
- Breakpoints:
  - desktop
  - mobile
- States:
  - default
  - loading
  - empty
  - error
  - dense-data (when available)
- Interactions:
  - tab switching
  - panel expand/collapse patterns
  - tab-level popups/overlays

## Baseline Capture Rules
- Use the same environment for before/after checks where possible:
  - same branch data freshness window
  - same browser zoom
  - same theme mode
- Capture with browser width visible in screenshot naming notes.
- Do not approve based on one screenshot only. Validate interaction flows too.
- If data is volatile, annotate "data expected to differ; layout/interaction must match."

## Screenshot Inventory (Phase 0)
Use this table to track all required baseline captures.

| ID | Tab | State | Viewport | Captured | File/Link | Notes |
|---|---|---|---|---|---|---|
| O-01 | overview | default | desktop | TODO |  |  |
| O-02 | overview | loading | desktop | TODO |  |  |
| O-03 | overview | empty | desktop | TODO |  |  |
| O-04 | overview | error | desktop | TODO |  |  |
| O-05 | overview | dense-data | desktop | TODO |  |  |
| O-06 | overview | default | mobile | TODO |  |  |
| O-07 | overview | loading | mobile | TODO |  |  |
| O-08 | overview | empty | mobile | TODO |  |  |
| O-09 | overview | error | mobile | TODO |  |  |
| O-10 | overview | dense-data | mobile | TODO |  |  |
| E-01 | economies | default | desktop | TODO |  |  |
| E-02 | economies | loading | desktop | TODO |  |  |
| E-03 | economies | empty | desktop | TODO |  |  |
| E-04 | economies | error | desktop | TODO |  |  |
| E-05 | economies | dense-data | desktop | TODO |  |  |
| E-06 | economies | default | mobile | TODO |  |  |
| E-07 | economies | loading | mobile | TODO |  |  |
| E-08 | economies | empty | mobile | TODO |  |  |
| E-09 | economies | error | mobile | TODO |  |  |
| E-10 | economies | dense-data | mobile | TODO |  |  |

## Interaction Flow Checklist
Record expected behavior exactly as observed today.

### 1) Tab Switching
- [ ] `overview` -> `economies` transition preserves shell layout.
- [ ] `economies` -> `overview` transition returns without stale visual artifacts.
- [ ] Selected tab visual state is always clear.
- [ ] No obvious layout jump beyond expected content change.

### 2) Expand/Collapse and Section Interactions
- [ ] Expanded panels show clear state change (icon/caret/text/animation).
- [ ] Collapsing restores previous layout cleanly (no dead spacing).
- [ ] Repeat toggling does not degrade state or cause flicker.

### 3) Popups/Overlays Used in These Tabs
- [ ] Popup opens anchored and visually layered correctly.
- [ ] Background remains usable as intended (or properly blocked if modal).
- [ ] Escape/click-away behavior matches current expected behavior.
- [ ] Popup close returns focus/interaction to expected area.

### 4) Loading/Empty/Error UX Integrity
- [ ] Loading state communicates progress and avoids severe layout shift.
- [ ] Empty state explains absence of data clearly.
- [ ] Error state is readable and actionable (retry/instruction if present).
- [ ] State transitions do not leave stale content behind.

## Visual Consistency Snapshot Notes
Use this section to describe current baseline quality (not redesign ideas yet).

### Overview Notes
- Spacing rhythm:
- Typography hierarchy:
- Card density and grouping:
- Any obvious inconsistency to preserve-check during refactor:

### Economies Notes
- Spacing rhythm:
- Typography hierarchy:
- Card density and grouping:
- Any obvious inconsistency to preserve-check during refactor:

## Manual Regression Checklist (Use in Every Phase)
Mark each item pass/fail after Phase 1+ changes.

- [ ] Desktop layout remains functionally intact in both tabs.
- [ ] Mobile layout remains navigable and readable in both tabs.
- [ ] Tab switching works with no broken active state.
- [ ] Loading/empty/error states still render and are understandable.
- [ ] Popups/overlays used in scope still open/close correctly.
- [ ] No clipping/overflow regression in dense content areas.
- [ ] Text contrast remains readable on core surfaces.
- [ ] No obvious cross-tab CSS leakage (styles from one tab affecting another).

## Pass/Fail Decision Rule
- A phase is considered safe to merge only when:
  - all required checklist items pass, or
  - failures are documented, intentional, and approved as scoped changes.

## Defect Log Template
Use this when something regresses.

| Defect ID | Phase | Area | Severity | Repro Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

## Sign-off
- Baseline prepared by:
- Date:
- Reviewers:
- Notes:
