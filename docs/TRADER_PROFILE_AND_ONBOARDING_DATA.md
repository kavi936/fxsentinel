# Trader profile & onboarding data

This document describes where onboarding and trading-preference data lives, how it is accessed, and how you can use it for product behavior, analysis, and marketing.

## Storage (Firestore)

All of this is stored on the **same document** as billing and other app state:

| Location | Description |
|----------|-------------|
| Collection | `users` |
| Document ID | Firebase Auth **UID** (same as `users/{uid}` used for Stripe, usage counts, etc.) |

Writes use **`set(..., merge=True)`**, so existing fields such as `subscription_status`, `monthly_analysis_count`, or `stripe_customer_id` are **not** wiped when saving `trader_profile` or onboarding timestamps.

### Fields at document root (`users/{uid}`)

| Field | Type | Purpose |
|-------|------|---------|
| `trader_profile` | `map` | See below — main preference payload |
| `onboarding_survey_completed_at` | `timestamp` | Set when the user **completes** the survey (full submit) |
| `onboarding_survey_skipped_at` | `timestamp` | Set when the user taps **Skip for now** (no `trader_profile` required) |
| `onboarding_survey_version` | `number` | Schema version (currently `1`); bump if you add breaking survey changes |
| `user_email` | `string` | Optional; may be set on merge when saving from the API |

If **both** `onboarding_survey_completed_at` and `onboarding_survey_skipped_at` are absent, the app treats the user as **needing the onboarding survey** (`needs_survey: true` from the API).

### Map: `trader_profile`

| Field | Type | Notes |
|-------|------|--------|
| `trading_style` | `string` | One of: `day`, `swing`, `both`, `unsure` |
| `experience_level` | `string` | One of: `beginner`, `intermediate`, `advanced` |
| `primary_pairs` | `array<string>` | Up to **24** instruments, each `BASE/QUOTE` (e.g. `EUR/USD`, `XAU/USD`, `US500/USD`). Validated server-side. |
| `marketing_opt_in` | `boolean` | Product tips / occasional offers by email |
| `primary_goal` | `string` | One of: `stay_informed`, `analysis_workflow`, `alerts`, `learning`, `other` |
| `referral_source` | `string` | One of the allowed slugs (search, social platforms, friend, etc.) — see backend `REFERRAL_SOURCES` |
| `updated_at` | `timestamp` | Set on full profile save (not on skip-only) |

Canonical validation and allowed enums live in:

- `backend/services/user_trader_profile.py` (`TRADING_STYLES`, `EXPERIENCE_LEVELS`, `PRIMARY_GOALS`, `REFERRAL_SOURCES`, `INSTRUMENT_PATTERN`, `MAX_PAIRS`)

Frontend labels for goals and referral (must stay in sync with backend slugs):

- `src/constants/onboardingSurveyOptions.js`

Instrument presets (UI only; stored values are still `BASE/QUOTE` strings):

- `src/constants/forexPairs.js` (`PRESET_MARKET_INSTRUMENTS`)

---

