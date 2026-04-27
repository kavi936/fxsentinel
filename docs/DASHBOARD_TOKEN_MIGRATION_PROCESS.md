# Dashboard Token Migration Process

## Purpose
This document defines how we move dashboard styling from hardcoded values to design tokens, starting with the Economic Calendar card and AI Analysis card.

The goal is to make rebranding faster, safer, and more consistent by centralizing style decisions (color, spacing, radius, shadows, typography) into named variables.

## Why This Process Exists
- The current dashboard styling contains repeated hardcoded values across large CSS files.
- Rebranding with hardcoded values causes drift (slightly different reds, spacing, borders, etc.).
- Tokenized styling lets us change brand visuals in one place and propagate globally.
- A phased rollout reduces visual regressions and preserves existing behavior.

## Scope (Phase 1)
Initial migration targets:
- `src/components/Overview.css`
  - Economic Calendar card styles (`.news-calendar`, `.calendar-*`, `.event-*`, `.calendar-table*`)
  - AI Analysis card styles (`.ai-analysis-card`, `.ai-*`)
- Token definitions in a global stylesheet (`src/App.css` or dedicated token file to be added next).

Out of scope for this phase:
- Functional/behavioral changes in React components.
- Full dashboard-wide token migration.
- Visual redesign of other cards (unless explicitly included in a later phase).

## Design Token Basics
A token is a named CSS custom property:

```css
:root {
  --dash-color-surface: #111111;
  --dash-space-md: 12px;
  --dash-radius-md: 10px;
}
```

Then used in component styles:

```css
.ai-analysis-card {
  background: var(--dash-color-surface);
  padding: var(--dash-space-md);
  border-radius: var(--dash-radius-md);
}
```

## Token Categories
Use a small, controlled set first (do not create hundreds immediately).

- **Color**
  - surface/background layers
  - text hierarchy (primary/secondary/muted)
  - borders (soft/strong)
  - semantic accents (brand, positive, warning, negative)
- **Spacing**
  - xs/sm/md/lg/xl
- **Radius**
  - sm/md/lg
- **Shadow**
  - card/elevated/interactive
- **Typography**
  - size + weight scale for card titles, labels, body text, micro text

## Naming Convention
Use dashboard-scoped token names:

- Prefix: `--dash-`
- Pattern: `--dash-{category}-{role}-{scale}`

Examples:
- `--dash-color-surface-1`
- `--dash-color-text-primary`
- `--dash-space-md`
- `--dash-radius-lg`
- `--dash-shadow-card`

Rules:
- Prefer semantic names over raw color names (`text-primary` > `white-90`).
- Reuse existing tokens before adding new ones.
- If a value is used once and intentionally unique, keep it local until reuse appears.

## Migration Rules
- Do **not** change UI behavior while tokenizing.
- Replace repeated hardcoded values first (high-frequency literals).
- Keep changes small and reviewable.
- Avoid changing selectors and structure unless required for token usage.
- Preserve current class names during initial migration to reduce cascade risk.

## Step-by-Step Workflow
1. **Inventory**
   - Identify repeated literals in target CSS blocks (colors, spacing, radii, shadows, typography).
2. **Define tokens**
   - Add minimal token set in root location.
3. **Map values**
   - Create a simple old-value to token mapping table.
4. **Migrate in batches**
   - Calendar card batch first, then AI card batch.
5. **Validate each batch**
   - Visual compare in key states.
6. **Refine**
   - Merge duplicate tokens, remove unnecessary one-offs.

## Suggested Migration Order (For Current Work)
1. Card shells (background, border, radius, shadow)
2. Headers/titles
3. Buttons/controls
4. Data rows/chips/badges
5. States (hover/selected/loading/error)
6. Responsive overrides

## QA Checklist (Must Pass)
- Desktop and mobile both render correctly.
- No change to functional flows:
  - selecting calendar event
  - AI analysis pending/loading/error/success states
  - alternate calendar table mode
- Hover/focus/active styles still visible.
- Contrast remains readable.
- No linter errors introduced in edited files.

## Common Pitfalls to Avoid
- Creating too many tokens too early.
- Mixing old hardcoded values and new token values randomly in the same block.
- Introducing behavior changes while doing style refactor.
- Renaming classes during token phase (save for decomposition phase).

## Definition of Done (Phase 1)
- Economic Calendar + AI Analysis card styles primarily reference dashboard tokens.
- Hardcoded repeated literals are substantially reduced in target sections.
- UI behavior is unchanged.
- Process is documented and reusable for next dashboard sections.

## Next Step
Create the initial dashboard token source file and migrate the first batch:
- card shell tokens
- text hierarchy tokens
- spacing and radius tokens
