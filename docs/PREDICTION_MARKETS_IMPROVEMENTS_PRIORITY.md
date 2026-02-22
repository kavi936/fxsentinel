# Prediction Markets Card – Prioritized Improvements

This list merges the earlier evaluation with your feedback. Items are ordered so we can tackle them in sequence. Your inputs are reflected in **P0** and **P1**.

---

## P0 – Do first (your priorities + “what does this mean for me”)

### 1. **Stop hiding low-volume markets**
- **Why:** Low-volume markets can still be useful; shading them out makes the card feel empty and hides relevant ones.
- **Changes:**
  - **Frontend:** Remove the `volume < 5000` filter in `Overview.jsx` (lines ~5743–5747) so all markets returned by the API are shown.
  - **Backend (optional, can follow):** Lower or make configurable `MIN_VOLUME_THRESHOLD` in `prediction_markets_service.py` (e.g. 500 or 0) so more markets are returned; otherwise frontend will still only show what the API sends.
- **Result:** More markets visible; low-volume markets no longer excluded by the card.

### 2. **Stop shading low-conviction / low-volume rows**
- **Why:** Conviction is volume-based; low volume → “low conviction” and currently those rows are visually dimmed (opacity 0.7), which feels like “less important” or “ignore”.
- **Changes:**
  - **CSS:** In `Overview.css`, remove or reduce the opacity difference for `.prediction-market-item.conviction-low` (and optionally `.conviction-medium`). For example: set all to `opacity: 1` so no row is shaded out by conviction.
- **Result:** Low-volume markets are still visible and look like first-class content, not “secondary”.

### 3. **Show more markets (raise or remove backend cap)**
- **Why:** “Too few markets” – backend currently returns at most 50 (`MAX_FILTERED_MARKETS`).
- **Changes:**
  - **Backend:** In `prediction_markets_service.py`, increase `MAX_FILTERED_MARKETS` (e.g. to 100 or 150) or make it configurable. Ensure sort order still puts most relevant first (see next item).
- **Result:** Card can display more markets; combined with (1) and (2), the list feels fuller and more useful.

### 4. **Most important markets at the top (use backend order; add relevance in UI)**
- **Why:** “Most important prediction markets should be displayed at the top” and “some titles are irrelevant” – backend already computes relevance and priority, but the frontend re-sorts by volume only.
- **Changes:**
  - **Frontend:** In `Overview.jsx`, remove the client-side sort that overwrites order (the `.sort((a, b) => volumeB - volumeA ...)` block). Use the API order as-is so backend’s relevance + priority + conviction + delta order is preserved.
  - **Optional:** Show a small “High relevance” / “Forex-relevant” badge or icon for markets where `relevance === 'high'` (and optionally `medium`) so users see why something is at the top.
- **Result:** Order reflects “importance” (relevance, priority, conviction, movement), not just volume; users see the most relevant markets first.

### 5. **Actionability: “What does this mean for me?”**
- **Why:** “No actionability” – markets are shown but it’s unclear what the user should do or how it affects them.
- **Changes (in order of impact):**
  - **Show affected pairs:** Backend already sends `affected_currency_pairs`. In each market row, display e.g. “Relevant to: EUR/USD, GBP/USD” (or “Pairs: …”). This directly answers “what does this mean for me” for a forex user.
  - **One-line implication (optional):** Add a short line under the question when possible, e.g. “Fed rate path → typically moves USD pairs” or “Resolves on FOMC day.” (Can start with affected pairs only.)
  - **Link to calendar (later):** If backend sends `related_event` or resolution date, add “Resolves: [date]” and later a link to the matching economic calendar event.
- **Result:** Each market has a clear “so what?” – which pairs and, over time, how it ties to the calendar.

---

## P1 – Trust and clarity (so the card feels reliable and understandable)

### 6. **Show “Last updated” and cache status**
- **Why:** Users need to know how fresh the data is; the hook already has `lastUpdate` and `summary`.
- **Changes:** In the prediction markets card header, show e.g. “Updated 5 min ago” (using `predictionMarketsLastUpdate`) and optionally “Cached” when `summary.cached === true`.
- **Result:** Trust in the data and less confusion when numbers don’t change.

