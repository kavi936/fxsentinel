# Markets Tab — Product Spec & Planning Doc

**Status:** Active — BTCUSD developer preview in progress  
**Last updated:** 2026-07-08 (linked master vision)  
**Owner intent:** Instrument-centric research dashboards that give **clear directional bias** for day and swing traders—without making users infer direction from Economies + Overview + sentiment separately.

**Product intent (source of truth):** [`MARKETS_MASTER_VISION.md`](./MARKETS_MASTER_VISION.md) — founder vision, priorities, session decisions. This spec expands engineering detail; if they conflict, update the master first.

Related docs:
- **Master vision:** [`MARKETS_MASTER_VISION.md`](./MARKETS_MASTER_VISION.md)
- **BTCUSD implementation strategy:** [`MARKETS_BTCUSD_STRATEGY.md`](./MARKETS_BTCUSD_STRATEGY.md)
- **BTCUSD data research + UI plan:** [`MARKETS_BTCUSD_DATA_AND_UI_PLAN.md`](./MARKETS_BTCUSD_DATA_AND_UI_PLAN.md)
- **Advanced Charts implementation roadmap:** [`MARKETS_ADVANCED_CHARTS_ROADMAP.md`](./MARKETS_ADVANCED_CHARTS_ROADMAP.md)
- **Chart datafeed evaluation (MT5 + Advanced Charts licensing/feasibility):** [`MARKETS_CHART_DATAFEED_EVALUATION.md`](./MARKETS_CHART_DATAFEED_EVALUATION.md)
- **Implementation plan (2-week, BTCUSD first):** [`MARKETS_TAB_IMPLEMENTATION_PLAN.md`](./MARKETS_TAB_IMPLEMENTATION_PLAN.md)
- **Dashboard fonts & colors (Markets should reuse):** [`DASHBOARD_BRANDING.md`](./DASHBOARD_BRANDING.md)
- Prior architecture discussion (agent session, 2026-06-03)
- `docs/FXSentinel_AI_Analysis_Review.md` §0.1 — level labeling deferred until OHLC exists
- `AI_ANALYSIS_FOUNDATION_ROADMAP.md` — `pair_macro_v1` spine profile (later)
- `backend/services/holistic_pair_commentary.py` — pattern for non–copy-paste pair copy
- `backend/services/tradingview_instruments.py` — current instrument catalog

---

## 1. Vision

The **Markets** tab is a set of **tailored research dashboards**—one per tradable market (Gold, EUR/USD or USD/JPY, BTC, etc.)—that combine **quantitative structure** (algorithmic levels from real OHLC), **macro/fundamental context**, and **scheduled catalysts** into a single bias view for **day traders** and **swing traders**. AI (GPT + Gemini) interprets and narrates; it does **not** invent levels. Charts use **TradingView-style** presentation as the visual benchmark. **Analysis runs are global** (one pipeline, same output for every user)—not per-user generation. UI shares **font and FXSentinel branding** with other tabs; layout is **Markets-native** (not a recycle of Overview/Economies card stacks).

### 1.1 North star — data aggregation hub

**Markets is not a chart widget.** It is the **trader-facing reference desk** — one place to see bias, structure, catalysts, and context without jumping tabs. The **data and intelligence live across the app** (Overview, Economies, calendar, news, sentiment); Markets **surfaces** what each market profile needs, assembled server-side.

```text
┌─────────────────────────────────────────────────────────────┐
│  FXSentinel platform (shared backend — build once)          │
│  calendar · news · economies · sentiment · prediction mkts │
│  + venue data (Binance/MT5) · level_engine · GPT runs     │
└───────────────────────────┬─────────────────────────────────┘
                            │ market profile picks relevant slices
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Markets tab (per instrument) — easy referral for traders   │
│  chart + zones + verdict + catalysts + news + cross-assets  │
└─────────────────────────────────────────────────────────────┘
```

**Do not rebuild Overview/Economies inside Markets.** Reuse existing services and APIs; compose them in `market_research_service` (and future `market_context_pack`) per **market profile**.

| Source | Where it lives today | Role in Markets |
|--------|----------------------|-----------------|
| **Binance** (BTC spot) | `ohlc_ingest_binance`, `binance_ticker` | OHLC, live quote, volume/taker, order book, optional futures OI/funding |
| **TradingView scanner** | `tradingview_market_data`, `/api/forex-prices` | Cross-asset quotes; non-crypto pickers later |
| **Economic calendar** | `hybrid_economic_calendar.py`, `/api/economic-calendar` | Catalysts filtered per market profile |
| **Live news cache** | `persistent_news_cache`, `/api/news`, `market_news_filter` | Minimized headline strip (crypto-filtered for BTC) |
| **Market sentiment** | `market_sentiment_service`, `/api/market-sentiment` | Risk-on/off, pair sentiment — verdict input |
| **Economy indicators** | Google Sheets API, `/api/economy-indicators/{country}` | Macro drivers (CPI, rates, growth) for FX/Gold profiles |
| **Economy holistic scan** | `economy_holistic_scan_service`, `/api/economy-scan/{country}` | US/EU/JP bias, drivers, theme highlights |
| **Calendar event analysis** | `enhanced_ai_analysis`, `/api/enhanced-analysis/{id}` | Pre/post-event context when catalyst is imminent |
| **Prediction markets** | `/api/prediction-markets` | Macro probability context (Fed cuts, elections) — optional strip |
| **Central bank docs** | Overview hook `/api/...` (central bank documents) | Policy narrative for FX/Gold — link or digest in thesis |
| **AnalysisContextPack** | `analysis_context_pack.py` | **Existing** shared pack builder for calendar/news/scan — extend for `surface=market_research` |
| **Global GPT runs** (planned) | `market_analysis_pipeline` | Narrative thesis, headline, conviction — allowlisted level IDs only |
| **MT5 / broker OHLC** (later) | Registry stubs | FX and Gold primary candles |

**Differentiation:** A trader can draw PDH/PDL on TradingView themselves. FXSentinel wins by **derived structure** (volume profile, flow, acceptance zones) **fused with macro context** (calendar, news, cross-asset) in a single verdict—not by offering more horizontal lines.

**Principle:** Raw data in → deterministic features → `structured_levels[]` + metrics → GPT narrates probability relative to **allowlisted** IDs only.

### 1.2 Division of responsibility — Quant vs GPT

This is the non-negotiable split for Markets research:

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **Quant system** (background) | *What* exists on the chart: key levels, zones, POIs, volume nodes, invalidation bounds; *why the zone exists mathematically* (stored as `basis`, `source`, optional `feature_metrics`) | Probabilistic language, macro narrative, “what happens if” storytelling |
| **GPT** (global runs) | *Probability* and *thesis*: which allowlisted zone is more likely to be tested first; what it **means** if price taps a zone; day vs swing framing; catalyst/news context | Inventing prices, drawing new zones, renaming levels without a matching `level_id` |

**Quant answers:** “There is a value area from 62,800–63,400 because 70% of 4H volume traded here (`basis: value_area_high/low`, POC at 63,100).”

