# Holistic Scan Direction (Economies Tab)

## Why this document exists

The `Hollistic Scan` section in `src/components/Economies.jsx` is still a placeholder (`Coming soon`), but the project already has a mature analysis pipeline in the Overview tab (`/api/enhanced-analysis/<news_id>`).  
This document defines the direction for building a real Holistic Scan by reusing proven patterns from Overview, instead of creating a disconnected second system.

Also, we should standardize naming to **Holistic Scan** (not `Hollistic`) across UI, API, and docs so search, analytics, and maintenance are consistent.

---

## Product intent (what Holistic Scan should do)

Holistic Scan should answer one practical FX question per economy:

1. What is the **short-term macro bias** (2-6 weeks)?
2. What is the **long-term macro bias** (3-12 months)?
3. How does that bias map to the economy's **correlated FX pairs**?
4. Why does the system think that (transparent drivers + confidence)?

This is intentionally different from event-level analysis.  
Overview explains one event deeply; Holistic Scan should synthesize many signals into a regime view.

---

## Current state in codebase

### Frontend placeholder
- `src/components/Economies.jsx`
  - `analysisRef` and "Hollistic Scan" button already exist.
  - Analysis panel currently renders:
    - title: `Hollistic Scan`
    - body: `Coming soon`

### Existing data already available
- Economy indicators:
  - frontend endpoint config: `src/config.js` -> `economyIndicators(countryCode)`
  - backend route: `backend/app.py` -> `/api/economy-indicators/<country_code>`
  - service: `backend/services/google_sheets_service.py`
- Economic event calendar:
  - backend route: `backend/app.py` -> `/api/economic-calendar`
  - source service: `backend/services/hybrid_economic_calendar.py`
- Extra macro context:
  - `/api/market-sentiment`
  - `/api/prediction-markets`

This means Holistic Scan can be built with mostly existing inputs.

---

## How Overview event analysis currently works (reference architecture)

This is the flow to mirror where appropriate.

### Frontend flow (`src/components/Overview.jsx`)
1. User triggers analysis for a selected event.
2. Frontend decides analysis type (`pre-event` vs `post-event`) based on `actual` data presence.
3. Frontend POSTs to `/api/enhanced-analysis/<event.id>` with:
   - event payload
   - analysis type
   - market context metadata
   - Firebase token in `Authorization` header if available
4. UI has explicit state machine:
   - `default`, `pending`, `loading`, `event-analysis`, `error`
5. UI normalizes backend payload with `normalizeAiAnalysis(...)` to tolerate snake_case/camelCase drift.
6. On error, UI maps backend status to typed UX messages (quota, validation, service, generic).
7. Frontend loads recent persisted analyses from `/api/calendar-analysis-history`.

### Backend flow (`backend/app.py`)
Route: `/api/enhanced-analysis/<news_id>`

1. Extract authenticated user from Firebase token (`_extract_user_from_token`).
2. Enforce per-user quota via Stripe usage checks (returns `429 analysis_limit_reached` when needed).
3. Validate event payload with `economic_data_validator.validate_event_data(...)` before expensive analysis.
4. Build market context from `live_market_data_service`.
5. Run GPT analyzer: `gpt_ai_analyzer.analyze_macro_event(...)`.
6. Track usage + increment billing counters.
7. Transform result into a stable response schema.
8. Persist snapshot in Firestore via `calendar_analysis_store.save_calendar_analysis(...)`.

Route: `/api/calendar-analysis-history`

1. Requires Firebase auth.
2. Returns per-user recent analysis snapshots from Firestore (`calendar_analysis_store.get_recent_calendar_analyses`).

### Why this matters for Holistic Scan

The Overview pipeline already solved the hard production concerns:
- auth and user linkage
- quota/rate handling
- data validation
- response normalization strategy
- persistence for "Recent"
- user-friendly error typing

Holistic Scan should reuse these patterns to avoid repeating known failure modes.

---

## Recommended Holistic Scan architecture

## 1) New backend endpoint

Add:
- `GET /api/economy-scan/<country_code>`
- Optional query params:
  - `horizon=short|long|both` (default `both`)
  - `refresh=true` (bypass scan cache)

Why:
- keeps synthesis logic server-side (versioned, testable, hidden weights)
- avoids exposing scoring internals in frontend JS

## 2) New backend service

Add a service module, e.g.:
- `backend/services/economy_holistic_scan_service.py`

Responsibilities:
- ingest normalized signals from:
  - economy indicators (Google Sheets service output)
  - economic calendar (hybrid calendar events)
  - optional market sentiment / prediction market context
- compute:
  - short-term score (`-100..100`)
  - long-term score (`-100..100`)
  - confidence score (`0..100`)
- produce transparent driver list and correlated pair mapping
- include `data_quality` and freshness metadata

## 3) Suggested response contract (v1)