## HTTP API

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/api/user/trader-profile` | `Authorization: Bearer <Firebase ID token>` |
| `PUT` | `/api/user/trader-profile` | Same |

Implemented in `backend/app.py` (`api_user_trader_profile`). The same route exists when running `scripts/main_app.py` (mirrored for local dev).

### `GET` response (conceptual)

- `needs_survey` — `true` if the user has not completed or skipped onboarding (and read succeeded).
- `trader_profile` — object with the fields above (nulls if never set).
- `onboarding_survey_completed_at`, `onboarding_survey_skipped_at` — ISO strings or `null`.
- `onboarding_survey_version`
- `firestore_available` — `false` if Firestore could not be read (degraded behavior).

### `PUT` body

**Skip onboarding**

```json
{ "skipped": true }
```

**Complete or update preferences** (validation requires all fields below)

```json
{
  "skipped": false,
  "trading_style": "day",
  "experience_level": "intermediate",
  "primary_pairs": ["EUR/USD", "XAU/USD"],
  "marketing_opt_in": false,
  "primary_goal": "stay_informed",
  "referral_source": "search"
}
```

---

## Where users see and edit this data

| Surface | Purpose |
|---------|---------|
| **Onboarding survey** (`/onboarding-survey`) | Multi-step flow after sign-in; writes via `PUT`. |
| **Profile → Trading preferences** (`ProfilePopup`) | Same payload; users can change answers later. |
| **Firebase Console** | Browse `users` → document by UID to inspect raw fields for support or one-off analysis. |

---

## How to use this data (current and future)

### Already wired

- **Onboarding gating**: `needs_survey` drives redirect to `/onboarding-survey` until complete or skip (`TraderProfileGate`, `OnboardingSurvey`).
- **Persistence**: All fields above are saved to Firestore when the user completes the survey or updates Profile.

### Natural next steps (not automatically connected today)

These are intentional integration points — implement when you prioritize them:

| Data | Possible use |
|------|----------------|
| `experience_level` | Softer vs denser copy in tooltips, AI prompts, or education modules. |
| `primary_pairs` | Prioritize calendar rows, news tags, or default alert pairs (align with `preferences.currencyPairs` in alert settings if you sync). |
| `trading_style` | Session-focused vs swing-focused defaults or ordering in the UI. |
| `primary_goal` | First-run emphasis (e.g. calendar vs alerts vs learning). |
| `referral_source` | Marketing attribution, channel ROI, cohort reports. |
| `marketing_opt_in` | ESP segments (only email users who opted in; respect unsubscribes in the mail tool). |

### Analysis and reporting

- **Firestore exports / BigQuery** (if linked): aggregate `trader_profile.*` and referral counts by `referral_source`.
- **Internal scripts**: Use Admin SDK to list `users` and read `trader_profile` (read-only analytics — follow privacy policy).
- **Product analytics**: Fire events with **non-sensitive** buckets (e.g. `experience_level`, `primary_goal`) if your analytics stack allows; avoid sending raw email in custom dimensions unless required.

### Privacy & compliance

- Treat `trader_profile` as **personal data** tied to UID (and often email on the same doc).
- Use `marketing_opt_in` only for the purposes described at collection time.
- `referral_source` is low sensitivity but still useful for internal metrics.

---

## Implementation reference (code)

| Piece | Location |
|-------|----------|
| Firestore read/write + validation | `backend/services/user_trader_profile.py` |
| Flask routes | `backend/app.py` (`/api/user/trader-profile`) |
| Lazy Firestore client | `UserTraderProfileStore._ensure_client()` — avoids connecting before Firebase Admin init |
| Survey UI | `src/components/OnboardingSurvey.jsx` |
| Profile editing | `src/components/ProfilePopup.jsx` |
| Instrument input parsing (client) | `src/utils/instrumentInput.js` |

---

## Related docs

- `docs/FIRESTORE_AND_AUTH_USER_SYNC.md` — how `users/{uid}` relates to Auth and billing.

---

## Personalization playbook from onboarding data

This section translates each onboarding field into concrete product behavior so onboarding data is not only stored, but actively used to improve experience quality.

### 1) `trading_style` (`day`, `swing`, `both`, `unsure`)

What it signals:

- Preferred trading horizon and analysis cadence.

How to use it:

- AI Analysis:
  - `day`: prioritize intraday catalysts, session timing, and short-term invalidation cues.
  - `swing`: prioritize multi-day structure, macro themes, and follow-through risk.
  - `both`: provide two-lens output (intraday + swing).
  - `unsure`: use lighter educational guidance and explain both horizons.
- Calendar ranking:
  - Up-rank immediate event timing for day traders.
  - Up-rank trend-shaping macro events for swing traders.
- Alert defaults:
  - Day users get tighter, time-sensitive defaults.
  - Swing users get broader thesis-level defaults.

Why this improves UX:

- Analysis style aligns with the user's decision horizon instead of forcing one generic format.

### 2) `experience_level` (`beginner`, `intermediate`, `advanced`)

What it signals:

- How much complexity and jargon the user can absorb without friction.

How to use it:

- AI Analysis:
  - `beginner`: define terms, add context, explain why each event matters.
  - `intermediate`: balanced detail and interpretation.
  - `advanced`: concise, dense signal-first analysis.
- UI and education:
  - Beginner-facing tooltips and guided hints.
  - Advanced-facing compact UI copy with fewer interrupts.
- Risk communication:
  - Stronger explicit risk reminders for beginners near high-volatility events.

Why this improves UX:

- Reduces cognitive overload for new users while avoiding shallow output for experienced users.

### 3) `primary_pairs` (`array<string>`, max 24)

What it signals:

- Markets the user actually tracks and acts on.

How to use it:

- AI Analysis:
  - Prioritize commentary and examples for selected instruments first.
- Calendar and news:
  - Rank and highlight events most likely to impact the selected pairs.
- Alerts and defaults:
  - Prefill watchlists and suggested alert instruments from this list.

Why this improves UX:

- Improves relevance immediately and removes broad-market noise.

### 4) `marketing_opt_in` (`boolean`)

What it signals:

- Email communication consent.

How to use it:

- Communication systems:
  - Segment lifecycle tips, education, and optional campaign messaging.
- Compliance:
  - Use strictly for consented communication purposes.

Why this improves UX:

- Supports trust-preserving outreach without overreaching into product inference.

### 5) `primary_goal` (`stay_informed`, `analysis_workflow`, `alerts`, `learning`, `other`)

What it signals:

- The primary "job to be done" the user expects from the product.

How to use it:

- AI Analysis format:
  - `stay_informed`: concise summary-first briefs.
  - `analysis_workflow`: structured scenario and level-driven output.
  - `alerts`: trigger-oriented, monitoring-focused summaries.
  - `learning`: educational and explanatory output.
- Product emphasis:
  - First-run highlights and nudges should map to the user's goal.

Why this improves UX:

- Aligns product behavior with intent, increasing perceived value and retention.

### 6) `referral_source` (allowed backend slug)

What it signals:

- Acquisition channel origin.

How to use it:

- Analytics and operations:
  - Attribution and channel-quality cohort reporting.
- UX refinement:
  - Detect channel-specific onboarding friction and improve copy/flow per cohort.

Why this improves UX:

- Improves onboarding quality indirectly by revealing where users struggle.

### Survey-state fields that matter operationally

These are not preference traits, but they determine onboarding behavior quality over time:

- `onboarding_survey_completed_at`: confirms full completion.
- `onboarding_survey_skipped_at`: confirms explicit skip.
- `onboarding_survey_version`: enables safe survey evolution and re-prompt strategy.
- `trader_profile.updated_at`: indicates data freshness.

Use cases:

- Keep onboarding gate logic reliable.
- Re-prompt stale profiles only when needed.
- Compare completion vs skip cohorts.

### Highest-value fields for in-app personalization

For direct UX quality, prioritize these fields in this order:

1. `primary_pairs`
2. `experience_level`
3. `trading_style`
4. `primary_goal`

`referral_source` is strongest for attribution/cohorts, while `marketing_opt_in` is primarily a consent control for messaging.

### Recommended implementation pattern

Instead of having each subsystem reinterpret raw survey values, derive one internal personalization object and reuse it across AI, calendar, and alerts. Example shape:

- `analysis_tone`
- `analysis_depth`
- `time_horizon_bias`
- `priority_instruments`
- `default_feature_emphasis`
- `education_mode`

Why this approach:

- Keeps personalization consistent across surfaces.
- Simplifies future changes to onboarding schema.
- Prevents drift between AI prompts, ranking logic, and UI defaults.

---

## AI analysis personalization implementation plan

This section turns the personalization playbook into an implementation path for the three core analysis surfaces:

- Economic calendar analysis (`AI Analysis` card)
- Live news analysis (`Live News` card)
- Economies (`Holistic Scan`)

### Current state (what is already in place)

- Onboarding preferences are saved and validated in Firestore under `users/{uid}.trader_profile`.
- AI analysis endpoints already extract authenticated user context from Firebase tokens.
- Calendar and Live News analysis pipelines already pass `user_info` through core analyzer code paths for usage tracking.
- Holistic Scan has a deterministic backend service with centralized output construction.

What is missing today:

- `trader_profile` is not yet systematically injected into AI prompts, instrument ranking, or deterministic narrative shaping.

### Architecture recommendation

Add a shared backend personalization adapter, then wire each analysis surface to it.

Proposed service:

- `backend/services/analysis_personalization.py`

Proposed responsibilities:

- Read and normalize onboarding profile (with safe defaults if missing/unavailable).
- Build compact prompt-context blocks for GPT surfaces.
- Re-rank instrument/pair lists with user preference priority.
- Map `experience_level`, `trading_style`, and `primary_goal` into stable UX behavior flags.

Suggested normalized object:

- `analysis_tone`
- `analysis_depth`
- `time_horizon_bias`
- `priority_instruments`
- `default_feature_emphasis`
- `education_mode`

### Surface-by-surface implementation

#### 1) Economic calendar analysis (`AI Analysis` card)

Primary files:

- `backend/app.py` (`/api/enhanced-analysis/<news_id>`)
- `backend/services/gpt_ai_analysis.py`

Implementation:

- Fetch user personalization after token extraction in the route.
- Pass personalization into `gpt_ai_analyzer.analyze_macro_event(...)`.
- Extend prompt-building in `GPTAIAnalyzer._create_analysis_prompt(...)` with a concise user-personalization block.
- Apply style/depth/horizon guidance from:
  - `experience_level`
  - `trading_style`
  - `primary_goal`
  - `primary_pairs` (where relevant to event/pair discussion)

Expected UX impact:

- Better analysis framing (intraday vs swing, dense vs explanatory) while keeping existing market-context rigor.

#### 2) Live News analysis (`Live News` card)

Primary files:

- `backend/app.py` (`/api/analysis/<news_id>`, `generate_news_analysis(...)`)
- `backend/services/mvp_news_analyzer.py`

Implementation:

- Resolve personalization once in the route and pass it through `generate_news_analysis(...)` into analyzer calls.
- Extend `MVPNewsAnalyzer` prompt assembly with the same normalized personalization context.
- Re-rank `key_pairs` output so `primary_pairs` are prioritized when relevant.

Expected UX impact:

- News commentary and pair focus become visibly more relevant to what each user actually trades.

#### 3) Economies (`Holistic Scan`)

Primary files:

- `backend/app.py` (`/api/economy-scan/<country_code>`)
- `backend/services/economy_holistic_scan_service.py`

Implementation:

- Keep core deterministic scoring unchanged initially.
- Apply personalization to presentation and ordering:
  - Prioritize user-relevant pairs in `fx_pairs` / `pair_setups`.
  - Shift emphasis in `trader_brief` and highlights based on `trading_style` (short-term vs long-term focus).
  - Adjust clarity layer based on `experience_level` (education-first vs concise framing).

Expected UX impact:

- Preserves scan stability while making output feel tailored to user intent and skill level.

### Rollout plan

#### Phase 1 (high impact / low risk)

- Implement shared personalization service.
- Wire into Calendar and Live News GPT prompts.
- Add pair prioritization in those two surfaces.

#### Phase 2

- Add Holistic Scan ordering/emphasis personalization (no scoring changes).

#### Phase 3

- Add personalization telemetry and quality checks:
  - personalization applied flag
  - profile completeness
  - engagement/retention deltas by profile segment

### Reliability and fallback rules (required)

- Never block analysis generation if profile fetch fails.
- If profile data is missing/stale/invalid, use neutral defaults.
- Keep billing/usage and analysis routes functional even when personalization is unavailable.
- Treat personalization as an additive layer, not a hard dependency.

---

## Implementation log (current state)

This section records what has been implemented so far across onboarding-based personalization and market-context relevance. Use it as the source of truth when revisiting or refining behavior.

### Scope completed

- Phase 1 completed: personalization integrated into Calendar AI Analysis and Live News prompts.
- Phase 2 completed: personalization integrated into Holistic Scan presentation/order (without changing deterministic scoring).
- Market context relevance upgrade completed: analyzers now consume expanded ticker universe via a relevance-ranked snapshot (not legacy major-FX only).

### New backend services added

#### `backend/services/analysis_personalization.py`

Purpose:

- Centralize onboarding-profile normalization for analysis surfaces.

What it provides:

- `get_user_personalization(user_id)`:
  - Reads `users/{uid}.trader_profile`
  - Returns normalized fields and behavior flags with safe defaults
- `build_prompt_personalization_block(...)`:
  - Prompt-ready personalization context block
- `prioritize_instruments(...)`:
  - Reorders instruments so user-preferred assets are prioritized

Why added:

- Prevent duplicated or drifting personalization logic across calendar/news/holistic systems.

#### `backend/services/relevant_market_context.py`

Purpose:

- Build compact, relevant price/change snapshots from the expanded TradingView instrument catalog for AI prompts.

What it provides:

- Relevance-based selection using:
  - event currency mapping
  - keyword/topic mapping
  - focus instruments
  - user preferred instruments
  - top movers fallback
- Weighted ranking model:
  - Event relevance
  - Market regime relevance
  - User preference relevance
  - Freshness/quality

Surface-specific weight profiles:

- Calendar (`surface="calendar"`): event-led  
  `event=0.60, regime=0.20, preference=0.15, freshness=0.05`
- News (`surface="news"`): more personalized  
  `event=0.45, regime=0.20, preference=0.30, freshness=0.05`
- Generic fallback  
  `event=0.50, regime=0.20, preference=0.25, freshness=0.05`

Why added:

- Live ticker expanded beyond major FX, but AI context was still mostly legacy FX-centric.
- This service bridges expanded ticker coverage into analysis context while controlling prompt noise.

### Files changed and integration points

#### `backend/app.py`

Changes:

- Imports `get_user_personalization`.
- `/api/enhanced-analysis/<news_id>`:
  - Builds personalization from authenticated user and passes into GPT analyzer.
- `/api/analysis/<news_id>`:
  - Builds personalization and passes it into `generate_news_analysis(...)`.
- `generate_news_analysis(...)`:
  - Updated signature to accept route-provided `token_user_info` and `personalization`.
  - Removed duplicate token extraction in helper path.
- `/api/economy-scan/<country_code>`:
  - Passes personalization into deterministic scan builder.

#### `backend/services/gpt_ai_analysis.py`

Changes:

- Accepts `personalization` in:
  - `analyze_macro_event(...)`
  - `_generate_enhanced_gpt_analysis(...)`
  - `_create_analysis_prompt(...)`
- Injects:
  - `USER PERSONALIZATION CONTEXT`
  - `RELEVANT LIVE MARKET SNAPSHOT` (expanded ticker, relevance-ranked)
- Calls snapshot builder with `surface="calendar"`.

#### `backend/services/mvp_news_analyzer.py`

Changes:

- Accepts `personalization` in:
  - `analyze_news(...)`
  - `_analyze_with_gpt(...)`
  - `_create_enhanced_prompt(...)`
- Uses `prioritize_instruments(...)` to rank affected instruments and `key_pairs`.
- Injects:
  - `USER PERSONALIZATION CONTEXT`
  - `RELEVANT LIVE MARKET SNAPSHOT`
- Calls snapshot builder with `surface="news"`.

#### `backend/services/economy_holistic_scan_service.py`

Changes:

- `build_scan(...)` accepts `personalization`.
- Pair ordering:
  - `_map_fx_pairs(...)` can prioritize preferred pairs when present.
- Presentation-level personalization only:
  - `_build_trader_brief(...)` adds style/experience guidance notes.
  - `_build_highlights(...)` adds personalized focus item and beginner guidance when relevant.

Important:

- Core deterministic scoring and regime math were intentionally left unchanged.

### Behavioral outcomes after implementation

- Calendar AI:
  - Macro analysis prompt now includes user profile guidance and relevant cross-asset snapshot.
- Live News AI:
  - News prompt now includes user profile guidance and relevance-ranked snapshot from expanded ticker universe.
  - Output pair ordering favors user preferences when relevant.
- Holistic Scan:
  - Output ordering/emphasis is personalized; deterministic score engine remains stable.

### Known tuning levers for future revisions

- Ranking weights by surface (`calendar` vs `news`).
- Keyword mapping coverage in relevant-market-context builder.
- Snapshot size (`limit`) to balance richness vs prompt token cost.
- Prompt personalization block length (compact vs verbose modes).
- Holistic-scan wording style for beginner-oriented guidance.

### Validation completed during implementation

- Lint checks were run after edits on modified files (no introduced lint errors).
- Python compile checks were run on modified backend services/routes (syntax passed).