**GPT answers:** “With spot at 63,050, price is **inside** the rotation zone. **More likely** to probe the upper bound (`btcusd_target_range_*`) before a sustained break of prior day low (`btcusd_pdl_*`), unless US CPI in 6h shifts risk-off — **medium conviction**, day horizon.”

**When a zone is tapped:** Quant flags the event (spot crossed into range, tagged level hit — future: `zone_events[]` in research payload). GPT **explains** whether the tap confirms or rejects the prior thesis using only allowlisted IDs + calendar/news.

**Validation rule:** Any price or zone in GPT output must map to an entry in `structured_levels[]` or `invalidation[]`. Prose that cites “support near 62k” without `level_id` is rejected.

**Why this matters:** Traders can get levels anywhere. FXSentinel’s edge is **curated structure + interpreted probability + macro context in one place** — not GPT guessing S/R.

### 1.3 Markets tab vs platform data — referral surface, not silo

**Markets is where traders look.** **The app is where the data lives.**

| Principle | Detail |
|-----------|--------|
| **One backend composition layer** | `market_research_service` (and GPT `market_context_pack`) **pulls from existing services** — same modules Overview/Economies/calendar analysis already use |
| **Market profile = wiring diagram** | Each instrument declares which platform sources matter (see §12). BTC weights news + risk assets; EURUSD weights US+EU scans + ECB/FOMC calendar |
| **No tab-exclusive APIs for shared facts** | Calendar events, economy bias, sentiment should not be re-fetched differently on Markets vs Overview — one cache, one truth |
| **Deep links optional** | Markets can link “Full calendar”, “US economy scan”, “Event analysis” for power users — but **default view must stand alone** |
| **Quant still venue-specific** | Binance/MT5 structure is computed in `level_engine`; macro context is **fused at research assembly + GPT**, not drawn on chart |

**Today’s gap:** Markets uses Binance + partial news + TV cross-assets. It does **not** yet consume economy holistic scans, calendar filters, market sentiment, or `AnalysisContextPack` — that wiring is the next platform integration step (before or alongside GPT runs).

**Target assembly flow:**

```text
market_profile (BTCUSD.json)
       │
       ├── level_engine + feature_engine  → structured_levels[]
       ├── hybrid_economic_calendar       → catalysts[]     (filtered)
       ├── persistent_news_cache          → news[]          (filtered)
       ├── market_sentiment_service       → risk_regime     (snapshot)
       ├── economy_holistic_scan (US…)    → macro_digest[]  (profile-defined countries)
       ├── tradingview / forex-prices     → cross_assets[]
       └── analysis_context_pack          → unified prompt context for GPT
                    │
                    ▼
           GET /api/markets/:id/research
```

**Reuse note:** `analysis_context_pack.py` already builds shared context for calendar, live news, and economy scan surfaces (`SURFACE_CALENDAR`, `SURFACE_LIVE_NEWS`, `SURFACE_ECONOMY_SCAN`). Add `SURFACE_MARKET_RESEARCH` with `market_id` + `structured_levels` + profile filters — do not fork a parallel pack builder.

## 2. Launch market candidates

### 2.1 Current shortlist (founder + Instagram feedback)

| Market | Internal id (today) | Asset class | Notes |
|--------|---------------------|-------------|--------|
| **Gold** | `GOLD` (`COMEX:GC1!` on TV) | Commodity / safe haven | Different driver template (real yields, USD, geopolitics)—not a FX clone |
| **EUR/USD** *or* **USD/JPY** | `EURUSD` / `USDJPY` | G10 FX | Pick one for v0 if scope is tight; both are already in ticker + pair commentary |
| **Bitcoin** | **`BTCUSD`** (display) → feeds **`BTCUSDT`** | Crypto | **First implementation market** — see implementation plan |

**EUR/USD vs USD/JPY (v0):** Document both profiles, ship **one** first unless Instagram feedback strongly favors JPY. Rationale: EUR/USD ties cleanly to existing US + EUR Economies data; USD/JPY adds risk/yield/BoJ narrative diversity.

### 2.2 Expansion gate: Instagram / user feedback

- Treat social feedback as **priority input** for the 4th/5th market (e.g. GBP/USD, Oil, ETH)—not as automatic scope creep.
- Suggested rule: add a market only when there is (a) a written **market profile**, (b) OHLC ingestion for that symbol, and (c) deterministic level pipeline passing QA.

### 2.3 Evaluation: shortlist vs codebase

| Check | Result (2026-06-09) |
|-------|------------------------|
| Live quotes | ✅ Binance BTCUSDT for BTCUSD chart + picker; TV for cross-assets + disabled markets |
| OHLC / levels | ✅ Binance klines → `ohlc_store`; `level_engine_v0` shipped |
| Research API | ✅ `GET /api/markets/BTCUSD/research` — deterministic verdict/headline |
| Live quote API | ✅ `GET /api/markets/BTCUSD/quote` — Binance 24hr ticker, 5s server cache |
| Global GPT runs | ❌ `latest_run: null`; narrative is deterministic fallback |
| Catalysts | ❌ API returns empty array — not wired |
| Pair-specific copy pattern | ✅ `holistic_pair_commentary.py` — extend to **market profiles** |
| Tab access | 🟡 **Developer-only** gate (`isDeveloper`); others see coming soon |
| Economies overlap | Gold needs **rates/USD** legs, not a full “Choose Economy” embed |

---

## 3. User outcomes

### 3.1 Who we serve

| Persona | Horizon | What “success” looks like on Markets tab |
|---------|---------|------------------------------------------|
| **Day trader** | Minutes–hours | Clear **intraday bias**, key levels for today/session, next high-impact events today, invalidation |
| **Swing trader** | Days–weeks | **Structural bias**, swing-relevant levels, catalyst calendar for the week, macro thesis |

Same page should expose **horizon toggles or sections** (Day / Swing)—not two separate products.

### 3.2 What we are not building (v1)

- Trade execution, position sizing as advice, or guaranteed signals
- Generic “one dashboard fits all instruments” prose
- AI-generated support/resistance without quantitative backing

---

## 4. Core product principles

1. **Quant levels in, narrative out** — Levels come from an **in-house algorithm** on OHLC; GPT/Gemini only describe *probability / context* relative to those levels (“more likely to test X before Y”).
2. **Honest data lineage** — Every level shows `basis`, `as_of`, `source` (see `FXSentinel_AI_Analysis_Review.md` Phase B/C).
3. **Tailored, not templated** — Each market has a **profile** (drivers, cross-assets, calendar filters, narrative frame). Reuse UI shell; differ content (see `holistic_pair_commentary` model).
4. **Visual benchmark: TradingView** — Charts, colors, candle semantics, and density should feel familiar to TV users.
5. **Branding consistency, not card recycling** — Same **font family**, color tokens, navbar, and FXSentinel identity as Economies/Overview. **Do not** reuse Overview/Economies card components as the default layout—that reads as generic “vibecoded” dashboard UI. Use cards **only where they earn their place** (e.g. one verdict block, one news strip); prefer clean sections, chart-first hierarchy, purposeful spacing.
6. **One truth for all users** — Scheduled analysis runs execute **once centrally**; every user sees the same bias, levels snapshot, and chart overlays for that run (no per-user GPT calls for Markets research—avoids discrepancy and bias drift between accounts).
7. **Filtered catalysts, minimized news** — Economic calendar can appear in a **market-relevant** catalyst section (not “minimized” as a product goal). **Live news** is the section to keep **small**: few headlines, market-filtered, beside analysis—not a full Live News Feed embed.

