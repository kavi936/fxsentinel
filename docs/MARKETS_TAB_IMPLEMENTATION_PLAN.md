# Markets Tab — Implementation Plan (BTCUSD first)

**Status:** Active — Phase 2 BTCUSD UI in developer preview  
**Horizon:** Phase 0 (layout) → ~2 weeks engineering for first **BTCUSD** dashboard (internal/staging)  
**Last updated:** 2026-06-09  

> **BTCUSD playbook:** [`MARKETS_BTCUSD_STRATEGY.md`](./MARKETS_BTCUSD_STRATEGY.md)  
> **Data research + UI surfaces:** [`MARKETS_BTCUSD_DATA_AND_UI_PLAN.md`](./MARKETS_BTCUSD_DATA_AND_UI_PLAN.md)
**Canonical market id:** `BTCUSD` (user-facing)  
**Data feed id:** `BTCUSDT` (TradingView + Binance klines — same underlying spot)

Parent spec: [`MARKETS_TAB_PRODUCT_SPEC.md`](./MARKETS_TAB_PRODUCT_SPEC.md) — see **§1.1 aggregation hub**, **§8.6 v1 roadmap**, **§14.1 status snapshot**  
Advanced Charts path: [`MARKETS_ADVANCED_CHARTS_ROADMAP.md`](./MARKETS_ADVANCED_CHARTS_ROADMAP.md)

---

## Current status (2026-06-09)

### Phase progress

| Phase | Name | Status |
|-------|------|--------|
| **0** | Layout | ~80% — chart-dominant + aside (analysis/news); not formally signed off |
| **1** | Data platform | ✅ Binance OHLC, level_engine_v0, research/ohlc/quote APIs |
| **2** | BTCUSD wired UI | ~85% — developer preview only |
| **3** | Intelligence | ~15% — deterministic verdict; no GPT runs |
| **4** | Market #2+ | Not started |

### Backend modules (shipped)

| Module | Path |
|--------|------|
| Registry | `backend/services/markets/market_registry.py` |
| Binance ingest | `ohlc_ingest_binance.py` |
| OHLC store + live refresh | `ohlc_store.py`, `udf_datafeed.py` |
| Level engine v0 | `level_engine.py` |
| Research DTO | `market_research_service.py` |
| Live quote | `market_quote_service.py`, `binance_ticker.py` |
| News filter | `market_news_filter.py` |
| Routes | `backend/routes/markets_udf_routes.py` |

### Frontend (shipped)

| Component | Notes |
|-----------|--------|
| `MarketsHub.jsx` | Picker, headline, chart section; single `useMarketQuote` poll |
| `MarketChart.jsx` | Lightweight Charts, overlays, range bands |
| `MarketChartToolbar.jsx` | TF + layers dropdowns on chart |
| `MarketChartSection.jsx` | Split: chart \| analysis/news aside |
| `marketChartTheme.js` | Red-branded canvas + grid |
| Hooks | `useMarketResearch`, `useMarketOhlc`, `useMarketQuote`, `useMarketNews` |

### Not yet built (from original week-2 plan)

- `feature_engine.py` — volume profile, delta, book (see spec §8.6)
- `market_analysis_run_service.py` / `run_market_analysis.py`
- `GET /api/markets/:id/runs`
- Catalysts in research payload
- Global GPT narrative (`latest_run`)
- `BTCUSD.json` profile file
- Public tab access (still `isDeveloper` gate)

### Immediate next work (agreed priority)

**See [`MARKETS_BTCUSD_STRATEGY.md`](./MARKETS_BTCUSD_STRATEGY.md) for sprint order.**

1. **Sprint 1** — `BTCUSD.json` profile + `market_context_service` (calendar, US scan, sentiment)
2. **Sprint 2** — enriched klines + volume POC/VAH/VAL (`level_engine_v1`)
3. **Sprint 3** — global GPT run + `SURFACE_MARKET_RESEARCH`
4. **Sprint 4** — staging access + BTCUSD v1 ship

