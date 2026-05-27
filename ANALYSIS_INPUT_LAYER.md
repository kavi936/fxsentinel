# Analysis Input Layer — Planning Document

**Status:** **input layer complete (Phases A–H)** — feature flags still **off by default** until production sign-off  
**Last updated:** 2026-05-27  
**Owner:** product + engineering

**Related docs**


| Doc                                 | Role                                                                |
| ----------------------------------- | ------------------------------------------------------------------- |
| `AI_ANALYSIS_WORKFLOW_IDEAS.md`     | Why we need a workflow; sample failures                             |
| `AI_ANALYSIS_V1_UNIFIED_SPEC.md`    | Spine + body ( **deferred** until input/prompt quality is good)     |
| `AI_ANALYSIS_FOUNDATION_ROADMAP.md` | What is already built in backend (spine, pipeline, scenario engine) |


**Explicitly out of scope for this doc (for now)**

- V1 spine UI (`AnalysisV1Spine.jsx`) and trader-brief block at top of cards  
- Router, pre/post event automations, outcome calibration (Phase 4+)

---

## Progress tracker (living)

| Phase | What | Status | Wired to production prompts? |
| ----- | ---- | ------ | ---------------------------- |
| **A** | Decisions in §8 | Done | — |
| **B** | `analysis_context_pack.py` + tests | Done | No |
| **C** | Calendar (`gpt_ai_analysis._create_analysis_prompt`) | **Done** | **Only when `ANALYSIS_CONTEXT_PACK_ENABLED=true`** |
| **D** | Live news (`mvp_news_analyzer.py`) | **Done** | **Only when `ANALYSIS_CONTEXT_PACK_ENABLED=true`** |
| **E** | Holistic `macro_snapshot` export | **Done** | Yes when pack on + fresh scan &lt; 72h |
| **F** | Prompt quality pass per surface | **Done** | When `ANALYSIS_CONTEXT_PACK_ENABLED=true` |
| **G** | Staging preview / debug | **Done** | `ANALYSIS_CONTEXT_PACK_DEBUG` — server logs + `macro_snapshot` on economy-scan response |
| **H** | Holistic GPT narrative (§13) | **Done** | When `HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED=true` + `OPENAI_API_KEY` |

**How to try Phase C–E locally**

1. In `backend/.env`: `ANALYSIS_CONTEXT_PACK_ENABLED=true` (optional: `ANALYSIS_CONTEXT_PACK_DEBUG=true`).
2. Restart backend.
3. **Phase E:** Run **US Holistic Scan** (Economies) while logged in — saves `macro_snapshot` on the Firestore doc.
4. Within 72h, run **calendar** (USD event) or **live news** (US headline) analysis — backend log should show pack build; GPT prompt includes `MACRO SNAPSHOT`.
5. With `ANALYSIS_CONTEXT_PACK_DEBUG=true`, economy-scan API response includes `macro_snapshot` for inspection.

**Tests:** `python3 -m unittest test_analysis_context_pack test_gpt_calendar_context_pack` (from `backend/`).

---

## 0. Holistic scan — deterministic core + optional GPT voice

When the user clicks **Run Holistic Scan**, the app calls `POST /api/economy-scan/<country>` → `economy_holistic_scan_service.build_scan()`.

| Layer | Always | When `HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED=true` |
| ----- | ------ | ------------------------------------------------ |
| Scores, bias, confidence, pair map, calendar stress | **Deterministic math** | Unchanged (GPT must not override) |
| `narrative.short_term` / `long_term` / `fx` | Python templates (`_build_narrative`) | **GPT** replaces after validation |
| `narrative.geopolitical_energy` | **Curated JSON** (`holistic_scan_context.json`) | **GPT** replaces in narrative block |
| `narrative.central_bank_context` | Central bank catalog snippets | Stays **deterministic** (not in GPT JSON shape) |
| `highlights[]`, `pair_setups[].key_risk` | Templates + **same JSON** overlay | Still **deterministic** (GPT does not touch highlights) |
| `pair_setups[].driver` / `invalidation` | Template strings | **GPT** per pair when validation passes |
| Metadata | `narrative_source`, `narrative_model_used`, `narrative_validation` | `gpt` or `deterministic_fallback` |

**GPT is used for:** calendar (`gpt_ai_analysis`), live news (`mvp_news_analyzer`), and optionally holistic narrative (Phase H).

