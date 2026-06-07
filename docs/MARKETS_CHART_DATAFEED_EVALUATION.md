# Markets Chart — Data Feed & TradingView Advanced Charts Evaluation

**Status:** Active — TV Advanced Charts application submitted; UDF backend v0 in repo  
**Last updated:** 2026-06-04  
**Context:** Founder evaluation (Claude conversation, 2026-06-04) + alignment with existing Markets tab specs

Related docs:
- **Implementation roadmap (phases 1–3):** [`MARKETS_ADVANCED_CHARTS_ROADMAP.md`](./MARKETS_ADVANCED_CHARTS_ROADMAP.md)
- [`MARKETS_TAB_PRODUCT_SPEC.md`](./MARKETS_TAB_PRODUCT_SPEC.md) — product vision, OHLC strategy (§6), chart overlays (§9)
- [`MARKETS_TAB_IMPLEMENTATION_PLAN.md`](./MARKETS_TAB_IMPLEMENTATION_PLAN.md) — BTCUSD first; Binance OHLC v0 while MT5 spikes in parallel
- [`TRADINGVIEW_API_ACCESS_GUIDE.md`](./TRADINGVIEW_API_ACCESS_GUIDE.md) — scanner API, widgets, Lightweight Charts (current repo usage)

---

## 1. What we are trying to build

FXSentinel **Markets** is an instrument-centric analysis area (BTC, Gold, FX, etc.) where:

- **Candles and structure** must come from **our own OHLC pipeline** (not invented by GPT).
- A **level engine** computes PDH/PDL, ranges, POI, etc.; AI only narrates probability relative to those levels.
- The chart should **look and feel like TradingView** (density, candles, grid) but display **our data** and **our overlays**.

The path under evaluation: **MT5 broker feed → MQL5 bridge → backend → TradingView Advanced Charts** (self-hosted charting library with a custom datafeed).

**Current repo state (Phase 0 UI):** Markets tab uses the **TradingView advanced chart embed widget** (`TradingViewMarketChart.jsx`) — TV hosts both chart *and* data. That is a **layout placeholder only**, not the target architecture.

---

## 2. Critical distinction — three different “TradingView chart” products

Do not conflate these. Licensing, data ownership, and engineering differ completely.

