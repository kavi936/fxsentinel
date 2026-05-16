# AI Analysis — V1 Unified Spec (working draft)

**Status:** draft for discussion — edit freely.  
**Goal:** Agree what each analysis area is *for*, what we **keep** from today, and what **every** response shares so traders get a consistent “spine” without forcing unrelated sections to look identical.

Related docs: `AI_ANALYSIS_WORKFLOW_IDEAS.md`, `AI_WORKFLOW_AND_MULTI_LLM_ARCHITECTURE.md`, `AI_ANALYSIS_FOUNDATION_ROADMAP.md`.

---

## 1. Principle: shared spine, different body

| Part | Rule |
|------|------|
| **Spine** | Same small set of fields on every analysis type (so users learn one mental model). |
| **Body** | Area-specific sections stay different — holistic stays dashboard-heavy, news stays headline-led, calendar stays scenario-led. |

---

## 2. V1 shared spine (all three areas)

Every analysis response should include these, written in plain language:

| Field | What it means |
|--------|----------------|
| **`summary_line`** | One sentence: what this analysis is telling you right now. |
| **`bias`** | Bullish / bearish / neutral for the **named subject** (e.g. “USD for this event,” “US short-term regime,” “risk sentiment for this headline”). Must name the subject. |
| **`time_horizon`** | What window this applies to (e.g. “into the release,” “2–6 weeks,” “when markets reopen”). |
| **`confidence`** | 0–100 or low/med/high — plus **one short line** why it is not higher (e.g. stale data, pending print, headline only). |
| **`invalidation`** | What would prove this view wrong or stale (can be the same idea repeated in area-specific detail below). |
| **`primary_instruments`** | Ordered list of pairs or symbols this view cares about most (respect user watchlist when relevant). |

**Optional spine (V1 if easy):** `data_quality_note` — stale indicators, closed market, missing actuals, etc.

The **body** below the spine is free to differ by area.

---

## 3. Area A — Holistic economy scan

### What it is for

Medium-term **regime read** for an economy: rates, drivers, event density, cross-pair map — not a single headline trade.

### Good parts to keep (current system)

- Short-term vs long-term regime strip with **score + confidence**.
- **Yield context** (levels, session change, curve diagnostics, dovish/tightening label).
- **Calendar stress** and plain-language warning when event density is high.
- **Pair biases** with conviction tier and **invalidation** (especially conditional risks like oil / geopolitics).
- **Transparency:** scan model version, staleness, reliability label, which indicator keys were used.
- **Personalization hook** (e.g. swing vs scalp) — but spine should still lead so the “hero line” matches trader mental model.
- **Central bank / overlay context** when it ties to that economy.

### V1 body (what stays unique here)

- Driver breakdown (short-term / long-term components).
- Highlights, narrative, trading-range view if we keep them — as **supporting** detail under the spine.
- FX map and geopolitical / energy overlay where relevant.

### V1 improvements (agree priorities)

- [ ] Lead with **spine** in UI/API so the first screenful matches other analysis types.
- [ ] Align “personalized long-term focus” with what we show first (avoid confusion).
- [ ] Differentiate **invalidation per pair** where the story genuinely differs (not copy-paste everywhere).

---

## 4. Area B — Economic calendar event analysis

### What it is for

**One scheduled release:** what is expected, what surprises mean, how to think about volatility and playbook — usually **around the print**.

### Good parts to keep (current system)

- **Scenario framing** (strong / in-line / weak vs forecast) with **pairs and rough levels**.
- Pre-release **risk language** (size, stops, avoid gambling into the number).
- **Volatility expectation** in intuitive terms.
- **Next catalysts** / forward focus when useful.

### V1 body (what stays unique here)

- Forecast vs previous vs actual (when available) and **post-print** refresh path later.
- Scenario table + playbook (“above / at / below”).
- Event-specific sections (CPI vs NFP vs central bank) can stay richer than news.

### V1 improvements (non-negotiable)

- [ ] **Single source of truth for scenarios:** bullish/bearish labels must match the written outcome for USD (no contradictory rows vs prose).
- [ ] **Anchor levels to context:** e.g. reference spot or last close when we cite ranges (or say “illustrative levels” explicitly).
- [ ] Same **spine** at top; scenario table is **body**.

---

## 5. Area C — Live news analysis

### What it is for

**One headline or article:** fast read on impact, risk, and what to watch **now** — often intraday or “next session.”

### Good parts to keep (current system)

- Short **market impact** + **trading implications** (two-block readability).
- **Immediate reaction** tag, **key pairs**, **volatility** and **timeframe**.
- **Risk assessment** block (volatility, liquidity, correlation).
- **Honest session context** (e.g. markets closed → “when reopen” framing instead of fake price certainty).
- Optional **key levels** when they are justified.

