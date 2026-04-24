# Overview + Economies Baseline Capture Runbook

## Purpose
This runbook operationalizes `docs/OVERVIEW_ECONOMIES_UI_BASELINE.md` so captures are consistent and comparable across refactor phases.

## Preconditions
- Dashboard app is running and reachable.
- Logged into a user profile that can access both `overview` and `economies`.
- Browser zoom is set to 100%.
- Theme mode is fixed for the full capture session.

## Standard Viewports
- Desktop: `1440x900`
- Mobile: `390x844`

Use these exact viewport dimensions unless a phase explicitly requires additional breakpoints.

## Screenshot File Naming Convention
Use:

`<id>_<tab>_<state>_<viewport>_<YYYY-MM-DD>.png`

Examples:
- `O-01_overview_default_desktop_2026-04-24.png`
- `E-07_economies_loading_mobile_2026-04-24.png`

Why this matters:
- IDs map directly to the baseline table.
- Uniform naming prevents confusion during before/after comparisons.

## Capture Sequence (Strict Order)
1. Capture all `overview` desktop states (`O-01` to `O-05`)
2. Capture all `overview` mobile states (`O-06` to `O-10`)
3. Capture all `economies` desktop states (`E-01` to `E-05`)
4. Capture all `economies` mobile states (`E-06` to `E-10`)

Do not mix tabs while capturing a sequence because context switching increases miss risk.

## Interaction Walkthrough Recording
After screenshots, execute and log:
- tab switching both directions
- panel expand/collapse where available
- relevant popup/overlay open and close flows

Record pass/fail in `OVERVIEW_ECONOMIES_UI_BASELINE.md` checklists.

## Handling Volatile Data
If metrics differ between captures:
- mark note as "data changed; validating layout/interaction parity only"
- still compare:
  - panel structure
  - spacing/typography rhythm
  - control states
  - overflow behavior

## Quality Gate Before Phase 1+
A baseline session is complete only when:
- all 20 screenshot rows are marked as captured
- interaction checklist is filled
- manual regression checklist is initialized
- any known defects are logged in defect table

## Suggested Storage Path
- `docs/assets/dashboard-baseline/<date>/`

Example:
- `docs/assets/dashboard-baseline/2026-04-24/`

Keep captures in dated folders so each phase can be compared against a stable reference set.