---

## 5. Page layout (target)

Shared shell per market; section **content** comes from market profile + APIs.

```
┌─────────────────────────────────────────────────────────────┐
│ Market picker: Gold | EUR/USD | BTC | …                     │
├─────────────────────────────────────────────────────────────┤
│ VERDICT: Bias + lean + conviction | Day / Swing summary     │
│ Updated: <as_of>  •  Analysis run #N today                │
├─────────────────────────────────────────────────────────────┤
│ CHART (TV-style) — primary surface                          │
│   • POIs, price ranges, levels (algorithmic)                │
│   • Past analysis zones + run markers                       │
├─────────────────────────────────────────────────────────────┤
│ FUNDAMENTAL THESIS (market-specific drivers)                │
├─────────────────────────────────────────────────────────────┤
│ CROSS-ASSET STRIP (profile-defined instruments)             │
├─────────────────────────────────────────────────────────────┤
│ CATALYSTS — calendar filtered to this market (§10.1)        │
├─────────────────────────────────────────────────────────────┤
│ LIVE NEWS — compact, market-filtered strip (§10.2)          │
├─────────────────────────────────────────────────────────────┤
│ AI ANALYSIS — global run output (§7)                        │
├─────────────────────────────────────────────────────────────┤
│ INVALIDATION & RISKS                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Data & OHLC strategy

### 6.1 Proposed source: MT5 + MQL5

**Idea:** Use broker data via MetaTrader 5 trading account(s) and MQL5 ecosystem (scripts, library, or exported history) to pull OHLC.

| Pros | Cons / risks |
|------|----------------|
| Real executable prices from broker you trust | **Ops:** MT5 terminal or bridge must run 24/5 (FX) / extended (crypto/gold) |
| Consistent with how many retail traders actually trade | **Multi-symbol:** Gold/XAU, BTC, FX may need different brokers or symbols |
| Potential cost advantage vs commercial REST APIs | **Backend integration:** Not a simple REST key—need bridge (Python `MetaTrader5` package, custom EA exporting bars, or scheduled CSV drop) |
| | **Compliance / ToS:** Confirm broker + MQL5 redistribution terms for displayed data |
| | **Latency & gaps:** Session breaks, broker maintenance, symbol mapping (`BTCUSD` vs `BTCUSDT`) |

### 6.2 Recommended architecture (when validating)

```
MT5 terminal(s) / EA or Python MetaTrader5
        ↓
  bar_ingest_job (scheduled: 1m/5m/1h/1d per market)
        ↓
  ohlc_store (DB or versioned JSON — pair, timeframe, ts, O,H,L,C,V)
        ↓
  level_engine (deterministic: prior day H/L/C, swings, zones — versioned)
        ↓
  structured_levels[]  →  AnalysisContextPack  →  GPT/Gemini prompts
        ↓
  Markets API + chart API