### V1 body (what stays unique here)

- Headline-led summary, source/time, “what changed.”
- Shorter than holistic; no obligation to repeat full macro dashboard.

### V1 improvements

- [ ] Same **spine** at top; bias subject must be explicit (e.g. “risk FX” not only “neutral” without saying what is neutral *about*).
- [ ] When holistic scan flags elevated geopolitical / energy risk, **optional one-line cross-check** (“aligned with / tension vs economy scan”) — can be phase 1.5.

---

## 6. Cross-cutting V1 rules (all areas)

- **Same vocabulary** for bias and horizon where possible (glossary in app copy).
- **Confidence always has a reason** — never a bare number.
- **No contradictory machine fields** (validate scenario vs bias before show).
- **Version tag** on every API payload once implemented — see **§10** (`analysis_format_version`).

---

## 7. Open decisions (fill in together)

| # | Question | Notes |
|---|----------|--------|
| 1 | Exact wording for `bias` subjects per area? | Calendar = “USD post-CPI”; scan = “US short-term regime”; news = headline-specific. |
| 2 | Required vs optional spine fields on day one? | Can ship spine with 5 fields first. |
| 3 | Do we show spine only in UI or also return it in API JSON first? | Implementation order. |

---

## 8. Revision log

| Date | Change |
|------|--------|
| 2026-05-12 | Initial draft: spine + body per area, keep/improve lists. |
| 2026-05-12 | Pre-implementation review: §9 — trace prior samples to spec; go checklist. |
| 2026-05-12 | §9.4 codebase plan; §10 `analysis_format_version` / additive spine / rollback; §11 one section at a time. |
| 2026-05-12 | Implemented `backend/services/analysis_v1_spine.py` + wired `app.py` (enhanced calendar, news analysis, economy scan, legacy calendar). Env: `ANALYSIS_V1_SPINE_ENABLED`. Tests: `backend/test_analysis_v1_spine.py`. |
| 2026-05-12 | Frontend: `AnalysisV1Spine.jsx` + CSS; Overview calendar transform preserves `spine` / `scenario_alignment_warnings`; LiveNewsFeed + Economies render spine; `sanitize.js` sanitizes spine fields for news. |
| 2026-05-13 | Holistic recents now persist/restore V1 spine metadata; calendar pass adds `scenario_alignment_status` + `level_context_note`; Overview shows context note above Probability Scenarios. |
| 2026-05-13 | Priority hardening pass: live-news vs latest US holistic cross-check note (`cross_context_note`), endpoint observability metadata (`v1_observability`), improved spine copy for holistic/news, prompt constraints for `market_bias` and anchored vs illustrative `key_levels`, shared spine typography tokens. |
| 2026-05-15 | Phase 2: `analysis_contract.py` + `analysis_pipeline.finalize_analysis()` — all three analysis APIs use one finalize path; responses include `analysis_kind`, `spine_profile`, `trace`. See `AI_ANALYSIS_FOUNDATION_ROADMAP.md`. |
| 2026-05-15 | Phase 3 (partial): `calendar_scenario_engine.py` — canonical `market_scenarios` + `forward_scenarios_by_outcome`; Overview uses API table when present. |

---

## 9. Final check before implementation (review)

### 9.1 Trace: prior real outputs vs this spec

| Issue we saw in samples | Where V1 addresses it | Residual risk |
|-------------------------|-------------------------|---------------|
| CPI “Probability scenarios” vs “Market Scenarios” **contradicted** USD bullish/bearish | §4 non-negotiable: single source of truth + §6 validate before show | Validator must be implemented and tested on CPI-shaped payloads |
| **80% confidence** with no clear meaning | §2 `confidence` + reason line; §6 never bare number | Team must define one vocabulary (e.g. “confidence = synthesis certainty” vs “edge”) |
| Live news **neutral** on Hormuz while scan said **elevated** geo/energy | §5 optional cross-check (phase 1.5); spine forces **named bias subject** | Cross-check is optional in V1 — first ship spine only, then add reconciliation |
| Holistic **strong body**, no common “first line” with other tabs | §2 spine + §3 lead with spine in UI/API | UX work: reorder without losing scan depth |
| **Same invalidation** on every pair | §3 improvement: per-pair where it differs | Can ship V1 with copy-paste invalidation if needed; refine in V1.1 |
| Levels **without spot anchor** | §4 anchor or label “illustrative” | Calendar path needs live quote or explicit disclaimer |

### 9.2 Spec health (quick audit)

- **Spine + body split** resolves the “everything can’t look the same” concern without abandoning consistency.
- **Keep lists** match what already works in production; **improve lists** target known failure modes.
- **Open decisions (§7)** are the only blocking product choices before coding: bias subject strings, mandatory spine subset, UI vs API first.

