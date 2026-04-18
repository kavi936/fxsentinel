# Market Sentiment Card — Evaluation & Roadmap

This document consolidates analysis of the Market Sentiment card codebase, how live ticker prices are sourced, how that data relates to sentiment today, and recommended improvements—including new sections and prioritization.

---

## 1. Architecture (end-to-end)

### Frontend

| Piece | Role |
|-------|------|
| `src/config.js` | `marketSentiment` → `GET /api/market-sentiment`; `sentimentRefresh` → `POST /api/sentiment/refresh`. |
| `src/hooks/useMarketSentiment.js` | Fetches on mount, polls every **5 minutes**, exposes `refreshSentiment`, helpers (`getSentimentColor`, `formatTimeAgo`, etc.), and a **client fallback** object if the API shape is incomplete. |
| `src/components/Overview.jsx` | Renders the card (`data-onboarding="market-sentiment"`): header + refresh, closed-market state, Fear Indicators (VIX + Crypto Fear & Greed), expandable “Use in Context”, Market Conditions grid, Major Pairs Sentiment, **Macro themes (general)**, outlook text. |

### Backend

| Piece | Role |
|-------|------|
| `backend/app.py` | `GET /api/market-sentiment` → `market_sentiment_service.get_market_sentiment()`; `POST /api/sentiment/refresh` clears in-memory cache and recalculates. |
| `backend/services/market_sentiment_service.py` | File cache (`market_sentiment_cache.json`), ~15 min sentiment TTL, VIX caching, weekend “market closed” branch, calculation from `get_tradingview_prices()`, external VIX (Alpha Vantage / Yahoo), Fear & Greed (Alternative.me), formatting for frontend. |

### JSON shape the UI expects

- `pairs_sentiment`, `market_conditions`, `vix`, `fng`, `is_market_closed`, `market_status`, `market_drivers`, `market_outlook`, timestamps, etc.

---

## 2. Codebase strengths

- Clear separation: hook ↔ API ↔ service; response shape matches the UI.
- Resilience: cached sentiment when recalculation fails; VIX has multiple sources and stale-cache fallbacks; Fear & Greed fetched on successful sentiment paths.
- UX: refresh with loading state, “last updated”, error/retry on pairs, tooltips and expandable VIX/FNG context.
- Tooltips explain VIX and crypto F&G as **macro proxies**, not native forex sentiment.

---

## 3. Codebase weaknesses and risks

| Area | Issue |
|------|--------|
| **Naming vs reality** | The card is mostly **price heuristics + equity vol (VIX) + crypto F&G**, not classical sentiment (news, positioning, surveys). |
| **“RSI”** | Backend derives a number from **daily % move**, not a true RSI window. Better labeled **momentum** or **daily impulse**. |
| **Pair “volatility”** | Implemented as **abs(daily change %)**, not annualized vol despite comments. |
| **Market drivers** | `_get_market_drivers` returns **static boilerplate** paragraphs, not live news or calendar—misleading if presented as current drivers. |
| **Confidence score** | Logic rewards `len(conditions) >= 3`, but only **two** market conditions are produced—branch never helps. |
| **Forex “open/closed”** | Weekends no longer gate the API; weekday hour check `0 <= hour <= 23` still makes the “closed by hour” branch dead. |
| **Security** | Alpha Vantage path historically included env/fallback key patterns—**keys should be env-only**, not committed. |
| **API handler** | `importlib.reload(services.market_sentiment_service)` on every GET is unusual: extra cost and reload side effects. |
| **`useMarketSentiment.js`** | Verbose `console.log` in production paths; `useEffect` + `fetchSentiment` both touch `loading`—redundant edge cases. |
| **`Overview.jsx`** | Very large inline JSX for VIX block—harder to maintain. |
| **Fallback mismatch** | Client `fallbackSentiment` can include a third condition (“Market Correlation”) that the **live backend does not compute**. |

**Verdict:** Treat the feature as a **“macro risk + G10 price snapshot”** dashboard unless you expand data sources; tighten copy and implementation where users might infer more precision than the math supports.

---

## 4. Live market ticker — how prices are loaded

### Pipeline