```

**Display quotes:** Can remain **TradingView scanner** (`fetch_tradingview_quotes`) for ticker consistency while OHLC comes from MT5—document any **basis risk** if TV symbol ≠ MT5 symbol.

### 6.3 Alternative / fallback providers (validation checklist)

| Provider type | Use when |
|---------------|----------|
| MT5/MQL5 | Primary if bridge is stable within 2 weeks of spike |
| OANDA / FXCM / Polygon / Twelve Data REST | Fallback if MT5 ops cost is too high |
| TradingView **Lightweight Charts** + **licensed** bar feed | UI only; bars still need a legal data source (`docs/TRADINGVIEW_API_ACCESS_GUIDE.md`) |

### 6.4 Timeframes for level engine (initial)

| Timeframe | Day trader | Swing trader |
|-----------|------------|--------------|
| Daily | Prior H/L/C, weekly context | Primary structure |
| 4H / 1H | Intraday zones | Swing pivots |
| 15m (optional v2) | Session levels | Usually noise for swing |

Ship **daily + 4H** first; expand after MT5 pipeline is stable.

---

## 7. AI analysis cadence (GPT + Gemini)

### 7.1 Stated intent

- Run combined analysis **2–6 times per day**; **6** is the current working target.
- Models: **GPT** (existing OpenAI path via `finalize_analysis` / context pack) + **Gemini** (already used for news grounding—`gemini_news_grounding_service.py`).

### 7.1.1 Global runs (critical — not per user)

| | Global (intended) | Per-user (not doing) |
|---|------------------|----------------------|
| **Who triggers** | Backend cron / worker **once** per schedule slot | User opens tab or “Refresh analysis” |
| **Who sees output** | All users get **identical** `market_analysis_run` for that market + slot | Different bias/levels per account |
| **Why** | One editorial truth; no “my GPT said bullish, yours said bearish” | Personalization belongs elsewhere (e.g. alert pairs), not Markets research body |
| **Cost** | `6 runs × N markets` per day total | Would multiply by MAU — unacceptable |

Implementation sketch:

- `market_analysis_scheduler` writes to `markets/{market_id}/runs/{run_id}` (or equivalent).
- API: `GET /api/markets/:id/research` returns **latest published run** (+ optional history).
- Frontend: read-only; no “generate my analysis” button in v1.
- Optional later: user **display** prefs only (hide news strip, default Day vs Swing tab)—not different AI output.

### 7.2 Evaluation & suggested split

| Role | Suggested model | Rationale |
|------|-----------------|-----------|
| **Structured narrative + bias** | GPT | Mature pipeline: context pack, validators, personalization |
| **Grounding / fresh web context** | Gemini + Google Search | Already spiked for news; useful for intraday headline shifts on Gold/BTC |
| **Levels / math** | Neither | Deterministic `level_engine` only |

**6 runs / day (example schedule—validate against cost):**

| Run | UTC intent | Focus |
|-----|------------|--------|
| 1 | Pre-Asia | Reset: overnight context, Asia liquidity |
| 2 | Pre-London | European open bias |
| 3 | Pre-NY | US catalyst window |
| 4 | Mid-NY | Post-data revision if events released |
| 5 | NY close | Day-trader summary + swing update |
| 6 | End of day | Archive + chart labels for “previous analysis” |

**Open decisions:**
- Same 6 UTC slots for all markets vs staggered per asset session (e.g. extra Gold run on London open)
- Whether Gemini runs on every global slot or only when news/calendar triggers fire
- Store each run as `market_analysis_run` with `run_id`, `model_trace`, `structured_levels_snapshot`, `chart_overlays` (POI + ranges)

**Cost model (corrected):**  
`daily_cost ≈ runs_per_day × markets_enabled × (GPT + optional Gemini)` — **not** × user count.

### 7.3 Prompt contract (aligns with review doc §0.1)

GPT/Gemini instructions must include:

- `structured_levels` allowlist — **only** cite `level`, `poi`, and `range` IDs from the engine output (no ad-hoc zones)
- Bias vocabulary — reuse `analysis_bias_classification` (true neutral, leans)
- Forbidden: inventing “swing low” without `basis` in data
- Output: “more likely to gravitate toward {level_id} before {level_id}” with probabilities as **qualitative** unless backtested

---

## 8. Level engine (quantitative edge → AI input only)

### 8.1 Principle

> Compute or algorithmically determine levels for a quantitative edge; give those levels **only** to GPT so it can say price is *more likely* to go toward X—not to discover X.

### 8.2 Phase A — MVP algorithms (deterministic, testable)

| Level type | Inputs | Example `basis` label |
|------------|--------|------------------------|
| Prior day high/low/close | Daily OHLC | `prior_day_high` |
| Weekly high/low | 5× daily | `weekly_high` |
| Round numbers | Spot | `illustrative_round` (tagged non-structural) |
| Simple swing | Local extrema on 4H window | `swing_high_4h` (Phase B+) |
| **Point of interest (POI)** | Confluence rules (e.g. swing + prior close cluster) | `poi_confluence` |
| **Price range / zone** | Algorithmic band (e.g. value area, ±X% from structure, session range) | `target_range`, `supply_zone`, `demand_zone` |

**POI** = discrete price the engine flags as reaction-likely (single price or tight band).  
**Price range** = zone where analysis expects price **may trade** (upper/lower bound); GPT may say “more likely to rotate inside range A before breaking B”—ranges must still originate from `level_engine`, not free-form GPT boxes.

Each level object:

```json
{
  "level_id": "eurusd_pdh_20260603",
  "kind": "level",
  "price": 1.09234,
  "basis": "prior_day_high",
  "timeframe": "1D",
  "as_of": "2026-06-03T21:00:00Z",
  "source": "mt5_broker_x",
  "strength": 0.72
}
```

Range object (chart + GPT allowlist):

```json
{
  "level_id": "gold_target_range_20260603",
  "kind": "range",
  "price_low": 3320.0,
  "price_high": 3355.0,
  "basis": "session_value_zone_4h",
  "label": "Expected rotation zone",
  "horizon": "day",
  "as_of": "2026-06-03T14:05:00Z",
  "source": "level_engine_v1"
}
```

### 8.3 What GPT receives

- Full `structured_levels[]` — each with `level_id`, `kind`, `basis`, `price` or `price_low`/`price_high`, `as_of`, `source`
- Optional **`feature_metrics`** per level (v1+) — e.g. `{ "volume_pct": 0.18, "taker_buy_pct": 0.62 }` so GPT can explain *why* the quant system flagged a zone without inventing math
- Distance from spot (%)
- Optional: `zone_events` — which levels/ranges were tapped since last run
- Optional: historical hit rate placeholder (future quant work)
- Catalyst + news summaries + cross-asset snapshot
- **Not** raw OHLC arrays in prompt (token cost)—summaries only

### 8.4 What GPT is asked to output (thesis + probability)

| Output field | GPT job | Quant job |
|--------------|---------|-----------|
| `headline` | One-line bias + key zone in play | — |
| `verdict.bias` / `display_bias` | Classify lean (reuse Overview bias vocabulary) | — |
| `verdict.day_summary` / `swing_summary` | Probabilistic path: “more likely A before B” citing `level_id`s | — |
| `thesis.body` | Why zones matter **now** (macro, flow, catalyst proximity) | Zones themselves |
| `levels_cited[]` | Subset of allowlist IDs referenced in copy | Full allowlist |
| `invalidation` | Narrate what break **disproves** the call | Price levels for invalidation |

Probabilities stay **qualitative** (high / medium / low, or “more likely / less likely”) unless backtested hit rates exist.

### 8.5 Validation gates before production

- [ ] Unit tests: same OHLC → same levels every run
- [ ] Validator strips GPT prose that cites prices not in allowlist
- [ ] UI shows basis tooltip on hover

### 8.6 Shipped today — `level_engine_v0` (honest assessment)

**File:** `backend/services/markets/level_engine.py`  
**Status:** Good **scaffold**, not a product moat.

| Output | `basis` | Limitation |
|--------|---------|------------|
| Prior day H/L/C | `prior_day_high`, `prior_day_low`, `prior_day_close` | Commodity — any trader draws these |
| Weekly H/L | `weekly_high`, `weekly_low` | Same |
| 4H rotation zone | `session_value_zone_4h` | Simple session box, not volume profile |
| 4H swing H/L | `swing_high_4h`, `swing_low_4h` | Basic extrema |
| Round-number POI | `poi_confluence` | PDH near $1k round only |

**Ingest gap:** `ohlc_ingest_binance.py` currently stores only O/H/L/C/volume. Binance klines also return **quote volume, trade count, taker buy volume** — discarded today. Enriching the store is **P0** for v1.

### 8.7 `level_engine_v1` — differentiation roadmap

**Goal:** Derived structure a solo TradingView user cannot replicate trivially, still deterministic and allowlisted for GPT.

#### Layer 1 — Volume structure (from enriched klines; no new API)

| Feature | Trader use | Chart `kind` | Example `basis` |
|---------|------------|--------------|-----------------|
| Volume POC + VAH/VAL | Where value traded; magnet prices | `poi`, `range` | `volume_poc`, `value_area_high`, `value_area_low` |
| High / low volume nodes (HVN/LVN) | Magnets vs air pockets | `poi` | `hvn`, `lvn` |
| Volume-confirmed levels | PDH promoted only if rejection had top-quintile volume | upgrades `level` → `poi` | `volume_confirmed_pdh` |
| Taker delta zones | Aggressive buy/sell imbalance bands | `range` | `taker_demand_zone`, `taker_supply_zone` |

#### Layer 2 — Order book microstructure (spot REST, cached 30–60s)

| Feature | Endpoint | Chart / aside |
|---------|----------|---------------|
| Bid/ask imbalance | `GET /api/v3/depth` | Aside metric + verdict input |
| Liquidity walls | same | `poi` — `liquidity_wall_bid`, `liquidity_wall_ask` |
| Spread stress | `GET /api/v3/ticker/bookTicker` | Headline flag when fragile |

#### Layer 3 — Regime & acceptance (pure OHLC math)

| Feature | Trader use | `basis` |
|---------|------------|---------|
| Opening range (OR) | First 1H UTC (or NY) H/L — day anchor | `opening_range` |
| Acceptance vs rejection | Close spent >60% above PDH → breakout **zone** not just line | `accepted_breakout_zone` |
| ATR-scaled invalidation | Invalidation at structure − 0.5× 4H ATR | feeds `invalidation[]` |

#### Layer 4 — Crypto positioning (Binance futures public API, optional)

| Feature | Endpoint | Use |
|---------|----------|-----|
| Open interest change | `fapi/v1/openInterest` | Leveraged vs spot-led move |
| Funding rate | `fapi/v1/premiumIndex` or funding history | Crowded long/short |
| Spot vs perp basis | spot − perp | Which venue leads |

Display in **aside + headline**, not as chart clutter by default.

#### Layer 5 — FXSentinel fusion (core moat)

Combine venue microstructure with data only FXSentinel already has:

| Signal | Source | Effect on verdict |
|--------|--------|-------------------|
| Catalyst proximity | Economic calendar | Widen ranges / lower breakout conviction before FOMC/CPI |
| News burst | `market_news_filter` | Flag headline-driven tape |
| Cross-asset confirmation | TV quotes in research | Downgrade BTC break without ETH/DXY/VIX alignment |

#### Architecture (target)

```text
Binance klines (enriched) ──┐
Binance depth (cached)   ──┼──► feature_engine.py ──► structured_levels[]
Futures OI/funding       ──┘         │
                                       ├──► level_engine (merge + rank)
