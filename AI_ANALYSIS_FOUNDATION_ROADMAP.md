# AI Analysis Foundation Roadmap

Living doc for engineering status. Product spine rules remain in `AI_ANALYSIS_V1_UNIFIED_SPEC.md`.

**Input layer (quality-first track):** see `ANALYSIS_INPUT_LAYER.md` for full spec and progress tracker.

---

## Input layer — AnalysisContextPack (in progress)

**Goal:** One shared context pack (user, macro snapshot, markets, session rules) before GPT writes calendar/news copy.

| Phase | Status | Notes |
|-------|--------|-------|
| B — `analysis_context_pack.py` | **Done** | Tests: `test_analysis_context_pack.py` |
| C — Calendar wiring | **Done** | `gpt_ai_analysis._create_analysis_prompt`; flag `ANALYSIS_CONTEXT_PACK_ENABLED` |
| D — Live news | **Done** | `mvp_news_analyzer.py`; flag `ANALYSIS_CONTEXT_PACK_ENABLED` |
| E — Holistic `macro_snapshot` export | **Done** | Write-through on save; calendar/news read &lt; 72h |
| F — Prompt quality pass (calendar + news) | **Done** | Regime vs event rules when pack enabled |
| G–H — Debug endpoint + GPT narrative | Not started | See `ANALYSIS_INPUT_LAYER.md` §13 |

**Default:** pack **off** in production (same pattern as V1 spine). Enable in `backend/.env` for staging.

---

## Phase 1 — Shared spine (complete)

**Goal:** One trader brief shape on calendar, live news, and holistic scan without removing legacy body fields.

**Shipped:**

- `backend/services/analysis_v1_spine.py` — spine builders, calendar alignment warnings, feature flag
- `app.py` wiring on all three APIs + legacy calendar
- `AnalysisV1Spine.jsx` on Overview, LiveNewsFeed, Economies
- Holistic Firestore recents save `spine` + `analysis_format_version`
- Tests: `backend/test_analysis_v1_spine.py`

**Not in Phase 1:** Central pipeline, scenario repair, router, calibration.

---

## Phase 2 — Unified finalize path (in progress)

**Goal:** One factory attaches envelope metadata and spine; new features call `finalize_analysis()` instead of merge helpers in routes.

**Shipped:**

| Piece | Location |
|-------|----------|
| Contract constants | `backend/services/analysis_contract.py` — `analysis_kind`, `spine_profile`, observability helpers |
| Finalize entry point | `backend/services/analysis_pipeline.py` — `finalize_analysis()`, `FinalizeContext` |
| Route refactor | `app.py` — calendar enhanced, news, economy scan, legacy calendar |
| Cross-context | Moved to `analysis_pipeline.build_live_news_cross_context_note` |
| Tests | `backend/test_analysis_pipeline.py` |

**Envelope fields (additive):**

| Field | Example |
|-------|---------|
| `analysis_kind` | `calendar_event`, `live_news`, `economy_scan`, `calendar_event_legacy` |
| `spine_profile` | `trader_brief_v1` (when spine enabled) |
| `analysis_format_version` | `v1` |
| `spine` | Trader brief object |
| `trace` | `{ "steps": [...], "finalized_at": "..." }` |
| `v1_observability` | Debug/metrics block |

**Still Phase 2 (optional follow-ups):**

- [ ] Frontend: read `analysis_kind` / `trace` only if needed (optional)
- [ ] Test with `ANALYSIS_V1_SPINE_ENABLED=false` in CI
- [ ] Export `finalize_analysis` from a single public import path for new features

---

## Phase 3 — Calendar trust (in progress)

**Shipped:**

- `backend/services/calendar_scenario_engine.py` — direction mapping, `market_scenarios` table, `forward_scenarios_by_outcome`, validation
- `merge_v1_calendar_response` attaches canonical fields on enhanced-analysis
- `Overview.jsx` renders API `market_scenarios` when present (client calc fallback only if missing)

**Still to do:**

- GPT repair pass when `scenario_alignment_status === "warning"`
- Live spot in prompt for levels
- Optional: rename Probability Scenarios UI to Above / On / Below using `forward_scenarios_by_outcome`

---

## Phase 4+ — Workflow

- Router: `light` / `standard` / `deep`
- Verifier on failures
- Outcome store + confidence calibration
- New `spine_profile` e.g. `pair_macro_v1` for pair/fundamental analysis

---

## How new features should integrate

1. Run your analyzer → produce a `body` dict (existing keys OK).
2. Call `finalize_analysis(body, analysis_kind=..., context=FinalizeContext(...))`.
3. Return JSON to client; render `spine` with `AnalysisV1Spine` when `spine_profile === "trader_brief_v1"`.
4. For a **new** analysis type, add an `analysis_kind`, define a new `spine_profile`, extend `_apply_spine` (or a profile registry).

---

## Pausing V1 (back to legacy UX)

V1 is **off by default** so the product looks and behaves like before the brief experiment.

| Layer | Flag | Default |
|-------|------|---------|
| Backend (no spine, no trace, no `market_scenarios` on wire) | `ANALYSIS_V1_ENABLED=false` in `backend/.env` | off in code |
| Frontend (hide Analysis brief block) | `VITE_ANALYSIS_V1_ENABLED` unset or `false` in frontend `.env` | off |

**To review spine work later:** set both to `true`, restart backend + Vite.

Code remains in repo: `analysis_v1_spine.py`, `analysis_pipeline.py`, `calendar_scenario_engine.py`, `AnalysisV1Spine.jsx`.

---

## Revision log

| Date | Change |
|------|--------|
| 2026-05-15 | Phase 2 started: `analysis_contract`, `analysis_pipeline`, `app.py` refactor, tests |
| 2026-05-15 | V1 paused: master flag default off; UI gated by `VITE_ANALYSIS_V1_ENABLED` |
| 2026-05-26 | Input layer Phase C: calendar uses AnalysisContextPack when `ANALYSIS_CONTEXT_PACK_ENABLED=true` |
| 2026-05-26 | Input layer Phase D: live news uses AnalysisContextPack when `ANALYSIS_CONTEXT_PACK_ENABLED=true` |
| 2026-05-26 | Input layer Phase E: holistic scan stores `macro_snapshot`; pack reads fresh scan for calendar/news |
| 2026-05-26 | Input layer Phase F: regime-vs-event prompt rules; calendar uses bullish/bearish/neutral scenarios when pack on |
