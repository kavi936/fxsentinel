# Markets — Advanced Charts Implementation Roadmap

**Status:** **Superseded for chart UI** — product decision (2026-06-04): ship **Lightweight Charts research chart**, not Advanced Charts workstation. Keep this doc for UDF/MT5 data-layer reference. TV library application may still be useful later; not blocking Markets v0.  
**Last updated:** 2026-06-04  
**Library access:** Application submitted to TradingView — optional; confirm commercial license only if revisiting Advanced Charts.

Related docs:
- [`MARKETS_CHART_DATAFEED_EVALUATION.md`](./MARKETS_CHART_DATAFEED_EVALUATION.md) — cost, licensing, MT5 feasibility
- [`MARKETS_TAB_PRODUCT_SPEC.md`](./MARKETS_TAB_PRODUCT_SPEC.md) — product requirements, overlays, level engine
- [`MARKETS_TAB_IMPLEMENTATION_PLAN.md`](./MARKETS_TAB_IMPLEMENTATION_PLAN.md) — BTCUSD vertical slice, Binance v0

---

## Overview

Work splits into **three phases**. Phase 1 blocks on TradingView approval. **Phases 2 and 3 can start now** using:

- **Backend:** UDF HTTP datafeed (implemented under `/api/udf/*`) with **Binance BTCUSDT** as interim OHLC until MT5 bridge is live.
- **Frontend:** TradingView **demo UDF** (`https://demo-feed-data.tradingview.com`) for chart widget integration tests until the private `charting_library` package is installed.

```text
Phase 1  Access & setup     [WAITING — TV application submitted]
Phase 2  Data backend       [IN PROGRESS — UDF + ohlc_store; MT5 spike parallel]
Phase 3  Frontend chart     [NEXT — demo feed now; swap to library when approved]
```

---

## Phase 1 — Library access & setup

### Step 1 — Request access ✅ Submitted

- Form submitted with FXSentinel company + website details.
- **Waiting on:** GitHub invitation to `tradingview/charting_library` (private repo).

### Step 2 — License agreement ⏳ Pending invite

Read terms before merging chart into production:

| Constraint | FXSentinel implication |
|------------|-------------------------|
| Free tier often requires **public** implementation + visible attribution | FXSentinel has **paid subscriptions** — confirm commercial license if Markets is behind paywall |
| Attribution must remain visible | Plan footer/branding on chart pane |
| Implementation not for private/internal-only use | Staging vs production visibility matters |

**Action when invite arrives:** Sign agreement, note paywall question in reply to TradingView if unclear.

### Step 3 — GitHub SSH key (do before `npm install`)

```bash
# Verify GitHub SSH auth works
ssh -T git@github.com
```

Charting library install uses:

```json
"charting_library": "git@github.com:tradingview/charting_library.git#semver:28.0.0"
```

Without SSH access to the private repo, `npm install` will fail.

### Step 4 — Parallel frontend prep (no library required)

Use TradingView’s **demo datafeed** while waiting:

```javascript
datafeed: new Datafeeds.UDFCompatibleDatafeed(
  "https://demo-feed-data.tradingview.com"
)
```

Swap to FXSentinel backend when UDF is tested:

```javascript
datafeed: new Datafeeds.UDFCompatibleDatafeed(
  `${API_BASE_URL}/api/udf`
)
```

---

## Phase 2 — Python data backend

**Goal:** Server between price source and Advanced Charts UDF adapter.

### Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  v0 (now)     Binance REST klines → ohlc_store → UDF REST   │
│  v1 (target)  MT5 EA (TCP client) → Python bridge → store   │
└─────────────────────────────────────────────────────────────┘
                              ↓
              GET /api/udf/config
              GET /api/udf/symbols?symbol=BTCUSD
              GET /api/udf/history?symbol=BTCUSD&resolution=240&from=&to=
              GET /api/udf/search?query=&limit=
                              ↓
              (optional v1.1) WebSocket live bars — full Datafeed API
```

### Step 5 — MT5 environment (parallel spike)

| Task | Detail |
|------|--------|
| Host | Windows VPS (~$20–60/mo), MT5 terminal 24/7 |
| Account | Demo first — no capital at risk while building |
| Symbols | Align with `market_registry` MT5 symbol names |
| Docs | See [`backend/mt5/README.md`](../backend/mt5/README.md) |

### Step 6 — MQL5 Expert Advisor

- EA runs **inside MT5**, connects as **TCP client** to Python server.
- Emits JSON: ticks, bar updates, historical bar responses.
- MQL5 cannot host the server — Python listens.

### Step 7 — Python bridge (extend current UDF layer)

**Implemented (v0):**

| Module | Purpose |
|--------|---------|
| `backend/services/markets/market_registry.py` | Symbol map, data source, UDF metadata |
| `backend/services/markets/ohlc_ingest_binance.py` | Pull Binance klines |
| `backend/services/markets/ohlc_store.py` | JSON bar cache on disk |
| `backend/services/markets/udf_datafeed.py` | UDF response builders |
| `backend/routes/markets_udf_routes.py` | Flask routes |

**To add (MT5 v1):**

| Module | Purpose |
|--------|---------|
| `backend/services/markets/mt5_bridge_server.py` | TCP listener, parse EA JSON |
| `backend/services/markets/ohlc_ingest_mt5.py` | Persist EA bars into `ohlc_store` |
| `backend/mt5/FXSentinelBridgeEA.mq5` | EA source |

### Step 8 — UDF response shape

Historical bars (`/history`) must return **ascending** timestamps:

```json
{
  "s": "ok",
  "t": [1710000000, 1710014400],
  "o": [104000.0, 104100.0],
  "h": [104200.0, 104300.0],
  "l": [103900.0, 104050.0],
  "c": [104100.0, 104250.0],
  "v": [1200.5, 980.2]
}
```

Also required: `/config`, `/symbols`, `/search` — see [TradingView UDF docs](https://www.tradingview.com/charting-library-docs/latest/connecting_data/udf/).

### Step 9 — Test backend in isolation

```bash
# Refresh BTC OHLC cache
cd backend && python scripts/ingest_market_ohlc.py --market BTCUSD

