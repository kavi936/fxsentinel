# BTCUSD — Data Research & UI Incorporation Plan

**Status:** Active — evaluate data **before** building each feature  
**Last updated:** 2026-07-08 (linked master vision)  
**Product intent:** [`MARKETS_MASTER_VISION.md`](./MARKETS_MASTER_VISION.md)  
**Companion:** [`MARKETS_BTCUSD_STRATEGY.md`](./MARKETS_BTCUSD_STRATEGY.md) (sprint order) · [`MARKETS_TAB_PRODUCT_SPEC.md`](./MARKETS_TAB_PRODUCT_SPEC.md) (product rules)

---

## 1. How to read this doc

Building Markets is not “add every indicator.” It is:

1. **Research** — what data exists, cost, refresh rules, legal/API limits  
2. **Transform** — deterministic features → `structured_levels[]` or `market_signals{}`  
3. **Place** — chart overlay vs aside vs metric chips vs GPT-only context  
4. **Narrate** — GPT cites allowlisted levels; metrics inform thesis prose  

```text
Phase R  Research spikes (this doc §4)
    ↓
Phase A  Venue quant → chart overlays
Phase B  Platform context → aside + GPT
Phase C  Derivatives metrics → aside “Flow” (mostly not on chart)
Phase D  GPT global runs
```

**Rule:** No UI mock for a data type until its **research row** (§3) is filled with a spike result.

---

## 2. UI surfaces (where things appear)

Markets stays **chart-first**. Not everything belongs on the candle pane.

| Surface | ID | Best for | Clutter risk |
|---------|-----|----------|--------------|
| **Chart overlays** | `chart` | Price levels, zones, POC, range bands — allowlisted `structured_levels` | High — max ~8–12 visible |
| **Toolbar metric chips** | `toolbar` | Live price (done), funding %, OI Δ, book imbalance — 1-line | Low |
| **Aside — Analysis** | `aside.analysis` | Bias, thesis, key structure list, invalidation, cross-assets | Medium |
| **Aside — Catalysts** | `aside.catalysts` | FOMC, CPI, NFP — next 7d | Low |
| **Aside — Flow** | `aside.flow` | Funding, OI, liq summary, positioning — **new tab** | Medium |
| **Aside — News** | `aside.news` | 3–5 headlines (done) | Low |
| **Chart footer** | `footer` | Source lineage, bar count, engine version | Low |
| **GPT only** | `gpt` | Full scan digest, prediction markets — not duplicated in UI | None |

**Default tabs (target):** Analysis · Catalysts · Flow · News  

**Layer toggles (chart):** Structure · Volume profile · Flow POIs · (not “Funding heatmap” full-screen in v1)

---

## 3. Data inventory & research matrix

Status key: ⬜ not started · 🟡 spike in progress · ✅ validated · ❌ defer / paid only

### 3.1 Binance spot (BTCUSDT) — primary venue

| Data | API | Auth | Refresh | Transform | UI surface | Tier | Status |
|------|-----|------|---------|-----------|------------|------|--------|
| OHLC klines | `GET /api/v3/klines` | None | 30s live | `ohlc_store` | Chart candles | **v1** | ✅ |
| Last + 24h change | `GET /api/v3/ticker/24hr` | None | 5s cache | `binance_ticker` | Toolbar + picker | **v1** | ✅ |
| **Taker buy vol** (in kline) | same klines `[9],[10]` | None | with OHLC | `feature_engine` delta | Zone overlay + `feature_metrics` | **v1** | ⬜ ingest gap |
| **Quote volume, trades** | same klines | None | with OHLC | volume profile | POC / VAH / VAL on chart | **v1** | ⬜ |
| Order book depth | `GET /api/v3/depth?limit=500` | None | 30–60s cache | wall detection → POI | Chart POI + aside imbalance | **v1.1** | ⬜ |
| Book ticker (spread) | `GET /api/v3/ticker/bookTicker` | None | 5–10s | spread stress flag | Toolbar chip + GPT | **v1.1** | ⬜ |
| Agg trades | `GET /api/v3/aggTrades` | None | on-demand | large print count | Aside flow (optional) | **v2** | ⬜ |
| Recent trades | `GET /api/v3/trades` | None | high freq | noisy — skip | — | defer | ⬜ |

