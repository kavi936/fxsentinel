# FXSentinel — AI Analysis Output Review
**Document Type:** Internal Development Reference
**Scope:** Economic Calendar, Live News, and Holistic Scan analysis sections
**Purpose:** Critique of current AI prompt structure and output quality, with actionable improvement recommendations for each section and cross-cutting issues that apply globally.

---

## Table of Contents
0. [Implementation Tracker](#0-implementation-tracker)
   - [0.1 #8 deferred — levels](#01-8-deferred--level-labeling-approach-when-data-is-ready)
   - [0.2 Active roadmap (next work)](#02-active-roadmap-next-work-in-order)
   - [0.3 Backlog & later](#03-backlog--later-no-blocker-on-8)
   - [0.4 Implemented rework summaries](#04-implemented-rework-summaries-whats-changed-for-users)
   - [0.5 Version 2 tracker](#05-version-2-implementation-tracker-after-v1-ships)
1. [Cross-Cutting Issues (All Sections)](#1-cross-cutting-issues-all-sections)
20. [Version 2 Review — source notes](#version-2-review-after-changes-source-notes)
2. [Economic Calendar Analysis](#2-economic-calendar-analysis)
3. [Live News Analysis](#3-live-news-analysis)
4. [Holistic Scan](#4-holistic-scan)
5. [Prompt Improvement Templates](#5-prompt-improvement-templates)
6. [Priority Action List](#6-priority-action-list)

---

## 0. Implementation Tracker

Track shipped work here so review findings stay tied to code changes.

### Workstream status (2026-05-27)

| Workstream | Focus | Status | Notes |
|---|---|---|---|
| **WS1 — Trust & Consistency** | Labels match body; probabilities sum; confidence reflects data quality | ✅ **Done** | #1–#3, #9, #10 shipped. |
| **WS2 — Trader Relevance** | Personalization changes structure, not just headers | ✅ **Done** | Prompt cascade + post-parse validators + `personalization_applied` metadata (#4). |
| **WS3 — Clarity & Actionability** | If X→Y triggers, level basis, holistic score transparency | 🟨 **Nearly done** | #5–#7, #9, #10 + calendar confidence/neutral zone shipped; **#8 deferred** (see §0.1). |

### Shipped changes

| Date | Priority | Status | Change | Key files |
|---|---|---|---|---|
| 2026-05-27 | #1 | ✅ Done | **Live News:** `immediate_reaction` auto-corrected when narrative implies a clear USD lean (label/body consistency). | `mvp_news_analyzer.py`, `test_mvp_news_analyzer.py` |
| 2026-05-27 | #2 | ✅ Done | **Calendar:** scenario probability contract — single integer %, sum=100, `[ABOVE]/[ON]/[BELOW]` framing in prompts and JSON spec. | `analysis_context_pack.py`, `gpt_ai_analysis.py`, `test_gpt_calendar_context_pack.py` |
| 2026-05-27 | #3 | ✅ Done | **Holistic:** staleness → confidence penalty/cap; `data_quality` exposes `confidence_penalty_points`, `confidence_cap`, `confidence_tier`. | `economy_holistic_scan_service.py`, `test_economy_holistic_scan_service.py` |
| 2026-05-27 | #4 | ✅ Done | **All surfaces:** personalization cascade in prompts (swing vs day structure, preferred pairs first) **plus** post-parse validators and `personalization_applied` QA metadata on API responses. Pair reordering uses normalized `EUR/USD` ↔ `EURUSD` matching. | `analysis_context_pack.py`, `gpt_ai_analysis.py`, `mvp_news_analyzer.py`, `economy_holistic_scan_service.py`, `analysis_personalization.py`, `analysis_personalization_validation.py`, `analysis_pipeline.py`, `app.py`, `test_analysis_personalization_validation.py` |
| 2026-05-27 | #5 | ✅ Done | **Holistic:** score scale contract + component breakdown on API and Economies UI (band position, driver contributions, position labels). | `economy_holistic_scan_service.py`, `Economies.jsx`, `Economies.css`, `test_economy_holistic_scan_service.py` |
| 2026-05-27 | #6 | ✅ Done | **Holistic:** per-pair unique drivers/invalidations (ECB/BoJ/AUD/GBP channels); GPT anti-copy-paste validation. | `holistic_pair_commentary.py`, `economy_holistic_scan_service.py`, `Economies.jsx`, `test_holistic_pair_commentary.py` |
| 2026-05-27 | #7 | ✅ Done | **All surfaces:** mandatory If→then triggers in prompts + post-parse enforcement (`actionable_triggers_applied` metadata); deterministic fallbacks when prose is passive-only. | `analysis_actionable_conditionals.py`, `analysis_pipeline.py`, context pack, `gpt_ai_analysis.py`, `mvp_news_analyzer.py`, `economy_holistic_scan_service.py` |
| 2026-05-27 | #9 | ✅ Done | **All surfaces:** NEUTRAL sub-classes (`true_neutral`, `neutral_bullish_lean`, `neutral_bearish_lean`); holistic from score band; news `reaction_display`; calendar `display_bias`; `bias_classification_applied` metadata. | `analysis_bias_classification.py`, `analysis_pipeline.py`, `economy_holistic_scan_service.py`, `Overview.jsx`, `LiveNewsFeed.jsx` |
| 2026-05-27 | #10 | ✅ Done | **Holistic:** score↔narrative bridge when `geo_severity` is CRITICAL/ELEVATED — GPT prompt + validator + deterministic fallback; `score_narrative_bridge`, `score_bridge_present`, highlight + collapsible UI. Scores unchanged. | `analysis_score_narrative_bridge.py`, `economy_holistic_scan_service.py`, `Economies.jsx`, `test_analysis_score_narrative_bridge.py` |
| 2026-05-27 | Backlog | ✅ Done | **Calendar confidence:** deterministic score/tier/reason + `confidence_methodology_applied`; macro freshness penalty; Overview shows `confidence_reason`. | `analysis_calendar_confidence.py`, `analysis_pipeline.py`, `Overview.jsx` |
| 2026-05-27 | Backlog | ✅ Done | **Calendar neutral zone:** ±0.1 pp inline band on `market_scenarios.neutral_zone` + GPT prompt rules. | `calendar_scenario_engine.py`, `analysis_context_pack.py` |
| 2026-05-27 | Backlog | ✅ Done | **Holistic pair staleness:** `stale_input` on `pair_setups` when scan quality poor / inputs >14d stale; UI badge. | `economy_holistic_scan_service.py`, `Economies.jsx` |
| 2026-05-28 | Backlog | ✅ Done | **Holistic §4.5 swing UI:** Economies now visually prioritizes long-term thesis for swing profile (primary card/pill), while short-term is explicitly framed as entry/noise filter. | `economy_holistic_scan_service.py`, `Economies.jsx`, `Economies.css` |
| 2026-05-28 | Backlog | ✅ Done | **Calendar §2.4 plan structure:** deterministic `trading_plan_structured` (trigger, direction, entry, target, invalidation, sizing) + prompt contract + Overview rendering block. | `analysis_calendar_trading_plan_structure.py`, `analysis_pipeline.py`, `analysis_context_pack.py`, `Overview.jsx` |
| 2026-05-28 | Backlog | ✅ Done | **Live News §3.5 correlation specificity:** deterministic pair/channel-aware `correlation_risk_detail`, `correlation_pairs`, and `correlation_risk_display` instead of generic medium label; Overview renders detail. | `analysis_news_correlation_risk.py`, `analysis_pipeline.py`, `analysis_context_pack.py`, `Overview.jsx`, `test_analysis_news_correlation_risk.py` |
| — | Input layer | ✅ Done (prior) | AnalysisContextPack, calendar/news/holistic wiring, `holistic_scan_context.json` v1.1.0 overlay, deterministic calendar scenario direction table (`calendar_scenario_engine.py`). | See Phase A–H work; not re-listed here unless regressions found. |

### Review section mapping (what improved)

| Review finding | Section | Addressed by |
|---|---|---|
| 1.1 Generic language / no conditionals | Cross-cutting | #7 — If→then prompts + validators + fallbacks |
| 1.4 Personalization cosmetic | Cross-cutting | #4 — prompt cascade + validators + metadata |
| 1.5 NEUTRAL overuse | Cross-cutting | #9 — lean sub-classes + #1 reaction guard |
| 1.2 Unexplained confidence | Cross-cutting | #3 holistic staleness; **calendar** `confidence_methodology_applied` + `confidence_reason` (2026-05-27 backlog) |
| 2.2 Neutral scenario too precise | Calendar | Inline `neutral_zone` band on `market_scenarios` + prompt rules |
| 2.3 90% confidence unanchored | Calendar | Deterministic confidence in `analysis_calendar_confidence.py` |
| 4.6 Stale data not acted on (pairs) | Holistic | `stale_input` on `pair_setups` + Economies **STALE DATA** badge |
| 2.x Scenario probabilities | Calendar | #2 |
| 3.x Reaction label contradiction | Live News | #1 |
| 4.x Stale confidence contradiction | Holistic | #3 |
| 4.1 Composite scores unexplained | Holistic | #5 — `score_scale`, `component_breakdown`, UI band + driver table |
| 4.3 Identical pair commentary | Holistic | #6 — pair sensitivity profiles + GPT distinctness checks |
| 4.4 CRITICAL theme vs neutral score | Holistic | #10 — score bridge sentence + driver references |
| 1.6 Narrative vs score disconnect | Cross-cutting | #10 — holistic bridge (geo CRITICAL/ELEVATED) |

### Test coverage added/updated (backend)

- `test_mvp_news_analyzer.py` — reaction consistency
- `test_economy_holistic_scan_service.py` — staleness confidence tiers + score scale/breakdown contract
- `test_analysis_personalization_validation.py` — validators + pair reordering
- `test_analysis_context_pack.py`, `test_gpt_calendar_context_pack.py`, `test_holistic_gpt_narrative.py` — personalization cascade in prompts
- `test_analysis_actionable_conditionals.py`, `test_holistic_pair_commentary.py` — If→then enforcement, per-pair commentary
- `test_analysis_score_narrative_bridge.py` — CRITICAL/ELEVATED score bridge copy + validator
- `test_analysis_calendar_confidence.py` — calendar confidence methodology + neutral zone

**Last regression run:** 55+ tests passing across the modules above (re-run `backend/` unittest suite before each PR).

### API metadata (QA)

Responses finalized through `finalize_analysis()` with a user profile now include:

```json
"personalization_applied": { "...": "see above" },
"actionable_triggers_applied": {
  "surface": "live_news",
  "conditional_count": 2,
  "checks": [{ "id": "trading_implications_conditional", "passed": true }],
  "compliance_score": 100,
  "enforcement_actions": []
}
```

`bias_classification_applied` (after **#9**). Holistic scans also expose `score_bridge_present`, `score_narrative_bridge`, and `score_bridge_applied` (after **#10**).

Validators measure compliance for QA; they do **not** block API responses when checks fail (same pattern as personalization).

### Priority queue (summary)

| Priority | Status | One-line |
|---|---|---|
| #1–#7 | ✅ Done | Trust, personalization, holistic transparency, If→then |
| #8 | ⏸️ Deferred | Level basis — needs OHLC provider ([§0.1](#01-8-deferred--level-labeling-approach-when-data-is-ready)) |
| **#9** | ✅ Done | NEUTRAL sub-classifications — `bias_classification`, `display_bias`, `reaction_display` + finalize metadata |
| **#10** | ✅ Done | Holistic score ↔ narrative bridge for CRITICAL/ELEVATED themes |
| Backlog | 📋 Later | See [§0.3](#03-backlog--later-no-blocker-on-8) |

**Order:** (return to **#8** when OHLC provider exists) → backlog items as needed.

### 0.1 #8 deferred — level labeling (approach when data is ready)

**Why deferred:** FXSentinel today has **last-trade quotes** (TradingView ticker feed) only. `live_market_data` explicitly removed computed `key_levels` because they were not trustworthy. GPT citing "1.1600 support" or "prior swing" without OHLC is worse than no level — it looks precise but is fabricated.

**What we already do (keep):**
- Context pack `level_anchor_policy`: `illustrative` when session closed; prompts say "Illustrative levels:" and avoid live-entry framing.
- Calendar `trading_plan.key_levels` must not pretend to be technical structure when markets are closed.

**Do not ship until data exists:**
- Post-parse auto-tags like `(prior weekly support)` unless that level came from your data layer.
- Renaming spot to "support/resistance" — review §3.2 calls this out as misleading.

**Phased approach when you add a provider:**

| Phase | Data | Allowed basis labels in copy | GPT rule |
|---|---|---|---|
| **A — Honest interim** (optional, no new vendor) | Spot quote only | `(current spot reference)`, `(illustrative round level)`, `(~0.5% from spot — illustrative)` | Ban pivot/swing/session high/low in prompts; validator rejects forbidden basis words |
| **B — Minimal structure** | Daily OHLC + prior day H/L/C | `(prior day high)`, `(prior day low)`, `(prior close)` | Pass levels in `AnalysisContextPack.market_snapshot.structured_levels`; GPT may only cite levels from that list |
| **C — Trader-grade** | Intraday bars + swings / pivots | `(session high)`, `(swing low)`, `(weekly pivot)` | Compute server-side; store `level_id` + `basis` + `price`; UI shows source + as-of time |

**Provider options (beginner-friendly):**
1. **TradingView / broker API** — if you already pay for bars, add a small daily-bar cache job per major pair.
2. **Polygon, Twelve Data, OANDA, FXCM** — REST OHLC; good for daily/4H structure first.
3. **Compute yourself** — ingest 1D CSV per pair, compute prior H/L and round levels in `backend/services/level_context_service.py` (deterministic, testable).

**Architecture sketch (Phase B+):**
```
level_context_service.build_levels(pair) → [{ price, basis, as_of, source }]
     ↓
analysis_context_pack (structured_levels in MARKET SNAPSHOT)
     ↓
GPT prompt: "Only cite levels from structured_levels; always include basis in parentheses."
     ↓
finalize_analysis: level_labeling validator (price must match allowlist or get stripped/flagged)
```

**Acceptance criteria before closing #8:**
- [ ] Every numeric level in API output maps to an entry in `structured_levels` OR is tagged illustrative/spot-reference.
- [ ] Validator fails QA if text contains "pivot/swing/support" without a matching structured level.
- [ ] UI can show "Level source: prior day low (2026-05-26)" when you want transparency.

### 0.2 Active roadmap (next work, in order)

Use this section when picking up the review again. **No external market-structure data required** for #9 or #10.

---

#### Next: #9 — NEUTRAL sub-classifications (all surfaces)

**Problem (review §1.5):** `NEUTRAL` is overused; traders cannot tell a mild lean from a true balance. News already has a partial fix (#1: label vs body), but labels are still coarse.

**Target labels (display):**

| Internal key | UI label | When to use |
|---|---|---|
| `true_neutral` | TRUE NEUTRAL | Score/narrative balanced; no consistent lean |
| `neutral_bullish_lean` | NEUTRAL · BULLISH LEAN | In neutral score band but positive drivers dominate |
| `neutral_bearish_lean` | NEUTRAL · BEARISH LEAN | In neutral score band but negative drivers dominate |
| `bullish` / `bearish` | Unchanged | Outside neutral band (existing thresholds) |

**Suggested implementation (same pattern as #4 and #7):**

1. **Deterministic derivation (holistic)** — in `economy_holistic_scan_service.py`:
   - If `bias == neutral` and score in neutral band (-20 to +20): set `display_bias` from score (e.g. score above +5 → bullish lean, below -5 → bearish lean, else true neutral).
   - Expose `bias_detail` or extend `display_bias` string (already used in UI).
2. **Calendar** — after GPT parse or in finalize:
   - Parse `implications_takeaways.market_bias` (starts with BULLISH/BEARISH/NEUTRAL).
   - If NEUTRAL but `forward_scenarios` probabilities skew above 55% one way, suggest lean in `display_bias` metadata.
3. **Live news** — extend beyond `immediate_reaction`:
   - Add optional `reaction_detail: neutral_bearish_lean` when body implies direction but magnitude is weak.
   - Or map `immediate_reaction` + confidence to lean for UI chip.
4. **Prompts** — add to `CALENDAR_PACK_PROMPT_RULES`, `NEWS_PACK_PROMPT_RULES`, holistic narrative rules: require lean sub-label when in neutral band.
5. **Validator** — new `analysis_bias_classification.py` (or extend existing validators):
   - If narrative contains clear directional words and label is `neutral` / `TRUE NEUTRAL` → flag or auto-correct lean.
   - Attach `bias_classification_applied` metadata on finalize (mirror `personalization_applied`).
6. **UI** — `Overview.jsx` (calendar/news), `Economies.jsx` (holistic regime pills): show `display_bias` when present.

**Acceptance criteria:**
- [ ] Holistic short/long `display_bias` distinguishes lean vs true neutral when score is in [-20, 20].
- [ ] News no longer shows plain NEUTRAL when body clearly leans (beyond current USD guard).
- [ ] Calendar `market_bias` line can show lean sub-class in API + UI.
- [ ] Tests for score→lean mapping and narrative↔label consistency.

**Review refs:** §1.5, priority #9, partial #1.

---

#### ✅ Done: #10 — Holistic score ↔ narrative bridge

Shipped in `analysis_score_narrative_bridge.py`: GPT prompt flag `score_bridge_required`, validator on merge, deterministic fallback via `_finalize_scan_score_bridge()`, API fields `score_narrative_bridge` / `score_bridge_present`, Economies collapsible under geopolitical context.

---

#### Next (after review priorities #1–#10)

| Item | Blocker | Notes |
|---|---|---|
| **#8 Level basis** | OHLC / levels provider | [§0.1](#01-8-deferred--level-labeling-approach-when-data-is-ready) |
| **§5 prompt templates** | Some need data | Consensus range, historical avg move, per-pair levels — track per field |
| **V1 analysis spine** | Product decision | `ANALYSIS_V1_ENABLED` off by default; large UX project |

### 0.3 Backlog & later (no blocker on #8)

Smaller or product-dependent items — not in the active queue until you choose them.

**Trust & consistency (no new vendors)**

- **Calendar confidence methodology (§1.2):** Document formula in API (`confidence_score` + `confidence_reason`); tie to data quality, event impact, scenario spread — similar to holistic staleness tiers.
- **Holistic pair-level staleness flags (§4.6):** Add `stale_input: true` on `pair_setups[]` when `data_quality.status == poor`; show badge in Economies UI.
- **Calendar neutral scenario as range (§2.x / §5.1):** Widen "on forecast" definition in prompts (e.g. within ±0.1% of consensus) — separate from #9 lean labels.

**Needs external or curated data (pair with #8 or calendar enrichment)**

- Prior 3 prints, consensus min/max, historical avg move (§5.1).
- Per-pair technical levels in prompts (§5.2–5.3) — same dependency as #8.

**Product / architecture**

- **Analysis V1 spine** — unified `spine` object across calendar/news/holistic; enable flag + Overview UI sections.
- **Fixture / golden tests** — snapshot real GPT outputs for regression (optional QA harness).

**When you return to this doc**

1. **V1 queue (#1–#10):** Complete except **#8** (deferred). See [Priority queue](#priority-queue-summary) and [§0.4](#04-implemented-rework-summaries-whats-changed-for-users).
2. **V2 work:** Start at [§0.5](#05-version-2-implementation-tracker-after-v1-ships) — Tier 1 trust bugs first.
3. Re-run backend tests; spot-check calendar, news, and US holistic per [V2 acceptance spot-checks](#v2-acceptance-spot-checks).
4. Revisit **#8** only when OHLC provider exists ([§0.1](#01-8-deferred--level-labeling-approach-when-data-is-ready)).

---

### 0.4 Implemented rework summaries (what's changed for users)

Use this as the short handoff view of what was reworked and why it matters in live usage.

**Core priorities shipped (#1-#7, #9, #10):**

- **#1 Label/body consistency (Live News):** reaction labels no longer stay neutral when narrative clearly leans; post-parse guard aligns enum with text so users do not see contradictory chips.
- **#2 Scenario math contract (Calendar):** forward scenarios were reworked to integer probabilities summing to 100 with canonical `[ABOVE]/[ON]/[BELOW]` framing; this removes overlapping/invalid scenario math.
- **#3 Staleness-aware confidence (Holistic):** confidence is now penalized/capped by staleness tier and exposed in `data_quality`; scans no longer present stale inputs with near-normal conviction.
- **#4 Personalization cascade (All surfaces):** personalization moved from cosmetic headers to output behavior (pair ordering, structure bias by style) with validation metadata `personalization_applied`.
- **#5 Score transparency (Holistic):** added explicit score scale, neutral band position, and component breakdown drivers; users can see why the regime score is where it is.
- **#6 Per-pair uniqueness (Holistic):** pair commentary was reworked from reusable templates to pair-specific macro channels with anti-duplication validation.
- **#7 Actionable conditionals (All surfaces):** passive watch-language is auto-replaced or supplemented with deterministic If→then triggers, tracked by `actionable_triggers_applied`.
- **#9 Neutral sub-classification (All surfaces):** plain NEUTRAL now resolves into TRUE NEUTRAL / BULLISH LEAN / BEARISH LEAN when appropriate, improving directional readability without forcing full conviction.
- **#10 Score↔narrative bridge (Holistic):** CRITICAL/ELEVATED geo themes now require an explicit bridge sentence to explain neutral-ish composite scores via driver offsets; no deterministic score changes.

**Backlog items now completed (non-#8):**

- **Calendar confidence methodology (§1.2):** confidence is now deterministic and explainable (`confidence_reason`, factor metadata), rather than GPT label mapping only.
- **Calendar neutral zone range (§2.2):** inline scenario reworked from exact tick to neutral band (`market_scenarios.neutral_zone`), reducing unrealistic “exact-print” assumptions.
- **Calendar trading-plan structure (§2.4):** added `trading_plan_structured` with trigger, direction, entry, target, invalidation, and sizing for execution-ready guidance.
- **Live news correlation specificity (§3.5):** generic correlation-risk labels replaced with pair/channel-aware detail (`correlation_risk_detail`, correlated pairs list).
- **Holistic swing UI execution (§4.5):** Economies now visually prioritizes long-term thesis for swing users and demotes short-term to entry/noise filter context.
- **Holistic pair staleness visibility (§4.6):** per-pair `stale_input` + UI badge added so uncertainty is visible where decisions are made, not only in top-level disclaimers.

**Still intentionally deferred:**

- **#8 Level basis / technical structure:** remains blocked on OHLC/structured levels provider; do not claim pivot/swing/support semantics without that data layer.

---

### 0.5 Version 2 Implementation Tracker (after V1 ships)

**Source:** Claude re-test of live outputs — see [Version 2 Review — source notes](#version-2-review-after-changes-source-notes) (bottom of this doc).

**Started:** 2026-05-28 · **Scope:** Integration bugs, UI wiring gaps, and new product ideas surfaced *after* V1 priority queue (#1–#10) shipped.

**How to use:** Work **Tier 1** first (trust-breaking). Mark rows ✅ when code + UI are verified on a real output (PCE calendar, ECB news, US holistic scan). Update **Last verified** column with date and fixture/event name.

#### V2 workstream status

| Workstream | Focus | Status | Open IDs |
|---|---|---|---|
| **V2-WS1 — Calendar integration** | Scenario table direction, confidence visible, spot honesty, catalyst specificity | ✅ Done | — |
| **V2-WS2 — Live News integration** | Label currency axis, correlation UI, timeframe/longevity, type + react playbook | ✅ Done | — |
| **V2-WS3 — Holistic integration** | Dedup bridge, lean in takeaways, share label, confidence strip | ✅ Done | — |
| **V2-WS4 — Cross-surface synthesis** | Regime alignment, session stamp | 📋 Planned | V2-X1–X2 |
| **V2-WS5 — Data enrichments** | Surprise history, options implied move, regime trend | 📋 Later | V2-CA1–CA2, V2-HA1–HA2 |

#### Tier 1 — Trust bugs (do first)

| ID | Surface | Issue | Likely fix area | Status | Last verified |
|---|---|---|---|---|---|
| **V2-C1** | Calendar | Market Scenarios table inverted vs probability section (Above→Bearish for USD) | `calendar_scenario_engine.py`, `Overview.jsx` | ✅ Done | 2026-05-28 — inflation/PCE: higher print = bullish for event currency |
| **V2-C2** | Calendar | Confidence % shown without visible `confidence_reason` | `Overview.jsx` (already wired; verify on next PCE run) | ✅ Done | 2026-05-28 — field renders when API provides it |
| **V2-N1** | Live News | Reaction label currency wrong (ECB hawkish → USD lean; body says EUR) | `analysis_bias_classification.py`, `mvp_news_analyzer.py`, `app.py` | ✅ Done | 2026-05-28 — `detect_news_primary_currency` + `(EUR)` display |
| **V2-N2** | Live News | Correlation risk still generic in UI (`MEDIUM` only) | `LiveNewsFeed.jsx` (+ Overview already had detail) | ✅ Done | 2026-05-28 |
| **V2-H3** | Holistic | Score bridge paragraph duplicated (Geopolitical + “Why score neutral?”) | `analysis_score_narrative_bridge.py`, `Economies.jsx` | ✅ Done | 2026-05-28 |
| **V2-H4** | Holistic | Key Takeaways still plain `NEUTRAL` (lean sub-class not cascaded) | `economy_holistic_scan_service.py` `_build_highlights` | ✅ Done | 2026-05-28 |
| **V2-H5** | Holistic | Regime strip confidence `N/A` vs 50% elsewhere | `Economies.jsx` `renderRegimeLine` 4-part parse | ✅ Done | 2026-05-28 |

#### Tier 2 — Clarity & honesty (no new vendors)

| ID | Surface | Issue | Likely fix area | Status | Last verified |
|---|---|---|---|---|---|
| **V2-C3** | Calendar | `key_levels` still spot anchors — misleading precision | `analysis_calendar_content_guard.py` + Overview `key_levels_label` | ✅ Done | 2026-05-28 |
| **V2-C4** | Calendar | Vague catalyst (“geopolitical developments in the Middle East”) | Post-parse filter + prompt rules | ✅ Done | 2026-05-28 |
| **V2-H2** | Holistic | Driver **Share** column exceeds 100% — misleading label | `Economies.jsx` → **Signal weight** + tooltip | ✅ Done | 2026-05-28 |
| **V2-H1** | Holistic | Short-term and long-term scores identical (-13) — looks like one pipeline | `score_horizon_note` when scores match; different driver sets documented | ✅ Done | 2026-05-28 |
| **V2-N3** | Live News | No signal that non-primary pairs were assessed/filtered | `pairs_focus_display` metadata + LiveNewsFeed line | ✅ Done | 2026-05-28 |
| **V2-N4** | Live News | Timeframe “2–4 hours” for multi-week ECB policy story | `impact_horizon`, `timeframe_immediate`, `timeframe_positioning` | ✅ Done | 2026-05-28 |
| **V2-R1** | Calendar | Generic “Forward focus: monitor inflation…” filler | Replaced at finalize when generic | ✅ Done | 2026-05-28 |
| **V2-R3** | Holistic | Developer file paths in trader-facing Source references | `Economies.jsx` — collapsed **Technical metadata** | ✅ Done | 2026-05-28 |
| **V2-R4** | Holistic | `sum(driver × weight)` footnote inline — move to methodology | Collapsible **How scores are calculated** | ✅ Done | 2026-05-28 |

#### Tier 3 — New features (product / data)

| ID | Surface | Suggestion | Dependency | Status |
|---|---|---|---|---|
| **V2-X1** | All | Regime alignment flag (calendar + news + holistic agree/conflict) | Cross-surface compare in `analysis_pipeline` or UI | 📋 Planned |
| **V2-X2** | All | Session context stamp (London/NY/Asia at generation) | Server timezone + session calendar | 📋 Planned |
| **V2-CA1** | Calendar | Surprise history table (last 4–6 prints) | Calendar/history data source | 📋 Later |
| **V2-CA2** | Calendar | Options-implied move around event | Options data vendor | 📋 Later |
| **V2-NA1** | Live News | News longevity classification (hours vs weeks) | `news_type` + chip; finalize heuristics | ✅ Done | 2026-05-28 |
| **V2-NA2** | Live News | Follow / fade / wait-for-confirmation label | `initial_reaction_guidance` + chip | ✅ Done | 2026-05-28 |
| **V2-HA1** | Holistic | Regime trend arrow vs prior scans | Persist scan history / compare last N | 📋 Later |
| **V2-HA2** | Holistic | Counter-economy regime snippet on pair rows | Second economy scan or cached bias | 📋 Later |

#### V2 — linked to V1 #8 (do not fake)

| ID | Surface | Issue | Status |
|---|---|---|---|
| **V2-C3** / **V2-R2** | Calendar | Key levels = spot only | ⏸️ Same as **#8** — rename/hide until OHLC ([§0.1](#01-8-deferred--level-labeling-approach-when-data-is-ready)) |

#### V2 shipped log

| Date | ID | Change | Key files |
|---|---|---|---|
| 2026-05-28 | V2-C1 | Inflation/PCE scenario direction: hot print = **bullish** for event currency (aligns table with `[ABOVE]` prose) | `calendar_scenario_engine.py`, `Overview.jsx`, `test_calendar_scenario_engine.py` |
| 2026-05-28 | V2-N1 | News reaction labels use detected event currency (`EUR`, `GBP`, …) not always `(USD)` | `analysis_bias_classification.py`, `mvp_news_analyzer.py`, `app.py` |
| 2026-05-28 | V2-N2 | Live News UI shows `correlation_risk_detail` + pairs list | `LiveNewsFeed.jsx` |
| 2026-05-28 | V2-H3–H5, H2, R3 | Holistic: no duplicate score bridge in geo block; `display_bias` in highlights/trader brief; regime strip parses confidence; Signal weight label; metadata collapsed | `analysis_score_narrative_bridge.py`, `economy_holistic_scan_service.py`, `Economies.jsx` |
| 2026-05-28 | Tier 2 batch | Calendar content guard (C3/C4/R1); news horizon + pairs focus (N3/N4); holistic H1 note + R4 methodology collapse | `analysis_calendar_content_guard.py`, `analysis_news_horizon.py`, `analysis_pipeline.py`, `Overview.jsx`, `LiveNewsFeed.jsx`, `Economies.jsx` |
| 2026-05-28 | V2-NA1, NA2 | News `news_type` chip + `initial_reaction_guidance` (follow/fade/wait); GPT + finalize overrides | `analysis_news_classification.py`, `mvp_news_analyzer.py`, `LiveNewsFeed.jsx` |

#### V2 acceptance spot-checks

Before marking Tier 1 done, re-run these three outputs:

1. **Calendar:** Core PCE (or similar USD inflation) — scenarios table direction matches `[ABOVE]` prose; `confidence_reason` visible.
2. **Live News:** ECB tightening / hawkish headline — reaction label names **EUR** (or event currency), not USD; correlation detail visible.
3. **Holistic:** US economy scan — no duplicate score-bridge paragraph; Key Takeaways show **Neutral · Bearish Lean**; strip confidence matches scorecard.

**When you return to V2 work**

1. **Tier 2** + news **NA1/NA2** shipped; remaining Tier 3: cross-surface (X1–X2), calendar/holistic data (CA/HA).
2. Next: [Tier 3](#tier-3--new-features-product--data) cross-surface or §0.6 golden-set tests.
3. Re-run spot-checks after deploy (calendar PCE, ECB news, US holistic).

### 0.6 Architecture deepening (2026-05-28) — quality & control

| Pillar | Problem | Approach shipped |
|---|---|---|
| **A Holistic direction** | Scores clustered in ±20 “neutral”; headline always felt flat | Narrow neutral band to **±12**, conviction at **±15**; `headline_bias` (e.g. **BULLISH LEAN**); split `data_confidence` vs `directional_conviction`; scan `v1.5` |
| **B News currency** | Heuristic-only `(USD)` suffix; no QA | GPT must return `primary_currency` + `reaction_rationale`; heuristics validate (`reaction_currency_source` metadata) |
| **C Calendar confidence** | Single % looked like “GPT sureness” | **Data quality score** (deterministic) + **Edge** (GPT `edge_confidence` + `edge_confidence_reason`); Overview labels both |

**Still open:** golden-set accuracy tests for news currency; holistic long/short using different driver sets but often similar totals (V2-H1).

---

## 1. Cross-Cutting Issues (All Sections)

These problems appear in **all three** analysis sections and should be addressed at the system/prompt level before section-specific fixes.

---

### 1.1 Generic Language — No Actionable Conditionals

**Problem:** Across all three sections, the AI uses passive observational language that describes a situation without telling the trader what to do about it.

Examples seen:
- *"Monitor upcoming inflation indicators"*
- *"Watch EUR/USD closely"*
- *"Consider swing trading strategies"*
- *"Traders should remain vigilant"*

This language has zero trading utility. A trader reading during a live session needs a conditional trigger — not a reminder to pay attention.

**Fix:** Every analysis section must include at minimum one **"If X → then Y"** statement. Replace observational language with conditional action framing.

> Example replacement: *"If print exceeds 0.3%, expect EUR/USD to test 1.1580 — a sustained break below would confirm USD bullish follow-through."*

---

### 1.2 Unexplained Confidence Scores

**Problem:** Confidence scores appear in both the Economic Calendar (90%) and Holistic Scan (60%) with no methodology behind them. They read as auto-generated placeholders.

Worse: In the Holistic Scan, the scan reliability is flagged as **POOR** (indicators 28 days stale), yet the confidence score remains unchanged at 60%. This is a direct contradiction that erodes trust.

**Fix:**
- Define confidence scoring methodology (e.g. data freshness weighting, consensus spread, historical volatility of the release)
- Make confidence **dynamically responsive** to data staleness
- If data is stale, reduce the displayed confidence score and state explicitly why it was reduced

---

### 1.3 Price Levels Cited Without Justification

**Problem:** All three sections reference price levels (e.g. EUR/USD 1.16392, 1.1600 support, USD/JPY 159.397) without explaining their significance. Are these daily pivots? Prior swing highs/lows? Round numbers? Session opens?

Without context, these numbers are arbitrary and potentially misleading.

**Fix:** Every price level cited must carry a one-word or short qualifier explaining its basis.

> Example: *"EUR/USD 1.1600 (prior weekly support)"* or *"USD/JPY 159.40 (current spot anchor)"*

---

### 1.4 Personalization Is Acknowledged But Not Executed

**Problem:** All three sections reference trader personalization (swing profile, currency preferences, trading style) in the header or metadata — but the body of the analysis remains generic. The personalization label is cosmetic.

Specifically:
- Holistic Scan detects swing-trading profile and says "prioritize long-term regime" — but the long-term section is equally thin as the short-term section
- Live News flags EUR/USD as the key pair regardless of the trader's actual preferred pairs
- Economic Calendar doesn't adjust strategy framing for trader type (swing vs. scalper vs. position)

**Fix:** Personalization must cascade into the output structure itself:
- Swing trader → long-term section is structurally deeper, short-term treated as noise filter
- Scalper → immediate reaction and volatility spike framing prioritised
- Currency preference → only pairs relevant to the trader are surfaced; irrelevant pairs are excluded or pushed to a secondary section

---

### 1.5 Overuse of "NEUTRAL" Label — Loss of Signal

**Problem:** In all three sections, NEUTRAL is applied broadly to situations that actually have directional lean. When everything is NEUTRAL, the label loses meaning and traders stop reading it.

Examples:
- Holistic Scan: both short-term AND long-term scores are NEUTRAL, all four pairs are NEUTRAL
- Live News: Immediate reaction labelled NEUTRAL while body text describes "downward pressure on the euro" and "tempered bullish sentiment" — a clear bearish lean
- Economic Calendar: Neutral scenario defined so narrowly (exactly 0.3%) it is nearly impossible to trigger

**Fix:** Introduce sub-classifications:
- **NEUTRAL-BULLISH LEAN** — score or narrative tilts positive but lacks conviction
- **NEUTRAL-BEARISH LEAN** — score or narrative tilts negative but lacks conviction
- **TRUE NEUTRAL** — balanced drivers, genuinely no directional read

Force internal consistency: if the narrative implies a direction, the label must match.

---

### 1.6 Narrative and Quantitative Output Are Disconnected

**Problem:** In the Holistic Scan particularly, critical geopolitical themes (Hormuz closure labelled CRITICAL, energy shock) exist in the narrative but have no visible effect on the regime scores. A trader reading both will ask: "If this is CRITICAL, why is the score only -16?"

The same pattern appears in the Economic Calendar — market reaction section references strong USD moves but the probability scenarios don't fully reflect this.

**Fix:** Require the prompt to include a **bridge rule**: any theme flagged as CRITICAL or ELEVATED must either (a) show a measurable contribution to the composite score, or (b) include an explicit sentence explaining why it is being discounted in the score (e.g. offset by a countervailing factor).

---

## 2. Economic Calendar Analysis

**Test Event:** Core PCE Price Index m/m

---

### 2.1 Probability Scenarios Don't Sum to 100%

**Problem:** The three probability ranges given are:
- Bullish: 40–50%
- Neutral: 20–30%
- Bearish: 30–40%

These ranges overlap and don't sum cleanly to 100%. At minimum they sum to 90%, at maximum 120%. This is a basic mathematical error that will undermine trader trust immediately, especially alongside a "90% Analysis Confidence" claim.

**Fix:** Instruct the AI to output **single integer probabilities that must sum to exactly 100%**. If ranges are preferred for communicating uncertainty, define non-overlapping bands (e.g. 35–45% / 20–25% / 30–40% with explicit note they represent estimate spread, not simultaneous possibilities).

---

### 2.2 Neutral Scenario Trigger Is Unrealistically Precise

**Problem:** The neutral scenario is defined as "print is exactly 0.3%." In reality, a 0.2% or 0.3% print may both be read by the market as "in-line." Defining neutral as a single data point makes this scenario statistically near-zero and practically useless.

**Fix:** Define the neutral zone as a **range**, informed by historical standard deviation of the release and current consensus spread.

> Example: *"Neutral: print between 0.25%–0.35%, within one standard deviation of consensus — limited market reaction expected."*

---

### 2.3 "90% Analysis Confidence" Is Unanchored

**Problem:** No methodology is provided for why this event receives 90% confidence. Is it based on: historical consistency of this release? Strength of consensus? Analyst survey spread? Fed's recent communication clarity?

Without a basis it reads as a default placeholder.

**Fix:** Tie confidence to measurable inputs. Suggested factors:
- Consensus analyst spread (tight = higher confidence)
- Fed's recent explicit guidance on this indicator
- Historical market sensitivity to this specific release
- Data availability and freshness

---

### 2.4 Trading Plan Lacks Specific Structure

**Problem:** The trading plan section says:
- *"Consider swing trading strategies on USD pairs"*
- *"Avoid aggressive short-term trades immediately post-release"*
- *"Key levels: anchored to current spot"*

None of these are a trading plan. A trader needs: entry condition, directional trigger, approximate target, and stop logic — even if framed conditionally.

**Fix:** Require the trading plan section to follow a structured template:

```
If [scenario trigger]:
  Direction: [long/short which pair]
  Entry condition: [price action confirmation or level break]
  Target zone: [approximate level with basis]
  Invalidation: [what price action would kill the thesis]
  Sizing note: [any volatility-adjusted guidance]
```

---

### 2.5 Key Levels Are Just Spot Prices

**Problem:** EUR/USD 1.16392 and USD/JPY 159.397 are listed as "key levels" but are simply current spot prices at time of generation. Anchoring to spot is not technical analysis — it's a timestamp.

**Fix:** Pass real technical levels (prior session high/low, weekly pivots, significant round numbers, recent swing points) into the prompt from your data layer, and require the AI to reference these instead of spot.

---

## 3. Live News Analysis

**Test Event:** ECB/Guindos growth warning headline

---

### 3.1 Reaction Label Contradicts Body Text

**Problem:** The immediate reaction is labelled **NEUTRAL**, but the analysis body states:
- *"downward pressure on the euro"*
- *"temper the bullish sentiment"*
- *"dovish ECB expectations"*

This is a bearish lean, not neutral. A trader making a fast decision on a live news event reads the label first — if it says NEUTRAL but the text is bearish, the output is actively misleading.

**Fix:** Implement a consistency rule in the prompt: **the reaction label must match the directional lean of the body text**. If the body implies bearish, label must be BEARISH or BEARISH-LIGHT. Only use NEUTRAL when the analysis is genuinely balanced across both directions.

---

### 3.2 Trader's Pair Preferences Are Not Reflected

**Problem:** This section is described as tailored to the trader's onboarding profile and currency preferences — but the output references EUR/USD without any check against whether this trader actually trades EUR/USD.

If a trader's profile shows they trade GBP/USD and USD/CAD, the entire output is irrelevant noise. No filtering has occurred.

**Fix:**
- Always pass trader's active pairs into the prompt explicitly
- Instruct the AI to open with: *"Based on your active pairs, [X] is the most relevant to this event"*
- If the news event has no direct relevance to the trader's pairs, say so explicitly rather than forcing a connection

---

### 3.3 No Actionable Trigger Defined

**Problem:** The trading implications section ends with: *"monitoring sentiment indicators and ECB communications will be crucial in the next 2–4 hours."*

This tells the trader nothing they couldn't infer themselves. There is no trigger condition, no confirmation signal, no specific action.

**Fix:** Require a **"What triggers a trade"** field in the output — one sentence that defines the specific price action or confirmation that would warrant acting on this news:

> Example: *"A sustained break below EUR/USD 1.1620 in the next 30 minutes, on above-average volume, would confirm bearish follow-through from Guindos' comments."*

---

### 3.4 Support Level Cited Without Context

**Problem:** *"Key levels such as 1.1600 support"* — why is 1.1600 support? Prior low? Round number? Daily pivot? Without this context the level is arbitrary.

**Fix:** Same as the cross-cutting level justification fix — all levels must carry a short basis label. Ideally sourced from your data layer rather than AI-generated.

---

### 3.5 Correlation Risk Label Is Meaningless Without Specificity

**Problem:** The risk assessment shows **Correlation Risk: MEDIUM** with no explanation of which correlations are elevated or why.

**Fix:** If correlation risk is flagged, name the specific correlations relevant to the event:

> Example: *"Correlation risk: EUR/CHF may move in tandem — ECB growth concerns historically spill into CHF safe-haven demand. Monitor EUR/CHF for divergence signals."*

---

## 4. Holistic Scan

**Test Economy:** United States

---

### 4.1 Composite Scores Are Unexplained Black Boxes

**Problem:** Short-term score: -16.21, Long-term score: -13.37. A trader has no idea:
- What the scale is (-100 to +100? -50 to +50?)
- What constitutes neutral, bearish, or bullish territory
- What each sub-component contributed to the total
- Why two scores covering different time horizons are so close to each other

The false precision of ".21" and ".37" actually increases distrust — it implies mathematical rigour that isn't explained anywhere.

**Fix:**
- Define and display the score scale explicitly (e.g. *"-100 (extreme bearish) ↔ 0 (neutral) ↔ +100 (extreme bullish)"*)
- Show score as a position on that band, not just a number
- Display a component contribution table showing what each driver contributed numerically to the composite

> Example output format:
> ```
> Score: -16.21 / 100-point scale
> Neutral band: -20 to +20
> Position: Low-neutral, bearish lean
>
> Component contributions:
>   Rate momentum:      -8.4  (negative)
>   Growth momentum:    -6.2  (negative)
>   Inflation momentum: +4.1  (positive)
>   [etc.]
> ```

---

### 4.2 Confidence Does Not Reflect Data Staleness

**Problem:** Both regime scores carry 60% confidence. However, the scan reliability is flagged as **POOR** with the oldest indicator 28 days behind UTC. These two outputs directly contradict each other.

If the data is stale, the confidence should be lower. Presenting unchanged confidence while simultaneously warning about staleness creates an unresolvable signal conflict for the trader.

**Fix:**
- Build a staleness → confidence penalty mapping into the prompt logic
- Example rule: *"If oldest indicator > 14 days, reduce confidence by 10%. If > 21 days, reduce by 20%. If > 28 days, flag as LOW CONFIDENCE and add a visible disclaimer to each score."*
- The stale data warning in the header must cascade into every score and pair bias it affects

---

### 4.3 All Pairs Have Identical Commentary

**Problem:** All four pairs (EUR/USD, USD/JPY, GBP/USD, AUD/USD) have near-identical analysis:
- Range conditions prevail
- Monitor for geopolitical breaks
- Conviction reduced — inputs stale
- Invalidation: USD safe-haven bid

Each pair's analysis should be driven by the macroeconomic factors most specific to that pair's base/quote currencies. JPY is a safe-haven currency with BoJ policy specifics. AUD is a commodity currency with China exposure. GBP has UK-specific macro dynamics. None of this differentiation is present.

**Fix:** Require the prompt to generate pair-specific commentary driven by each currency's known sensitivities:
- JPY: risk-off flows, BoJ yield curve control status, Hormuz oil shock impact on Japan as energy importer
- AUD: commodity channel, China demand indicators, RBA policy stance
- GBP: UK growth/inflation divergence from US, BoE forward guidance
- EUR: ECB policy stance, European energy exposure, strategic autonomy divergence from USD

---

### 4.4 Critical Geopolitical Risk Not Reflected in Score

**Problem:** The Strait of Hormuz closure is labelled **CRITICAL** and described in significant detail — yet the regime scores sit at only -16 and -13 (within what appears to be a neutral band). A trader will reasonably ask why a CRITICAL geopolitical event produces a near-neutral score.

There is no bridge between the narrative and the quantitative output.

**Fix:** Require an explicit **score-narrative bridge sentence** whenever a CRITICAL or ELEVATED theme is present:

> Example: *"The Hormuz closure contributes approximately -8 to the composite score. The offset comes from the USD safe-haven bid (+6) and AI capex-driven growth resilience (+4), which partially neutralise the geopolitical drag — keeping the score in bearish-neutral territory rather than outright bearish."*

---

### 4.5 Swing Trader Personalization Is Not Executed in Output

**Problem:** The scan correctly identifies a swing-trading profile and states *"prioritize long-term regime and macro follow-through"* — but the long-term section receives no more depth, space, or structural emphasis than the short-term section.

For a swing trader, the short-term section should function as a noise filter (is now a bad time to enter a longer-term thesis?), while the long-term section should be the primary analysis with multi-week setup framing.

**Fix:** When swing-trading profile is detected, the output structure should change:
- Long-term section: expanded with multi-week directional thesis, macro follow-through narrative, and 3–12 month scenario framing
- Short-term section: condensed to a "current entry conditions" note — is the short-term regime aligned or opposed to the long-term thesis?
- Language: shift from "next 2–4 hours" to "over coming weeks/months"

---

### 4.6 Stale Data Warning Is Not Acted Upon

**Problem:** *"Inputs are stale — reduce conviction and refresh frequently"* appears in the header but produces no downstream effect on any output. Scores, confidence levels, and pair biases are presented identically to how they would appear with fresh data.

A warning that changes nothing is not a warning — it's a disclaimer that protects the system without protecting the trader.

**Fix:** Staleness must have concrete, visible consequences in the output:
- Confidence scores reduced (see 4.2)
- Each pair bias marked with a staleness flag visible at the pair level
- Score displayed with an uncertainty band rather than false precision
- A "last reliable as of [date]" timestamp shown prominently, not buried in source references

---

## 5. Prompt Improvement Templates

### 5.1 Economic Calendar — Additional Prompt Fields to Add

```
- Consensus range (min/max analyst estimates, not just central estimate)
- Previous 3 prints for this release
- Historical average market move on this release (pips, % move)
- Fed's current stated threshold or target for this indicator
- Instruction: probabilities must be single integers summing to 100
- Instruction: neutral zone must be a range, not a single value
- Technical levels for relevant pairs (from data layer, not AI-generated)
- Trader profile: style (swing/scalper/position) — adjust strategy framing accordingly
```

### 5.2 Live News — Additional Prompt Fields to Add

```
- Trader's active currency pairs (mandatory — filter all analysis through this)
- Trader's session preference (London / NY / Asia)
- Trader's risk profile (conservative / moderate / aggressive)
- Instruction: reaction label MUST match directional lean of body text
- Instruction: include one "What triggers a trade" sentence with specific price/action condition
- Key technical levels for trader's active pairs (from data layer)
- Instruction: if event has no relevance to trader's pairs, state this explicitly
```

### 5.3 Holistic Scan — Additional Prompt Fields to Add

```
- Score scale definition passed into prompt (e.g. -100 to +100, neutral band -20 to +20)
- Component weight definitions so AI can report contribution per driver
- Staleness → confidence penalty mapping rule
- Instruction: CRITICAL/ELEVATED themes must include score contribution bridge sentence
- Trader profile: when swing detected, expand long-term section and condense short-term
- Instruction: each pair must receive unique commentary based on its currency-specific sensitivities
- Instruction: neutral sub-classify as NEUTRAL-BULLISH, NEUTRAL-BEARISH, or TRUE NEUTRAL
- Per-pair technical levels (sourced externally, not AI-generated)
```

---

## 6. Priority Action List

Ordered by impact on trader trust and output quality:

| Priority | Issue | Affects | Action | Status |
|---|---|---|---|---|
| 1 | Reaction label vs. body text contradiction | Live News | Add consistency rule to prompt | ✅ Done — post-parse guard in `mvp_news_analyzer.py` |
| 2 | Probabilities don't sum to 100% | Economic Calendar | Force single integers, sum-to-100 rule | ✅ Done — prompt + JSON spec |
| 3 | Confidence unchanged despite stale data | Holistic Scan | Build staleness → confidence penalty | ✅ Done — tiered penalty/cap in scan service |
| 4 | Personalization cosmetic only | All Sections | Cascade profile into output structure | ✅ Done — prompt cascade + validators + `personalization_applied` |
| 5 | Score scale undefined | Holistic Scan | Define and display scale + component breakdown | ✅ Done — `score_scale`, breakdown table, band UI |
| 6 | Generic pair commentary | Holistic Scan | Per-pair currency-specific sensitivity prompt | ✅ Done — `holistic_pair_commentary.py` + validation |
| 7 | No actionable triggers | All Sections | Require conditional "If X → then Y" statements | ✅ Done — prompts + `analysis_actionable_conditionals.py` |
| 8 | Price levels unjustified | All Sections | Source levels from data layer + add basis label | ⏸️ Deferred — see §0.1 |
| 9 | NEUTRAL overused | All Sections | Introduce sub-classifications | ✅ Done — `analysis_bias_classification.py` |
| 10 | Narrative disconnected from score | Holistic Scan | Require score-narrative bridge sentence | ✅ Done |

---

*Document generated from FXSentinel AI analysis review session. Covers Economic Calendar (Core PCE), Live News (ECB/Guindos), and Holistic Scan (United States) outputs.*

Testing after conducting fixes and improvements based on review. Levels are still illustrative for now, since our available data does not contain market OHLC so that the LLM is provided with levels.

Here are the events and outputs for each ->

Economic event analysis (Core PCE Price Index M/M):

   Core PCE Price Index: Key Indicator for Fed's Inflation Trajectory
   USD
   The upcoming Core PCE Price Index release is pivotal for USD, with expectations at 0.3%. Its alignment with the Fed's inflation targets will shape market reactions.
   Analysis Confidence
   95%
   Core Impact
   Strong
   Volatility
   High
   Risk Level
   Elevated
   Market Sentiment
   Neutral · Bullish lean
   Probability Scenarios
   Bullish
   [ABOVE] 30%: A print above 0.3% would signal persistent inflationary pressures, reinforcing the Fed's cautious stance on rate cuts. Expect USD strength, particularly against JPY and EUR, as markets price in a prolonged high-rate environment.

   Neutral
   [ON] 45%: An inline print within the 0.25%–0.35% band would likely result in limited market reaction, as it aligns with current expectations and the Fed's data-dependent approach.

   Bearish
   [BELOW] 25%: A print below 0.3% would suggest easing inflation, potentially accelerating rate cut expectations. USD could weaken notably against EUR and JPY as markets anticipate a dovish shift.

   Market Scenarios
   Above
   >0.3%
   Bearish
   On forecast
   0.3%
   Ranging
   Below
   <0.3%
   Bullish
   For the USD Currency

   In-depth analysis
   Release: Core PCE Price Index m/m

   Outcome: The expected value of 0.3% aligns with previous readings, suggesting stable inflation pressures. This is consistent with the Fed's current inflation trajectory and policy stance.

   Actual
   TBD
   Expected
   0.3%
   Previous
   0.3%
   Market reaction
   Price action: USD likely to strengthen against JPY and EUR if the print exceeds expectations, testing levels such as USD/JPY 160.00. Conversely, a weaker print could see EUR/USD approach 1.1700.

   Volatility: Expect elevated volatility during the London session, driven by the high-impact nature of the release and current medium VIX levels.

   Why: The Core PCE is a key inflation measure for the Fed. A deviation from expectations could significantly alter rate path projections, impacting USD pairs.

   Implications
   Economic context: The Core PCE is a critical gauge of underlying inflation, closely watched by the Fed. Current readings suggest inflation is stable but above the Fed's long-term target.

   Policy implications: A higher-than-expected print would complicate the Fed's path towards easing, reinforcing a hawkish bias. Conversely, a lower print could ease policy pressure, aligning with the Fed's desire for inflation moderation.

   Risk level: Medium risk given the geopolitical backdrop and potential for significant policy shifts.

   Trading plan
   Best approach: If Core PCE exceeds 0.3%, consider going long USD/JPY targeting 160.00, with a stop below 159.00. A print below expectations could warrant a short EUR/USD position targeting 1.1700. If the USD print confirms a hawkish surprise vs 0.3%, extend bullish follow-through in affected pairs; if inline or soft, expect range conditions until the next catalyst reprices yields.

   Avoid: Avoid aggressive positioning ahead of the release, given potential for surprise outcomes.

   Key levels: Anchored to current spot: USD/JPY 159.444, EUR/USD 1.16169.

   Position sizing: Consider moderate sizing due to elevated volatility expectations.

   Big picture
   Economic outlook: The US economy faces mixed signals with stable inflation but geopolitical risks. Core PCE will be pivotal in shaping medium-term economic expectations.

   Medium-term direction: USD likely to maintain a neutral to bullish trajectory if inflation remains above target, supporting a cautious Fed.

   Policy trajectory: The Fed's policy trajectory remains data-dependent, with inflation trends being the primary driver. A sustained inflationary trend could delay rate cuts.

   Forward focus: Monitor upcoming inflation data and geopolitical developments, particularly those affecting energy prices and supply chains.

   Next catalysts:
   FOMC Meeting - June 2026
   US Non-Farm Payrolls - June 2026
   Geopolitical developments in the Middle East

Live News Analysis:

Header and body text of live news event: 

   ECB: Tightening bias with cuts pencilled for 2027 – ABN AMRO
   ABN AMRO analysts note the European Central Bank (ECB) Governing Council has adopted a tightening bias and is expected to raise the deposit rate to 2.50% with hikes in June and July. Higher long-term inflation expectations support this stance.

Output Analysis for this Live news event:

   Market Impact
   The ECB's tightening bias, with expected rate hikes in June and July, supports a stronger euro in the medium term, particularly affecting EUR/USD. This stance aligns with higher long-term inflation expectations, suggesting a potential upward trajectory for the euro against the dollar. Current market sentiment for EUR/USD is neutral, but the tightening bias may shift this sentiment towards bullishness if the ECB's actions align with market expectations. The London session is active, typically increasing volatility, which could amplify movements in EUR/USD.

   Immediate Reaction:
   NEUTRAL · BULLISH LEAN (USD)
   Key Pairs:
   EUR/USD
   Volatility:
   MEDIUM
   Timeframe:
   next 2-4 hours
   Trading Implications
   For EUR/USD, watch for potential resistance around 1.1700 as the ECB's tightening bias unfolds. If the pair breaks above this level during the London session, it could signal further upside potential. Given the medium volatility and neutral sentiment, traders should be prepared for increased fluctuations. If the ECB's hawkish stance is reinforced, expect EUR/USD to test higher resistance levels, particularly if the dollar weakens in response to broader market dynamics.

   Risk Assessment
   Market Volatility:
   MEDIUM
   Liquidity Impact:
   MEDIUM
   Correlation Risk:
   MEDIUM

Hollistic Scan (US):

   Regime Strip
   Short-term (entry/noise filter)
   Neutral · Score / 100 -13 · N/A Neutral band, bearish lean
   Long-term (primary swing thesis)
   Neutral · Score / 100 -13 · N/A Neutral band, bearish lean
   Top Pair Bias
   EURUSD → NEUTRAL (light)
   |
   Calendar Stress
   88/100
   High event density — regime signal may reprice sharply. Size accordingly.
   Inputs are stale relative to UTC; reduce conviction and refresh frequently.
   Personalization: swing-trading profile detected — prioritize long-term regime and macro follow-through.
   2Y Yield
   4.06%
   +0.02
   10Y Yield
   4.50%
   +0.01
   30Y Yield
   5.03%
   +0.02
   Short-Term (2-6 weeks)
   NEUTRAL · BEARISH LEAN
   Score: -13 / 100|Neutral band, bearish lean|Confidence: 50%
   -100
   Neutral band (-20 to +20)
   +100
   Short-term driver contributions
   Driver
   Contribution
   Share
   Rate momentum
   -2.3
   16.8%
   Inflation momentum
   +19.6
   145.9%
   Growth momentum
   -18.9
   141%
   Yield daily impulse
   +1.3
   9.5%
   Event risk
   -13.1
   97.6%
   sum(driver_signal × weight); driver_signal bounded [-100, +100]

   Long-Term (3-12 months)
   NEUTRAL · BEARISH LEAN
   Score: -13 / 100|Neutral band, bearish lean|Confidence: 50%
   -100
   Neutral band (-20 to +20)
   +100
   Long-term driver contributions
   Driver
   Contribution
   Share
   Policy alignment
   -10.6
   79.8%
   Growth trend
   -23.7
   178.2%
   Inflation trend
   +15.7
   118.1%
   Labor trend
   +0.9
   6.8%
   Yield curve regime
   +4.4
   33.1%
   sum(driver_signal × weight); driver_signal bounded [-100, +100]

   -100 = extreme bearish macro impulse, 0 = balanced, +100 = extreme bullish macro impulse. Scores are rounded to whole points for readability; drivers retain one decimal.

   Key takeaways
   Personalized focus
   LONG-TERM
   Long-term regime is prioritized based on your onboarding trading style preference.

   Short-term regime
   NEUTRAL
   Composite score -13 with 50% confidence on a 2–6 week horizon.

   Long-term regime
   NEUTRAL
   Composite score -13 with 50% confidence on a 3–12 month horizon.

   Strait of Hormuz closure & structural oil supply shock
   CRITICAL
   The US-Israel joint military operation against Iran (launched Feb 28 2026), resulting in the death of Supreme Leader Khamenei, triggered an effective closure of the Strait of Hormuz — through which roughly 20 mb/d of crude and 30% of global seaborne hydrocarbons normally transit. As of late May 2026 the closure has been in effect for approximately 12 weeks, the longest in the strait's modern history. The IEA reports… The Fed is on hold with cuts deferred to 2027, as the energy shock layered onto pre-existing tariff-driven inflation (core PCE 2.5–3%) has eliminated near-term easing room. US is a net energy exporter, providing partial insulation vs. energy-importing peers. AI capex boom is generating positive data surprises in manufacturing, employment, and earnings, keeping the dollar resilient. Fed independence risks (political pressure, Powell succession) add a tail risk to inflation expectations. The dominant FX channel: USD is being treated as the sole reliable safe-haven in FX per BofA quant models, with DXY strength driven by geopolitical stress rather than rate differentials — the key question is whether this reflex becomes structural.

   Why is the score still neutral?
   CRITICAL
   The Strait of Hormuz closure & structural oil supply shock is CRITICAL, but the short-term composite stays Neutral · Bearish Lean (score -13) because rate momentum (-2.3) is partly offset by yield daily impulse (+1.3) — net effect keeps the regime from a full risk-off read.

   Central banks on hold — 'disciplined optionality' replaces easing cycle
   ELEVATED
   The energy shock has materially shifted the monetary policy landscape. Prior to the February escalation, the base case was for cautious Fed and ECB cuts mid-2026. As of May 2026, Amundi's Global Investment Views characterises the new central bank stance as 'disciplined optionality': protecting credibility, keeping inflation expectations anchored, watching second-round energy pass-through closely, and retaining flexi…

   US tariffs, trade fragmentation & stagflationary US domestic pressure
   ELEVATED
   US tariff policy under Trump is a parallel macro headwind operating alongside the energy shock. Tariffs are keeping headline and core US inflation elevated — delaying the return to the Fed's 2% target and creating stagflationary pressure domestically. Global geoeconomic fragmentation is deepening, with competing financial infrastructures, payment systems, and trade blocs. Europe is accelerating strategic autonomy; t…

   AI-driven capex cycle & growth divergence
   MODERATE
   AI infrastructure investment is a structural tailwind for US growth and corporate earnings, partially offsetting macro headwinds. Firms like Fidelity, BlackRock, and JPMorgan identify AI as 'the defining theme for equity markets' in 2026. However, valuations have outrun near-term fundamentals in some segments, raising bubble-echo concerns. The AI capex boom supports US manufacturing PMI, employment data, retail sale…

   Central bank document context
   FED · 2026-03-18
   FOMC Press Conference - March 18, 2026 — Federal Reserve FOMC press conference transcript/materials from March 18, 2026. Includes Chair commentary on policy decision rationale, inflation progress, labo…

   Live sovereign yields
   NORMALIZING GROWTH BIAS
   2Y / 10Y / 30Y: 4.06% / 4.50% / 5.03%. Session change (Δ): +0.02 / +0.01 / +0.02.

   Curve diagnostics
   2s10s +0.44 pp
   10s30s +0.53 pp. Steepening often ties to growth/reflation; flat/inverted warns late-cycle or recession pricing.

   FX map (correlated pairs)
   EURUSD → NEUTRAL; USDJPY → NEUTRAL
   Bias uses base/quote orientation vs this economy’s currency; strength label reflects composite short-term score.

   Calendar stress (14 days)
   88 / 100
   Higher = more high/medium-impact events for this currency in the next two weeks; raises volatility of interpretation.

   Scan reliability
   POOR
   Oldest indicator ~29d behind UTC. Missing signal families: 0 ().

   Comprehensive Context
   Long-term regime (primary swing thesis)
   Neutral · Bearish Lean (score -13) suggests a balanced outlook with policy alignment (-10.6) and growth trend (-23.7) weighing heavily, while inflation trend (+15.7) provides some support. The focus should remain on the long-term trajectory as macro conditions evolve.

   Geopolitical & energy
   The Strait of Hormuz closure & structural oil supply shock is CRITICAL, but the short-term composite stays Neutral · Bearish Lean (score -13) because rate momentum (-2.3) is partly offset by yield daily impulse (+1.3) — net effect keeps the regime from a full risk-off read.

   Why is the composite score still in the neutral band?

   The Strait of Hormuz closure & structural oil supply shock is CRITICAL, but the short-term composite stays Neutral · Bearish Lean (score -13) because rate momentum (-2.3) is partly offset by yield daily impulse (+1.3) — net effect keeps the regime from a full risk-off read.

   Policy communications
   Policy communication context (FED, from the same document catalog as Overview’s Central Bank Analysis): “Federal Reserve FOMC press conference transcript/materials from March 18, 2026. Includes Chair commentary on policy decision rationale, inflation progress, labor market conditions, and forward guidance.” (see FOMC Press Conference - March 18, 2026 dated 2026-03-18).

   Short-term macro (entry/noise filter)
   Neutral · Bearish Lean (score -13) reflects mixed signals as inflation momentum (+19.6) is countered by growth momentum (-18.9) — the regime remains cautious amid event risks. If upcoming high-impact events trigger volatility, then the score could shift, impacting positioning.

   FX mapping
   In the current environment, EURUSD is framed by ECB's terminal-rate hold against Fed's disciplined optionality. If euro-area energy import costs escalate, then the USD may strengthen as a safe haven. Conversely, if inflation surprises prompt ECB action, then the EUR could gain traction.

   Source references
   Overlay context
   1.1.0
   File: backend/data/holistic_scan_context.json; last updated: 2026-05-27

   Central bank documents
   FED
   File: src/data/central-bank-documents.json; catalog version: 1.0.0; sampled: 3 docs

   Live market inputs
   TRADINGVIEW
   Indicator staleness: 29d 9h; yield staleness: 0h; calendar staleness: N/A; scan model: economy_scan_v1.4; generated UTC: 2026-05-28T09:12:24.349130

   Short-Term Trading Range View
   Short-term regime is neutral. Daily yield impulse and event risk suggest range-to-trend conditions over coming sessions.
   Long-Term Trading Range View
   Long-term regime is neutral. Curve structure (normalizing_growth_bias) implies gradual macro trend development across weeks to months.
   Short-Term Drivers
   Rate momentum - Policy-rate direction over recent prints
   Negative
   Inflation momentum - Disinflation supports easing; re-acceleration supports tightening
   Positive
   Growth momentum - Near-term growth surprise impulse
   Negative
   Long-Term Drivers
   Policy alignment - Real-rate / policy alignment proxy
   Negative
   Growth trend - Medium-term growth trajectory
   Negative
   Inflation trend - Inflation regime pressure
   Positive
   Labor trend - Employment backdrop resilience
   Positive
   Top Pair Biases
   EURUSDSTALE DATA - NEUTRAL (light) — Focus: ECB–Fed repricing + euro-area energy import costs. Overlay: Strait of Hormuz closure & structural oil supply shock (CRITICAL) — prioritize energy/terms-of-trade channel. — EURUSD dynamics hinge on the ECB's stance against the Fed's disciplined optionality. If euro-area energy import costs rise sharply, then the USD could see increased demand as a safe haven. — Conviction reduced on EUR/USD — macro inputs are stale; refresh before sizing.
   Invalidated if inflation surprises force ECB to hike, boosting EUR.
   USDJPYSTALE DATA - NEUTRAL (light) — Focus: BoJ pace + Gulf energy pass-through to Japan CPI. Overlay: Strait of Hormuz closure & structural oil supply shock (CRITICAL) — prioritize energy/terms-of-trade channel. — USDJPY is influenced by Japan's energy-import vulnerability, with BoJ's gradual tightening facing pressure from rising import costs. If risk sentiment deteriorates, then JPY may weaken against the USD. — Conviction reduced on USD/JPY — macro inputs are stale; refresh before sizing.
   Invalidated if MoF/BoJ intervention occurs below 157.
   GBPUSDSTALE DATA - NEUTRAL (light) — Focus: BoE policy mispricing vs energy shock. Overlay: Strait of Hormuz closure & structural oil supply shock (CRITICAL) — prioritize energy/terms-of-trade channel. — GBPUSD is shaped by the BoE's balancing act between energy-driven inflation and soft growth. If UK energy pressures ease, then GBP could strengthen against the USD. — Conviction reduced on GBP/USD — macro inputs are stale; refresh before sizing.
   Invalidated if BoE's pushback caps hike pricing.
   AUDUSDSTALE DATA - NEUTRAL (light) — Focus: China growth + commodity beta vs USD haven. Overlay: Strait of Hormuz closure & structural oil supply shock (CRITICAL) — prioritize energy/terms-of-trade channel. — AUDUSD reflects commodity demand and China's economic performance against the USD's haven appeal. If China's stimulus boosts demand, then AUD may rally despite USD strength. — Conviction reduced on AUD/USD — macro inputs are stale; refresh before sizing.
   Invalidated if broad risk-off sentiment crushes AUD.

## Version 2 Review (After changes) — source notes

> **Tracker:** Active work is tracked in [§0.5 Version 2 Implementation Tracker](#05-version-2-implementation-tracker-after-v1-ships). This section is the full qualitative review that produced those IDs.

Claude re-tested outputs after V1 ships. Below: section-by-section breakdown and addition/removal suggestions.

---

## Economic Calendar — What Improved

The probability fix is clean — 30/45/25 summing to 100 is exactly right, and the [ABOVE]/[ON]/[BELOW] framing is much clearer than before. The neutral zone as a range (0.25%–0.35%) instead of a single tick is a meaningful improvement. The trading plan is now genuinely structured — long USD/JPY targeting 160.00 with stop below 159.00 is a real trade idea.

### Remaining Issues

**1. Market Scenarios table is inverted**
The table shows:
- Above >0.3% → Bearish
- Below <0.3% → Bullish

This is for the USD currency, but it's labelled backwards relative to the probability section above it, which correctly frames above as bullish USD. This is a logic inversion that will confuse traders fast. The table needs to either specify "For USD" explicitly in each cell, or flip the labels to match the probability section's framing.

**2. Confidence jumped from 90% to 95% — unexplained**
The previous output had 90%, this one has 95%. Without methodology being visible to the trader, this just looks like a higher random number. Even if the confidence engine is now deterministic under the hood, the trader still sees a raw percentage with no reasoning shown in the UI. Consider surfacing the `confidence_reason` field visibly — even a one-liner like *"High confidence: tight analyst consensus, Fed has explicitly cited this release"* would make 95% feel earned.

**3. Key levels are still just spot anchors**
USD/JPY 159.444 and EUR/USD 1.16169 — same problem as before. The trading plan now has a real target (160.00) but the "key levels" field still just timestamps spot. This field should either be removed until #8 is resolved, or renamed to "Spot reference" to be honest about what it is.

**4. "Geopolitical developments in the Middle East" as a next catalyst is vague**
The other two catalysts (FOMC June, NFP June) are specific and dated. The third one is a non-event — it's always true. Either remove it or make it specific: *"Strait of Hormuz — IEA supply report, early June"* or similar.

---

## Live News — What Improved

The NEUTRAL · BULLISH LEAN (USD) label is a direct improvement — it has sub-classification and it's specific to USD. The If→then structure is present in the trading implications section. These are real gains.

### Remaining Issues

**1. The reaction label direction is wrong for the event**
The news is ECB tightening bias with rate hikes expected — this is EUR bullish, not USD bullish. The immediate reaction is labelled "NEUTRAL · BULLISH LEAN (USD)" which implies the dollar benefits, but the event is about ECB hawkishness strengthening the euro. The label should read "NEUTRAL · BULLISH LEAN (EUR)" or "EUR BULLISH LEAN." The body text actually gets this right — it says "supports a stronger euro" — so the label/body contradiction from before has reappeared, just in the opposite direction.

**2. Correlation Risk still generic**
The §3.5 fix was supposed to replace the generic MEDIUM label with pair/channel-specific detail. The output still shows just "Correlation Risk: MEDIUM" with no elaboration. This backlog item appears to not have fully cascaded into the UI output yet, even if the `correlation_risk_detail` field exists in the API.

**3. No "irrelevant pairs" handling shown**
If this trader's profile includes pairs beyond EUR/USD, there's no indication the system filtered or acknowledged other pairs. The output focuses entirely on EUR/USD — which may be correct for this event — but there's no signal to the trader that other pairs were assessed and found less relevant.

**4. Timeframe "next 2-4 hours" for a medium-term ECB policy story**
An ECB tightening bias with hikes pencilled for June and July is a multi-week macro story, not a 2-4 hour event. The timeframe label doesn't match the nature of the news. This could be improved by adding a secondary timeframe: immediate reaction window vs. medium-term positioning window.

---

## Holistic Scan — What Improved

The score transparency is dramatically better. The component breakdown table with contribution values and share percentages is exactly what was needed — a trader can now see that growth momentum (-18.9, 141% share) and event risk (-13.1, 97.6% share) are doing the heavy lifting on the bearish side. The per-pair commentary is now meaningfully differentiated — EUR/USD gets ECB/Fed repricing framing, USD/JPY gets Japan energy-import vulnerability, GBP gets BoE balancing act, AUD gets China/commodity channel. The score-narrative bridge for the CRITICAL Hormuz theme is present and functional. These are significant improvements.

### Remaining Issues

**1. Short-term and long-term scores are identical (-13 both)**
This is the same value for two completely different time horizons with different driver sets. While mathematically possible, it looks like a bug or a model artefact. A trader will immediately question whether the long-term engine is actually running independently. Even a one-point difference would look more credible — worth investigating whether the two scoring pipelines are genuinely independent.

**2. Driver "Share" percentages exceed 100%**
Inflation momentum shows 145.9% share, growth momentum shows 141%, event risk shows 97.6%. These can't be shares of a whole in any conventional sense. The label "Share" is misleading — what this likely means is the driver's signal contribution relative to the final score magnitude, which is a different thing. Rename this column to something like "Signal weight" or "Contribution magnitude" and add a tooltip or footnote explaining what it represents. As-is, a trader seeing 145.9% will think there's a calculation error.

**3. "Why is the score still neutral?" appears twice**
In the comprehensive context section, the score bridge sentence appears verbatim under both "Geopolitical & energy" and "Why is the composite score still in the neutral band?" — the exact same paragraph duplicated. This looks like a rendering bug where the same content is being injected into two different slots.

**4. Key takeaways still show plain "NEUTRAL" labels**
The regime strip at the top correctly shows "NEUTRAL · BEARISH LEAN" with sub-classification. But the Key Takeaways section further down reverts to just "NEUTRAL" for both short-term and long-term regime. The sub-classification work from #9 hasn't cascaded into this section.

**5. Confidence shows "N/A" in the regime strip**
The strip reads "Score / 100 -13 · N/A Neutral band, bearish lean." The N/A for confidence is unexplained — elsewhere in the output confidence is shown as 50%. This inconsistency between the strip and the full scorecard will confuse traders. Either show 50% consistently, or explain why N/A is displayed in the strip specifically.

---

## Additions Worth Considering

**For all three sections:**

- **Regime alignment indicator** — a simple flag showing whether the holistic scan regime, the calendar event direction, and any live news lean are all pointing the same way or conflicting. When all three align on USD bullish for example, that's high-conviction. When they conflict, that's a reason to reduce size. This is the kind of cross-surface synthesis traders actually need.

- **Session context stamp** — which trading session is active at time of generation (London/NY/Asia/overlap), and whether the current session is historically high or low volatility for this pair/event type. One line, but very useful for position timing.

**For Economic Calendar:**

- **Surprise history** — last 4–6 actual vs expected prints for this specific release, shown as a small table. Traders want to know if this release consistently surprises to the upside or downside. This would directly strengthen the probability scenarios and make the confidence score defensible.

- **Options market implied move** — if you can source it, the options-implied 1-day move for the relevant pair around this event is one of the most useful pre-event data points for a retail trader. Even a rough "options market pricing ~40 pip move in EUR/USD" would be highly valuable.

**For Live News:**

- **Longevity classification** — explicitly flag whether this news is a 2-4 hour reaction event, a multi-day repricing event, or a structural/weeks-long theme shift. The ECB tightening story is a good example where the current 2-4 hour framing undersells the impact horizon. A "News Type: Policy Signal (multi-week)" label would help traders categorise how to position.

- **Fading vs following guidance** — for experienced traders, a one-line note on whether the initial reaction is typically worth following or fading for this type of event. Some news categories (central banker speeches, analyst notes like this one) have weak initial reactions that reverse. Others (hard data prints, emergency rate decisions) are worth following. A simple "React type: follow / fade / wait for confirmation" label would be a differentiated feature.

**For Holistic Scan:**

- **Regime trend direction** — not just the current score, but whether it's been improving or deteriorating over the last 2–4 scans. A score of -13 that was -5 three weeks ago means something very different to a -13 that was -20. An arrow (↑ improving / ↓ deteriorating / → stable) next to the score would communicate this instantly.

- **Cross-economy comparison snippet** — for the primary pairs shown, a one-line note on the counterpart economy's regime. Right now EUR/USD shows only the US side. A trader looking at EUR/USD also needs to know where the EUR holistic scan sits. Even a compact "EUR regime: Neutral · Bearish Lean (-8)" next to the pair bias would complete the picture.

---

## Fields to Consider Removing or Restructuring

- **"Forward focus: Monitor upcoming inflation data and geopolitical developments"** in the Calendar big picture — this is filler that appears in every output regardless of the event. Either make it specific to this release or remove it.

- **"Key levels: Anchored to current spot"** in Calendar until #8 is resolved — as discussed, this is a timestamp not a level. Showing it creates false precision.

- **Source references block in Holistic** — the raw file paths (`backend/data/holistic_scan_context.json`) are developer-facing, not trader-facing. These should be hidden from the trader UI and kept in a developer/debug view only.

- **The "sum(driver_signal × weight)" formula footnote** — useful for developers, confusing for most traders. Move to a collapsible "methodology" section rather than showing inline in the scorecard.