Calendar / news / TV   ──────────────┘
                                       │
                                       ▼
                              GET /research + chart overlays
                                       │
                                       ▼
                              GPT cites allowlisted level_ids only
```

Split **`feature_engine`** (raw transforms) from **`level_engine`** (which features become chart objects). v0 remains; v1 adds without breaking API shape.

#### v1 build priority (max differentiation / min Railway cost)

| Priority | Deliverable | New external calls |
|----------|-------------|---------------------|
| **P0** | Enrich kline store: taker buy, quote vol, trade count | None (already in klines) |
| **P1** | 5-day volume POC + VAH/VAL on 4H | Derived |
| **P2** | Taker delta supply/demand zones | Derived |
| **P3** | Volume-confirmed PDH/PDL promotion | Derived |
| **P4** | Opening range + acceptance bands | Derived |
| **P5** | Order book walls (cached depth) | ~1 REST / 60s per market |
| **P6** | Funding + OI context | Futures REST, low frequency |

**Defer:** sub-minute WebSocket streams, full DOM heatmap, ML — overkill for v1.

#### UI — “Research overlays” not “Indicators”

Future layer toggles (evolve from current Levels / POI / Ranges):

| Toggle | Content |
|--------|---------|
| **Structure** | PDH/PDL, swings (v0) |
| **Volume profile** | POC, VAH/VAL, HVN |
| **Flow** | Delta zones, book imbalance |
| **FXSentinel runs** | Past analysis areas (when GPT pipeline exists) |

Default on: **Structure + Volume profile** only (clutter control per §9.4).

---

## 9. Chart overlays & labels

The chart is the **hero** of the Markets tab—not a widget inside a card grid. All labels below are **data-driven** (engine and/or published global runs), then optionally annotated in prose by GPT.

### 9.1 Chart UI — research chart (decided)

**Product intent:** A **FXSentinel research chart** — our bars, our overlays, our findings visualized for actionable insight. **Not** a TradingView workstation. Users who want drawing tools, indicators, and full charting use their own TV account; this chart is where **we** show what our pipeline computed.

| In scope | Out of scope (v1) |
|----------|-------------------|
| Live + historical OHLC, TV-like candle formatting | User drawing tools (trendlines, fib, annotations) |
| **System** levels, POI, ranges, analysis areas (from `level_engine` + global runs) | User-added indicators / studies |
| Layer toggles (levels, POI, ranges, past runs) | Symbol search / compare / multi-chart layouts |
| Hover tooltips: `basis`, `as_of`, level id | Trade execution or order placement |
| Read-only pan/zoom/timeframe | Editable chart markup |

**Library:** **TradingView Lightweight Charts** (MIT) — see `docs/TRADINGVIEW_API_ACCESS_GUIDE.md`. TV-like presentation without Advanced Charts licensing or UDF complexity. The current **embed widget** remains a temporary layout placeholder until Lightweight Charts ships.

**Data:**
- **Candles:** `ohlc_store` (Binance v0 for BTC; MT5 or REST for FX/Gold when ready) — not scanner tickers alone.
- **Live:** Append/update the forming bar on a schedule (e.g. 15–60s poll or push); full tick streaming deferred unless needed.
- **Analytics:** Same OHLC store (+ derived series) exposed to `level_engine`, comparison jobs, and GPT context — chart is one **consumer**, not the source of truth.

**Typography / chrome:** FXSentinel fonts and brand colors; dark grid/candle conventions per `DASHBOARD_BRANDING.md`. **Implemented (2026-06-09):** warm red-black chart theme (`#120809` canvas, red-tinted grid/borders, branded toolbar) — see `marketChartTheme.js`, `MarketsChart.css`.

### 9.1.1 Chart toolbar (implemented)

Replaced 10 inline buttons (7 timeframes + 3 layers) with compact controls:

| Control | Behavior |
|---------|----------|
| **Timeframe pill** | Shows active TF (e.g. `4H`) + chevron; dropdown overlays chart pane |
| **Layers icon** | Stack icon + badge when not all layers on; checkbox menu for Levels / POI / Ranges |
| **Live quote** | Right-aligned BTCUSDT price + daily % (Binance) |

Menus render **over the chart** (top-left portal), not in a crowded header row. Escape / click-outside dismisses.

**Timeframes shipped:** 15m, 30m, 1H, 2H, 4H, 1D, 1W — up to 1000 bars per request (Binance max).

### 9.1.2 Live data paths (BTCUSD)

| Surface | Source | Refresh |
|---------|--------|---------|
| Chart candles | Binance klines via `ohlc_store` | Frontend poll ~30s; backend re-ingest when cache ≥30s |
| Chart toolbar + picker price | `GET /api/markets/BTCUSD/quote` | Frontend poll 5s; **server cache 5s** (one Binance call shared across clients) |
| Headline spot | Binance via `/research` | Research poll ~90s |
| Cross-assets in aside | TradingView scanner | Via research payload |

**Single quote hook:** `MarketsHub` polls once; passes `liveQuote` to chart (avoids duplicate requests).

**Cost note (Railway):** WebSocket for sub-second ticks is a **UX** upgrade, not a cost saver. Prefer server-side quote cache + optional **client-side Binance WS** for live price if sub-second needed later. Backend WebSocket proxy only worth it at high concurrent user counts.

### 9.2 Overlay types (what appears on the chart)

| Overlay type | Source | Visual (TV-style) | Purpose |
|--------------|--------|-------------------|---------|
| **Levels** | `level_engine` | Horizontal lines | PDH/PDL, swings, etc. |
| **POI (points of interest)** | `level_engine` | Marker / cross / dot + short label | “Reaction likely” prices (confluence) |
| **Price ranges / zones** | `level_engine` | Shaded band between `price_low`–`price_high` | Where price **may trade** (day/swing target zones—not GPT-drawn rectangles) |
| **Past analysis area** | Global `market_analysis_run` | Shaded time–price region or bounded box active for that run’s validity window | “What we called when” — spatial context, not only a timestamp tick |
| **Run marker** | Same run record | Vertical line at `created_at` + optional flag | Pin when a global run published |