**Curated overlay file:** `backend/data/holistic_scan_context.json` — still loaded on every scan; see §13 for how it interacts with GPT.

---

## 1. What we are building (plain language)

Before the model writes analysis, every surface should receive:

1. **The same “professional context”** — who the user is, what economy/currency matters, what macro regime says, what markets are doing, whether data is trustworthy.
2. **Plus one area-specific fact block** — calendar event fields, news headline/body, or full holistic indicator bundle.

Today each analyzer assembles context **independently**. That causes generic copy, missing cross-links (e.g. news vs holistic geo risk), and uneven use of personalization.

**Goal:** one **input layer** that builds a standard `AnalysisContextPack`, then each analyzer appends its own facts and passes the result to prompts.

```
┌──────────────────────────────────────────────────────────────┐
│  AnalysisContextPack (shared)                                 │
│  user · subject · macro snapshot · market snapshot · quality  │
└────────────────────────────┬─────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   + calendar_facts    + news_facts      + holistic_facts
         │                   │                   │
         ▼                   ▼                   ▼
   calendar prompt      news prompt       scan logic / optional LLM
```

---

## 2. Design principles


| Principle                          | Meaning                                                                                                                             |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Shared where it matters**        | User profile, macro snapshot, market quotes, data quality — same rules for all GPT-backed surfaces.                                 |
| **Different where it must**        | Event actuals vs headline text vs indicator math stay area-specific.                                                                |
| **Structured first, prose second** | Pack is a JSON object; prompt blocks are rendered from it (testable, loggable).                                                     |
| **Freshness and honesty**          | Pack includes staleness, closed market, missing actuals — model must not fake certainty.                                            |
| **Token budget**                   | Pack is ranked and truncated; not “dump everything we have.”                                                                        |
| **Holistic is special**            | Scan is mostly **deterministic** today; pack still applies for **cross-feed** (news/calendar) and any future narrative LLM on scan. |


---

## 3. Proposed `AnalysisContextPack` shape (draft)

This is the target contract the new module will produce. Field names can change after decisions below.

### 3.1 Shared block (all surfaces)

```yaml
pack_version: "2026-05-18"          # bump when pack semantics change
surface: calendar_event | live_news | economy_scan
generated_at_utc: ISO-8601

user:
  profile_available: bool
  trading_style: day | swing | both | unsure
  experience_level: beginner | intermediate | advanced
  primary_pairs: [EURUSD, ...]      # capped list
  analysis_depth: guided | balanced | concise_expert
  time_horizon_bias: intraday | multi_day | dual_horizon | balanced

subject:
  currency: USD                       # primary CCY for this analysis
  country_code: US                    # when applicable
  economy_label: United States

macro_snapshot:                       # optional if stale/unavailable
  source: holistic_scan | economy_context | none
  freshness_hours: number | null
  short_term_bias: bullish | bearish | neutral | null
  short_term_score: number | null
  long_term_bias: ...
  calendar_stress_14d: 0-100 | null
  geopolitical_energy_risk: low | elevated | null   # TBD naming
  one_line_summary: string | null                   # human-readable for prompt

market_snapshot:
  instruments:                        # ranked, capped
    - id: EURUSD
      label: ...
      price: ...
      change_pct: ...
  selection_reason: event_currency | user_pairs | keywords | macro_proxies

session_and_quality:
  market_session: open | closed | unknown
  data_quality: validated | partial | stale | unknown
  quality_notes: [string]             # e.g. "actual pending", "indicators 11d old"
  level_anchor_policy: anchored | illustrative | unavailable   # TBD

cross_surface:                        # optional
  related_headline_hint: string | null
  holistic_vs_headline_note: string | null   # only when tension detected
```

### 3.2 Area-specific blocks

**Calendar (`calendar_facts`)**

```yaml
event_id: string
title: string
scheduled_at_utc: ISO-8601
release_status: pre | post | unknown
actual: number | string | null
forecast: ...
previous: ...
impact_tier: high | medium | low
central_bank_context_snippet: string | null   # may move to shared later
```

**Live news (`news_facts`)**

```yaml
news_id: string
headline: string
body_excerpt: string              # truncated
source: string
published_at_utc: ISO-8601
detected_currencies: [USD, ...]
detected_themes: [oil, rates, ...]   # from keywords / classifier
```

**Holistic (`holistic_facts`)**