### 3.2 Binance USD-M futures (BTCUSDT perp) — positioning context

Spot chart; **futures for context** (not mixed candles without research sign-off).

| Data | API | Auth | Refresh | Transform | UI surface | Tier | Status |
|------|-----|------|---------|-----------|------------|------|--------|
| **Funding rate** (current + hist) | `GET /fapi/v1/premiumIndex` + `/fapi/v1/fundingRate` | None | 5–15 min | extreme flag, 8h trend | Toolbar chip + aside Flow | **v1.1** | ⬜ |
| **Open interest** | `GET /fapi/v1/openInterest` | None | 5–15 min | OI Δ vs 24h | Aside Flow | **v1.1** | ⬜ |
| OI history | `GET /futures/data/openInterestHist` | None | 15 min | trend chart sparkline | Aside Flow | **v1.2** | ⬜ |
| Long/short ratio | `GET /futures/data/globalLongShortAccountRatio` | None | 15 min | positioning skew | Aside Flow + GPT | **v1.2** | ⬜ |
| Mark / index price | `GET /fapi/v1/premiumIndex` | None | 30s | basis = mark − spot | Toolbar basis bps | **v1.1** | ⬜ |
| **Liquidations (live)** | WS `!forceOrder@arr` | None | stream | roll up 24h clusters | Aside Flow summary | **v1.2** | ⬜ |
| Liquidation **heatmap** (Coinglass-style) | No free full history API | — | — | needs aggregated history or vendor | Full heatmap | **v3 / vendor** | ❌ research |

**Research note (liquidations):** Public WS gives **real-time** force orders, not a historical price×time heatmap. To approximate a heatmap we must **buffer** liqs (e.g. 24–72h), bin by price, render as horizontal intensity — doable v1.2, not v1. A true multi-day liquidation heatmap like third-party terminals usually needs **paid data** or heavy infra.

### 3.3 “Liquidity heatmap” — evaluate honestly

| What traders mean | FXSentinel approach | Tier |
|-------------------|---------------------|------|
| **Volume profile** (price × volume) | Histogram from enriched klines → POC/VAH/VAL bands on chart | **v1** |
| **Order book liquidity** (resting size by price) | Snapshot depth → top bid/ask walls as POI lines; optional mini depth profile in aside | **v1.1** |
| **Liquidation heatmap** (historical liqs at price) | Buffer WS liquidations → price bins → **simplified** side panel or faint band overlay | **v1.2** |
| **Full 2D time×price heatmap** (Coinglass/Hyblock) | Vendor API or major engineering — **out of BTC v1** | **v3** |

**Product call:** Call volume profile “**Volume zones**” in UI — not “heatmap” — until liq aggregation ships.

### 3.4 FXSentinel platform (already in app)

| Data | Service / API | Transform | UI surface | Tier | Status |
|------|---------------|-----------|------------|------|--------|
| Economic calendar | `hybrid_economic_calendar` | profile filter | Aside Catalysts | **v1** | ⬜ wire |
| US holistic scan | `economy_holistic_scan_service` | digest | Aside Analysis + GPT | **v1** | ⬜ |
| Market sentiment | `market_sentiment_service` | risk regime | Aside Analysis | **v1** | ⬜ |
| Live news | `persistent_news_cache` | crypto filter | Aside News | **v1** | ✅ partial |
| Cross-asset quotes | TV / `forex-prices` | list | Aside Analysis | **v1** | ✅ |
| Prediction markets | `/api/prediction-markets` | Fed cut probs | Aside or GPT only | **v2** | ⬜ |
| Calendar event AI | enhanced analysis | catalyst detail | Catalyst row expand | **v2** | ⬜ |

---

## 4. Phase R — Research spikes (do before build)

**Duration:** ~3–5 days (can overlap Sprint 1).  
**Deliverable:** `docs/research/BTCUSD_DATA_SPIKE_RESULTS.md` (create when spikes run) + updated Status column in §3.