**GPT’s role on ranges:** Narrate probability *inside / between* allowlisted range IDs (“more likely to reach upper bound of `gold_target_range_*` before breaking `gold_pdh_*`”). It does not create new bounds.

### 9.3 Past analysis areas (not just timestamp pins)

When a **global run** publishes, persist geometry + narrative hook:

```json
{
  "market_id": "GOLD",
  "run_id": "uuid",
  "created_at": "2026-06-03T14:05:00Z",
  "valid_until": "2026-06-03T21:00:00Z",
  "spot_at_run": 3342.5,
  "bias": "bearish",
  "display_bias": "NEUTRAL · BEARISH LEAN",
  "label_short": "Lean lower into PDH retest",
  "levels_cited": ["gold_pdh_20260603", "gold_swing_low_4h_1"],
  "ranges_cited": ["gold_target_range_20260603"],
  "pois_cited": ["gold_poi_3328"],
  "analysis_area": {
    "price_low": 3320.0,
    "price_high": 3355.0,
    "time_start": "2026-06-03T14:05:00Z",
    "time_end": "2026-06-03T21:00:00Z"
  }
}
```

Render as:
- **Area:** semi-transparent rectangle (time × price) for `analysis_area` while valid
- **Marker:** vertical line at `created_at` with tooltip (bias, summary, link to run detail)
- **Toggle:** user can show/hide “Past runs” and “POI / ranges” layers to reduce clutter

**Storage:** Global runs in `markets/{id}/runs/{run_id}` (Firestore or DB)—single source read by all users.

**Clutter control:** Default chart shows **current** POI/ranges/levels; past analysis areas off or last 2–3 runs only; full history in a side list.

### 9.4 Evaluation

- ✅ POI + ranges make “where could it go” visible without reading paragraphs
- ✅ Past **areas** communicate regime context better than a lone vertical line
- ⚠️ Too many shaded zones → require layer toggles and strict engine rules on overlap

---

## 10. Calendar & live news integration

### 10.1 Calendar (catalysts) — market-filtered, not “minimized”

Clarification: the founder did **not** ask for a shrunk calendar as the main idea; the **live news** slice is what should stay small (§10.2).

- Reuse hybrid calendar backend (`hybrid_economic_calendar.py`) with **market profile filters**:
  - Gold: US CPI, FOMC, real yields, geopolitical tags, DXY proxy events
  - EUR/USD: FOMC, ECB, US/EU CPI & employment
  - BTC: FOMC, risk sentiment; calendar thinner, news carries more weight
- UI: **market-relevant** upcoming events (e.g. next 3–7 days, high impact)—purpose-built section, not a dumbed-down Overview calendar grid. Density TBD in wireframes; goal is **clarity for this instrument**, not minimalism for its own sake.

### 10.2 Live news — minimized section (explicit product goal)

- **Not** the full Overview Live News Feed (no infinite scroll, no large cards).
- **Compact strip** in the analysis column: e.g. **3–5 headlines**, market-filtered via `relevant_market_context` logic.
- Headlines support intraday context for the **current global run**; optional Gemini grounding on breakers (reuse `gemini_news_grounding_service` patterns).
- Visual: single slim block—title + source + time—**Markets-native** styling (§11), not recycled news cards.

### 10.3 Cross-app data inventory (reuse, don’t duplicate)

Platform endpoints and services Markets should consume **server-side** (not reimplemented in React):

| Data | Backend / service | API (frontend today) | Markets profile use |
|------|-------------------|----------------------|---------------------|
| Economic calendar | `hybrid_economic_calendar.py` | `GET /api/economic-calendar` | `catalysts[]` — filter by profile tags |
| Live news | `persistent_news_cache`, news pipeline | `GET /api/news` | `news[]` — `market_news_filter` / `relevant_market_context` |
| Forex + cross-asset quotes | `tradingview_market_data` | `GET /api/forex-prices` | `cross_assets[]` ✅ partial |
| Market sentiment | `market_sentiment_service` | `GET /api/market-sentiment` | Risk regime in verdict / GPT pack |
| Economy indicators | Google Sheets integration | `GET /api/economy-indicators/{country}` | Driver snapshot for FX/Gold |
| Holistic economy scan | `economy_holistic_scan_service` | `POST /api/economy-scan/{country}` | Macro bias digest (US for BTC risk, US+EU for EURUSD) |
| Scan history | `economy_holistic_scan_store` | `GET /api/economy-scan-history` | “Last US scan said…” in thesis |
| Calendar event AI | Enhanced analysis pipeline | `GET /api/enhanced-analysis/{id}` | Catalyst row expansion / GPT context |
| Prediction markets | Prediction markets service | `GET /api/prediction-markets` | Optional macro probability chip |
| Central bank documents | Central bank docs service | Overview hook | Policy citations in swing thesis |
| Shared analysis pack | `analysis_context_pack.py` | (internal) | GPT global run input |
| Venue OHLC + quote | `ohlc_store`, `binance_ticker` | `GET /api/markets/.../ohlc`, `/quote` | Chart + quant ✅ |

**Implementation rule:** New Markets features should add a **row to the market profile** (“pull US holistic scan if age < 72h”) and a **function in `market_research_service`**, not a new frontend-only fetch in `MarketsHub`.

### 10.4 Example — BTCUSD pulls from the rest of the app

| Platform source | Why BTC cares |
|-----------------|---------------|
| US holistic scan | Risk appetite / liquidity narrative |
| `market_sentiment` | Cross-pair risk-on/off |
| FOMC + US CPI from calendar | Dominant macro catalysts for crypto |
| Crypto-filtered news | Idiosyncratic BTC shocks |
| ETH, SPX, VIX, US10Y, GOLD quotes | Confirmation or divergence vs BTC structure |
| Binance volume/delta (v1) | Venue-specific structure GPT explains |

EURUSD (later) would swap in US **+ EU** scans, ECB/FOMC calendar filters, and `holistic_pair_commentary` tokens — **same shell, different profile wiring**.

---

## 11. UI / UX — branding without “vibecoded” card stacks

### 11.1 What we share with other tabs

| Element | Shared |
|---------|--------|
| Font stack & scale | Yes — same as dashboard |
| Color tokens (dark bg, red accent, muted text) | Yes |
| Top navbar / tab chrome | Yes |
| Legal / educational disclaimer tone | Yes |
| Optional: `FormattedScanParagraph` / emphasis in **analysis prose** only | Yes, where long-form text appears |

### 11.2 What we deliberately do not copy

| Element | Approach |
|---------|----------|
| Overview/Economies **card grids** as default layout | **No** — reads generic and “vibecoded” |
| Live News Feed card UI | **No** — use minimized news strip (§10.2) |
| Holistic scan card stack | **No** — Markets has its own section rhythm |

### 11.3 Markets-native layout principles