```yaml
# Mostly populated by existing economy_holistic_scan_service output.
# Input layer may only add user + cross-links when building scan, not re-fetch everything.
scan_model_version: string
indicator_map: ...
yield_map: ...
calendar_events_14d: ...
```

---

## 4. What each surface gets today (backend map)

Use this when integrating — **substitute** pack builder calls into these paths rather than duplicating logic.


| Surface                 | Primary code                                        | Personalization                                                   | Market quotes                                              | Economy / macro                                                       | Notes                                                                                 |
| ----------------------- | --------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Live news**           | `backend/services/mvp_news_analyzer.py`             | `get_user_personalization` + `build_prompt_personalization_block` | `build_relevant_market_context_block` (surface=`news`)     | **No** holistic snapshot in prompt today                              | Cross-check only in `analysis_pipeline.build_live_news_cross_context_note` when V1 on |
| **Calendar (enhanced)** | `backend/services/gpt_ai_analysis.py`               | same helpers, surface=`economic_calendar`                         | `build_relevant_market_context_block` (surface=`calendar`) | `economy_context_service`, `central_bank_ai_context`, policy snippets | Richest calendar context path                                                         |
| **Holistic scan**       | `backend/services/economy_holistic_scan_service.py` | `personalization` dict in `build_scan`                            | Yields via TradingView internally                          | `holistic_scan_context.json`, central bank catalog                    | **Deterministic only — no GPT on `/api/economy-scan`** (see §0)                       |


**Existing modules to reuse (do not rewrite from scratch)**


| Module                             | Reuse for                                                 |
| ---------------------------------- | --------------------------------------------------------- |
| `analysis_personalization.py`      | `user` section of pack                                    |
| `relevant_market_context.py`       | `market_snapshot` ranking + formatting                    |
| `economy_context_service.py`       | Indicator/CBR fallback when no fresh holistic             |
| `economy_holistic_scan_store.py`   | Recent scan → `macro_snapshot`                            |
| `economy_holistic_scan_service.py` | Holistic body; optional consumer of pack `user` + quality |
| `central_bank_ai_context.py`       | Calendar policy snippets                                  |
| `analysis_pipeline.py`             | Cross-surface note logic → move into pack `cross_surface` |


**Planned new module (implementation later)**

`backend/services/analysis_context_pack.py`

- `build_analysis_context_pack(surface, user_id, subject, area_facts, options) -> dict`  
- `render_pack_for_prompt(pack, max_tokens_hint) -> str`  
- Unit tests with fixtures per surface

**Call sites (integration status)**

| # | File | Status |
|---|------|--------|
| 1 | `gpt_ai_analysis.py` — `_create_analysis_prompt` | **Done (Phase C)** — uses `build_calendar_context_pack_section` when flag on |
| 2 | `mvp_news_analyzer.py` | **Done (Phase D)** |
| 3 | `economy_holistic_scan_store.py` + scan save | **Done (Phase E)** — `macro_snapshot` write-through |
| 4 | `economy_holistic_scan_service.py` | **Done (Phase H)** — optional GPT narrative merge |
| 5 | Debug (no separate preview route) | **Done (Phase G)** — `ANALYSIS_CONTEXT_PACK_DEBUG` + economy-scan `macro_snapshot` |

---

## 5. Pack → prompt rules

Implemented in `CALENDAR_PACK_PROMPT_RULES` / `NEWS_PACK_PROMPT_RULES` when `ANALYSIS_CONTEXT_PACK_ENABLED=true`.

Shared instructions derived from pack (all surfaces):

- Name the **bias subject** (e.g. “USD around this CPI”, not bare “neutral”).  
- If `session_and_quality.market_session == closed`, frame as “when markets reopen”.  
- If `quality_notes` mention stale/missing data, lower confidence and say why.  
- Prefer `user.primary_pairs` when discussing instruments.  
- If `cross_surface.holistic_vs_headline_note` is set, include one reconciling sentence.

Area prompts add section-specific output JSON (existing shapes); **no spine block** until product approves.

---

## 6. Freshness, staleness, and “do not use” rules (draft)


| Data source                                    | Suggested max age for pack inclusion                               | If older                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| Holistic scan for same `country_code`          | **72 hours** (TBD)                                                 | Omit `macro_snapshot` or mark `source: none` + note in `quality_notes` |
| TradingView quotes                             | **15 minutes** for intraday surfaces; **24h** for swing bias (TBD) | Still include with `stale` flag                                        |
| Economy indicators (`economy_context_service`) | Use service’s own timestamps                                       | Pass through `quality_notes`                                           |
| News body                                      | N/A                                                                | Truncate to N chars (TBD)                                              |