### 9.3 Go recommendation

- **Green to start** on implementation **if** first slice is: spine fields + calendar scenario validation (highest trust bug).
- **Defer** optional news↔scan cross-check to **V1.1** unless cheap to add.

### 9.4 Codebase implementation plan (where to change code)

| Area | Primary endpoint | Where to attach spine / validators (first pass) |
|------|------------------|--------------------------------------------------|
| **Calendar (rich, Overview)** | `POST /api/enhanced-analysis/<event_id>` | `backend/app.py` → `get_enhanced_analysis` — after GPT result, before `jsonify(enhanced_analysis)`. Scenario validation / repair here or in a small service imported by this route. |
| **Live news** | `GET /api/analysis/<news_id>` | `backend/app.py` → `generate_news_analysis` — merge `spine` into return dict alongside existing MVP keys. |
| **Holistic scan** | `GET /api/economy-scan/<country>` | `backend/app.py` (economy scan handler) — after `economy_holistic_scan_service.build_scan(...)`, add `spine` from existing fields. |

**New module (recommended):** `backend/services/analysis_v1_spine.py` (name TBD) — spine builders + calendar scenario validator. Keeps `app.py` to import + call only.

**Avoid first:** Using `hybrid_economic_calendar.py` (~20k lines) for V1 **presentation** work — that file is mainly calendar **data**. Change it only when fixing **event fields** feeding analysis, not for spine JSON shape.

**Legacy calendar path:** `GET /api/analysis/<id>` can resolve to `generate_ai_analysis` (local analyzer) for some event IDs — **secondary** to enhanced-analysis. Decide later whether to add `spine` there or deprecate.

**Frontend (after first backend slice):** `Overview.jsx` (`normalizeAiAnalysis` / enhanced payload), `LiveNewsFeed` (or consumer of `/api/analysis`), `Economies.jsx` (holistic). Render shared spine header when `analysis_format_version` indicates V1 and `spine` is present.

**Tests:** Unit tests on spine builder + scenario validator with JSON fixtures; optional integration test with mocked GPT.

**Optional rollout flag:** e.g. env `ANALYSIS_V1_SPINE_ENABLED` — ship code with spine off, enable in staging then production.

---

## 10. `analysis_format_version` and getting back to “original” output

Use a single constant in code (name can match repo style), e.g. **`ANALYSIS_FORMAT_VERSION = "v1"`**, exposed on each response as **`analysis_format_version`** (string). Purpose: clients, logs, and Firestore snapshots know which shape to expect.

### How this preserves the original output

1. **Additive fields (default approach)**  
   Keep **all existing response keys unchanged**. Add only:
   - `analysis_format_version`: `"v1"` when spine is included (or `"legacy"` / omit if you want explicit legacy labeling).
   - `spine`: `{ ... }` object per §2.  
   Any consumer that ignores unknown keys behaves exactly as today → **original output is still there** in the same JSON.

2. **UI rollback without redeploying logic removal**  
   - If the UI checks `analysis_format_version === "v1"` before rendering the spine block, turning off the new UI is a **one-line branch** or feature flag.  
   - Body-only layout = original visual experience even though `spine` may still be present on the wire.

3. **Server-side “original only” mode (strong rollback)**  
   - Env or flag: when **off**, omit `spine` and optionally set `analysis_format_version` to `"legacy"` or omit the field — wire payload matches historical behavior for strict clients.

4. **Stored history (Firestore / recent analyses)**  
   Old documents lack `analysis_format_version` or `spine` → treat as **legacy** in UI (no spine block). New saves include version + spine. No migration required to “go back.”

5. **Future v2**  
   Bump to `"v2"` when spine fields change; keep v1 parsing path or adapters until history expires.

**Rule of thumb:** Version string answers “what schema is this?”; **never deleting old top-level fields** (until a planned major version) is what guarantees you can always reconstruct original consumer behavior.

---

## 11. Should we work one section at a time?

**Yes.** Recommended sequence:

| Step | Section | Why |
|------|---------|-----|
| 1 | **Shared module + calendar (enhanced-analysis)** | Highest trust impact (scenario consistency); single endpoint; clear `jsonify` seam. |
| 2 | **Live news** (`/api/analysis` news branch) | Same spine module; smaller payload; validates the pattern on a second surface. |
| 3 | **Holistic scan** | Richest existing body; map `trader_brief` / scores into `spine` once the pattern is proven. |
| 4 | **UI** per screen | After each backend slice, optionally add spine header for that area only — avoids a big-bang UI change. |

Do **not** try to land spine + validator + all three UIs in one PR unless the team is very small and timeboxed — serial **vertical slices** reduce merge risk and make bugs easier to attribute.
