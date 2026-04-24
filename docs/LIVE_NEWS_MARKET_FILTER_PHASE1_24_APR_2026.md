# Live News Market Filter Phase 1
**Date:** 24 April 2026  
**Scope:** Move live news filtering from forex-first to market-wide policy.

## Why this change was made

The live news system was originally built around forex relevance, which created multiple stacked forex-only gates:
- Source ingestion filters
- API cleanup filters
- Frontend rendering filters
- Alert qualification filters

This conflicted with the product direction to support broader market coverage.  
Target policy is now:
- **Include:** FX, crypto, indices, commodities, macro/rates
- **Exclude:** Stocks/equities and company-specific equity news

## What was implemented (Phase 1)

### 1) Removed repetitive FXStreet gold slop variants

We replaced exact phrase checks with a broader pattern match for headlines like:
- `"<Country> Gold price today: ... according to FXStreet data"`

This was applied consistently in:
- `backend/services/news_aggregator.py`
- `backend/services/alternative_news_sources.py`
- `backend/app.py`
- `src/components/LiveNewsFeed.jsx`

Regex family used (case-insensitive):  
`gold price today:.*according to fxstreet data`

### 2) Updated backend relevance gate to market-wide policy

File:
- `backend/services/enhanced_forex_filter.py`

Key behavior changes:
- Added market-positive coverage for:
  - Crypto (bitcoin, ethereum, crypto, etc.)
  - Indices (S&P 500, Nasdaq 100, Dow, FTSE, DAX, Nikkei, etc.)
  - Commodities (gold, silver, oil, gas, copper)
  - Rates/macro plumbing (treasury yield, bond yield, yield curve, policy rate)
- Added explicit **stock/equity exclusion** logic for company/equity-specific items.
- Kept backwards-compatible method names (`is_forex_related`, `is_forex` output key) to avoid breaking callers, while behavior is now market-wide.
- Added `is_market` in scoring output.

### 3) Updated frontend feed gate to match backend policy

File:
- `src/components/LiveNewsFeed.jsx`

Changes:
- Replaced forex-only gating functions with market policy equivalents:
  - `isMarketRelevant`
  - `isHighImpactMarket`
- `all/high/medium/low` filtering now follows market-wide inclusion + stock exclusion policy.

### 4) Updated alert path to stop forex-only gating

Files:
- `backend/services/news_alert_trigger.py`
- `backend/services/unified_alert_processor.py`

Changes:
- Unified alert filtering now uses high-impact **market** gating.
- `is_forex_high_impact` retained as backward-compatible alias to avoid breaking references.

## Cleanup operation performed (24 April 2026)

A one-time cleanup was run to purge existing cached/history FXStreet gold slop entries:
- Endpoint used: `POST /api/remove-filtered-news`
- Payload used:
  - `filter_phrase: "Gold price today:"`
  - `confirm: true`

Result:
- Removed total: **19**
- Removed from cache: **5**
- Removed from history: **14**

## Validation completed

- Linter checks passed on edited files.
- Python syntax compile passed for backend edits.
- Smoke-test headlines showed expected behavior:
  - Crypto headline -> included
  - Index headline -> included
  - Commodity headline -> included
  - Rates/yields headline -> included
  - Stock earnings/company shares headline -> excluded

## Notes

This is a **minimal-safe Phase 1 patch** (small blast radius, no major refactor).

Recommended next step:
- Add a permanent must-include / must-exclude headline test suite to lock policy and prevent regression.

## Additional implementation (24 April 2026): Internal market relevance metadata

To support upcoming ecosystem features, we added an internal per-news-item market relevance component.
This metadata is stored on news items but is not rendered in user-facing UI cards.

### 5) Added internal market relevance classifier

File:
- `backend/services/enhanced_forex_filter.py`

Changes:
- Added `market_keyword_map` buckets:
  - `forex`
  - `crypto`
  - `indices`
  - `commodities`
  - `rates`
  - `macro`
- Added `get_market_relevance(title, summary, top_n=5)` that returns top market buckets (3-5) with:
  - `market`
  - `score` (keyword hit count)
  - `matched_keywords`

### 6) Stored market relevance on newly ingested items

Files:
- `backend/services/news_aggregator.py`
- `backend/services/alternative_news_sources.py`
- `backend/services/telegram_sync_wrapper.py`

Changes:
- During parsing, each news item now gets:
  - `market_relevance: [...]`
- This is stored with the item for downstream internal use (ranking, routing, ecosystem features).

### 7) Backfilled missing market relevance for cached items at read time

File:
- `backend/app.py`

Changes:
- Added helper: `enrich_market_relevance(news_list)`
- `/api/news` now enriches items missing `market_relevance` before response generation.
- This avoids waiting for full cache churn after deployment.

### 8) Added internal debug endpoint for QA

File:
- `backend/app.py`

Endpoint:
- `GET /api/news-market-relevance-debug?limit=25`

Purpose:
- Quick internal verification of tagging quality without touching visible UI.
- Returns compact fields:
  - `id`, `title`, `source`, `impact`, `published_at`, `market_relevance`

Operational note:
- Endpoint appears after backend restart/redeploy, because route registration happens on process startup.

## Validation for this additional implementation

- Linter checks passed on updated files.
- Python syntax compile passed.
- API rate-limit and restart behavior observed during validation:
  - `429` can occur on repeated local `/api/news` calls due to limiter policy.
  - `404` on the new debug route indicates old process still running; restart resolves it.