---

## 7. Implementation phases (after decisions)


| Phase | Deliverable                                                         | Success check                                                  |
| ----- | ------------------------------------------------------------------- | -------------------------------------------------------------- |
| **A** | This doc + filled Decision sections                                 | Team agrees on pack fields                                     |
| **B** | `analysis_context_pack.py` + tests (fixtures only)                  | Same user/event → identical shared block on news vs calendar   |
| **C** | Wire **calendar** first (per §8.8)                                  | **Done** — flag-gated in `gpt_ai_analysis.py`                 |
| **D** | Wire **live news**                                                  | Hormuz-style headline reconciles with US scan when fresh       |
| **E** | Holistic: shared `user` in `build_scan` + `macro_snapshot` for pack | News/calendar read latest scan summary                         |
| **F** | Prompt layer refactor (news + calendar)                             | Subjective quality review on 5 fixed samples                   |
| **G** | Debug logging + economy-scan `macro_snapshot` when debug flag on    | Inspect pack/macro without a separate admin route              |
| **H** | **Holistic GPT narrative** (§13)                                    | One GPT call; merge narrative + pair driver/invalidation       |


---

## 8. Decisions (locked 2026-05-18)

### Summary table

| # | Topic | Decision |
|---|--------|----------|
| 8.1 | Macro snapshot attach | **A (hybrid):** attach latest holistic when **&lt; 72h**; evaluate accuracy + multi-economy coverage as we build |
| 8.1 | Snapshot contents | Regime strip, geo when elevated, calendar stress, top 2 pair biases, one-line summary — **not** full trader brief |
| 8.2 | Personalization | **Tiered:** soft for calendar/holistic (economy CCY); **hard** for news (user pairs first) |
| 8.2 | Gold/crypto in snapshot | Include when user listed them in onboarding pairs |
| 8.3 | Market snapshot | Driven by user pairs + event CCY; calendar adds gold/crypto if user trades them |
| 8.4 | Market closed | **Illustrative levels only** (~levels, % moves); reopen / 24h markets (e.g. BTC) called out; not presented as live signals |
| 8.4 | Confidence | **Edge strength** + what supports / negates the trade idea |
| 8.5 | Holistic role | **H1+H2+H3:** pack in, `macro_snapshot` out, **GPT narrative** later (§13); scores stay deterministic |
| 8.5 | Rescan vs old news | **No regenerate;** optional “context updated” on next open |
| 8.6 | News vs scan tension | **Both** prompt reconciliation + UI cross-check note |
| 8.7 | Tokens / Firestore | OK with extra read; token budget TBD at implementation |
| 8.8 | Build order | **Calendar → live news → holistic alignment** |
| 8.9 | Fixtures / bar | **You will test later;** interim bar: news should address scan when geo elevated |

---

### 8.1–8.9 (detail)

### 8.1 Macro snapshot — what should every analysis “remember”?

When a user runs **news** or **calendar** for USD, should we always attach the latest **US holistic scan** summary?


| Option                                                 | Pros                                             | Cons                                    |
| ------------------------------------------------------ | ------------------------------------------------ | --------------------------------------- |
| **A. Always if < 72h**                                 | Strong cross-context; fixes news vs scan tension | Extra Firestore read; scan may be stale |
| **B. Only for USD-headline news and USD events**       | Cheaper                                          | EUR event won’t see US geo spillover    |
| **C. Only when keywords match (oil, Iran, Fed, etc.)** | Token-efficient                                  | May miss subtle links                   |
| **D. Never in v1; calendar/news stay isolated**        | Simplest                                         | Keeps inconsistency                     |


**Your answer (A/B/C/D or hybrid):**  

```
This sounds like a very good idea, but then relies on how accurate the analysis of the holistic scan summary is and it depends on if the user has ran analysis for all economies. "A" sounds most reasonable, but we will have to evaluate how this should be done.
```

**How much of holistic should appear in the pack?**

- One-line summary only  
- Regime strip (short + long bias/score/confidence)  
- Geo/energy flag only when elevated  
- Calendar stress score  
- Top pair biases (top 2)  
- Full trader brief (too large — not recommended)

