# BTCUSD Markets — Implementation Strategy

**Status:** Active playbook (read this before other Markets work)  
**Last updated:** 2026-06-09  
**Audience:** Engineering + product — get BTCUSD straight before Gold/EUR/MT5  

**Canonical ids:** Display **`BTCUSD`** · Data **`BTCUSDT`** (Binance + TV)  
**Parent docs:** [`MARKETS_TAB_PRODUCT_SPEC.md`](./MARKETS_TAB_PRODUCT_SPEC.md) · [`MARKETS_TAB_IMPLEMENTATION_PLAN.md`](./MARKETS_TAB_IMPLEMENTATION_PLAN.md)

---

## 1. What we are building (one paragraph)

A **BTC/USD research desk** inside FXSentinel: live Binance chart + **our** derived zones/levels, fused with **platform macro context** (US scan, FOMC/CPI calendar, sentiment, cross-assets, crypto news), narrated by **global GPT runs** that only cite allowlisted structure. Same output for every user. Markets tab is the **referral surface**; data is composed **server-side** in `/api/markets/BTCUSD/research`.

---

## 2. Three lanes (do not blur these)

| Lane | Owner | BTCUSD examples | Where it runs |
|------|--------|-----------------|---------------|
| **A — Venue quant** | `feature_engine` + `level_engine` | Volume POC/VAH/VAL, delta zones, PDH/PDL, 4H rotation | Background; output = `structured_levels[]` |
| **B — Platform context** | `market_context_service` (new) + profile | US holistic scan digest, FOMC/CPI catalysts, sentiment, ETH/SPX/VIX/US10Y/GOLD, filtered news | Pulled from **existing** app services |
| **C — Narrative** | Global GPT run + validator | Probability, thesis, zone-tap explanation | 2×/day cron; cites lane A IDs only |

**Rule:** GPT never invents prices or zones. Quant never writes prose. Platform context never draws chart lines.

---

## 3. Where we are today

### Done ✅

| Area | Detail |
|------|--------|
| **Registry** | `BTCUSD` enabled, `binance_symbol: BTCUSDT` |
| **OHLC** | Binance klines, multi-TF (15m–1W), live refresh ~30s, up to 1000 bars |
| **Live quote** | `/quote` Binance 24hr, 5s server cache |
| **Levels v0** | PDH/PDL/PDC, weekly H/L, 4H swing, rotation range, round POI |
| **Research API** | `/research` — levels, deterministic verdict/headline, cross-assets, news |
| **Chart UI** | Lightweight Charts, overlays, range bands, TF/layers menus, red theme |
| **Layout** | Headline + chart \| analysis/news aside |
| **Access** | Developer preview only |

### Not done ❌ (blocks “BTCUSD v1”)

| Gap | Why it matters |
|-----|----------------|
| **`BTCUSD.json` profile** | No single wiring diagram for data sources |
| **Enriched klines** | Taker buy / quote vol discarded — blocks real differentiation |
| **`level_engine_v1`** | v0 levels are commodity (traders can DIY) |
| **`catalysts[]`** | Empty — calendar not wired |
| **US scan + sentiment** | Platform context not in research payload |
| **Global GPT run** | `latest_run: null` — headline is deterministic placeholder |
| **Staging users** | Tab gated on `isDeveloper` |

---

## 4. BTCUSD profile (target config)

Create `backend/services/markets/profiles/BTCUSD.json` (or equivalent in registry):

```json
{
  "market_id": "BTCUSD",
  "label": "BTC/USD",
  "quote_instrument_id": "BTCUSDT",
  "ohlc_source": "binance",
  "narrative_frame": "Risk-on liquidity vs crypto-specific shock",

  "cross_assets": ["ETHUSDT", "SPX", "VIX", "US10Y", "GOLD"],

  "economy_scans": [{ "country": "US", "max_age_hours": 72 }],

  "calendar_filter": {
    "tags": ["FOMC", "CPI", "PCE", "NFP", "GDP", "risk"],
    "currencies": ["USD"],
    "impact_min": "medium",
    "horizon_days": 7,
    "max_items": 8
  },

  "news_filter": {
    "keywords": ["bitcoin", "btc", "crypto", "etf", "sec", "fed", "liquidity"],
    "max_items": 5
  },

  "platform_context": {
    "market_sentiment": true,
    "prediction_markets": false
  }
}
```