- **Chart-first:** largest visual weight on price + overlays (§9).
- **Cards sparingly:** e.g. one verdict block or one catalyst block if it helps scanability—not every section in a rounded rectangle.
- **Purposeful density:** trader terminal feel (TV benchmark), not marketing landing page blocks.
- **Market picker:** simple instrument selector (dropdown or tabs)—function like Economies selector, **visuals not cloned** from `economies-main-card`.

### 11.4 Anti-patterns to avoid in design review

- Identical card + icon + bullet templates repeated six times down the page
- Gradient orbs / glassmorphism stacks copied from “coming soon” placeholder (`Markets.jsx` today is fine for launch marketing, not for shipped research UI)
- Per-user “Your analysis” framing when output is global (§7.1.1)

---

## 12. Market profiles (draft sketches)

Profiles live in config (JSON or Python) per instrument—**required before** GPT narrative.

### 12.1 Gold (`GOLD`)

- **Drivers:** Real yields (US10Y), USD strength, risk-off flows, geopolitical premium
- **Cross-assets:** `US10Y`, `US02Y`, `EURUSD`, `VIX`, `USOIL`
- **Calendar:** FOMC, US CPI/PCE, major geopolitical (manual tags)
- **Narrative frame:** “Is gold driven by rates, USD, or fear—and which channel dominates today?”
- **Day vs swing:** Day = session range + prior day; Swing = weekly structure + Fed path

### 12.2 EUR/USD (`EURUSD`)

- **Drivers:** Fed–ECB policy divergence, growth surprise, risk sentiment
- **Cross-assets:** `EU10Y`, `US10Y`, `EURGBP`, `VIX`
- **Calendar:** FOMC, ECB, NFP, US/EU CPI
- **Narrative frame:** “Who is relatively more dovish—and is it priced?”
- **Reuse:** `PAIR_REQUIRED_TOKENS` / `holistic_pair_commentary` for EUR leg

### 12.3 USD/JPY (`USDJPY`) — if chosen over EUR for v0

- **Drivers:** Yield spread, BoJ intervention risk, risk-on/off, Nikkei correlation
- **Cross-assets:** `JP10Y`, `US10Y`, `SPX`, `VIX`, `GOLD`
- **Calendar:** BoJ, FOMC, US CPI, Tankan / JP CPI
- **Narrative frame:** “Yield gap + risk regime vs yen intervention threat”

### 12.4 Bitcoin (`BTCUSDT` / `BTCUSD`)

- **Drivers:** Risk appetite, USD liquidity, ETF/flow narrative, regulatory news
- **Cross-assets:** `ETHUSDT`, `SPX`, `VIX`, `US10Y`, `GOLD`
- **Calendar:** Thin—weight **news** filter higher
- **Symbol alignment:** Resolve `BTCUSD` vs `BTCUSDT` for MT5 and TV catalog
- **Narrative frame:** “Risk-on liquidity vs crypto-specific shock”

---

## 13. API & backend sketch (for validation)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/markets` | List enabled markets + metadata |
| `GET /api/markets/:id/research` | Verdict, levels, thesis, events, latest run summary |
| `GET /api/markets/:id/ohlc?tf=1D` | Candles for chart |
| `GET /api/markets/:id/quote` | Live spot quote (Binance for crypto) |
| `GET /api/markets/:id/analysis-runs` | History for chart markers |
| `POST /api/markets/:id/analyze` (internal/cron) | Trigger GPT+Gemini run |

Services (proposed + shipped):

- `market_research_profiles/` — per-market config (registry in code today; JSON profiles TBD)
- `market_research_service.py` — assemble DTO ✅
- `market_quote_service.py` + `binance_ticker.py` — live quote ✅
- `ohlc_ingest_binance.py` — ingestion ✅
- `ohlc_store.py`, `udf_datafeed.py` — read/serve bars ✅
- `level_engine.py` — deterministic levels v0 ✅
- `market_news_filter.py` — BTC headline filter ✅
- `feature_engine.py` — **planned** — volume profile, delta, book features
- `market_context_service.py` — **planned** — compose cross-app snapshots per profile (calendar, scans, sentiment)
- Extend `analysis_context_pack.py` — **`SURFACE_MARKET_RESEARCH`** for GPT runs
- `ohlc_ingest_mt5.py` — ingestion (spike first)
- `market_analysis_pipeline.py` — `finalize_analysis(..., analysis_kind="market_research")`

---

## 14. Phased rollout (validation order)

| Phase | Deliverable | Blocker |
|-------|-------------|---------|
| **V0 — Doc + profiles** | This doc + 3–4 market profile JSON drafts | — |
| **V1 — MT5 spike** | 7 days daily OHLC for 1 symbol; manual CSV acceptable | Broker account |
| **V2 — Level engine** | `structured_levels` in API; no AI | V1 |
| **V3 — Markets UI shell** | Picker + chart + levels + verdict (deterministic bias) | V2 |
| **V4 — AI runs** | 2→6 scheduled runs; store runs; chart markers | V3 + cost sign-off |
| **V5 — Gemini grounding** | Intraday headline refresh path | V4 |
| **V6 — Instagram-driven market #4** | New profile + ingest | User signal |

### 14.1 Implementation status snapshot (2026-06-09)

Cross-reference: [`MARKETS_TAB_IMPLEMENTATION_PLAN.md`](./MARKETS_TAB_IMPLEMENTATION_PLAN.md)

```text
Phase 0  Layout          ████████░░  ~80%  (chart + aside chosen; not formally signed off)
Phase 1  Data platform   ██████████  100%  (Binance path; MT5 deferred)
Phase 2  BTCUSD UI       ████████░░  ~85%  (developer preview)
Phase 3  Intelligence    ██░░░░░░░░  ~15%  (deterministic bias only)
Phase 4  Market #2       ░░░░░░░░░░   0%
```

#### Shipped (developer preview)

**Backend:** `market_registry`, Binance ingest/store, UDF routes, `level_engine_v0`, `/research`, `/ohlc` (multi-TF, live refresh), `/quote` (cached), `market_news_filter`, cross-assets in research.

**Frontend:** `MarketsHub` layout (picker, headline, chart split, analysis/news aside), Lightweight Charts + level/POI/range overlays + range bands, compact toolbar, red-branded theme, hooks (`useMarketResearch`, `useMarketOhlc`, `useMarketQuote`, `useMarketNews`).

#### BTCUSD v0 definition-of-done gaps

| Item | Status |
|------|--------|
| Tab open for all users (not coming soon) | ❌ Developer gate only |
| Verdict/thesis from **global GPT run** | ❌ Deterministic fallback |
| Catalysts in research | ❌ Empty array |
| `GET .../runs` + chart run markers | ❌ Not built |
| `BTCUSD.json` profile file | ❌ Registry in Python only |
| Unit tests for level engine | ❌ |

#### Recommended next milestones

1. **P0 + P1 level engine** — enriched kline ingest + volume POC/VAH/VAL (differentiation)
2. **Catalysts** — calendar filter for BTC-relevant events (quick win)
3. **Global run pipeline** — manual script → store run → GPT headline replaces deterministic copy
4. **Staging access** — widen or remove developer gate
5. **Past run markers on chart** — after runs exist
6. **Market #2** — after BTC feedback