```json
{
  "country": "US",
  "timestamp": "2026-03-23T10:30:00Z",
  "short_term": {
    "bias": "bullish",
    "score": 34,
    "confidence": 72,
    "drivers": [
      {"name": "Rate differential momentum", "direction": "positive", "weight": 0.30, "note": "Front-end yields favor USD"},
      {"name": "Upcoming high-impact events", "direction": "negative", "weight": 0.20, "note": "CPI/FOMC event risk"}
    ]
  },
  "long_term": {
    "bias": "neutral",
    "score": 8,
    "confidence": 64,
    "drivers": [
      {"name": "Inflation trend", "direction": "positive", "weight": 0.25, "note": "Disinflation progressing"},
      {"name": "Growth momentum", "direction": "neutral", "weight": 0.25, "note": "Mixed PMI/GDP signal"}
    ]
  },
  "fx_pairs": [
    {"pair": "EURUSD", "bias": "bearish", "strength": "medium", "reason": "USD short-term macro edge"},
    {"pair": "USDJPY", "bias": "bullish", "strength": "medium", "reason": "Yield differential support"}
  ],
  "data_quality": {
    "status": "good",
    "missing_signals": [],
    "staleness_seconds": 412
  },
  "model_version": "economy_scan_v1"
}
```

Why:
- this gives useful UI output and keeps "why" visible to the user
- confidence + quality fields prevent false precision

---

## Scoring model direction (deterministic first)

Start rule-based and transparent, then optionally layer AI narrative later.

### Short-term bucket (2-6 weeks)
- latest momentum in inflation/jobs/PMI indicators
- near-term high-impact calendar event risk
- rate/yield differential trend proxy
- market sentiment/prediction market tilt (low weight)

### Long-term bucket (3-12 months)
- growth trend composite (GDP/PMI/labor trend)
- inflation regime vs target
- policy trajectory trend (tightening/easing bias)
- structural macro stability proxy

### Mapping score to bias
- `score > 20` -> bullish
- `score < -20` -> bearish
- otherwise neutral

### Confidence calculation
Confidence should degrade when:
- signals are missing
- inputs are stale
- signals strongly disagree

Why this approach:
- deterministic output is debuggable and testable
- less brittle than AI-only generation for first production release

---

## Correlated pair strategy

Define a static country->pair map in config/service:

- `US`: `EURUSD`, `USDJPY`, `GBPUSD`, `AUDUSD`
- `EUR`: `EURUSD`, `EURGBP`, `EURJPY`
- `GBP`: `GBPUSD`, `EURGBP`, `GBPJPY`
- `JPY`: `USDJPY`, `EURJPY`, `GBPJPY`

Then convert economy bias to pair direction using base/quote orientation.

Why:
- users trade pairs, not isolated economies
- deterministic mapping keeps output consistent

---

## Frontend implementation direction (`Economies.jsx`)

Replace the placeholder analysis card with a stateful panel similar to Overview:

### Suggested state machine
- `default` (no response yet)
- `loading`
- `ready`
- `error`

### Fetch behavior
- call `/api/economy-scan/<selectedEconomy>` when:
  - economy selection changes
  - user taps "refresh"
- cache per-economy responses (e.g., 30-60s) to avoid noisy refetching

### UI sections
1. Short-term bias card
2. Long-term bias card
3. Correlated pairs outlook list
4. "Top drivers" bullets
5. Data quality/freshness footer

### Error UX (copy Overview strategy)
- quota/rate limits
- validation/data-quality issues
- temporary service unavailability
- generic fallback message

Why:
- consistent UX patterns reduce user confusion
- easier implementation because team already uses this in Overview

---

## Persistence and "Recent Scans" (Phase 2)

After MVP works, add per-user scan history:
- backend route: `/api/economy-scan-history?limit=...`
- storage model patterned after `calendar_analysis_store`
- frontend dropdown "Recent Scans" for quick restore

Why:
- reusability without recomputation
- continuity across sessions, same as event analysis UX

---

## Delivery plan

### Phase 1 (MVP, deterministic, no GPT dependency)
1. Create `economy_holistic_scan_service`.
2. Add `/api/economy-scan/<country_code>` route.
3. Implement score + confidence + fx pair mapping.
4. Wire `Economies.jsx` panel to endpoint and remove "Coming soon".
5. Rename UI labels to `Holistic Scan`.
6. Add backend tests for scoring and schema.

### Phase 2 (hardening)
1. Add scan history persistence + retrieval endpoints.
2. Add stronger data quality diagnostics.
3. Add observability (latency, cache-hit, missing-signal metrics).

### Phase 3 (optional AI narrative layer)
1. Generate one-paragraph narrative from deterministic output.
2. Keep deterministic payload as source-of-truth.
3. Enforce quota and fallback rules mirroring Overview.

---

## Guardrails / non-goals

- Do not make v1 fully AI-generated.  
  Reason: less predictable, harder to test, harder to trust for beginners.
- Do not block UI if one source is unavailable.  
  Reason: existing product favors graceful degradation.
- Do not hide drivers behind a single label.  
  Reason: users need explanatory transparency to trust signals.

---

## Immediate code tasks to start next

1. Rename "Hollistic Scan" to "Holistic Scan" in `src/components/Economies.jsx`.
2. Add backend endpoint stub for `/api/economy-scan/<country_code>`.
3. Define shared response schema (Python dict contract + frontend normalizer).
4. Implement first 3-5 deterministic drivers using existing indicator/calendar inputs.
5. Render short/long bias cards in the Economies analysis panel.