`market_research_service.build_research("BTCUSD")` reads this profile — **no hardcoded BTC branches** scattered in Python long-term.

---

## 5. Phased implementation (strict order)

Work **top to bottom**. Do not start Gold/EUR or MT5 until **BTCUSD v1** exit criteria (§7) pass.

### Sprint 1 — Profile + platform context (≈3–5 days)

**Goal:** Research payload feels like FXSentinel, not an isolated Binance chart.

| # | Task | Output |
|---|------|--------|
| 1.1 | Add `BTCUSD.json` + loader in `market_registry` | Single profile source |
| 1.2 | `market_context_service.py` — catalysts from `hybrid_economic_calendar` using profile filter | `catalysts[]` populated |
| 1.3 | Pull latest **US holistic scan** (if &lt;72h) into `macro_context` block | Digest in research + aside |
| 1.4 | Pull **market sentiment** snapshot | `risk_regime` in research |
| 1.5 | Wire aside UI to show catalysts + macro digest (minimal list) | Trader-visible context |

**Exit:** `/research` returns non-empty `catalysts`, `macro_context`, `sentiment`; aside reflects them.

---

### Sprint 2 — Venue quant v1 (≈5–7 days)

**Goal:** Chart overlays traders cannot trivially replicate on TV.

| # | Task | Output |
|---|------|--------|
| 2.1 | Extend `ohlc_ingest_binance` + `ohlc_store` bar schema: `quote_volume`, `trades`, `taker_buy_volume` | Enriched bars |
| 2.2 | Add `feature_engine.py` — 5D 4H volume histogram → POC, VAH, VAL | Feature structs |
| 2.3 | `level_engine_v1` merges v0 + volume profile levels (`basis: volume_poc`, `value_area_*`) | New `structured_levels` |
| 2.4 | Chart: new layer or include in “Ranges” / “POI”; tooltips show `feature_metrics` | Visible differentiation |
| 2.5 | Snapshot unit test: frozen bars → stable level IDs | Regression safety |

**Exit:** Chart shows volume-derived zone + POC; research `data_quality.levels_ok` true; tests pass.

**Defer to v1.1:** taker delta zones (2.6), order book walls (2.7), Binance futures OI/funding (2.8).

---

### Sprint 3 — Global GPT run (≈5–7 days)

**Goal:** Headline and thesis come from AI citing **only** allowlisted structure + platform context.

| # | Task | Output |
|---|------|--------|
| 3.1 | Extend `analysis_context_pack.py` — `SURFACE_MARKET_RESEARCH` | Shared pack for Markets |
| 3.2 | `market_analysis_run_service.py` — persist runs to `data/market_runs/BTCUSD/` JSON (v0 storage) | `latest_run` |
| 3.3 | `scripts/run_market_analysis.py --market BTCUSD` manual trigger | Dev workflow |
| 3.4 | GPT prompt: structured_levels allowlist + catalysts + macro digest + probability language | Narrative output |
| 3.5 | Validator: reject prose citing prices without `level_id` | Safety |
| 3.6 | `/research` returns `latest_run`; headline/thesis from run when fresh | UI updates |

**Exit:** Manual run produces stored narrative; `/research` serves it; validator tests pass.

**Defer:** 2×/day cron (wire after manual stable), Gemini grounding, chart past-run areas.

---

### Sprint 4 — Ship BTCUSD v1 (≈2–3 days)

| # | Task | Output |
|---|------|--------|
| 4.1 | Staging access policy — widen beyond `isDeveloper` (feature flag or tier) | Real users can open tab |
| 4.2 | Error/empty states (no OHLC, Binance down, stale scan) | Production hygiene |
| 4.3 | Footer lineage labels (Binance · level_engine version · run as_of) | Trust |
| 4.4 | Doc: symbol map + profile README in repo | Onboarding |

**Exit:** §7 definition of done all checked.

---

## 6. API shape (BTCUSD research — target)

`GET /api/markets/BTCUSD/research` should converge to:

```json
{
  "market_id": "BTCUSD",
  "as_of": "ISO8601",
  "quote": { "price", "changePercent", "source": "binance", "instrument_id": "BTCUSDT" },
  "structured_levels": [],
  "catalysts": [{ "title", "time", "impact", "currency" }],
  "macro_context": {
    "us_scan_summary": "",
    "us_scan_as_of": "",
    "risk_regime": ""
  },
  "cross_assets": [],
  "news": [],
  "verdict": { "bias", "display_bias", "day_summary", "swing_summary", "conviction" },
  "headline": "",
  "headline_emphasis": [],
  "thesis": { "headline", "body" },
  "invalidation": [],
  "latest_run": { "run_id", "created_at", "model" } | null,
  "data_quality": { "ohlc_as_of", "levels_ok", "levels_version": "v1" }
}
```

Frontend keeps **one hook** (`useMarketResearch`) — no new client fetches for calendar/scan.

---

## 7. Definition of done — BTCUSD v1

- [ ] Developer **or staging user** opens Markets → **BTC/USD** research (not coming soon)
- [ ] Chart: real Binance candles + **volume profile zone/POC** (v1), not just PDH/PDL
- [ ] `/research`: **catalysts** (FOMC/CPI/etc.), **US macro digest**, **sentiment**, cross-assets, news
- [ ] **Latest global GPT run** drives headline + thesis when run exists (&lt;24h); deterministic fallback documented
- [ ] GPT output passes allowlist validator in tests
- [ ] `BTCUSD.json` profile drives wiring (no scattered BTC-only hacks)
- [ ] Same payload for all users; manual run script documented

---

## 8. Explicitly out of scope until BTCUSD v1 ships

| Item | Why wait |
|------|----------|
| Gold / EURUSD / USDJPY enabled in picker | Prove template on BTC first |
| MT5 OHLC | Binance sufficient for BTC v1 |
| 6×/day GPT runs | Start manual + 2×/day |
| Gemini co-write | Grounding optional later |
| Past analysis areas on chart | Needs run history UI |
| Client-side Binance WebSocket | 5s REST + cache is enough |
| Order book / futures OI overlays | v1.1 after volume profile |
| Per-user Markets analysis | Global runs only |

---

## 9. Architecture diagram (BTCUSD only)

```text
                    ┌─────────────────────┐
                    │   BTCUSD.json       │
                    │   (profile)         │
                    └──────────┬──────────┘
                               │
     ┌─────────────────────────┼─────────────────────────┐
     │                         │                         │
     ▼                         ▼                         ▼
┌─────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│ Binance     │    │ Platform (existing) │    │ GPT global run  │
│ klines      │    │ calendar · US scan   │    │ (manual→cron)   │
│ ticker      │    │ sentiment · news · TV│    │ allowlist valid.│
└──────┬──────┘    └──────────┬───────────┘    └────────┬────────┘
       │                      │                          │
       ▼                      ▼                          │
 feature_engine         market_context_service           │
 level_engine_v1                │                        │
       │                      │                          │
       └──────────┬───────────┘                          │
                  ▼                                      │
        market_research_service ◄────────────────────────┘
                  │
                  ▼
        GET /api/markets/BTCUSD/research
                  │
                  ▼
           MarketsHub (React)
        chart · headline · aside
```

---

## 10. Decision log (BTCUSD-specific)

| Date | Decision |
|------|----------|
| 2026-06-03 | BTCUSD first; `BTCUSDT` data feed |
| 2026-06-07 | Lightweight Charts research chart; Binance OHLC |
| 2026-06-08 | Binance live quote; chart toolbar UX |
| 2026-06-09 | Three lanes: venue quant / platform context / GPT narrative |
| 2026-06-09 | Sprint order: **platform context → quant v1 → GPT → ship** |
| 2026-06-09 | Profile file owns wiring; deprecate hardcoded BTC branches over time |

---

## 11. What to do Monday morning

1. Create **`BTCUSD.json`** profile + loader.  
2. Implement **`market_context_service`** — catalysts + US scan + sentiment.  
3. Verify `/research` JSON in browser — aside should show real macro/calendar context.  
4. Then start **enriched klines** (Sprint 2) — do not skip Sprint 1; context without differentiation still beats differentiation without context for FXSentinel’s brand.

---

## Revision log

| Date | Change |
|------|--------|
| 2026-06-09 | Initial BTCUSD-focused strategy — sprints, profile, DoD, out-of-scope |