---

## 0. Why BTCUSD first

| Reason | Detail |
|--------|--------|
| **24/7 market** | No FX session-close / illustrative-level mess for v0 |
| **Quotes already live** | `BTCUSDT` in `tradingview_instruments.py` + `useForexPrices` |
| **News density** | Crypto keywords already in live-news filters; good for minimized news strip |
| **OHLC without MT5 day 1** | Binance public klines (`BTCUSDT`) unblock `level_engine` while MT5 spike runs in parallel |
| **Validates crypto template** | Gold/FX profiles differ later; BTC proves chart + global runs + news-heavy layout |

**Naming rule:** API routes and UI say `BTCUSD`; config maps `quote_id: BTCUSDT`, `tv: BINANCE:BTCUSDT`.

---

## 1. Phases overview (read this first)

You have **product spec** (what the tab must do) but not **presentation** (exact layout). Do **not** skip straight to production UI. Use the phases below.

| Phase | Name | Goal | UI work? |
|-------|------|------|----------|
| **0** | Discover & layout | Decide **what appears where** with fake data | Wireframe + static prototype only |
| **1** | Data platform | OHLC, levels, research API (BTCUSD) | None required (API + JSON) |
| **2** | BTCUSD wired UI | Replace coming-soon; real chart + API | Built to Phase 0 layout |
| **3** | BTCUSD intelligence | Global GPT runs, news/catalysts live | Refine copy/placement from feedback |
| **4** | Market #2+ | Gold / EURUSD profiles | Reuse layout shell |

**Phase 0 is not “build the tab.”** It is **validate the tab** before expensive backend + AI wiring.

---

## 1.1 Phase 0 — Layout & presentation (do this first)

**Duration:** ~3–5 days (can overlap with a small backend spike, see below).

### What you produce (exit criteria)

- [ ] **One chosen layout** (A or B below) — written down, not “we’ll see in code”
- [ ] **Section order + priority** — what is above the fold on laptop + mobile
- [ ] **Chart overlay legend** — how levels / POI / ranges / past runs look (labels, toggles)
- [ ] **Static prototype** in the repo: `MarketResearch` with **hardcoded mock JSON** (no API)
- [ ] **API sketch signed off** — fields in `GET .../research` match what the prototype needs
- [ ] **Explicit “not in v0” list** — e.g. past analysis areas on chart → v0.2

### What you do *not* need in Phase 0

- Final GPT prompts
- MT5 connection
- Firestore
- Pixel-perfect Figma
- All six daily runs

### Phase 0 activities (in order)

1. **Information architecture (half day)**  
   List every **block** and one sentence why it exists:

   | Block | User question it answers |
   |-------|---------------------------|
   | Verdict bar | Bullish/bearish for day & swing? |
   | Chart | Where is price vs structure? |
   | Cross-asset strip | What else is moving with BTC? |
   | Catalysts | What macro dates matter? |
   | News strip | What headlines matter *now*? |
   | Thesis / AI block | Why is bias X? |
   | Invalidation | What proves us wrong? |

2. **Layout options (1 day) — pick one direction**  

   **Layout A — Chart-dominant (recommended in spec)**  
   Chart ~50–60vh top; verdict slim under chart; news + catalysts in a **right column** or **below** on mobile.

   **Layout B — Verdict-first**  
   Bias hero at top; chart below; better for “direction first” marketing, worse for TV-trader habit.

   Sketch on paper or drop ASCII in this doc. No code required yet.

3. **Chart spike (1 day)**  
   Isolated page or Storybook-style component: `lightweight-charts` + **fake** candles + 2 horizontal lines + 1 shaded range.  
   Answers: readability, colors on your dark theme, label clutter.

4. **Black canvas + build top → bottom (current)**  
   - `MarketsHub` = minimal top bar + empty `.markets-canvas` (`#000`)  
   - Section skeleton kept in `MarketResearch.jsx` / `mockBtcusdResearch.json` — re-enable one block at a time  
   - Styling tokens: [`DASHBOARD_BRANDING.md`](./DASHBOARD_BRANDING.md)

