# FXSentinel — CV, Codebase & Career Guide

> **Purpose:** A single reference for CV bullets, interview prep, skills alignment, and growth areas — grounded in what the codebase actually contains.
>
> **Last updated:** July 2026

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What FXSentinel Is](#what-fxsentinel-is)
3. [Architecture Overview](#architecture-overview)
4. [Tech Stack (Actual vs CV)](#tech-stack-actual-vs-cv)
5. [Core Product Areas](#core-product-areas)
6. [Key Files & Directories](#key-files--directories)
7. [CV Bullets (Ready to Use)](#cv-bullets-ready-to-use)
8. [Technical Skills Section (Revised)](#technical-skills-section-revised)
9. [Interview Talking Points](#interview-talking-points)
10. [External APIs & Data Providers](#external-apis--data-providers)
11. [Growth Areas (High Impact)](#growth-areas-high-impact)
12. [What NOT to Overclaim](#what-not-to-overclaim)
13. [Metrics You Can Cite](#metrics-you-can-cite)

---

## Executive Summary

FXSentinel is a **full-stack fintech web application** — not a tutorial or MVP demo. The repo contains **1,200+ files**, **105+ backend service modules**, **60+ REST API endpoints**, **15+ external API integrations**, and production deployment across **Vercel (frontend)** and **Railway (backend + worker)**.

The strongest technical narrative:

> **Sole founder who built a multi-model AI analysis platform on top of a multi-source data ingestion layer (news, macro, market data, prediction markets), with alerts, payments, and full growth analytics.**

---

## What FXSentinel Is

An AI-powered forex analysis platform for retail traders that:

- Aggregates financial news from **8+ RSS feeds** and **Telegram channels**
- Filters for forex relevance, deduplicates, and caches persistently
- Runs a **hybrid LLM pipeline** (Gemini grounding → GPT structured analysis)
- Delivers insights via a **React dashboard**, **Telegram/email alerts**, and **Stripe subscriptions**
- Tracks user acquisition from **TikTok/IG/X** through to paid conversion via **GA4/GTM/Firebase Analytics**

**Live URL:** [fxsentinel.io](https://fxsentinel.io)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vercel)                         │
│  React 19 + Vite | GA4/GTM/Firebase Analytics | Stripe UI   │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP API
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Main App — Flask (Railway)                      │
│  60+ REST endpoints | Auth | AI analysis | Stripe webhooks  │
└────────────────────────────┬────────────────────────────────┘
                             │ Internal API
                             ▼
┌─────────────────────────────────────────────────────────────┐
│           Background Worker (Railway)                        │
│  News polling (~60s) | Alert triggers | Calendar alerts     │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   ┌──────────┐      ┌──────────────┐    ┌─────────────┐
   │ Firebase │      │  AI Layer    │    │ Data Sources│
   │ Auth     │      │ Gemini+GPT   │    │ RSS/Telegram│
   │ Firestore│      │ Caching      │    │ Finnhub     │
   │ Realtime │      │ Cost tracking│    │ Alpha Vantage│
   └──────────┘      └──────────────┘    │ TradingView │
                                         └─────────────┘
```

### Deployment Entry Points

| File | Role |
|------|------|
| `main.py` | Railway entry point for Flask app |
| `Dockerfile` | Container definition |
| `Procfile` | Process definition |
| `railway.json` | Railway deployment config |
| `vercel.json` | Vercel frontend deployment |
| `backend/worker_app.py` | Background worker entry |

---

## Tech Stack (Actual vs CV)

### What's Actually in the Repo

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, Vite 7, React Router 7, Axios, Framer Motion |
| **Charts** | lightweight-charts, TradingView UDF datafeed |
| **Backend** | Python 3, Flask, Gunicorn |
| **AI** | OpenAI GPT API, Google Gemini (web grounding) |
| **Database** | Firebase Auth, Firestore, Realtime Database |
| **Cache** | Redis, in-memory, Firebase, local disk fallback |
| **Payments** | Stripe (subscriptions, coupons) |
| **Email** | Resend (verification, welcome emails) |
| **Alerts** | Telegram Bot API, Telethon |
| **Analytics** | Firebase Analytics, GA4, Google Tag Manager |
| **Hosting** | Vercel (frontend), Railway (backend + worker) |
| **News** | RSS (feedparser), Telegram channels |
| **Market Data** | Finnhub, Alpha Vantage, TradingView APIs |
| **Prediction Markets** | Polymarket, Propheseer/Dome API |

### CV Skills Alignment

| CV Skill | In Repo? | Recommendation |
|----------|----------|----------------|
| **Dart / Flutter** | ❌ No | Remove or mark "learning" unless separate project exists |
| **JavaScript (basic)** | ✅ Substantial React frontend | Upgrade to **JavaScript / React** |
| **HTML/CSS** | ✅ Yes | Keep — custom CSS, landing, email templates |
| **Swift (basic)** | ❌ No | Keep only if separate iOS work exists |
| **Firebase** | ✅ Heavy use | Strong — Auth, Firestore, Realtime DB, Analytics |
| **Git/GitHub** | ✅ Yes | Keep |
| **Prompt engineering / LLM** | ✅ Very strong | **Lead with this** — multi-model orchestration |
| **Swing trading / indicators** | ✅ Domain logic in product | Frame as product domain, not just personal trading |
| **Backtesting** | ❌ Not implemented | Keep TradingView/Excel for personal use; don't claim in-product backtesting |
| **TikTok / SEO / Canva** | ✅ Analytics + blog SEO | Valid as growth skills, separate from engineering |
| **ManyChat** | ❌ Not in codebase | Fine on CV as marketing — not "built into app" |
| **Python** | ✅ Not on CV but should be | **Add Python, Flask** — core backend language |

### Revised Skills Section for CV

**Programming & Tools:** Python, JavaScript, React, HTML/CSS, Flask, Firebase, Git/GitHub, Stripe, Resend, Vercel, Railway

**AI & Machine Learning:** Prompt engineering, multi-model LLM orchestration (Gemini + OpenAI), RAG-style web grounding, AI cost optimization & caching

**Finance & Trading:** Macroeconomic indicator analysis, economic calendar systems, forex sentiment analysis, swing trading (personal)

**Growth & Marketing:** TikTok/IG/X content strategy, GA4/GTM analytics, SEO, ManyChat automation, UTM funnel design

---

## Core Product Areas

### 1. Live News Aggregation & Filtering

**What it does:** Pulls forex-relevant news from multiple sources, filters, deduplicates, and serves a real-time feed.

**Key components:**
- `backend/services/news_aggregator.py` — RSS feeds (Reuters, Bloomberg, CNBC, MarketWatch, FXStreet, Investing.com, ForexLive, DailyFX)
- `backend/services/alternative_news_sources.py` — Additional sources
- `backend/services/telegram_sync_wrapper.py` — Telegram channel ingestion
- `backend/services/enhanced_forex_filter.py` — Relevance scoring
- `backend/services/persistent_news_cache.py` — Firebase persistence + local disk fallback
- `src/components/LiveNewsFeed.jsx` — Frontend feed with filters and AI trigger

**CV language:** *"Built multi-source news ingestion from 8+ RSS feeds and Telegram channels with forex relevance filtering, deduplication, and Firebase-backed persistent caching."*

---

### 2. Hybrid AI Analysis Pipeline ⭐ (Strongest Technical Story)

**What it does:** Two-model LLM workflow where Gemini gathers web evidence and GPT produces structured trade analysis.

**Flow:**
1. User clicks "Analyze" on a news item
2. **Gemini** (`gemini_news_grounding_service.py`) searches the web for related headlines
3. Evidence is tier-ranked (Reuters, Bloomberg, FT, central banks = Tier 1)
4. **GPT** (`mvp_news_analyzer.py`, `gpt_ai_analysis.py`) produces structured analysis, constrained to cite only provided evidence
5. **Finalize pipeline** (`analysis_pipeline.py`) adds bias classification, trading plans, calendar scenarios, personalization

**Supporting services:**
| File | Purpose |
|------|---------|
| `gemini_news_grounding_service.py` | Web grounding, evidence tiering |
| `mvp_news_analyzer.py` | Hybrid analyzer (free vs GPT routing) |
| `gpt_ai_analysis.py` | Core GPT analysis with structured output |
| `optimized_chatgpt_analyzer.py` | Smart model selection by impact level |
| `smart_chatgpt_cache.py` | Analysis result caching |
| `ai_usage_tracker.py` | Per-user OpenAI cost tracking |
| `analysis_pipeline.py` | Single finalize path for all analysis |
| `analysis_contract.py` | Response envelope semantics |
| `analysis_v1_spine.py` | Structured analysis spine |
| `analysis_bias_classification.py` | Bullish/bearish/neutral classification |
| `analysis_actionable_conditionals.py` | Trading plan conditionals |
| `calendar_scenario_engine.py` | Calendar event scenarios |

**CV language:** *"Architected hybrid LLM pipeline: Gemini for real-time web grounding and evidence retrieval, OpenAI GPT for structured trade analysis — with smart caching, per-user cost tracking, and fail-open fallbacks."*

---

### 3. Economic Calendar & Macro Analysis

**What it does:** Tracks upcoming/released economic events, provides pre/post-event AI analysis, powers the Economies tab.

**Key components:**
- `backend/services/hybrid_economic_calendar.py` — Main calendar (27k+ lines, multi-source merge)
- `backend/services/reliable_economic_calendar.py` — Reliability layer
- `backend/services/finnhub_calendar.py` — Finnhub integration
- `backend/services/trading_economics_calendar.py` — TradingEconomics data
- `backend/services/economy_holistic_scan_service.py` — Deterministic macro scoring + GPT narrative
- `backend/services/economy_holistic_scan_store.py` — Scan history persistence
- `backend/services/economic_calendar_alerts.py` — Automated calendar alerts
- `src/components/Economies.jsx` — Economies tab UI
- `src/components/EconomicChartPopup.jsx` — Historical chart popups

**CV language:** *"Built hybrid economic calendar merging multiple data sources with pre/post-event AI analysis and automated alert integration."*

---

### 4. Alerts System

**What it does:** Background worker monitors news 24/7, filters high-impact items, delivers personalized alerts via Telegram and email.

**Key components:**
- `backend/services/background_alert_worker.py` — Continuous news polling
- `backend/services/production_alert_worker.py` — Production worker
- `backend/services/alert_service.py` — Alert delivery orchestration
- `backend/services/alert_triggers.py` — Trigger logic
- `backend/services/unified_alert_deduplication.py` — Prevent duplicate alerts
- `backend/services/persistent_alert_deduplication.py` — Firebase-backed dedup
- `backend/services/alert_quality_enhancer.py` — Quality scoring
- `backend/services/scalable_alert_distributor.py` — Multi-user distribution
- `backend/services/robust_telegram_service.py` — Telegram delivery
- `backend/services/dead_letter_queue.py` — Failed alert retry
- `src/components/Alerts.jsx` — User alert settings UI

**CV language:** *"Shipped automated Telegram + email alert system with deduplication, impact scoring, and economic calendar integration."*

---

### 5. Markets & Charts

**What it does:** Live forex prices, charts, technical analysis, market sentiment.

**Key components:**
- `src/components/Markets.jsx` — Markets hub
- `src/components/markets/MarketChart.jsx` — Chart component
- `src/components/markets/MarketsHub.jsx` — Markets layout
- `backend/services/markets/udf_datafeed.py` — TradingView-style datafeed
- `backend/services/markets/level_engine.py` — Support/resistance levels
- `backend/services/markets/ohlc_store.py` — OHLC data storage
- `backend/services/technical_analysis_service.py` — TA indicators
- `backend/services/market_sentiment_service.py` — Sentiment scoring
- `backend/services/live_market_data.py` — Live price feeds
- `backend/services/tradingview_market_data.py` — TradingView integration

---

### 6. Prediction Markets

**What it does:** Integrates prediction market data (Polymarket, etc.) as macro context for analysis.

**Key components:**
- `backend/services/prediction_markets_service.py` — Main service
- `backend/services/propheseer_api_client.py` — Propheseer API
- `backend/services/polyrouter_api_client.py` — Polyrouter API
- `backend/services/curated_prediction_markets.py` — Curated market list
- `backend/services/prediction_markets_context.py` — Context injection for AI
- `src/components/PredictionMarketChartPopup.jsx` — Chart popup UI

**Growth opportunity:** Feature is partially built — finishing user-facing integration is a unique differentiator.

---

### 7. Monetization & User Lifecycle

**What it does:** Stripe subscriptions, Firebase auth, email verification, onboarding, trial flow.

**Key components:**
- `backend/services/stripe_service.py` — Stripe integration
- `backend/services/coupon_service.py` — Discount coupons
- `backend/services/email_service.py` — Resend transactional emails
- `backend/services/subscription_cache.py` — Subscription state caching
- `backend/services/user_trader_profile.py` — Trader profile/onboarding
- `src/components/Signup.jsx`, `Login.jsx` — Auth UI
- `src/components/VerifyEmail.jsx` — Email verification
- `src/components/TrialWelcome.jsx` — Trial onboarding
- `src/components/OnboardingTour.jsx` — Product tour (driver.js)
- `src/components/TraderProfileGate.jsx` — Profile completion gate
- `src/contexts/AuthContext.jsx` — Firebase auth state

**CV language:** *"Integrated Stripe subscriptions, Firebase Auth, and Resend transactional email for onboarding and verification."*

---

### 8. Growth & Analytics

**What it does:** Full-funnel tracking from social acquisition through paid conversion.

**Key components:**
- `src/utils/analytics.js` — Custom analytics class (750+ lines)
  - UTM parameter persistence across redirects
  - Short source codes (`?s=tk` → TikTok, `?s=ig` → Instagram)
  - Referrer detection (Google, TikTok, X, etc.)
  - Funnel steps: landing → signup → trial → payment
  - Scroll depth, time on page, element visibility
  - Dual push: Firebase Analytics + GTM dataLayer + gtag
- `src/components/blog-posts/` — 13 SEO blog posts
- `scripts/generate-blog-static-html.js` — Static HTML generation for SEO
- `public/sitemap.xml` — SEO sitemap
- `src/hooks/useMeta.js` — Dynamic meta tags

**CV language:** *"Implemented GA4/GTM/Firebase Analytics funnel tracking with UTM attribution across TikTok, Instagram, and X."*

---

## External APIs & Data Providers

This section covers integrations that were easy to understate on a CV. FXSentinel is not a single-API wrapper — it orchestrates **15+ external data sources** across news, market data, macro, prediction markets, and payments.

### Summary Table

| Category | Provider | What It Powers | Key Files |
|----------|----------|----------------|-----------|
| **AI** | OpenAI GPT | Structured news/calendar/economy analysis | `gpt_ai_analysis.py`, `mvp_news_analyzer.py` |
| **AI** | Google Gemini | Web grounding / related evidence for news | `gemini_news_grounding_service.py` |
| **Crypto OHLC** | **Binance** (`/api/v3/klines`) | BTC chart bars, volume, taker-buy data | `ohlc_ingest_binance.py`, `ohlc_store.py` |
| **Crypto quotes** | **Binance** (`/ticker/24hr`, `/ticker/price`) | Live BTC price aligned with chart venue | `binance_ticker.py`, `market_quote_service.py` |
| **Multi-asset quotes** | **TradingView Scanner** | Forex, crypto, commodities, bonds, indices | `tradingview_market_data.py`, `tradingview_instruments.py` |
| **Economic calendar** | **Finnhub** | Calendar events, historical macro series | `finnhub_calendar.py`, `finnhub_historical.py` |
| **Economic calendar** | **ForexFactory** (JSON feed) | Global event calendar (free tier) | `global_economic_calendar.py` |
| **Economic calendar** | Hybrid merge | Multi-source calendar normalization | `hybrid_economic_calendar.py` |
| **Macro indicators** | **Google Sheets** (gspread) | US/EU/UK/JP economy indicator tabs | `google_sheets_service.py` |
| **Market sentiment** | **Alternative.me** | Crypto Fear & Greed Index | `market_sentiment_service.py` |
| **Market sentiment** | **Alpha Vantage** | VIX daily series (fallback) | `market_sentiment_service.py` |
| **Prediction markets** | **Polymarket** (Gamma + CLOB APIs) | Event discovery + Yes/No prices | `prediction_markets_service.py` |
| **Prediction markets** | **Kalshi** via **DOME API** | Institutional prediction market data | `prediction_markets_service.py`, `dome_api_rate_limiter.py` |
| **Prediction markets** | **PolyRouter** | Unified prediction market aggregator | `polyrouter_api_client.py` |
| **Prediction markets** | **PropheSeer** | Multi-platform market API | `propheseer_api_client.py` |
| **News** | RSS (8 feeds) | Reuters, Bloomberg, CNBC, FXStreet, etc. | `news_aggregator.py` |
| **News** | **Telegram** (Telethon) | WatcherGuru + channel monitoring | `telegram_sync_wrapper.py`, `telegram_monitor_user.py` |
| **Alerts** | **Telegram Bot API** | User alert delivery + webhooks | `robust_telegram_service.py`, `telegram_bot_setup.py` |
| **Payments** | **Stripe** | Subscriptions, webhooks, coupons | `stripe_service.py`, `coupon_service.py` |
| **Email** | **Resend** | Verification + welcome emails | `email_service.py` |
| **Auth / storage** | **Firebase** | Auth, Firestore, Realtime DB | `firebase_realtime_storage.py` |
| **Cache** | **Redis** | GPT analysis cache (optional) | `gpt_ai_analysis.py`, `smart_chatgpt_cache.py` |
| **Charts (planned)** | **MetaTrader 5** | Broker OHLC bridge for FX pairs | `backend/mt5/README.md` (not yet live) |

---

### Binance Integration (Klines + Live Quotes) ⭐

**Why it matters for CV:** You built a proper market data pipeline — not just calling a price API, but ingesting OHLC, mapping TradingView resolutions, storing bars, and computing technical levels.

**What’s implemented:**

| Component | Details |
|-----------|---------|
| **Klines endpoint** | `GET https://api.binance.com/api/v3/klines` |
| **Resolutions** | 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w mapped from TradingView UDF codes |
| **Bar fields** | OHLC, volume, quote volume, trade count, taker-buy volume |
| **Storage** | `ohlc_store.py` — persisted bar files per market + resolution |
| **Live quote** | `binance_ticker.py` — 24hr ticker + last price (same venue as chart) |
| **Active market** | `BTCUSD` → `BTCUSDT` on Binance (enabled in `market_registry.py`) |

**Downstream use:**
- `level_engine.py` — prior day high/low, weekly levels, 4H rotation zones, volume profile POC/VAH/VAL
- `feature_engine.py` — 5-day 4H volume profile computation
- `market_research_service.py` — assembles quote + levels + deterministic verdict + platform context
- `udf_datafeed.py` — TradingView-compatible UDF history endpoint for charts

**API routes:**
| Endpoint | Purpose |
|----------|---------|
| `GET /api/markets/BTCUSD/ohlc?tf=4H` | OHLC bars for charts |
| `GET /api/markets/BTCUSD/quote` | Live Binance spot quote |
| `GET /api/markets/BTCUSD/research` | Full research DTO (levels, verdict, catalysts) |
| `GET /api/udf/history` | TradingView UDF-compatible history |
| `GET /api/udf/config` | UDF datafeed config |

**CV language:** *"Built Binance klines ingestion pipeline with TradingView UDF resolution mapping, OHLC persistence, volume-profile level engine, and live quote alignment for BTC markets research."*

---

### TradingView Scanner (Multi-Asset Quotes)

**What it does:** Parallel POST requests to TradingView scanner namespaces, merged into a single instrument catalog.

**Instrument coverage (40+ instruments in `tradingview_instruments.py`):**

| Namespace | Examples |
|-----------|----------|
| `forex` (15 pairs) | EURUSD, GBPUSD, USDJPY, AUDUSD, EURJPY… |
| `crypto` | BTCUSDT, ETHUSDT |
| `futures` (commodities) | Gold (GC), Silver (SI), WTI Crude |
| `bonds` (yields) | US/DE/GB/JP/EU/AU/CA/IT 2Y/10Y/30Y |
| `cfd` (indices) | S&P 500, Dow, Nasdaq, VIX |

**Implementation details:**
- `ThreadPoolExecutor` for parallel namespace fetches
- Rate limit handling (429 responses)
- Staleness detection (data age, weekend/market hours flags)
- Powers `/api/forex-prices`, live ticker, market sentiment, cross-asset context

**CV language:** *"Integrated TradingView scanner API across 5 market namespaces (forex, crypto, futures, bonds, indices) with parallel fetching and staleness detection."*

---

### Economic Data Providers

**Finnhub** (`FINNHUB_API_KEY`)
- Economic calendar API (`/calendar/economic`)
- Historical macro data extraction with deduplication (`finnhub_historical.py`)
- Used for economic chart popups and calendar enrichment

**ForexFactory** (free JSON feed)
- `https://nfs.faireconomy.media/ff_calendar_thisweek.json`
- 6-hour file cache with stale fallback (`global_economic_calendar.py`)

**Hybrid Calendar** (`hybrid_economic_calendar.py`)
- Merges and normalizes multiple calendar sources into one API
- 27k+ lines — largest single service file in the project
- Powers `/api/economic-calendar` and calendar alerts

**Google Sheets** (`GOOGLE_SHEETS_CREDENTIALS_JSON`)
- Service account via `gspread` + `google-auth`
- Per-country indicator tabs: US, EUR, UK, JP (CPI, rates, GDP, unemployment, etc.)
- 30-second in-memory cache
- Powers Economies tab via `/api/economy-indicators/{country}`

**CV language:** *"Aggregated economic data from Finnhub, ForexFactory, and Google Sheets into a unified hybrid calendar and per-country macro indicator API."*

---

### Prediction Markets (Multi-Platform)

A sophisticated multi-source aggregation system — one of the more unique technical areas in the project.

| Platform | API | Auth | Role |
|----------|-----|------|------|
| **Polymarket** | Gamma API (`gamma-api.polymarket.com/events`) | None | Event/market discovery |
| **Polymarket** | CLOB API (`clob.polymarket.com`) | None | Yes/No token prices, orderbook |
| **Kalshi** | DOME API (`api.domeapi.io/v1/kalshi`) | `DOME_API_KEY` | Institutional prediction markets |
| **PolyRouter** | `polyrouter` client | `POLYROUTER_API_KEY` | Unified aggregator |
| **PropheSeer** | PropheSeer API | `PROPHESEER_API_KEY` | Multi-platform markets |

**Engineering patterns:**
- `dome_api_rate_limiter.py` — token bucket (1 req/s, 10 req/10s) with exponential backoff
- Curated keyword filtering for forex-relevant events (Fed, CPI, ECB, elections)
- Price history tracking + conviction scoring
- Firebase persistent cache (`persistent_prediction_markets_cache.py`)
- Injected as macro context into AI analysis pipeline

**CV language:** *"Built multi-platform prediction markets aggregator (Polymarket, Kalshi/DOME, PolyRouter) with rate limiting, relevance filtering, and price history tracking for macro probability context."*

---

### Market Sentiment (Multi-Source Fusion)

`market_sentiment_service.py` fuses several data sources into pair-level sentiment:

| Source | Data |
|--------|------|
| TradingView quotes | Daily price change per pair |
| Alternative.me | Crypto Fear & Greed Index |
| Alpha Vantage | VIX daily series |
| NumPy/Pandas | RSI-style impulse, volatility, support/resistance |
| Economic calendar | Upcoming high-impact events as market drivers |

Outputs: per-pair bullish/bearish/neutral %, market conditions, risk-on/off regime.

---

### Telegram (Dual Integration)

FXSentinel uses Telegram in **two distinct ways**:

| Use | Library | Purpose |
|-----|---------|---------|
| **News ingestion** | Telethon (user client) | Monitor @WatcherGuru and other channels for breaking news |
| **Alert delivery** | python-telegram-bot | Send alerts to subscribed users via bot |

**Telethon specifics:**
- Session-isolated wrapper to prevent session corruption (`telegram_sync_wrapper.py`)
- Unique temp session per call with file copy
- Requires `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`

**CV language:** *"Integrated Telethon for real-time Telegram news ingestion and Telegram Bot API for user alert delivery."*

---

### Markets Tab — Composed Research Pipeline

The Markets tab is not a standalone chart — it **composes data from across the platform**:

```
Binance klines → ohlc_store → level_engine → market_research_service
TradingView quotes → cross-asset context
Economic calendar → catalysts[]
News cache → filtered headlines
Economy holistic scan → macro bias digest
Prediction markets → optional probability chips
Market sentiment → risk regime
```

**Market profiles** (`backend/services/markets/profiles/`) define per-instrument which platform sources to pull.

**Planned:** MT5 bridge for FX OHLC (`backend/mt5/README.md`) — EURUSD/GBPUSD/USDJPY registered but disabled until broker feed is live.

---

### Production Engineering Patterns

Worth highlighting in interviews — these show maturity beyond "I called some APIs":

| Pattern | File | Purpose |
|---------|------|---------|
| **Circuit breaker** | `circuit_breaker.py` | Stop cascading failures when external APIs fail |
| **Rate limiting** | `api_rate_limiter.py`, `dome_api_rate_limiter.py` | Respect free-tier API limits |
| **Multi-tier cache** | `persistent_news_cache.py` | Firebase → memory → disk fallback |
| **Smart GPT cache** | `smart_chatgpt_cache.py` | Cache analysis by event fingerprint |
| **Dead letter queue** | `dead_letter_queue.py` | Retry failed alert deliveries |
| **Cost tracking** | `ai_usage_tracker.py` | Per-user OpenAI spend |
| **Health endpoints** | `/api/health/*` | Per-subsystem health checks (news, AI, alerts, calendar) |
| **Fail-open AI** | `gemini_news_grounding_service.py` | Analysis continues if grounding fails |

**CV language:** *"Implemented production patterns including circuit breakers, multi-tier caching, API rate limiting, dead-letter queues, and per-user AI cost tracking."*

---

### Additional CV Bullets (Data/API Focus)

Add these to strengthen the technical story:

- Integrated **15+ external data APIs** across news (RSS, Telegram), market data (Binance klines, TradingView scanner), macro (Finnhub, ForexFactory, Google Sheets), and prediction markets (Polymarket, Kalshi/DOME).

- Built **Binance OHLC ingestion pipeline** with TradingView UDF resolution mapping, volume-profile level engine, and live quote alignment for crypto markets research.

- Designed **TradingView scanner integration** across forex, crypto, commodities, bonds, and indices with parallel multi-namespace fetching.

- Aggregated **prediction market data** from Polymarket (Gamma + CLOB) and Kalshi (DOME API) with custom rate limiting and forex-relevant event filtering.

- Connected **Google Sheets** as a live macro indicator data source for US/EU/UK/JP economies via service-account API.

---

## Key Files & Directories

### Root Structure

```
/fxsentinel
├── main.py                 # Railway Flask entry point
├── Dockerfile              # Container definition
├── Procfile                # Process definition
├── railway.json            # Railway config
├── vercel.json             # Vercel config
├── package.json            # Frontend dependencies
├── requirements.txt        # Python dependencies
├── index.html              # Vite entry
│
├── src/                    # React frontend
│   ├── components/         # UI components (43 files)
│   ├── contexts/           # React contexts (Auth, Notifications)
│   ├── hooks/              # Custom hooks
│   ├── utils/              # Analytics, helpers
│   └── config/             # Firebase, API config
│
├── backend/                # Python backend
│   ├── app.py              # Main Flask app (60+ routes)
│   ├── worker_app.py       # Background worker
│   └── services/           # 105+ service modules
│
├── api/                    # Serverless/webhook handlers
├── tests/                  # Test suite
├── docs/                   # Documentation (100+ files)
├── scripts/                # Utility scripts
└── data/                   # Static data (indicators, COT reports)
```

### Most Important Backend Services

| Category | Files |
|----------|-------|
| **AI Analysis** | `mvp_news_analyzer.py`, `gpt_ai_analysis.py`, `gemini_news_grounding_service.py`, `analysis_pipeline.py`, `optimized_chatgpt_analyzer.py` |
| **News** | `news_aggregator.py`, `persistent_news_cache.py`, `enhanced_forex_filter.py`, `telegram_sync_wrapper.py` |
| **Calendar** | `hybrid_economic_calendar.py`, `economy_holistic_scan_service.py`, `economic_calendar_alerts.py` |
| **Alerts** | `background_alert_worker.py`, `alert_service.py`, `unified_alert_deduplication.py` |
| **Payments** | `stripe_service.py`, `coupon_service.py`, `email_service.py` |
| **Market data** | `ohlc_ingest_binance.py`, `binance_ticker.py`, `tradingview_market_data.py`, `level_engine.py`, `market_research_service.py` |
| **Prediction markets** | `prediction_markets_service.py`, `dome_api_rate_limiter.py`, `polyrouter_api_client.py` |
| **Macro data** | `google_sheets_service.py`, `finnhub_historical.py`, `global_economic_calendar.py` |
| **Infrastructure** | `firebase_realtime_storage.py`, `smart_chatgpt_cache.py`, `ai_usage_tracker.py`, `circuit_breaker.py` |

### Most Important Frontend Components

| Component | Purpose |
|-----------|---------|
| `Dashboard.jsx` | Main app shell with tabs |
| `Overview.jsx` | Overview tab (news feed, calendar, sentiment) |
| `LiveNewsFeed.jsx` | Live news with AI analysis |
| `Economies.jsx` | Macro economies tab |
| `Markets.jsx` | Markets & charts tab |
| `Alerts.jsx` | Alert settings & history |
| `LandingPage.jsx` | Marketing landing page |
| `Login.jsx` / `Signup.jsx` | Authentication |

---

## CV Bullets (Ready to Use)

### Founder, Web App — FXSentinel (fxsentinel.io) | Remote | July 2025 – July 2026

- Solo-built a full-stack AI forex analysis platform across a **1,200+ file** codebase with **60+ REST endpoints**, integrating **15+ external APIs** including Stripe, Binance, TradingView, Finnhub and Kalshi with circuit breakers, rate limiters and caching.

- Grew to **525+ users**, **3,800+ followers**, and **6M+ social views** through GA4/GTM funnel tracking, ManyChat automation, and multi-channel content across TikTok, Instagram, and X; shipped a background alert system with impact scoring.

- Architected a hybrid LLM pipeline: Gemini for real-time web grounding and evidence retrieval, GPT for structured trade analysis, with smart caching, per-user cost tracking, fail-open fallbacks, and multi-source news ingestion from **8+ RSS feeds**.

---

## Interview Talking Points

### 30-Second Elevator Pitch

> "I built FXSentinel — an AI forex analysis platform for retail traders. It aggregates news from major financial sources, uses Gemini to ground analysis in real web evidence, then GPT to produce structured trade insights. There's a background alert worker, Stripe subscriptions, and full analytics from TikTok through to paid conversion. I'm the sole founder — product, backend, frontend, AI pipeline, and growth."

### "Hardest Technical Problem" — Pick One

**1. Hybrid LLM Pipeline**
- Challenge: Single-model analysis hallucinated or lacked context
- Solution: Gemini gathers tier-ranked web evidence first; GPT analysis is constrained to cite only that evidence
- Result: More grounded, verifiable analysis with fail-open fallback

**2. Multi-Source Data Orchestration**
- Challenge: 15+ APIs with different formats, rate limits, and failure modes
- Solution: Circuit breakers, tiered caching, rate limiters (e.g. DOME 1 req/s), stale fallbacks, hybrid calendar merge
- Files: `hybrid_economic_calendar.py`, `dome_api_rate_limiter.py`, `persistent_news_cache.py`, `circuit_breaker.py`

**3. Binance OHLC + Level Engine**
- Challenge: Need chart-quality bars and deterministic support/resistance for BTC research
- Solution: Binance klines ingest → `ohlc_store` → `level_engine` (PDH/PDL, volume profile POC/VAH/VAL) → `market_research_service`
- Files: `ohlc_ingest_binance.py`, `level_engine.py`, `feature_engine.py`

**4. Alert Deduplication at Scale**
- Challenge: Race conditions caused duplicate alerts to users
- Solution: Firebase-backed persistent deduplication with unified processor
- Files: `unified_alert_deduplication.py`, `persistent_alert_deduplication.py`

**3. News Cache Surviving Deploys + Outages**
- Challenge: Firebase egress outages caused slow synchronous fetches, hanging dashboard
- Solution: Multi-tier fallback — Firebase → in-memory → local disk mirror
- File: `persistent_news_cache.py`

**5. Economic Calendar Hybrid System**
- Challenge: Multiple data sources with inconsistent formats and missing events
- Solution: 27k-line hybrid merge system with validation and gap-filling
- File: `hybrid_economic_calendar.py`

### "What Would You Improve?"

1. **LLM evaluation framework** — systematic accuracy testing on known events
2. **Backtesting module** — validate AI signal performance historically
3. **TypeScript migration** — type safety for growing frontend
4. **Mobile client** — API is ready; Flutter/React Native read-only app
5. **CI/CD pipeline** — GitHub Actions on every PR

### Technical Depth Questions

| Question | Where to Point |
|----------|----------------|
| How does AI analysis work? | `mvp_news_analyzer.py` → `gemini_news_grounding_service.py` → `analysis_pipeline.py` |
| How do Binance klines work? | `ohlc_ingest_binance.py` → `ohlc_store.py` → `level_engine.py` → `/api/markets/{id}/ohlc` |
| How do prediction markets work? | `prediction_markets_service.py` → Polymarket Gamma/CLOB + Kalshi DOME + rate limiter |
| Where does macro data come from? | Finnhub + ForexFactory + Google Sheets → `hybrid_economic_calendar.py` + `google_sheets_service.py` |
| How do alerts work? | `background_alert_worker.py` → `alert_triggers.py` → `alert_service.py` |
| How is news cached? | `persistent_news_cache.py` with Firebase + local fallback |
| How do you track AI costs? | `ai_usage_tracker.py` with per-user OpenAI `user` parameter |
| How does auth work? | Firebase Auth → `AuthContext.jsx` → protected routes |

---

## Growth Areas (High Impact)

### 1. LLM Evaluation & Observability ⭐
**Why:** Turns "prompt engineering" into "production ML engineering"
**What exists:** `analysis_contract.py`, trace steps, `v1_observability`
**Next step:** Systematic evals — accuracy on known CPI/FOMC events, hallucination rate, evidence citation quality

### 2. Backtesting Module
**Why:** Closes gap with trading CV line; unique product differentiator
**What exists:** `persistent_news_cache.py` retains 30 days history "for future backtest features"
**Next step:** Simple report — "How did our AI bias perform after CPI releases?"

### 3. TypeScript Migration
**Why:** Standard interview-friendly upgrade for large React codebase
**Scope:** Start with `src/utils/`, `src/hooks/`, then components

### 4. Mobile App
**Why:** Adds Flutter to CV legitimately; API is ready
**Scope:** Read-only client — news feed, alerts, analysis viewer

### 5. CI/CD Pipeline
**Why:** Strengthens "production engineering" story
**What exists:** Many tests in `tests/` and `backend/test_*.py`
**Next step:** GitHub Actions — lint, test, deploy on PR

### 6. Prediction Markets (Finish Feature)
**Why:** Unique angle vs generic "AI news summarizers"
**What exists:** `prediction_markets_service.py`, API clients, chart popup
**Next step:** User-facing integration in Overview/Economies tabs

---

## What NOT to Overclaim

| Claim | Reality | Safe Alternative |
|-------|---------|------------------|
| "Built with Flutter" | React web app | "Built full-stack web app with React" |
| "In-app backtesting" | Not implemented | "Personal backtesting with TradingView/Excel" |
| "MT5 broker integration" | Planned, not live (`backend/mt5/`) | "Binance klines live; MT5 bridge planned for FX OHLC" |
| "ManyChat integration" | Marketing tool, not in code | "ManyChat automation for social-to-product conversion" |
| "Institutional-grade" | Retail-focused tool | "Institutional-style analysis for retail traders" |
| "Real-time WebSockets" | Polling-based updates | "Near real-time updates via polling" |

---

## Metrics You Can Cite

### Product Metrics
- **525+ registered users**
- Freemium → paid subscription (historically Stripe)

### Growth Metrics
- **6M+** social views
- **3,800+** social followers
- **Multi-channel acquisition:** TikTok, Instagram, X (+ ManyChat automation, GA4/GTM funnels)

### Technical Metrics
- **1,200+ files** in codebase
- **60+ REST API endpoints**
- **15+ external API integrations** (incl. Stripe, Binance, TradingView, Finnhub, Kalshi)
- Circuit breakers, rate limiters, caching
- Hybrid Gemini → GPT analysis pipeline
- **8+ RSS** news sources (+ Telegram)
- Background alert system with impact scoring

---

## Related Documentation

| Doc | Topic |
|-----|-------|
| `docs/FXSENTINEL_COMPREHENSIVE_DOCUMENTATION.md` | Full project documentation |
| `docs/LIVE_NEWS_FEED_SYSTEM_EVALUATION.md` | News system deep dive |
| `docs/AI_ANALYSIS_STRATEGY.md` | AI analysis approach |
| `docs/TRACKING_AND_SEO_IMPLEMENTATION_SUMMARY.md` | Analytics implementation |
| `docs/RAILWAY_DEPLOYMENT_FIXED.md` | Deployment architecture |
| `docs/BACKGROUND_WORKER_VS_MAIN_APP_EVALUATION.md` | Worker architecture |
| `docs/PREDICTION_MARKETS_SYSTEM.md` | Polymarket/Kalshi/DOME integration |
| `docs/MARKETS_TAB_PRODUCT_SPEC.md` | Markets tab + Binance/MT5 architecture |
| `docs/FINNHUB_INTEGRATION.md` | Finnhub calendar setup |
| `docs/DOME_API_INTEGRATION.md` | Kalshi via DOME API |
| `docs/GOOGLE_SHEETS_INTEGRATION_EVALUATION.md` | Google Sheets macro data |
| `docs/TRADINGVIEW_API_ACCESS_GUIDE.md` | TradingView scanner usage |
| `backend/mt5/README.md` | Planned MT5 OHLC bridge |

---

## Quick Reference: API Endpoints

Key endpoints for understanding the system:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/news` | Aggregated news feed |
| `GET /api/analysis/<news_id>` | AI analysis for news item |
| `GET /api/analysis/<news_id>/related-evidence` | Gemini grounding warmup |
| `GET /api/economic-calendar` | Economic events |
| `POST /api/economy-scan/<country>` | Holistic macro scan |
| `GET /api/alerts` | User alerts |
| `POST /api/alerts/trigger` | Trigger alert (worker) |
| `GET /api/forex-prices` | Live forex prices (TradingView scanner) |
| `GET /api/market-sentiment` | Multi-source sentiment fusion |
| `GET /api/prediction-markets` | Prediction market data (Polymarket/Kalshi) |
| `GET /api/economy-indicators/{country}` | Macro indicators (Google Sheets) |
| `GET /api/markets` | Enabled markets list |
| `GET /api/markets/BTCUSD/ohlc` | Binance OHLC bars |
| `GET /api/markets/BTCUSD/quote` | Live Binance spot quote |
| `GET /api/markets/BTCUSD/research` | Full market research DTO |
| `GET /api/udf/history` | TradingView UDF chart history |
| `GET /api/health` | System health check |

---

*This document is grounded in codebase analysis as of July 2026. Update metrics and claims as the product grows.*