#### Key files (reference)

| Area | Paths |
|------|--------|
| Layout | `MarketsHub.jsx`, `MarketsLayout.css`, `MarketChartSection.jsx`, `MarketChartAside.jsx` |
| Chart | `MarketChart.jsx`, `MarketChartToolbar.jsx`, `marketChartTheme.js`, `marketChartOverlays.js`, `marketChartRangeBands.js` |
| Data hooks | `useMarketResearch.js`, `useMarketOhlc.js`, `useMarketQuote.js`, `useMarketNews.js` |
| Backend | `market_research_service.py`, `level_engine.py`, `market_quote_service.py`, `markets_udf_routes.py` |
| Access gate | `Markets.jsx` → `MarketsComingSoon` for non-developers |

#### Session notes (2026-06-07 — 2026-06-09)

- **Focus:** Chart + data quality first; full analysis aside de-prioritized (still present as tab).
- **Layout fix:** Scoped coming-soon flex styles to `.markets-tab--coming-soon`; vertical stack with 80px top padding for navbar.
- **Live OHLC:** Backend `OHLC_LIVE_REFRESH_SEC=30`; chart polls ~30s so forming candle updates.
- **Live quote:** Binance-first for BTC; 5s server cache; one poll in `MarketsHub` (no duplicate chart hook).
- **Chart toolbar:** Compact TF pill + layers icon; menus overlay chart pane.
- **Branding:** Red-black chart theme aligned with `--accent-red` / `DASHBOARD_BRANDING.md`.
- **Cost (Railway):** Bill is always-on compute, not per-request; cache beats WebSocket for savings.

---

## 15. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| MT5 bridge unreliable | Time-box spike; keep REST fallback vendor shortlisted |
| GPT cites fake levels | Allowlist validator + no levels in prompt until `structured_levels` populated |
| 6× GPT+Gemini/day cost | Global runs only: `6 × markets`, not × users; start at 2 runs/market |
| BTC vs BTCUSDT mismatch | Single canonical `market_id` in config |
| Chart marker clutter | Collapse runs; show only bias flips or user-selected history |
| TV visual vs non-TV data | Label chart data source in footer |

---

## 16. Open questions (for validation sessions)

1. **v0 FX pair:** EUR/USD or USD/JPY if only one?
2. **BTC symbol:** `BTCUSD` (MT5) vs `BTCUSDT` (current TV catalog)—which is canonical?
3. **MT5:** One broker account or multiple? Who maintains the terminal?
4. **6 analysis runs:** Fixed UTC schedule vs event-triggered (calendar release)?
5. **Gemini on Markets:** Full narrative co-write vs grounding-only adjunct to GPT?
6. **Firestore vs Postgres** for `ohlc_store` and `analysis_runs`?
7. **Instagram feedback:** Formal voting mechanism or manual tally?
8. **Day/Swing:** Tabs on same page or separate bias fields in one verdict card?

---

## 17. Decision log

| Date | Decision | Status |
|------|----------|--------|
| 2026-06-03 | Markets tab = instrument-centric synthesis, not Economies clone | Agreed |
| 2026-06-03 | Levels algorithmic → AI narrates probability only | Agreed |
| 2026-06-03 | Candidate markets: Gold, EUR/USD or USD/JPY, BTC (+ IG feedback) | Proposed |
| 2026-06-03 | OHLC via MT5/MQL5 broker data | Proposed — needs spike |
| 2026-06-03 | TV-style charts; **font/branding** aligned, not card layout clone | Agreed |
| 2026-06-03 | GPT+Gemini 2–6×/day (6 target), **global runs for all users** | Agreed |
| 2026-06-03 | **Minimized live news** strip (not full feed); calendar market-filtered | Agreed |
| 2026-06-03 | Chart: POI + price ranges + past analysis **areas** + run markers | Agreed |
| 2026-06-03 | Avoid vibecoded card-stack UI; chart-first Markets-native layout | Agreed |
| 2026-06-04 | Chart = **research chart** (our levels on our bars); **no user drawing**; Lightweight Charts | Agreed |
| 2026-06-04 | Advanced Charts deprioritized — not needed for read-only FXSentinel overlays | Agreed |
| 2026-06-07 | **Lightweight Charts research chart shipped** — `level_engine_v0`, `/api/markets/BTCUSD/research`, live OHLC poll | Implemented |
| 2026-06-08 | **Binance live quote** — `/quote`, picker + chart toolbar; server 5s cache; single frontend poll | Implemented |
| 2026-06-08 | **Chart UX** — compact TF/layers dropdowns; red-branded chart theme; range bands behind candles | Implemented |
| 2026-06-09 | **Markets = aggregation hub** — fuse Binance microstructure + calendar + news + cross-asset; v0 levels are scaffold | Agreed |
| 2026-06-09 | **`level_engine_v1` priority** — enriched klines → volume profile + delta zones before book/futures | Agreed |
| 2026-06-09 | **Live price cost** — keep REST + cache; defer backend WS; client Binance WS optional later | Agreed |
| 2026-06-09 | **Markets = referral desk; app = data platform** — reuse Overview/Economies/calendar/sentiment via backend composition, not tab silos | Agreed |
| 2026-06-09 | **Quant vs GPT split** — quant owns levels/zones + `basis`; GPT owns probability, thesis, zone-tap narrative (allowlist only) | Agreed |

---

## 18. Validation checklist (next session)

- [ ] MT5/MQL5 spike: pull 30 days daily bars for `XAUUSD`, `EURUSD`, `BTCUSD`
- [ ] Symbol mapping table: MT5 ↔ TV ↔ internal `id`
- [ ] Level engine prototype on spike data; snapshot tests
- [ ] **P0:** Enrich `ohlc_store` with taker buy / quote vol / trade count from Binance klines
- [ ] **P1:** Volume POC + VAH/VAL on 4H → new `structured_levels` + chart overlays
- [ ] Cost estimate: 6 × (GPT + Gemini) × 3 markets × 30 days (**global**, not per user)
- [ ] **Wire cross-app context:** calendar → `catalysts[]`, US holistic scan → macro digest, sentiment → research payload
- [ ] Extend `analysis_context_pack` with `SURFACE_MARKET_RESEARCH`
- [ ] Global run: manual `run_market_analysis` → `latest_run` in research
- [ ] Staging rollout: developer gate policy
- [ ] Instagram: define how feedback maps to market priority
- [ ] Legal: broker data display terms

---

## Revision log

| Date | Change |
|------|--------|
| 2026-06-03 | Initial draft from founder notes + codebase evaluation |
| 2026-06-03 | Clarifications: global analysis, UI branding vs cards, news vs calendar, chart POI/ranges/areas |
| 2026-06-03 | Rollout order: **BTCUSD** first (`BTCUSDT` feeds); 2-week implementation plan added |
| 2026-06-09 | §1.1–1.3 aggregation hub + platform vs Markets tab + cross-app reuse; §10.3–10.4 data inventory; quant/GPT split; level engine v1; status snapshot |