5. **Contract lock (half day)**  
   Adjust `BTCUSD.json` + implementation plan API section if the prototype needs extra fields (e.g. `verdict.day_summary`).

### Phase 0 backend (optional parallel — safe)

While UI is mocked, one dev can run **technical spikes** that do not dictate layout:

- Binance klines script (30 bars)
- `level_engine` unit test on CSV

Do **not** build full `market_research_service` until Phase 0 exit criteria pass.

---

## 1.2 Rollout strategy (market-by-market, after Phase 0)

```
Phase 1 — Data platform (BTCUSD)
  registry → OHLC store → level_engine → research API (real JSON, no polished UI)

Phase 2 — BTCUSD UI
  Wire prototype to API; chart real candles + overlays

Phase 3 — BTCUSD intelligence
  global runs (2×/day) → GPT narrative → news/catalysts filters live

Phase 4 — Market #2
  New profile JSON; same layout shell

Phase 5 — MT5 primary (when ready)
  Swap OHLC source in profile
```

Do **not** build three market UIs in parallel. One vertical slice on BTCUSD until layout + API feel right.

---

## 2. Two-week schedule (starts after Phase 0 sign-off)

### Week 1 — Data + API + wire UI to API

| Day | Focus | Deliverable |
|-----|--------|-------------|
| **1** | Registry + profile | `BTCUSD.json` profile; `market_registry.py`; doc symbol map |
| **2** | Research API (stub) | `GET /api/markets`, `GET /api/markets/BTCUSD/research` with static/mock verdict |
| **3** | OHLC ingest v0 | `ohlc_ingest_binance.py` — 1D + 4H bars → `data/ohlc/BTCUSD/` or SQLite |
| **4** | Level engine v0 | `level_engine.py` — PDH/PDL/PDC, weekly H/L, round POI, one `target_range` |
| **5** | Wire research API | Real `structured_levels` + quote from TV in research payload |
| **6** | Wire prototype → API | Connect Phase 0 static UI to real `GET .../research` |
| **7** | Chart live data | Swap mock candles for `GET .../ohlc?tf=4H` |

### Week 2 — BTCUSD “real” dashboard

| Day | Focus | Deliverable |
|-----|--------|-------------|
| **8** | Chart overlays | Horizontal levels + shaded `range` zones + POI markers |
| **9** | Cross-asset strip | `ETHUSDT`, `SPX`, `VIX`, `US10Y`, `GOLD` quotes in research API |
| **10** | News strip | 3–5 headlines — filter existing news API by BTC/crypto keywords |
| **11** | Catalysts | Thin FOMC/CPI/risk events from calendar filter in profile |
| **12** | Global runs (manual) | `POST /internal/markets/BTCUSD/run` + Firestore/JSON `runs/`; store `chart_overlays` |
| **13** | GPT narrative v0 | One prompt path `analysis_kind=market_research`; **2 runs/day** cron or manual |
| **14** | Polish + staging | Layer toggles, “as of” labels, error states; enable tab for staging users |

**Defer past day 14 (BTCUSD v1.1):** Gemini grounding, 6 runs/day, past analysis **areas** on chart, MT5-only ingest.

---

## 3. File / module checklist (create in this order)

### Backend

| Order | Path | Purpose |
|-------|------|---------|
| 1 | `backend/services/market_research_profiles/BTCUSD.json` | Single source of truth for filters + copy seeds |
| 2 | `backend/services/market_registry.py` | `market_id` → quote id, OHLC source, enabled flag |
| 3 | `backend/services/ohlc_ingest_binance.py` | Pull klines; normalize to internal OHLC schema |
| 4 | `backend/services/ohlc_store.py` | Read/write bars (filesystem v0 → DB later) |
| 5 | `backend/services/level_engine.py` | `build_structured_levels(market_id, tf)` |
| 6 | `backend/services/market_research_service.py` | Assemble research DTO |
| 7 | `backend/services/market_analysis_run_service.py` | Persist global runs (v0: JSON/Firestore) |
| 8 | `backend/routes/markets.py` or routes in `app.py` | Public GET endpoints |
| 9 | `backend/scripts/run_market_analysis.py` | Manual trigger for dev |
| 10 | `backend/services/market_analysis_pipeline.py` | GPT + `finalize_analysis` (week 2) |