**Your checkboxes / notes:**  

```
Lets add everything but the full trader brief.
```

---

### 8.2 Personalization — how hard should we steer?

`analysis_personalization.py` already maps onboarding → prompt block.

**Should the pack treat personalization as:**


| Stance     | Behavior                                                               |
| ---------- | ---------------------------------------------------------------------- |
| **Soft**   | Prefer user pairs when relevant; still cover macro movers              |
| **Hard**   | Only discuss instruments in `primary_pairs` unless event forces others |
| **Tiered** | Soft for holistic/calendar; harder for news                            |


**Your answer:**  

```
Tiered - for calendar and hollistic events that are tailored to a base currency of an economy, like USD, it should be soft mentioning on relevent pairs when it makes sense. For News, the user would definelty want to know how it could affect the pairs they trade so hard.
```

**For your profile (swing, advanced, EURUSD/GBPJPY/…):** should gold/crypto pairs appear in market snapshot when the headline is macro USD, or only when mentioned?

**Your answer:**  

```
If the user has mentioned trading gold, or crypto it should appear in market snapshot.
```

---

### 8.3 Market snapshot — how many instruments?

`relevant_market_context.py` already ranks by surface (calendar vs news weights differ).

**Max instruments in pack:**

- Calendar: **6** / **8** / **10** ?  
- News: **6** / **8** / **10** ?

**Always include for USD events (yields, VIX, oil)?**

- US02Y / US10Y  
- VIX  
- USOIL / GOLD  
- SPX

**Your answer:**  

```
Lets make the market snapshot relevant to the users onboarding and pairs they trade. For calendar, it should mostly be relevant to same currency pairs and also if the user is involved in gold or crypto it should mention it. 
```

---

### 8.4 Data quality and session — what must the model be told?

**When market is closed (weekend / holiday), should analysis:**

- Refuse to give levels  
- Give levels labeled illustrative only  
- Give “when reopen” framing only (no numbers)

**Your answer:**  

```
During market close, live news such as war or gepotlical tensioncs can still affect the market when it is reopened, or for some 24 hour markets like bitcoin. I believe levels should only be illustrative, and not like a signal, saying price could drop to "~109.00 etc". We dont have OHLC, but we can still determine key levels or numbers that are psychological where price could go to after market opens. For example, if live news has shown their has been bombing in iran, we can suggest or give an illustrative level that when markets repopne price could go to +2% ~4500$/oz.
```

**Confidence vocabulary (pick one team definition for later prompts):**


| Definition              | Meaning                                       |
| ----------------------- | --------------------------------------------- |
| **Synthesis certainty** | How sure the model is given available data    |
| **Edge strength**       | How strong the directional trade idea is      |
| **Data completeness**   | Mostly about missing actuals/stale indicators |


**Your answer:**  

```
Edge strength, what supports the directional trade idea and what negates it.
```

---

### 8.5 Holistic scan — role in input layer

Holistic is **not** GPT-generated for the main report today (see **§0**). Text comes from templates + curated files; scores/bias are math.

**Target architecture (recommended):**

1. **Keep deterministic core** — regime scores, pair map, calendar stress, data quality (source of truth).
2. **Shared input pack** feeds holistic the same user/macro/market context as news/calendar.
3. **Add LLM narrative layer** — GPT writes/refreshes `narrative`, highlights prose, and pair rationales from pack + deterministic JSON (do not let model override scores).
4. **Export `macro_snapshot`** from each scan for news/calendar prompts (H2).

**Choose approach:**


| Option       | Description                                                                                         |
| ------------ | --------------------------------------------------------------------------------------------------- |
| **H1**       | Pack only feeds **news + calendar**; holistic unchanged except reading shared `user`                |
| **H2**       | Holistic `build_scan` also stores a `macro_snapshot` blob for others (write-through)                |
| **H3**       | Add LLM narrative section using same pack ( **priority** — replaces static geo/templates over time) |
| **H1+H2+H3** | Shared pack in + snapshot out + GPT narrative on scan (recommended)                                 |


**Your answer (H1/H2/H3):**  

```
Pack should still feed input to Holistic, and we should also have a macro snapshot blob to be used in news + calendar.
We also want real GPT (or hybrid) writing for holistic narrative — not only templates/JSON (see §13).
```

**Should running a new holistic scan invalidate or refresh cached news analysis?**