# UDF config
curl -s "http://localhost:5001/api/udf/config" | python -m json.tool

# Symbol info
curl -s "http://localhost:5001/api/udf/symbols?symbol=BTCUSD" | python -m json.tool

# History (4H bars)
curl -s "http://localhost:5001/api/udf/history?symbol=BTCUSD&resolution=240&from=1700000000&to=2000000000" | python -m json.tool
```

**Pass criteria:** `s: "ok"`, monotonic `t[]`, no duplicate timestamps, `len(t)==len(o)==len(h)==len(l)==len(c)`.

---

## Phase 3 — Frontend integration

### Step 10 — Install charting library (after GitHub access)

```bash
npm install
# package.json dependency (add when approved):
# "charting_library": "git@github.com:tradingview/charting_library.git#semver:28.0.0"
```

Postinstall copies static assets to `public/charting_library/` (configure per TV docs).

### Step 11 — Chart widget component

New file (planned): `src/components/markets/AdvancedMarketChart.jsx`

```javascript
new TradingView.widget({
  container: chartContainerRef.current,
  locale: 'en',
  library_path: '/charting_library/',
  datafeed: new Datafeeds.UDFCompatibleDatafeed(`${config.API_BASE_URL}/api/udf`),
  symbol: 'BTCUSD',
  interval: '240',
  fullscreen: false,
  theme: 'dark',
  // overrides: match DASHBOARD_BRANDING.md
});
```

**Until library arrives:** keep `TradingViewMarketChart.jsx` embed as layout placeholder OR spike with demo UDF in a dev-only route.

### Step 12 — Symbol switching

Markets picker already changes `marketId`. On change:

```javascript
widget.setSymbol(udfSymbol, interval, () => {});
```

Map `marketId` → UDF symbol via `market_registry` / `marketTvSymbols.js`.

### Step 13 — Styling

- Dark background `#000`, grid `rgba(255,255,255,0.06)` — match current `MarketsChart.css`
- Toolbar: hide side toolbar if clutter; keep timeframe for v1
- Attribution: required by TV license — do not remove
- Chart height: reuse existing flex chain (`--markets-chart-min-h` tokens)

### Step 14 — Live streaming (week 4+)

UDF adapter alone is **historical REST**. For live candles:

- Implement full **Datafeed API** `subscribeBars` / `unsubscribeBars`
- Push from MT5 bridge WebSocket or poll Binance for crypto v0
- Not required for first historical chart render

---

## Recommended timeline

| Week | Focus | Blocker |
|------|--------|---------|
| **1** | ✅ TV application; SSH key; UDF backend + Binance BTC; curl tests | None |
| **2** | MT5 demo + EA spike; FX symbols in registry (disabled); `level_engine` v0 | Windows VPS |
| **3** | Install charting library (if approved); widget + **demo or own UDF** | GitHub invite |
| **4** | MT5 → store; live subscribeBars; wire Markets picker `setSymbol` | MT5 stability |

---

## FXSentinel file checklist

### Backend — done / planned

| Path | Status |
|------|--------|
| `backend/services/markets/market_registry.py` | ✅ v0 |
| `backend/services/markets/ohlc_ingest_binance.py` | ✅ v0 |
| `backend/services/markets/ohlc_store.py` | ✅ v0 |
| `backend/services/markets/udf_datafeed.py` | ✅ v0 |
| `backend/routes/markets_udf_routes.py` | ✅ v0 |
| `backend/scripts/ingest_market_ohlc.py` | ✅ v0 |
| `backend/mt5/README.md` | ✅ spike guide |
| `backend/services/markets/mt5_bridge_server.py` | ⏳ |
| `backend/services/markets/level_engine.py` | ⏳ |
| `backend/services/market_research_service.py` | ⏳ |

### Frontend — planned

| Path | Status |
|------|--------|
| `src/components/markets/TradingViewMarketChart.jsx` | ✅ embed placeholder |
| `src/components/markets/AdvancedMarketChart.jsx` | ⏳ after library access |
| `src/config.js` → `endpoints.udfDatafeed` | ⏳ |
| Replace embed in `MarketChartSection.jsx` | ⏳ after spike |

---

## What to do right now (waiting on TV)

1. **Run UDF backend locally** — ingest BTC, curl-test all UDF endpoints.
2. **Set up GitHub SSH** — ready for day-one `npm install` when invite lands.
3. **Order / provision Windows VPS** — MT5 demo account.
4. **Read EA spike doc** — `backend/mt5/README.md`.
5. **Optional:** dev page with demo UDF + static HTML widget shell (no private repo yet).

Do **not** block Markets progress on TV approval: `ohlc_store` + `level_engine` + research API are the same whether the UI uses Advanced Charts or Lightweight Charts.

---

## Decision log

| Date | Decision |
|------|----------|
| 2026-06-04 | Advanced Charts application submitted to TradingView |
| 2026-06-04 | Build UDF backend immediately; Binance BTCUSDT interim feed |
| 2026-06-04 | MT5 EA spike in parallel; swap ingest source per `market_registry` |
| 2026-06-04 | Keep TV embed widget until `charting_library` package installed |

---

## Revision log

| Date | Change |
|------|--------|
| 2026-06-04 | Initial roadmap from Claude session + FXSentinel codebase alignment |