| # | Spike | Script / method | Pass criteria |
|---|-------|-----------------|---------------|
| R1 | Enriched kline fields | Extend ingest; log one bar JSON | taker_buy, quote_vol present in store |
| R2 | Volume profile POC on 1000×4H bars | notebook or `scripts/spike_volume_profile.py` | stable POC/VAH/VAL within 0.1% on rerun |
| R3 | Depth snapshot walls | `GET depth limit=500` every 60s × 1h | top 3 bid/ask walls identifiable |
| R4 | Funding + OI + basis | `fapi` calls from Railway IP | no geo block; rate limits documented |
| R5 | Liquidation WS sample | 1h listen `!forceOrder@arr` | events received; CSV schema defined |
| R6 | Calendar filter for BTC | filter hybrid calendar by FOMC/CPI | 3–8 events in 7d window |
| R7 | US scan age + size | pull latest from store | payload fits research JSON (&lt;4KB digest) |
| R8 | Railway cost estimate | count req/min at planned refresh | stays within Hobby/Pro budget |

**Exit Phase R:** Every **v1** and **v1.1** row has ✅ or explicit ❌ with reason.

---

## 5. Backend incorporation model

### 5.1 New modules (target)

```text
profiles/BTCUSD.json          — toggles which data sources are on
venue_data_binance_spot.py    — depth, enriched klines (extend ingest)
venue_data_binance_futures.py — funding, OI, basis (new)
feature_engine.py             — volume profile, delta, depth walls
level_engine.py               — merges features → structured_levels[]
market_context_service.py     — calendar, scan, sentiment, news
market_signals_service.py     — non-overlay metrics → market_signals{}
market_research_service.py    — composes final DTO
```

### 5.2 Research API extensions

`GET /api/markets/BTCUSD/research` adds blocks (additive — don’t break chart):

```json
{
  "structured_levels": [],
  "market_signals": {
    "funding": { "rate", "next_time", "extreme": "neutral|crowded_long|crowded_short" },
    "open_interest": { "value", "change_24h_pct" },
    "basis_bps": 0,
    "book_imbalance": { "bid_pct", "ask_pct", "as_of" },
    "liquidation_24h": { "long_usd", "short_usd", "top_bins": [] }
  },
  "catalysts": [],
  "macro_context": {},
  "sentiment": {}
}
```

**`market_signals`** = metrics for aside/toolbar/GPT — **not** draw on chart unless promoted to `structured_levels` (e.g. liquidity wall POI).

### 5.3 Promotion rules (metric → chart overlay)

| Condition | Action |
|-----------|--------|
| Fixed price level with `basis` + stable ID | → `structured_levels` POI/level |
| Zone with upper/lower bound | → `structured_levels` range + band on chart |
| Scalar (funding %, OI Δ) | → `market_signals` + toolbar/aside only |
| Noisy / unvalidated | → GPT context only or defer |

---

## 6. UI incorporation plan (by tier)

### Tier v1 — BTCUSD ship (Sprints 1–4 in strategy doc)

| Feature | Data | UI |
|---------|------|-----|
| Platform context | calendar, US scan, sentiment | Aside: Catalysts section inside Analysis or new tab |
| Volume zones | enriched klines | Chart: VAH/VAL band + POC line; layer toggle “Volume profile” |
| Structure v0 | level_engine | Chart: existing layers |
| News + cross-assets | existing | Aside: News tab + cross-asset list |
| GPT thesis | global run | Headline + Analysis body |

**Aside layout v1:**

```text
[ Analysis | Catalysts | News ]     ← Flow tab in v1.1

Analysis: bias · conviction · thesis · key structure · invalidation · cross-assets
Catalysts: next 7d events (title · time · impact)
News: (existing)
```

### Tier v1.1 — Flow & microstructure (~1 week after v1)

| Feature | Data | UI |
|---------|------|-----|
| Funding chip | fapi premiumIndex | Toolbar: `Funding · +0.01%` |
| Basis chip | mark − spot | Toolbar: `Basis · +12 bps` |
| OI summary | openInterest | Aside **Flow** tab |
| Book imbalance | depth snapshot | Aside Flow + optional POI if wall &gt; threshold |
| Liquidity walls | depth | Chart POI lines (“Bid wall 62.5k”) — max 2 each side |

### Tier v1.2 — Liquidation context (~1–2 weeks)