- No — news stands alone  
- Show optional “context updated” on next open  
- Regenerate (expensive; unlikely)

**Your answer:**  

```
No — news stands alone, and Show optional “context updated” on next open  
```

---

### 8.6 Cross-surface tension (news vs scan)

Today `build_live_news_cross_context_note` runs only when V1 is enabled.

**When holistic says elevated geo/energy and news says neutral, should we:**

- Add one sentence to **prompt** (model writes reconciliation)  
- Add note to **UI only** after generation  
- Both  
- Skip unless user has run scan in last N hours

**Your answer:**  

```
Both
```

---

### 8.7 Token budget and cost

Rough target for shared pack prose (excluding area facts):

- ~400 tokens  
- ~800 tokens  
- ~1200 tokens

**Are you willing to add one extra Firestore read per news/calendar analysis for recent holistic?**

**Your answer:**  

```
Yes
```

---

### 8.8 Priority order (confirm)

Proposed wire order:

1. Live news
2. Calendar (enhanced)
3. Holistic alignment

**Agree / change:**  

```
Lets work on calendar -> live news -> Hollistic alignment
```

---

### 8.9 Success criteria — what does “good” look like?

Pick **3–5** real examples we will re-run after Phase C/D:


| #   | Fixture                         | Why                        |
| --- | ------------------------------- | -------------------------- |
| 1   | USD CPI (pre-release)           | Scenarios + macro context  |
| 2   | USD Retail Sales (post-release) | Actual vs forecast         |
| 3   | Hormuz / oil headline (news)    | Geo cross-check vs US scan |
| 4   | US holistic scan                | Baseline regime output     |
| 5   | (your choice)                   |                            |


**Your list:**  

```
I'll conduct testing later, and determine the sucess criteria.
```

**Subjective bar in one sentence:**  

```
e.g. "News analysis must mention whether it agrees with my last US scan when geo risk is elevated."
```

---

## 9. Risks and mitigations


| Risk                                           | Mitigation                                                       |
| ---------------------------------------------- | ---------------------------------------------------------------- |
| Pack too large → cost/latency                  | Rank + cap instruments; one-line macro default                   |
| Stale holistic misleads                        | `freshness_hours` + omit if over threshold                       |
| Breaking existing prompts                      | Pack behind env `ANALYSIS_CONTEXT_PACK_ENABLED`; A/B in staging  |
| Holistic deterministic path breaks             | H1: minimal changes; only shared `user` first                    |
| Duplication with `economy_context` vs holistic | Rule: prefer holistic when fresh, else `economy_context_service` |


---

## 10. Environment flags (planned)


| Flag                                     | Purpose                                     |
| ---------------------------------------- | ------------------------------------------- |
| `ANALYSIS_CONTEXT_PACK_ENABLED`          | Master switch for new pack in prompts       |
| `ANALYSIS_CONTEXT_PACK_INCLUDE_HOLISTIC` | Sub-flag for macro_snapshot from scan       |
| `ANALYSIS_CONTEXT_PACK_DEBUG`            | Log full pack to server logs (staging only) |


| Flag | Default | Effect |
|------|---------|--------|
| `ANALYSIS_CONTEXT_PACK_ENABLED` | off | Calendar prompts use pack instead of legacy personalization + market blocks |
| `ANALYSIS_CONTEXT_PACK_INCLUDE_HOLISTIC` | on (when pack on) | Attach holistic macro snapshot if scan &lt; 72h |
| `ANALYSIS_CONTEXT_PACK_DEBUG` | off | Log pack build in server logs |

Documented in `backend/.env.example`.

---

## 13. Holistic Scan — GPT narrative layer (shipped)

**Principle:** **Deterministic brain, GPT voice.**


| Layer                                                       | Owner                                      | Must not                             |
| ----------------------------------------------------------- | ------------------------------------------ | ------------------------------------ |
| Scores, bias, confidence %, pair direction, calendar stress | `economy_holistic_scan_service` math       | Be overridden by GPT                 |
| Narrative, driver explanations, geo framing, pair “why”     | GPT from `AnalysisContextPack` + scan JSON | Contradict deterministic bias/scores |


**Flow (as implemented):**

```
build_scan() → deterministic JSON (incl. template narrative + JSON geo)
       ↓
_build_holistic_narrative_prompt_payload(scan) → single GPT call
       ↓
validate → merge narrative.* + pair_explanations → API → UI
```