1. **`get_tradingview_prices()`** in `backend/app.py` calls **`fetch_tradingview_quotes()`** in `backend/services/tradingview_market_data.py`.
2. Instruments are defined in **`backend/services/tradingview_instruments.py`** (`INSTRUMENTS`): forex, crypto, commodities (futures), **bond yields**, indices (including **VIX**).
3. **`fetch_tradingview_quotes()`** groups by TradingView **market** (`forex`, `crypto`, `futures`, `bonds`, `cfd`), runs **parallel** `POST` requests to `https://scanner.tradingview.com/{market}/scan`, merges into one dict keyed by internal ids (`EURUSD`, `BTCUSDT`, `GOLD`, `US10Y`, `SPX`, `VIX`, …).
4. Each quote includes: `price`, `change` (absolute), **`changePercent`**, `category`, `decimals`, `tvSymbol`, `source`, `lastUpdate`.

### API surface

- **`GET /api/forex-prices`** — Name kept for compatibility; returns **all** merged instruments plus an `instruments` catalog and `dataQuality` metadata.

### Relationship to sentiment

- **Market sentiment already calls the same `get_tradingview_prices()`** as the ticker.
- **`_calculate_pairs_sentiment`** only uses **four** FX ids: `EURUSD`, `GBPUSD`, `USDJPY`, `USDCHF`.
- **Risk appetite** uses a **subset of FX** pairs for safe-haven logic.
- **VIX** is fetched separately (Alpha Vantage / yfinance) even though **`VIX` exists in `INSTRUMENTS`** (`CBOE:VIX` on the `cfd` scanner)—possible duplication or inconsistency with the ticker.

---

## 5. Using more market prices in sentiment (summary)

The merged quote map already includes **crypto, commodities, bonds, indices**. Sentiment can use **`changePercent`** and **`category`** without a new vendor.

**High-value uses:**

1. **Cross-asset risk** — Indices (SPX, DJI, IXIC), BTC/ETH, Gold, WTI: daily % as risk-on/risk-off context for FX.
2. **Rates / policy** — `US10Y`, `DE10Y`, etc.: yield **changes**; optional **US10Y − DE10Y** spread change for EURUSD narrative.
3. **Breadth** — % of tracked symbols up/down by category, or average |changePercent| as a “who is moving” stress measure.
4. **VIX alignment** — Prefer TradingView **VIX** when present for the card/ticker alignment; keep external VIX as fallback.

**Design notes:**

- Label bonds as **yield change** (bps or %), not bond price.
- Commodity symbols are **front futures**—disclose in tooltips if needed.

---

## 6. Improving the card — additional sections & UX

### Current sections (approximate)

Fear proxies (VIX + Crypto F&G) → Market conditions → Major pairs → Market drivers → Outlook.

### Fix trust before adding UI

1. **Market drivers** — Replace with real inputs (headlines, next high-impact events, scan themes) **or** rename to static “Macro themes (general)” and shorten.
2. **Metrics** — Rename misleading labels (RSI → momentum; clarify vol).
3. **Duplication** — Unify VIX story (Fear Indicators vs volatility text) via one source of truth where possible.

### Prioritized new / upgraded sections

#### Tier A — Strong fit (existing data)

| Idea | Content |
|------|---------|
| **Cross-asset risk strip** | One row: SPX, Nasdaq, BTC, Gold, WTI with daily % and a compact risk bias hint. |
| **Rates / policy snapshot** | US10Y, DE10Y changes; optional US−DE spread change. |
| **Yield curve hint (optional)** | US 2Y vs 10Y: steepening/flattening label from daily changes. |

#### Tier B — High value, careful UX

| Idea | Content |
|------|---------|
| **Session / liquidity context** | Which major session is active + simple volatility regime (e.g. median |FX move|). |
| **Breadth / agreement** | “X of Y pairs green” or bucket-level counts. |
| **Commodity–FX link** | Short educational line (oil ↔ CAD, etc.) using sign of today’s moves. |

#### Tier C — Later / heavier

- COT / positioning (weekly)—different cadence; maybe another surface.
- News sentiment—only with a reliable pipeline.

### UI patterns to avoid clutter

- **Accordions** by theme: Fear & liquidity | Rates & USD | FX pairs.
- **One summary line** at top: single sentence risk bias from rules, details below.
- **Cap visible pairs** (e.g. 4 + “more”).
- **Do not** duplicate the full ticker—link mentally to the ticker for raw lists.

### What not to add here

- Long instrument lists (ticker owns that).
- Huge duplicate crypto panels unless product scope expands.

---

## 7. Suggested implementation roadmap