| Feature | Data | UI |
|---------|------|-----|
| 24h liq rollup | WS buffer + worker | Aside Flow: “Liqs 24h: $XM long / $YM short” |
| Liq price bins | aggregated buffer | **Mini horizontal bar profile** in Flow tab (not full chart heatmap) |
| Long/short ratio | futures data API | Flow tab row |

### Tier v2+ — defer

- Full liquidation heatmap on chart  
- Agg trade tape  
- Prediction markets strip  
- Sub-second WS price  
- ETH/BTC correlation regime panel  

---

## 7. Master timeline (research + build)

| Week | Phase | Focus |
|------|-------|--------|
| **W0** | **R** | Spikes R1–R8; fill §3 status; write spike results doc |
| **W1** | Sprint 1 | Profile + `market_context_service` + Aside Catalysts |
| **W2** | Sprint 2 | Enriched klines + volume profile + chart layer |
| **W3** | Sprint 3 | GPT global run + validator |
| **W4** | Sprint 4 | Staging ship BTCUSD v1 |
| **W5** | v1.1 | Funding, OI, basis, depth walls, Flow tab |
| **W6+** | v1.2 | Liquidation buffer worker + liq bin panel |

**Parallel rule:** UI work for a tier only starts when **all** that tier’s research rows are ✅.

---

## 8. Component checklist (frontend)

| Component | Purpose | Tier |
|-----------|---------|------|
| `MarketChartToolbar` | TF, layers, live quote, **metric chips** | v1 / v1.1 |
| `MarketChartAside` | tabs + panels | v1 |
| `MarketCatalystsPanel` | catalyst list | v1 |
| `MarketFlowPanel` | funding, OI, liqs, book | v1.1–v1.2 |
| `MarketStructureList` | key levels from research | v1 (extract from aside) |
| `MarketMetricChip` | reusable toolbar chip | v1.1 |
| `MarketLiqBinProfile` | horizontal liq histogram (aside) | v1.2 |
| Chart range bands / POI | existing overlay system | v1 |

**No new chart library** for heatmaps in v1 — use Lightweight Charts bands + aside SVG/profile bars.

---

## 9. GPT incorporation (all tiers)

GPT pack includes:

- `structured_levels[]` (allowlist)
- `market_signals` summary (funding extreme, OI direction — **no invented numbers**)
- `macro_context`, `catalysts`, `news` digests
- Instruction: explain **probability** of tapping zone IDs; mention funding/catalysts as **context**, not as new levels

Example allowed: “Funding crowded long (+0.05%) while price sits in `btcusd_value_area_*` — elevated long-squeeze risk into `btcusd_pdl_*`.”  
Example rejected: “Support at 61,800” (no level_id).

---

## 10. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Binance rate limits | Server-side cache; one poll per signal type |
| Futures API blocked on Railway region | Spike R4 early; fallback: omit Flow tier |
| Liquidation heatmap expectation gap | UI copy: “Volume zones” + “24h liq summary”, not “heatmap” until v1.2 |
| Chart clutter | Promotion rules (§5.3); default layers Structure + Volume only |
| Paid vendor pressure | Defer full heatmap to v3; evaluate Coinglass/Glassnode only if users demand |

---

## 11. Definition of done — research phase (Phase R)

- [ ] §3 matrix: all v1 + v1.1 rows ✅ or ❌ with written rationale  
- [ ] `BTCUSD_DATA_SPIKE_RESULTS.md` committed with sample payloads  
- [ ] Profile schema updated with `venue_data` toggles (spot depth, futures flow)  
- [ ] UI wireframe agreed: Analysis | Catalysts | News (+ Flow v1.1)  
- [ ] Team aligned: **volume profile ≠ liquidation heatmap** for v1 messaging  

---

## 12. Links & next action

1. Run **R1 + R4** first (enriched klines + futures API from deploy environment).  
2. Update §3 status column.  
3. Proceed [`MARKETS_BTCUSD_STRATEGY.md`](./MARKETS_BTCUSD_STRATEGY.md) Sprint 1 in parallel with remaining spikes.  

---

## Revision log

| Date | Change |
|------|--------|
| 2026-06-09 | Initial data research matrix, UI surfaces, tier plan, Phase R spikes |