### Frontend

| Order | Path | Purpose |
|-------|------|---------|
| 1 | `src/components/markets/MarketsHub.jsx` | Picker (only BTCUSD enabled initially) |
| 2 | `src/components/markets/MarketResearch.jsx` | Layout sections per spec |
| 3 | `src/components/markets/MarketChart.jsx` | Lightweight Charts + overlay layer |
| 4 | `src/components/markets/sections/` | Verdict, NewsStrip, Catalysts, CrossAsset, Thesis |
| 5 | `src/hooks/useMarketResearch.js` | Fetch research + ohlc |
| 6 | `src/components/Markets.css` | Replace coming-soon styles with Markets-native |
| 7 | `src/config.js` | `endpoints.marketResearch` |

### Dependencies

```bash
npm install lightweight-charts
```

---

## 4. API contracts (implement stub → real)

### `GET /api/markets`

```json
{
  "markets": [
    {
      "id": "BTCUSD",
      "label": "BTC/USD",
      "enabled": true,
      "category": "crypto"
    }
  ]
}
```

### `GET /api/markets/BTCUSD/research`

```json
{
  "market_id": "BTCUSD",
  "as_of": "ISO8601",
  "quote": { "price": 0, "changePercent": 0, "source": "tradingview", "instrument_id": "BTCUSDT" },
  "verdict": {
    "bias": "neutral",
    "display_bias": "TRUE NEUTRAL",
    "day_summary": "",
    "swing_summary": "",
    "conviction": "low"
  },
  "structured_levels": [],
  "cross_assets": [],
  "catalysts": [],
  "news": [],
  "latest_run": null,
  "data_quality": { "ohlc_as_of": null, "levels_ok": false }
}
```

### `GET /api/markets/BTCUSD/ohlc?tf=4H&limit=200`

```json
{
  "market_id": "BTCUSD",
  "timeframe": "4H",
  "bars": [{ "time": 1710000000, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0 }]
}
```

### `GET /api/markets/BTCUSD/runs?limit=10`

History for chart markers / past areas (week 2).

### Internal: `POST /internal/markets/BTCUSD/analyze` (auth/admin)

Triggers **one global run** — not exposed to retail users in v0.

---

## 5. OHLC: pragmatic path for BTC (week 1)

**v0 (ship):** Binance REST klines — `GET /api/v3/klines?symbol=BTCUSDT&interval=1d` (and `4h`).  
- No API key for public klines.  
- Aligns with `BINANCE:BTCUSDT` on TradingView.  
- Run ingest every 15–60 min via cron or on-demand before global run.

**Parallel (don’t block UI):** MT5 spike on `BTCUSD` broker symbol — when stable, set `ohlc_primary: mt5` in profile.

**Why not wait for MT5:** Week 1 goal is level_engine + chart proof; BTC is the best market to decouple from terminal ops.

---

## 6. Level engine v0 (BTCUSD)

Minimum algorithms for first chart overlay:

1. Prior day high / low / close (`1D`)
2. Current week high / low (last 5× `1D`)
3. Prior 4H swing high/low (simple local extrema)
4. **POI:** confluence = PDH near round $1k (e.g. within 0.3%)
5. **Range:** prior 4H session high–low band tagged `target_range` + `horizon: day`

Output: unified list with `kind: level | poi | range` (see product spec §8).

Unit test: frozen CSV of 30 bars → snapshot `structured_levels`.

---

## 7. Global analysis runs (week 2)

**v0 trigger:** Manual script or admin endpoint only.

```bash
cd backend && python scripts/run_market_analysis.py --market BTCUSD
```