### 7. **Explain conviction (tooltip or short copy)**
- **Why:** “High / Medium / Low” is unexplained; users don’t know it’s volume-based.
- **Changes:** Add a tooltip or info icon next to the conviction badge: e.g. “Conviction: based on trading volume (high = more volume).”
- **Result:** Users understand why some markets are labeled high/medium/low and don’t mistake it for “accuracy” or “importance.”

### 8. **Explain missing price deltas**
- **Why:** 24h/48h/7d deltas are often null on first load; users may think something is broken.
- **Changes:** When `price_delta_24h` (and 48h/7d) are null, show a short line or tooltip: e.g. “Movement data available after we’ve tracked prices for 24h.”
- **Result:** Clear expectation and fewer “why is there no change?” moments.

### 9. **Fix “All” status filter**
- **Why:** “All” currently means “Active + resolved in last 7 days”; older resolved markets never show.
- **Changes:** When Status = “All”, show all markets (active + resolved, any age), or add a “Resolved (last 30 days)” option and make “All” truly all. Avoid hiding resolved markets by default unless the user chooses “Active only.”
- **Result:** “All” matches user expectation; users can review past outcomes.

---

## P2 – Better discovery and filtering

### 10. **Inline search (no modal-only search)**
- **Why:** Search in a modal is heavy for quick filtering; active query is not visible when the modal is closed.
- **Changes:** Add a persistent search input in the card header (or above the list) that filters by question/title in real time; keep the modal as optional “advanced” or remove it.
- **Result:** Faster, clearer discovery without opening modals.

### 11. **Single “Filters” panel (Topic + Status + Conviction)**
- **Why:** Four separate modals (Topic, Status, Conviction, Search) are too many for one card.
- **Changes:** Replace the four modal triggers with one “Filters” control that opens a single panel (dropdown or slide-out) containing Topic, Status, Conviction (and optionally search). Show a one-line summary when any filter is active, e.g. “Topic: Fed · Status: Active.”
- **Result:** Fewer clicks, clearer active state, easier to clear all.