**GPT overwrites today:** `narrative.short_term`, `long_term`, `fx`, `geopolitical_energy`; `pair_setups[].driver`, `invalidation`.

**Still deterministic (not GPT):** scores/bias; `highlights[]`; `central_bank_context`; `pair_setups[].key_risk` (still uses JSON geo title); fallback narrative if GPT off/fails.

**Follow-up (optional):** pass `global_themes` / economy hooks into GPT payload; GPT `highlights[].detail`; UI badge (see table below).

**Guardrails:**

- Prompt: “Do not change bullish/bearish/neutral scores; explain them.”  
- Validator: narrative bias words must match `short_term.bias` / `long_term.bias` or be clearly labeled as risk scenario.  
- Fallback: if GPT fails, use today’s deterministic `narrative` (current behavior).  
- Env: `HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED` (default off until staging sign-off).  
- Quota: same analysis billing pool as scan run (one GPT call per scan, capped tokens).

### `holistic_scan_context.json` — what is hardcoded vs GPT?

**File:** `backend/data/holistic_scan_context.json` (`global_themes`, `economy_hooks`). Last curated update in file metadata (e.g. `lastUpdated`).

| Consumer | Uses JSON when | Uses GPT when |
| -------- | -------------- | ------------- |
| `narrative.geopolitical_energy` | Flag off or GPT fallback | Flag on + validation passed → **GPT text** (JSON not copied into prompt today) |
| Highlights geo row (`_build_highlights`) | **Always** — title/severity/detail from `global_themes[0]` + `economy_hooks[country]` | Never |
| `pair_setups[].key_risk` | **Always** — geo theme title | Never |
| Template `narrative` (fallback) | **Always** built first; kept if GPT fails | Overwritten on success |

So geo is **not fully hardcoded** in the UI anymore when Phase H is on: the **Comprehensive Context → Geopolitical & energy** paragraph is GPT-generated, but the **Key highlights** geo chip can still show curated JSON — possible copy mismatch until we align (pass JSON into GPT prompt or derive highlights from narrative).

**GPT prompt payload today** (`_build_holistic_narrative_prompt_payload`): scores, yields, event flags, trader brief, highlights dict, pair list, personalization — **does not include** `holistic_scan_context.json` text. GPT infers geo only from scan numbers + highlight blobs.

### Product decisions (recorded from shipped code — change if you want different behavior)


| # | Question | Shipped behavior (2026-05-27) |
| --- | -------- | ------------------------------ |
| H-GPT-1 | One GPT call vs several? | **One call** per scan (`max_tokens` 900, `gpt-4o-mini` default via `OPENAI_HOLISTIC_MODEL`) |
| H-GPT-2 | Replace JSON geo or augment? | **Hybrid:** JSON remains source for highlights + `key_risk` + fallback; GPT **replaces** `narrative.geopolitical_energy` (and other narrative fields) when enabled — JSON **not** injected into GPT prompt yet |
| H-GPT-3 | UI honesty badge? | **Not built** — API exposes `narrative_source` (`gpt` / `deterministic_fallback` / `deterministic_disabled`); Economies tab does not display it |

---

## 11. Revision log


| Date       | Change                                                                     |
| ---------- | -------------------------------------------------------------------------- |
| 2026-05-18 | Initial planning doc; spine deferred; backend map + decision questionnaire |
| 2026-05-18 | §0 holistic deterministic truth; §13 GPT narrative plan; §8.5/§7 updated   |
| 2026-05-18 | §8 decisions locked; build order calendar → news → holistic                  |
| 2026-05-23 | Phase B: `analysis_context_pack.py` + `test_analysis_context_pack.py`        |
| 2026-05-26 | Phase C: calendar wired in `gpt_ai_analysis.py`; progress tracker + env flags |
| 2026-05-26 | Phase D: live news wired in `mvp_news_analyzer.py` |
| 2026-05-26 | Phase E–F: macro_snapshot + prompt quality pass |
| 2026-05-27 | Phase G–H: debug flags + holistic GPT narrative; §13 decisions documented |
| 2026-05-27 | Input layer Phases A–H marked complete (flags still default off) |
| 2026-05-27 | §12 post-input-layer sequence + manual `holistic_scan_context.json` workflow |
| 2026-05-27 | Full overlay integration: multi-theme highlights, GPT payload, macro_snapshot digest, `critical` → elevated |