| Product | What it is | Data source | FXSentinel today |
|---------|------------|-------------|------------------|
| **Chart embed widget** | `<script>` from `s3.tradingview.com` | **TradingView’s** live/historical data | ✅ `TradingViewMarketChart.jsx` (Markets tab placeholder) |
| **Advanced Charts** (Charting Library) | Self-hosted JS library you download | **You** implement a [datafeed API](https://www.tradingview.com/charting-library-docs/latest/connecting_data/) (UDF REST and/or WebSocket) | ❌ Not integrated |
| **Lightweight Charts** | Open-source MIT library (`npm install lightweight-charts`) | **You** pass bar arrays directly in JS | ❌ Planned in implementation plan; no MT5/UDF required for v0 |

**MQL5 does not plug into the embed widget.** To use MT5 data you either:

1. Build a **backend datafeed** → connect **Advanced Charts**, or  
2. Ingest OHLC into **`ohlc_store`** → serve `GET /api/markets/:id/ohlc` → render with **Lightweight Charts** (simpler; same data path as level engine).

The product spec already allows both UI options (§9.1); the implementation plan currently favours **Lightweight Charts + REST OHLC** for week 1, with MT5 as the long-term primary ingest.

---

## 3. Proposed architecture — MT5 → backend → TradingView Advanced Charts

### 3.1 Data flow (target)

```text
MT5 Terminal (broker price feed, Windows)
    ↓
MQL5 Expert Advisor (EA) — JSON over TCP socket (client)
    ↓
Python backend — TCP server, bar aggregation, cache/store
    ↓
TradingView UDF-compatible layer
    ├── REST  — historical bars (onChartReady, scroll-back)
    └── WebSocket — optional live tick/bar updates
    ↓
Advanced Charts (self-hosted) in FXSentinel frontend
    ↓
level_engine reads same ohlc_store → overlays + GPT allowlist
```

### 3.2 Why Python must be the TCP server

MQL5 **only supports client-side sockets** in EAs. The usual pattern:

- Python process listens on a port.
- MT5 EA connects outbound and streams ticks/OHLC as JSON.
- Python normalizes, aggregates bars, persists to `ohlc_store`, exposes UDF endpoints.

Reference implementations exist in the community (search: MT5 EA + Python socket + TradingView UDF). Expect on the order of **a few hundred lines of Python** for a minimal bridge plus UDF handlers — not trivial, but a well-trodden path.

### 3.3 Advanced Charts datafeed contract

TradingView Advanced Charts expects you to implement their **datafeed interface**:

- **Historical:** HTTP in [UDF (Universal Data Feed)](https://www.tradingview.com/charting-library-docs/latest/connecting_data/udf/) shape — `history`, `config`, `symbols`, etc.
- **Realtime (optional):** WebSocket or polling adapter for live updates.

Your backend is responsible for mapping internal symbols (`BTCUSD`, `EURUSD`, `GOLD`) to broker symbols (`BTCUSD`, `EURUSD`, `XAUUSD`, …) and timeframes (`1`, `240`, `1D`, …).

### 3.4 Overlap with existing FXSentinel OHLC design

Regardless of chart library, the **same middle layer** from the product spec applies:

```text
bar_ingest_job (MT5 EA and/or Python MetaTrader5 package and/or scheduled CSV)
        ↓
ohlc_store (pair, timeframe, ts, O, H, L, C, V)
        ↓
level_engine → structured_levels[] → research API + chart overlays
```

Advanced Charts adds a **presentation adapter** (UDF) on top of `ohlc_store`. Lightweight Charts skips UDF and reads JSON bars from `GET /api/markets/:id/ohlc`.

---

## 4. Licensing & cost — TradingView Advanced Charts

*Source: external evaluation (2026-06-04); **verify with TradingView** before production — terms change.*

### 4.1 Advanced Charts (Charting Library)

| Scenario | Typical licensing | Cost |
|----------|-------------------|------|
| **Public, free product** — chart visible without paywall; attribution visible | Free tier often available for qualifying public implementations | **$0** (subject to TV approval / terms) |
| **Commercial / paid product** — Markets behind subscription or paid tier | **Enterprise / commercial license** — negotiated with TradingView | **Not public** — typically **thousands USD/year** (order-of-magnitude; get a quote) |

**FXSentinel note:** The platform has **paid subscriptions** (Stripe, analysis limits, Premium). Even if Markets is free today, **any monetized product** using Advanced Charts likely needs a **commercial license conversation with TradingView** — do not assume the free tier applies.

**Lightweight Charts** is **MIT licensed** — no TradingView commercial charting license for the library itself. You still need **legal rights to the price data** you display (broker ToS, not TV).

### 4.2 What does *not* buy you API access

TradingView **website subscriptions** (Essential / Plus / Premium) are for **tradingview.com** — they do **not** grant Advanced Charts library access or a data redistribution license. See [`TRADINGVIEW_API_ACCESS_GUIDE.md`](./TRADINGVIEW_API_ACCESS_GUIDE.md).

### 4.3 Infrastructure cost (MT5 path)

| Item | Estimate | Notes |
|------|----------|-------|
| Windows VPS for MT5 terminal 24/7 | **~$20–60/month** | MT5 is Windows-native; dedicated VM, not a dev laptop |
| Linux app server (Python API) | Existing / marginal | May already host `backend/` |
| Commercial TV license (if required) | **TBD — negotiate** | Blocker for paid-product launch with Advanced Charts |
| MQL5 / broker account | Varies | Often $0 minimum deposit demo; live account for production feed |

### 4.4 Engineering effort (order of magnitude)

| Workstream | Estimate | Notes |
|------------|----------|-------|
| MT5 EA + Python TCP bridge | 3–7 days | Spike first on one symbol |
| `ohlc_store` + ingest jobs | 2–5 days | Align with implementation plan |
| UDF REST + optional WebSocket | 3–7 days | Advanced Charts only |
| Advanced Charts frontend integration | 3–7 days | Theming, symbol resolve, resize |
| `level_engine` + chart overlays | 3–7 days | Library-agnostic |
| **Total (clean v1)** | **~2–4 weeks** | Matches external feasibility assessment |

Binance REST klines for **BTCUSD v0** (implementation plan) can ship **level_engine + chart** in parallel **without** MT5 or Advanced Charts licensing.

---

## 5. Feasibility assessment

| Dimension | Assessment | Detail |
|-----------|------------|--------|
| **Technical feasibility** | **High** | MT5 → Python → UDF → Advanced Charts is documented and has open-source references |
| **Ops complexity** | **Medium–High** | MT5 terminal must run continuously; Windows VM; monitoring required |
| **Data quality** | **Broker-dependent** | Gaps, spikes, session breaks, symbol naming — flows into level_engine and AI |
| **Latency** | **Acceptable for analysis** | MT5 → Python → WS → browser adds delay vs direct API; not HFT |
| **Scaling** | **Needs caching** | One terminal; many users must hit **cached bars**, not MT5 per request. TV client caches; server must too |
| **Multi-asset** | **Harder** | FX 24/5, crypto 24/7, gold — may need multiple brokers/symbols/terminals |
| **Alignment with FXSentinel roadmap** | **Good long-term** | Matches product spec §6.1; **not** required for BTC Binance v0 |

### 5.1 Real feasibility concerns (operational)

1. **Single point of failure** — MT5 crash or broker disconnect kills the feed until recovery or fallback.
2. **Historical depth** — Broker-dependent; may be insufficient for swing structure on some symbols.
3. **Symbol mapping** — `BTCUSD` (display) vs `BTCUSDT` (Binance/TV) vs broker `BTCUSD` — one canonical map per market in `market_registry`.
4. **24/7 for crypto** — FX terminals often idle on weekends; crypto needs always-on ingest or a hybrid (Binance for BTC, MT5 for FX/Gold).

---

## 6. Safety & compliance risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Broker ToS / redistribution** | **Medium–High** | Some brokers prohibit serving their quotes to third parties (even indirectly). **Check broker terms before build.** Developer-friendly brokers (often cited: IC Markets, Pepperstone, LMAX) — verify in writing. |
| **TradingView license (paid product)** | **High if ignored** | Contact TradingView for commercial terms before shipping Advanced Charts to paying users. |
| **Bad ticks → bad levels → bad AI** | **Medium** | Anomaly filters; `data_quality` flags in research API; validator strips uncited levels (spec §8.4). |
| **Infrastructure SPOF** | **Medium** | Fallback: cached last-good bars, secondary broker, REST vendor (OANDA, Polygon, Twelve Data), graceful “data unavailable” UI. |
| **Security** | **Medium** | MT5 TCP bridge **internal only** — not public internet. Public edge: UDF/OHLC API with normal app auth/rate limits. |
| **Basis risk** | **Low–Medium** | TV scanner quotes vs MT5 OHLC vs Binance — label `source` and `as_of` on chart footer (spec §15). |

---

## 7. Comparison — paths for FXSentinel Markets chart

| Path | Data | Chart UI | License risk | Time to v0 candles |
|------|------|----------|--------------|-------------------|
| **A. TV embed widget (current)** | TV’s data | TV widget | Low (widget ToS) | ✅ Done (placeholder) |
| **B. Lightweight Charts + REST OHLC** | Binance → `ohlc_store` → API | MIT library | Data ToS only | **~1 week** (per implementation plan) |
| **C. Lightweight Charts + MT5 OHLC** | MT5 → `ohlc_store` → API | MIT library | Broker ToS | ~2–3 weeks after MT5 spike |
| **D. Advanced Charts + MT5 UDF** | MT5 → UDF backend | TV Charting Library | **TV commercial + broker** | ~2–4 weeks |

**Recommendation (aligned with existing plan):**

1. **Ship v0 on path B** — Binance `BTCUSDT` ingest, `GET .../ohlc`, Lightweight Charts, `level_engine` overlays. Proves chart + levels + research API without MT5 ops or TV enterprise licensing.
2. **Spike MT5 in parallel** — 30 days daily bars for one FX symbol + `XAUUSD`; validate bridge stability and broker ToS.
3. **Decide Advanced Charts vs Lightweight Charts** after:
   - TV commercial quote (if Markets is behind paywall),
   - Whether you need Advanced Charts–specific features (full TV indicator set, trading UI) vs custom FXSentinel overlays only.

Lightweight Charts is sufficient for spec §9 overlays (horizontal levels, shaded ranges, markers). Advanced Charts is justified if you want **parity with tradingview.com UX** and accept licensing + UDF maintenance.

---

## 8. Alternative data sources (fallback / hybrid)

From product spec §6.3 and [`TRADINGVIEW_API_ACCESS_GUIDE.md`](./TRADINGVIEW_API_ACCESS_GUIDE.md):

| Provider | Best for | Notes |
|----------|----------|-------|
| **Binance public klines** | BTC v0 | No key; aligns with `BINANCE:BTCUSDT`; already in implementation plan |
| **Python `MetaTrader5` package** | Same machine as terminal | Alternative to custom EA socket |
| **OANDA / FXCM REST** | FX OHLC | Documented APIs; no Windows VM |
| **Polygon / Twelve Data** | Multi-asset REST | Paid; clearer redistribution terms |
| **Finnhub / Alpha Vantage** | Already in FXSentinel | Lower priority for OHLC structure |

---

## 9. Decision checklist (before committing to Advanced Charts + MT5)

- [ ] **Paywall:** Will Markets chart be visible to free users, paid only, or all logged-in users? → drives TV license tier.
- [ ] **Broker:** Which broker/account will host MT5? Written OK to display quotes to FXSentinel users?
- [ ] **Hosting:** Who maintains the Windows MT5 VM (uptime, alerts, reconnect)?
- [ ] **Symbols:** Canonical map MT5 ↔ internal `market_id` ↔ TV display symbol.
- [ ] **Chart library:** Advanced Charts vs Lightweight Charts — document choice in decision log.
- [ ] **v0 shortcut:** Ship Binance BTC OHLC first regardless of MT5 timeline?
- [ ] **Fallback:** What does the chart show when feed is down?

---

## 10. Summary table (external evaluation + FXSentinel context)

| Dimension | Assessment |
|-----------|------------|
| **TV Advanced Charts cost (free tier)** | $0 only if product/implementation qualifies as public per TV terms — **unlikely for paid FXSentinel without enterprise deal** |
| **TV Advanced Charts cost (commercial)** | Custom enterprise pricing — budget line item before launch |
| **Technical feasibility (MT5 → TV)** | **High** — proven pattern |
| **Engineering effort** | **Medium** — ~2–4 weeks end-to-end |
| **Infrastructure** | **~$20–60/mo** Windows VPS + ops time |
| **Broker ToS** | **Medium risk** — validate before build |
| **Reliability** | **Moderate** — single MT5 terminal is fragile; plan fallbacks |
| **Fits FXSentinel architecture** | **Yes** — feeds `ohlc_store` and `level_engine`; chart library is swappable |

**Bottom line:** MT5 → own backend → own chart is **sound for v1** of Markets analysis, but it is **not** a plug-in to the current TV embed widget. Treat **licensing (TV + broker)** and **ops (24/7 MT5)** as gating items. The repo’s **pragmatic near-term path** remains Binance OHLC + Lightweight Charts for BTCUSD while MT5 and Advanced Charts licensing are validated.

---

## 11. Open questions (carry forward)

1. Enterprise quote from TradingView for FXSentinel’s subscription model?
2. One MT5 broker for all markets or separate terminals (crypto vs FX vs gold)?
3. Custom EA socket vs official `MetaTrader5` Python package on same VPS?
4. Real-time WebSocket on chart v1, or historical + periodic refresh sufficient for analysis product?
5. Keep TV embed as optional “open in full TV” popup while primary chart uses own feed?

---

## Revision log

| Date | Change |
|------|--------|
| 2026-06-04 | Initial doc from founder Claude evaluation + alignment with Markets tab specs and current codebase |
