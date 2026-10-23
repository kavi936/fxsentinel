# FXSentinel — General System Architecture

> **Purpose:** Call prep and mental model for explaining FXSentinel technically.  
> Simplified for memorization — file names included where they help you sound credible.

---

## One-Line Pitch

**React frontend → Flask API → background worker → 15+ data APIs → hybrid Gemini+GPT analysis → Firebase cache → Telegram/email alerts.**

---

## The 4 Boxes (memorize this first)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Main API   │◀────│   Worker    │     │  Firebase   │
│  React/Vite │     │  Flask      │     │  Alerts     │────▶│  Cache/Auth │
│  (Vercel)   │     │  (Railway)  │     │  (Railway)  │     │  + Stripe   │
└─────────────┘     └──────┬──────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │ Data + AI   │
                    │ RSS/Telegram│
                    │ Gemini→GPT  │
                    └─────────────┘
```

| Box | What it does | Key file |
|-----|--------------|----------|
| **Frontend** | Dashboard, news feed, analysis UI | `src/components/` |
| **Main API** | All `/api/*` endpoints | `backend/app.py`, `main.py` |
| **Worker** | Polls news/calendar, sends alerts | `backend/worker_app.py`, `background_alert_worker.py` |
| **Firebase** | News cache, alert settings, user usage | `persistent_news_cache.py`, `firebase_realtime_storage.py` |

---

## Request Flow: Open App → See Analysis

### Step 1: Load news feed
1. User opens app → `GET /api/news`
2. Check **Firebase cache** first (`persistent_news_cache.py`)
3. If stale (>5 min) → fetch in parallel:
   - **RSS** (8 feeds) — `news_aggregator.py`
   - **Telegram** — `telegram_sync_wrapper.py`
   - **Alt sources** — `alternative_news_sources.py`
4. Filter forex relevance → dedupe → save cache → return JSON

### Step 2: User clicks "Analyze"
1. `GET /api/analysis/<news_id>`
2. **Quota check** — `stripe_service.can_perform_analysis` (don't burn $ if over limit)
3. **Gemini** — `fetch_related_evidence()` — web grounding, related headlines
4. **GPT** — `mvp_news_analyzer.analyze_news()` — structured analysis
5. **Finalize** — `finalize_analysis()` — bias, horizon, observability
6. Increment usage count → return to UI

**Memorize:** Cache → Quota → Gemini → GPT → Finalize → Bill

---

## LLM Pipeline (your strongest story)

### Two models, two jobs

| Model | Job | File |
|-------|-----|------|
| **Gemini** | Find related web evidence (grounding) | `gemini_news_grounding_service.py` |
| **GPT** | Write structured trade analysis | `mvp_news_analyzer.py` |

**Why two?** Retrieval vs reasoning. Gemini searches; GPT synthesizes. Less hallucination, explainable citations.

### Fallback chain (fail-open)
```
Gemini fails     → skip grounding, continue
GPT fails        → free sentiment analysis (_analyze_with_free)
Everything fails → mock placeholder (last resort)
```

### Cost control
- Check quota **before** calling OpenAI
- Pass `user` param to OpenAI for attribution
- Log usage in Firestore — `ai_usage_tracker.py`
- Increment billing — `stripe_service.increment_analysis_count`

### Caching
- **Gemini:** in-memory, ~30 min TTL
- **News feed:** Firebase + local disk fallback (survives outages)
- **GPT:** smart cache by event fingerprint — `smart_chatgpt_cache.py`

---

## Data Ingestion

### News sources
| Source | How | File |
|--------|-----|------|
| RSS (8 feeds) | `feedparser`, keyword filter | `news_aggregator.py` |
| Telegram | Telethon user client | `telegram_sync_wrapper.py` |
| Alt feeds | Backup RSS | `alternative_news_sources.py` |

**RSS feeds:** Reuters, Bloomberg, CNBC, MarketWatch, FXStreet, Investing.com, ForexLive, DailyFX

### Filtering pipeline
1. **Forex relevance** — `enhanced_forex_filter.py` (keywords, pairs, impact)
2. **Dedup** — title similarity in `remove_duplicates()`
3. **Spam filter** — e.g. FXStreet gold price slop

### Firebase role
- **Realtime DB:** live news cache, alert settings, alert history
- **Firestore:** user billing, AI usage logs, subscription status

---

## Alert System

### Two processes
- **Worker** (`worker_app.py`) — runs every 60s, separate Railway service
- **Main app** — receives `POST /api/alerts/trigger`, fans out to users

### Flow
```
Worker polls /api/news or calendar
    → filters high-impact (enhanced_forex_filter)
    → POST /api/alerts/trigger
    → main app loads users from Firebase
    → dedup check (unified_alert_deduplication)
    → send via Telegram bot (or email if enabled)
```

### Dedup
- Per user + content hash + 24h TTL
- `unified_alert_deduplication.py` + `persistent_alert_deduplication.py`

### Impact scoring
- `news_alert_trigger.is_high_impact_news()` — Fed, CPI, NFP, breaking, etc.
- User prefs: pairs, impact level, quiet hours

**Note:** Worker news alerts can be disabled (`DISABLE_WORKER_NEWS_ALERTS=true`) — unified path on news save handles it instead.

---

## External APIs (quick reference)

| API | Purpose | Challenge solved |
|-----|---------|------------------|
| **Binance** | BTC klines + live quote | `ohlc_ingest_binance.py`, UDF resolution mapping |
| **TradingView** | 40+ instruments (FX, crypto, bonds) | Parallel namespace fetch, 429 handling |
| **Finnhub** | Economic calendar | Demo key limits, cached fallback |
| **ForexFactory** | Free calendar JSON | 6h cache |
| **Polymarket** | Prediction markets (Gamma + CLOB) | Pagination, no auth |
| **Kalshi/DOME** | Prediction markets | `dome_api_rate_limiter.py` — 1 req/s |
| **Google Sheets** | Macro indicators (US/EU/UK/JP) | `gspread` service account |
| **Stripe** | Subscriptions, quotas | Firestore sync |
| **Resend** | Verification/welcome email | Transactional only |
| **Firebase** | Auth, cache, alerts | Timeout + local mirror on outage |

**Binance detail:** `BTCUSD` display → `BTCUSDT` on Binance. Klines → `ohlc_store` → `level_engine` (PDH/PDL, volume profile).

**MT5:** Planned, not live. EURUSD/GBPUSD disabled in `market_registry.py`.

---

## Production Patterns (sound mature)

| Pattern | Where | Why |
|---------|-------|-----|
| **Split deploy** | Main app + worker on Railway | Scale/isolate alert load |
| **Multi-tier cache** | Firebase → memory → disk | Survive Firebase outages |
| **Fail-open AI** | Gemini/GPT fallbacks | Never block user on one provider |
| **Quota before spend** | `can_perform_analysis` | No OpenAI call if over limit |
| **Rate limiters** | Flask-Limiter, DOME 1 req/s | Respect API tiers |
| **Circuit breaker** | `circuit_breaker.py` (Telegram) | Stop cascade on failures |
| **Health endpoints** | `/api/health/*` | Per-subsystem checks |

---

## Analytics & Growth

| Layer | What |
|-------|------|
| **Firebase Analytics** | `logEvent` in `analytics.js` |
| **GTM** | `dataLayer.push` |
| **GA4** | `gtag` |
| **UTM** | Stored in `sessionStorage` — survives auth redirects |
| **Funnel** | landing → signup → dashboard → trial → payment |

**ManyChat:** Marketing tool, not in codebase. Say "external growth ops."

---

## Memorization Cheat Sheet

### Architecture (30 sec)
"React on Vercel, Flask API on Railway, separate worker for alerts. News from RSS and Telegram into Firebase cache. Analysis is Gemini grounding then GPT, with quota checks and fallbacks."

### LLM (20 sec)
"Gemini retrieves web evidence. GPT writes structured analysis. Two models because retrieval and reasoning are different jobs. If anything fails, we degrade gracefully."

### Alerts (15 sec)
"Worker polls every 60 seconds, filters high-impact, hits main app trigger endpoint, dedupes per user, sends Telegram based on preferences."

### APIs (15 sec)
"Fifteen plus integrations — Binance for BTC charts, TradingView for quotes, Finnhub and ForexFactory for calendar, Polymarket and Kalshi for prediction context, Stripe for billing."

### What broke first (15 sec)
"Cache pressure and duplicate alerts when traffic grew. Fixed with multi-tier cache fallback and stronger dedup."

### Do differently (15 sec)
"Smaller services instead of one giant app.py. Event queue for alerts. Unified dedup. Observability from day one."

---

## Don't Overclaim

| Say | Don't say |
|-----|-----------|
| Binance BTC live | MT5 broker integration live |
| React + Python full-stack | Built with Flutter (not in repo) |
| ManyChat as marketing ops | ManyChat built into app |
| Hybrid LLM with fallbacks | Single ChatGPT wrapper |
| 525+ users, 3,800+ followers, 6M+ views | Institutional-grade platform |

---

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/news` | News feed |
| `GET /api/analysis/<id>` | AI analysis |
| `GET /api/economic-calendar` | Calendar events |
| `POST /api/economy-scan/<country>` | Macro scan |
| `GET /api/forex-prices` | TradingView quotes |
| `GET /api/markets/BTCUSD/research` | Market research DTO |
| `POST /api/alerts/trigger` | Worker → main app alerts |
| `GET /api/health` | System health |

---

## Parallels to MRKT (if asked)

**You already solved:**
- Multi-API ingestion + rate limits
- Retrieval + reasoning LLM split
- Per-user cost/quota on inference
- Alert fanout + personalization
- Cache tiers + degraded mode

**You'd contribute on:**
- Inference pipeline reliability
- Tool/routing policies for conversational AI
- Data normalization + confidence scoring
- Unit economics on LLM spend

---

## Related Docs

- `FXSENTINEL_CV_AND_CODEBASE_GUIDE.md` — CV bullets, skills alignment
- `MARKETS_BTCUSD_DATA_AND_UI_PLAN.md` — Markets tab + Binance
- `PREDICTION_MARKETS_SYSTEM.md` — Polymarket/Kalshi
- `BACKGROUND_WORKER_VS_MAIN_APP_EVALUATION.md` — Why split deploy

---

*Simplified for call prep. Update as the system evolves.*