---

## 12. Suggested sequence (after input layer)

Input layer implementation (Phases A–H) is **complete**. Product/engineering order below reflects team decisions (2026-05-27). **V1 spine is deferred** until prompts and response fields feel stable.

See also: `AI_ANALYSIS_FOUNDATION_ROADMAP.md` → **Post-input-layer sequence**.

### Priority order

| Step | Focus | Goal | Automation |
| ---- | ----- | ---- | ---------- |
| **1** | `backend/data/holistic_scan_context.json` | Accurate curated geo/macro floor for highlights, `key_risk`, fallback narrative | **Manual** — refresh a few times per month; no automation planned (low effort vs. cost/complexity) |
| **1b** | Wire overlay into holistic GPT (engineering) | **Done** — `curated_macro_overlay` on scan; GPT prompt + multi-theme highlights + richer `macro_snapshot` |
| **2** | **Prompt tailoring per surface** | Sharper, section-specific instructions (holistic → calendar → news) | Prompt edits only |
| **3** | **Response fields review** | Add/remove/rename JSON fields and UI sections per surface (body copy, not spine) | Product + schema pass |
| **4** | **§8.9 fixture review** | Subjective quality bar on fixed samples (CPI, Retail Sales, Hormuz, US scan) | You test when ready |
| **5** | **Phase 3 — calendar trust** | Scenario repair pass, live spot in prompt, Above/On/Below UI | See foundation roadmap |
| **6** | **Production flags** | Turn on `ANALYSIS_CONTEXT_PACK_ENABLED` and `HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED` for all users | When staging sign-off passes |
| **Later** | **V1 spine** | Re-enable `ANALYSIS_V1_ENABLED` + `VITE_ANALYSIS_V1_ENABLED` | After steps 1–3 feel good |
| **Later** | **Phase 4+** | Router, verifier, outcome store, calibration | Not now |

### Holistic GPT decisions (locked)

| Topic | Decision |
| ----- | -------- |
| H-GPT-1 | **One GPT call** per holistic scan (narrative + pair explanations in one JSON response) |
| H-GPT-2 | **Augment** with human-edited `holistic_scan_context.json` (not replace with automation); inject into GPT prompt when step 1b ships |
| H-GPT-3 | UI honesty badge (`narrative_source`) — **optional**, not blocking |

### Maintaining `holistic_scan_context.json` (manual workflow)

**File:** `backend/data/holistic_scan_context.json`

**When to update (roughly):** a few times per month, or when a major geo/energy/policy theme clearly shifts (e.g. new conflict corridor, OPEC shock, sustained oil move).

**What to edit:**

| Field | Purpose |
| ----- | ------- |
| `lastUpdated` | Bump to today (ISO date) on every edit |
| `global_themes[]` | Active cross-market risks (title, summary, energy_channel, severity) |
| `economy_hooks` | Per-economy (US, EUR, GBP, JPY) one-liner on how that theme hits policy/FX |

**After saving:** restart backend (or redeploy) so scans load the new overlay. Re-run a holistic scan to verify highlights + geo narrative.

**Not in scope:** automated news scraping, scheduled GPT refresh of this file, or third-party geo APIs — manual curation is intentional.

### Prompt tailoring (step 2) — surfaces

| Surface | Code | What to tune |
| ------- | ---- | ------------- |
| Holistic | `economy_holistic_scan_service.py` → `_create_holistic_narrative_prompt` | Per-field rules: short-term vs long-term vs fx vs geo vs pair driver/invalidation; emphasis `**` |
| Calendar | `gpt_ai_analysis.py` + `analysis_context_pack.py` (`CALENDAR_PACK_PROMPT_RULES`) | Regime vs event, scenarios, levels, post-event vs pre-event |
| Live news | `mvp_news_analyzer.py` + `NEWS_PACK_PROMPT_RULES` | Headline reconciliation with macro snapshot, pair focus, illustrative levels when closed |

### Response fields (step 3) — questions to answer per surface

- Which fields do traders actually read vs skip?
- Should holistic `highlights` be GPT-generated to match narrative?
- Should calendar scenarios use `forward_scenarios_by_outcome` as the primary UI?
- Keep `central_bank_context` as its own holistic block or fold into short-term narrative?

Document answers here or in `AI_ANALYSIS_V1_UNIFIED_SPEC.md` when decided — **without** enabling spine UI until copy is stable.