Pipeline:

1. Refresh OHLC ingest  
2. `level_engine.build("BTCUSD")`  
3. Pull quote + cross-assets + filtered news + catalysts  
4. Build `AnalysisContextPack` (extend existing pack with `market_id`, levels)  
5. GPT → `finalize_analysis(..., analysis_kind="market_research")`  
6. Save run doc + attach `chart_overlays` from levels/ranges  
7. Research API returns `latest_run`

**Scheduler (after manual works):** 2×/day UTC — e.g. 08:00 and 20:00 — single worker, idempotent `run_slot` key.

**Cost:** `2 runs × 1 market × GPT` — not per user.

---

## 8. Frontend UX (BTCUSD only)

1. **Markets tab** loads `MarketsHub` → default `BTCUSD`.  
2. **Chart** top ~50vh; dark TV-like grid.  
3. **Verdict** slim bar under chart (bias pill — reuse **styles** from holistic scan, not the card component).  
4. **News strip** — 3–5 rows, no Overview card markup.  
5. **Catalysts** — simple list (week 2).  
6. **Thesis** — static from profile + latest run body (week 2).  
7. Disable picker entries for Gold/EUR until `enabled: true` in registry.

---

## 9. Definition of done — BTCUSD v0 (end of week 2)

- [ ] User opens Markets tab and sees **BTC/USD** research (not coming soon) — **dev gate only today**
- [x] Chart shows **real 4H candles** from your OHLC store (+ 7 TFs, 1000 bars)
- [x] At least **PDH/PDL + one range** on chart from `level_engine`
- [ ] Verdict + thesis from **latest global run** (or deterministic fallback if run missing) — **fallback only**
- [x] **3–5 news** headlines, crypto-filtered
- [x] Quote updates via **Binance BTCUSDT** (upgraded from TV-only plan)
- [x] No per-user analysis; same payload for all users
- [ ] Docs: symbol map `BTCUSD` ↔ `BTCUSDT` in profile README
- [ ] **Differentiation:** volume profile / enriched kline features (v1 — see spec §8.6)

---

## 10. After BTCUSD — market #2

| Candidate | Extra work beyond platform |
|-----------|----------------------------|
| **GOLD** | Commodity profile; `COMEX:GC1!` OHLC source; rates cross-assets |
| **EURUSD** | Two economy legs; richer calendar; reuse `holistic_pair_commentary` tokens |

Copy **no** BTC-specific strings into profile #2 — only config + `level_engine` params.

---

## 11. Risks for this sprint

| Risk | Mitigation |
|------|------------|
| Scope creep (GPT 6×, Gemini, MT5) | Stick to § “Defer past day 14” |
| Binance rate limits | Cache bars; ingest only new candles |
| `BTCUSD` vs `BTCUSDT` confusion | Single `market_registry` map; never branch in UI |
| Chart library learning curve | Day 7 boxed; use TV docs + one timeframe |
| Firestore vs files | Week 2 runs in `backend/data/market_runs/BTCUSD/` JSON is fine |

---

## 12. What to do next (Phase 0 start)

**If layout is not decided yet, start here — not the backend checklist.**

1. Fill in §1.1 information architecture table; agree block list with yourself / one user screenshot.  
2. Sketch Layout A vs B; pick one.  
3. `npm install lightweight-charts` → 2-hour chart spike (fake data).  
4. Build static `MarketResearch` + `mockBtcusdResearch.json` (no API).  
5. Sign off Phase 0 exit criteria → then begin Week 1 (§2).

**After Phase 0:** `market_registry.py`, Binance ingest, research API — see Week 1 table.

---

## Revision log

| Date | Change |
|------|--------|
| 2026-06-03 | Initial 2-week plan; BTCUSD first; Binance OHLC v0 |
| 2026-06-03 | Added Phase 0 (layout/presentation) before engineering weeks |
| 2026-06-09 | Current status section; definition-of-done checkboxes updated; links to spec §8.6 / §14.1 |
