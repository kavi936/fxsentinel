# Economic Calendar Style 2 – Readability Evaluation & Recommendations

## Goal
Make Style 2 (table view) easier to read and closer to the scannability of Forex Factory’s calendar, using evidence from psychology and table-design research.

---

## Research Summary: How People Read Tables

### 1. **Row tracking and zebra striping**
- **Finding**: Alternating row backgrounds (zebra striping) help users track across **wide** tables and reduce “losing the line” when scanning horizontally.
- **Evidence**: Some studies report ~20% better comprehension/recall and fewer data-retrieval errors with alternating rows. UX experts (e.g. NNG) recommend **subtle** contrast—enough to guide the eye, not dominate.
- **Implication**: Style 2 has 8 columns; adding **subtle** zebra striping will make it easier to follow a single event across Date → Previous.

### 2. **Alignment: text vs numbers**
- **Finding**: **Text columns**: left-aligned. **Numeric columns**: right-aligned. Headers should match their column’s alignment.
- **Reason**: Right-aligned numbers line up by magnitude (units, decimals), so comparing Actual vs Forecast vs Previous is faster. This comes from accounting practice and carries over to any numeric data table.
- **Avoid**: Center alignment for data—it’s harder to scan and often needs extra visual structure.
- **Implication**: **Actual**, **Forecast**, and **Previous** (and their headers) should be **right-aligned**. Date/Time can stay left or be left for consistency with “read in order.”

### 3. **Numeric columns: fixed-width digits**
- **Finding**: Proportional digits (variable width) cause jagged columns. **Tabular (lining) figures** give equal width per digit so columns align vertically.
- **CSS**: `font-variant-numeric: tabular-nums` (and optionally `font-feature-settings: 'tnum'` for older support).
- **Implication**: Apply to the Actual, Forecast, and Previous cells so values line up cleanly.

### 4. **Cognitive load and visual hierarchy**
- **Finding**: Working memory holds ~5 chunks; too many competing cues (many colors, sizes) reduce effectiveness. Use **one** strong preattentive attribute (e.g. color for impact) and keep the rest consistent.
- **Implication**: Keep impact as the main visual cue (e.g. left border or small indicator). Don’t add lots of extra colors beyond that and zebra striping.

### 5. **Sticky header and context**
- **Finding**: Fixed/sticky headers keep column meaning in view while scrolling; identifier columns (e.g. Date, Time) on the left help users keep their place.
- **Implication**: Style 2 already has a sticky header; ensure it has enough contrast so it’s clearly “header” not “first row.”

### 6. **Forex Factory’s patterns**
- Impact as **color** (red / orange / yellow) for quick filtering by importance.
- **Actual vs forecast**: Green = better than forecast, Red = worse (interpretation aid).
- Clear column order: Date, Time, Currency, Impact, Detail, Actual, Forecast, Previous (and Graph).
- **Implication**: We can mirror alignment and structure; optional enhancement is green/red for actual when it’s “better” or “worse” than forecast (needs simple comparison logic).

---

## Current Style 2: What’s Working and What Isn’t

**Working**
- Sticky header.
- Impact indicated by left border (high/medium/low).
- Semantic table markup.
- Horizontal scroll wrapper for small screens.

**Problems**
1. **No row separation** – Rows rely on a very subtle bottom border (`rgba(255,255,255,0.06)`), so long lists feel like a single block and horizontal scanning is harder.
2. **All columns left-aligned** – Actual, Forecast, Previous are numeric but left-aligned, so magnitudes don’t line up and comparison is slower.
3. **No zebra striping** – Harder to track one row across 8 columns.
4. **Impact as text only** – “High”/“Med”/“Low” is clear but less instant than a small colored marker (Forex Factory uses icons).
5. **Dense typography** – 12px body, 10px header; acceptable but on the tight side for quick scanning.
6. **No “better/worse” cue** – Actual isn’t colored vs forecast, so users must mentally compare.

---

## Recommendations (in order of impact)

### High impact (implement first)

1. **Zebra striping**  
   - Add subtle alternating row backgrounds (e.g. transparent white/gray) so odd/even rows differ slightly.  
   - Keep selected and hover states stronger than the stripe so they still stand out.

2. **Right-align numeric columns**  
   - Right-align **Actual**, **Forecast**, **Previous** (and their `<th>`).  
   - Use `text-align: right` and consistent padding so headers and cells line up.

3. **Tabular figures for numeric columns**  
   - Add `font-variant-numeric: tabular-nums` (and optional `font-feature-settings: 'tnum'`) to the Actual, Forecast, and Previous cells so digits align vertically.

4. **Stronger row separation**  
   - Slightly increase padding and/or use a bit more visible border or zebra contrast so each row reads as one unit without adding clutter.

### Medium impact (optional next)

5. **Impact as a colored dot/badge**  
   - Add a small impact indicator (e.g. colored circle or pill) next to or instead of “High”/“Med”/“Low” so impact is scannable at a glance (red / orange / green or yellow).

6. **Slightly larger type**  
   - Consider 13px for body and 11px for headers if the card layout allows, to reduce eye strain on long lists.

### Lower priority / future

7. **Color actual vs forecast**  
   - If actual is “better” than forecast (e.g. unemployment lower, growth higher), style Actual green; if “worse,” style red. Requires simple comparison rules and handling of N/A and non-numeric values.

8. **Header contrast**  
   - Ensure the sticky header background and text contrast are clearly distinct from body rows (already red-tinted; can tune if needed).

---

## Implementation Notes

- **CSS-only** for zebra striping, alignment, tabular-nums, padding, and borders.
- **JSX** only if we add impact icons or “better/worse” logic for Actual (e.g. a small helper that compares `event.actual` and `event.expected` and returns a class or inline style).
- **Accessibility**: Keep sufficient contrast for zebra rows; don’t rely on color alone for impact (left border or icon + text preserves meaning).
- **Consistency**: Match any new patterns (e.g. impact icon) with Style 1 or the rest of the app so the calendar feels like one product.

---

## References (conceptual)

- Spreadsheet/table comprehension and human–spreadsheet interaction (comprehension, guesswork, clarification).
- Web table formatting and mobile: cell padding, frozen headers, zebra striping (subjective preference and some task gains).
- Visual aids in numeric tables: zebra striping vs color/bar encodings for different tasks; gaze behavior.
- Alignment: text left, numbers right; headers match column alignment (UX best practice).
- Data table design: cognitive load, preattentive attributes, row styling, fixed headers, alignment.
- Tabular figures: `font-variant-numeric: tabular-nums` for numeric columns.