### 12. **Sort control (optional)**
- **Why:** Default order will be “importance” (P0 #4); some users may want “Resolves soon” or “Biggest 24h move.”
- **Changes:** Add a small “Sort by” dropdown: e.g. “Most relevant” (default), “Resolves soon”, “24h move”, “Volume.” Implement by sorting the already-filtered list in the frontend.
- **Result:** Power users can reorder without changing backend.

---

## P3 – Deeper usefulness (after P0–P2)

### 13. **Link prediction markets to economic calendar**
- **Why:** Markets that resolve on event days (FOMC, NFP) are more actionable when tied to the calendar.
- **Changes:** Show “Resolves: [date]” and, when backend supports it, “Same day as [event name]” with a link to that event in the Economic Calendar card.
- **Result:** One place to see “this market resolves on FOMC day” and jump to the calendar.

### 14. **Watchlist / pinned markets**
- **Why:** Users want to track the same markets repeatedly.
- **Changes:** Allow “Pin” or “Add to watchlist” per market; store in localStorage (or account if logged in); show pinned markets at the top or in a separate “Pinned” section.
- **Result:** Recurring use without re-searching.

### 15. **Topic options from backend (single source of truth)**
- **Why:** Topic list is duplicated and hardcoded in the frontend; backend has richer topic logic.
- **Changes:** Add an API field or endpoint that returns topic options (and optionally counts). Frontend uses that for the Topic filter instead of hardcoded GDP/CPI/Fed/….
- **Result:** One place to add or change topics; no frontend/backend drift.

---

## P4 – Polish and performance

### 16. **Auto-refresh prediction markets**
- **Why:** Data is only refreshed on manual click; odds change around events.
- **Changes:** In `usePredictionMarkets.js`, add a periodic refresh (e.g. every 10–15 minutes), similar to the economic calendar. Optionally show “Updating…” without replacing the whole list with a spinner.
- **Result:** Fresher odds without user action.

### 17. **Background refresh (no full-screen spinner)**
- **Why:** Manual refresh currently hides the whole list behind a loading state.
- **Changes:** On refresh, keep showing the previous list and show a small “Updating…” in the header; swap in the new list when the request completes. Use full-screen loading only on initial load when there is no data.
- **Result:** Smoother UX and less “flash of empty.”

### 18. **Chart cache invalidation**
- **Why:** After refreshing markets, expanded charts still show old history.
- **Changes:** When the user triggers a prediction-markets refresh, clear `pmChartDataCache` (or invalidate entries for visible markets) so the next expand fetches fresh history.
- **Result:** Charts stay in sync with the refreshed list.

### 19. **Unify empty states**
- **Why:** “No markets” and “No Active Markets” can both appear; logic is redundant.
- **Changes:** Single empty state that respects filters: e.g. “No markets match your filters” when filters are on, “No active prediction markets right now” when list is empty and no filters. Remove the duplicate notice block that checks `hasMarkets` after the list.
- **Result:** Clear, non-repetitive messaging.

### 20. **Remove or reduce conviction-based opacity in CSS**
- **Already covered in P0 #2;** if you do it there, no separate P4 item. If you only do P0 #2 for “low”, consider leaving medium slightly different or making it a subtle border instead of opacity so low-volume rows are not shaded.

---

## Summary table (order to tackle)

| Priority | #   | Improvement                                      | Main change (short)                                  |
|----------|-----|--------------------------------------------------|------------------------------------------------------|
| **P0**   | 1   | Stop hiding low-volume markets                   | Remove frontend `volume < 5000` filter               |
| **P0**   | 2   | Stop shading low-conviction rows                 | Set conviction-low (and optionally medium) opacity 1 |
| **P0**   | 3   | Show more markets                                | Increase `MAX_FILTERED_MARKETS` (e.g. 100–150)       |
| **P0**   | 4   | Most important at top                            | Use API order; optionally show relevance badge        |
| **P0**   | 5   | Actionability (“what for me”)                    | Show `affected_currency_pairs`; optional one-liner   |
| **P1**   | 6   | Last updated + cache                             | Show `lastUpdate` / `summary` in header              |
| **P1**   | 7   | Explain conviction                               | Tooltip or short copy on badge                       |
| **P1**   | 8   | Explain missing deltas                            | Copy when deltas are null                            |
| **P1**   | 9   | Fix “All” status                                 | Show all resolved or add “Resolved (30d)”             |
| **P2**   | 10  | Inline search                                    | Persistent search field in card                       |
| **P2**   | 11  | Single Filters panel                             | One panel for Topic + Status + Conviction            |
| **P2**   | 12  | Sort control                                     | “Sort by” dropdown                                   |
| **P3**   | 13  | Calendar link                                    | Resolves date + link to calendar event               |
| **P3**   | 14  | Watchlist / pins                                 | Pin markets; show at top or in section               |
| **P3**   | 15  | Topic from backend                               | API-driven topic list                                |
| **P4**   | 16  | Auto-refresh                                     | Periodic refresh in hook                              |
| **P4**   | 17  | Background refresh UX                            | No full-screen spinner on refresh                    |
| **P4**   | 18  | Chart cache invalidation                         | Clear/invalidate on markets refresh                  |
| **P4**   | 19  | Unify empty states                               | Single empty message by context                      |

---

## Suggested first sprint (quick wins)

1. **P0-1:** Remove frontend `volume < 5000` filter.  
2. **P0-2:** Set `.prediction-market-item.conviction-low` (and optionally `.conviction-medium`) to `opacity: 1`.  
3. **P0-4:** Use API order (remove frontend re-sort by volume); optionally show relevance.  
4. **P0-5:** Render `affected_currency_pairs` in each market row as “Relevant to: EUR/USD, …”.  
5. **P1-6:** Show “Updated …” in the card header using `predictionMarketsLastUpdate`.

After that, do P0-3 (raise `MAX_FILTERED_MARKETS`) and P1-7, P1-8, P1-9, then P2 and beyond as capacity allows.
