# Plan: Images and Charts in AI Analysis Card (Future)

**Status:** Deferred – to revisit after current analysis improvements are tested and stable.  
**Goal:** Add visuals (economy mini charts, later TradingView widgets) to the AI Analysis card to improve scanability and credibility.

---

## Why do it

- **Readability:** A small chart next to “CPI above target” or “EUR/USD bullish” makes the narrative easier to scan.
- **Trust:** Showing the data the analysis is based on (e.g. indicator trend, pair price) reinforces the narrative.
- **Reuse:** Economies already has SVG mini charts; `/api/economic-chart/{eventName}` exists; TradingView is used elsewhere.
- **Differentiation:** Many tools are text-only; one or two well-chosen visuals would make the card feel more professional.

---

## What it would take

### 1. Economy-style mini charts

- **Data:** Show “the indicator this event is about” (e.g. US CPI event → US inflation mini chart). Options:
  - Use **`/api/economic-chart/{eventName}?months=...`** and a small chart component that consumes that response, or
  - Reuse **Economies’** pipeline: event → currency + concept → indicator id → same economy/indicator data (e.g. `economyIndicators.json` or economy API).
- **UI:** Economies’ mini chart is an inline SVG (area + line, axes, hover). Either:
  - Extract a **shared** `EconomyMiniChart` component (props: time series + optional target line), or
  - Add a slimmed-down chart component used only in the AI card.
- **Placement:** Card is already dense. Need a clear slot (e.g. “Key context” strip with one small chart, or one chart per section). Requires a layout/design decision.

### 2. TradingView widgets (later)

- **What:** Embeds (iframe or script) for a **pair + timeframe** (e.g. EUR/USD 1H) to show price context next to the analysis.
- **Fit:** Choose pair(s) from the event (e.g. event currency USD → EUR/USD or USD/JPY). Separate integration: TradingView embed API, sizing, terms, performance.
- **Best as Phase 2** after one economy mini chart is in place and layout is stable.

---

## Why deferred (not now)

1. **Current work is already substantial** – Central bank + prediction markets, bold, context-referencing. Validate those first.
2. **Design/placement not yet decided** – “Where exactly does the chart sit?” and “one chart vs several?” need a quick mock or decision.
3. **Implementation is non-trivial** – Shared component or dedicated “event → one indicator chart” path; TradingView adds embed and layout work. Deserves its own focused task list.
4. **No structural blocker** – Charts can be driven by **event metadata** (event name, currency, indicator type) when the card renders; no change to the AI response shape required.

---

## Recommended order when you return

### Phase 1 – One economy mini chart

1. **Design:** Decide placement (e.g. “Key context” strip at top, or beside key takeaway). One chart per analysis for the “main” indicator only.
2. **Data:** Resolve event → one main indicator (reuse existing economy/event → indicator mapping used for GPT economy context). Fetch that indicator’s time series via `/api/economic-chart` or economy data.
3. **Component:** Add a small chart component (shared with Economies or AI-specific) that accepts a time series and optional target line; render in the chosen slot.
4. **Scope:** Only show for supported event types (e.g. CPI, NFP, rate) so the card doesn’t get cluttered for every event.

### Phase 2 – TradingView widget

1. Add a small TradingView embed (one pair, e.g. main pair for event currency) in a defined slot.
2. Handle embed constraints (sizing, layout) and ensure the card remains usable on small screens.

---

## References

- **Economies mini charts:** `src/components/Economies.jsx` (e.g. `mini-chart`, `normalizeChartData`, SVG area/line), `Economies.css` (`.mini-chart`, `.chart-line`, etc.).
- **Economic chart API:** `config.endpoints.economicChart` → `/api/economic-chart/{eventName}?months=...`; `EconomicChartPopup.jsx` for usage.
- **Event → indicator mapping:** Same idea as in `gpt_ai_analysis.py` (`_get_relevant_indicators`, economy context) and `economy_context_service` / `economyIndicators.json`.
- **AI Analysis card layout:** `Overview.jsx` (AI Analysis card block), `Overview.css` (`.ai-analysis-card`, `.ai-analysis-content`).

---

*Document created when deferring “images in AI Analysis”; revisit when starting the “AI card visuals” iteration.*