1. **Trust** — Fix or rename drivers; clarify momentum/vol labels.
2. **Cross-asset strip** — Indices + BTC + gold + oil from merged quotes.
3. **Rates** — US/DE (and optional spread) from bond ids.
4. **Optional** — Session/breadth one-liners; TV VIX alignment with fallback.

Backend: extend `market_sentiment_service` (and API JSON) with structured fields, e.g. `cross_asset_summary`, `rates_snapshot`, without breaking existing keys. Frontend: new subsections in `Overview.jsx` + CSS, or small presentational components.

---

## 8. Key file references

| File | Purpose |
|------|---------|
| `src/hooks/useMarketSentiment.js` | Client fetch, refresh, helpers, fallback. |
| `src/components/Overview.jsx` | Market Sentiment card UI. |
| `src/config.js` | API endpoints. |
| `backend/app.py` | `get_tradingview_prices`, `/api/market-sentiment`, `/api/sentiment/refresh`, `/api/forex-prices`. |
| `backend/services/market_sentiment_service.py` | Sentiment calculation and caching. |
| `backend/services/tradingview_market_data.py` | `fetch_tradingview_quotes()`. |
| `backend/services/tradingview_instruments.py` | Instrument whitelist and categories. |
| `docs/MARKET_TICKER_MULTI_ASSET_IMPLEMENTATION.md` | Multi-asset ticker implementation log. |

---

## Implemented (trust / labeling)

- **Macro themes (general):** Section renamed; microcopy states educational context, not live headlines/calendar; primer line; backend themes shortened with `source` empty (no fake “Source:” lines).
- **Volatility Environment row:** Removed from the Market Conditions grid; VIX stays only under **Fear Indicators**. The API may still include the condition for outlook / parsing / other consumers.
- **Daily impulse:** UI shows **Impulse** beside the gauge; **Daily Change** above remains the source for today’s % move. API still includes `impulse` and `daily_abs_move_pct` (aliases of `rsi` / `volatility`) for consumers.
- **Major-pair gauge:** Bar is **center-zero** (midline = flat); length scales with **absolute daily %**, capped at **±1.15%** to the track edge (`getDailyChangeGaugeLayout` / backend `percentage` = 50 + *t*×50 with same cap).
- **Tier A (API + UI):** **`cross_asset_strip`** — SPX, Nasdaq, BTC, Gold, WTI daily % from merged TradingView quotes; **`rates_snapshot`** — US10Y & DE10Y levels + session Δ, **US10Y Δ − DE10Y Δ**, and a simple **US 2Y vs 10Y** steepening / flattening / neutral hint (`_build_tier_a_data` in `market_sentiment_service.py`, rendered in `Overview.jsx`).
- **Weekends:** `get_market_sentiment` no longer returns the stub `_get_market_closed_sentiment()` on weekends; it runs the same **full calculation** as weekdays. **`is_market_closed`** is always **`false`** for that path; **`market_status`** may still be **`weekend`** for calendar context.

---

## 9. Backlog — return later (not implemented)

Use this section when prioritizing deeper work. Items below are **future** improvements; they are **not** covered by the “Implemented” block above.

### 9.1 Option 3 — Differentiate equity fear vs FX volatility (no merge, no conflict)

**Idea:** Stop treating the same conceptual input (VIX) as both the hero “fear” number and the FX “volatility environment” story.

| Area | Role |
|------|------|
| **Fear Indicators** | Keep **raw VIX** (equity implied volatility) as the primary read—macro fear gauge. |
| **Volatility Environment** | Make it **explicitly FX-centric**: e.g. a **blended FX realized move**, **ATR-style** measure, or similar derived from the **FX ticker** / `get_tradingview_prices()` forex set—not VIX driving the bar. Optionally show VIX only as a **small secondary** label if you still want a cross-asset hint. |

**Pros:** Conceptually clean—**equity fear** vs **FX volatility regime**—and avoids users seeing two blocks that feel like duplicate stories.

**Cons:** Requires a **real FX-vol input** (engineering: define the blend or window, handle stale data, document limitations). More work than copy-only fixes.

**Integration hints:** Forex pairs already have daily `changePercent` in the merged quote map; a simple first version could be mean/median **absolute** daily % across G10 majors, or max of |Δ%|—then iterate toward ATR if you add history.

---

*Document generated from codebase review and product evaluation; update as implementations land.*
