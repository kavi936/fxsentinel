# FXSentinel

**AI-powered forex & macro intelligence** — turn market-moving news into clear trading context.

**Live:** [fxsentinel.io](https://fxsentinel.io)  
**Founder:** [Kavi C](https://github.com/kavi936) · sole builder (product, engineering, AI, growth)

> Portfolio / demo deployment of a production fintech system I designed, shipped, and operated as a founder. Built end-to-end over ~a year: multi-source data ingestion, hybrid LLM analysis, alerts, payments, and growth analytics.

---

## What it does

Retail traders drown in headlines and miss *why* a release moves EUR/USD, gold, or risk sentiment. FXSentinel:

1. **Aggregates** forex-relevant news (RSS + optional Telegram)
2. **Filters & caches** for relevance (Firebase-backed persistence)
3. **Analyzes** with a hybrid LLM pipeline — Gemini for web grounding, GPT for structured insight
4. **Surfaces** everything in a React dashboard (Overview, Economies, Markets) with calendar, sentiment, and research context
5. **Monetized** via freemium AI quotas + Stripe (demo deploy has checkout soft-disabled)

---

## Impact (from professional CV)

**Founder, Web App — FXSentinel** ([fxsentinel.io](https://fxsentinel.io)) · Remote · July 2025 – July 2026

| Metric | Figure |
|--------|--------|
| Codebase | **1,200+** files |
| API surface | **60+** REST endpoints · **15+** external APIs |
| Users | **525+** |
| Social | **3,800+** followers · **6M+** views |
| News | **8+** RSS feeds (+ Telegram) |

- Solo-built a full-stack AI forex analysis platform across a **1,200+ file** codebase with **60+ REST endpoints**, integrating **15+ external APIs** including Stripe, Binance, TradingView, Finnhub and Kalshi with circuit breakers, rate limiters and caching.
- Grew to **525+ users**, **3,800+ followers**, and **6M+ social views** through GA4/GTM funnel tracking, ManyChat automation, and multi-channel content across TikTok, Instagram, and X; shipped a background alert system with impact scoring.
- Architected a hybrid LLM pipeline: Gemini for real-time web grounding and evidence retrieval, GPT for structured trade analysis, with smart caching, per-user cost tracking, fail-open fallbacks, and multi-source news ingestion from **8+ RSS feeds**.

The company is no longer operating as an active SaaS; this repo and site are kept as a **working technical portfolio**. Current demo API runs on Render (web-only / live-lite); production historically used Railway for API + worker.

---

## System highlights

| Area | Outcome |
|------|---------|
| **Full-stack product** | React 19 + Vite frontend (Vercel) · Python/Flask API (60+ routes, 100+ services) |
| **Hybrid AI** | Gemini grounding → GPT structured analysis, caching, per-user cost tracking, fail-open fallbacks |
| **Data layer** | 15+ integrations: RSS, Finnhub, TradingView, Binance OHLC, Google Sheets macro, Polymarket/Kalshi context |
| **Macro desk** | Hybrid economic calendar, Economies scans, central-bank document library |
| **Alerts** | Telegram + email worker with dedup / DLQ (disabled on this lean demo host to cut cost) |
| **Growth** | Stripe freemium, Firebase Auth, GA4/GTM funnels, SEO blog, social acquisition |
| **Ops maturity** | Circuit breakers, rate limits, multi-tier cache, health endpoints |

---

## Architecture (current demo)

```text
Browser  →  Vercel (React SPA + SEO)
                │  VITE_API_URL
                ▼
         Render free (Flask + Gunicorn, web only)
                │
     Firebase · RSS / public APIs · optional OpenAI/Gemini
```

- **No alert worker** on the free-tier host (`LIVE_LITE_MODE=true`) — keeps memory/cost near zero.
- Render free tier **cold-starts** after idle (~30–60s). Warm [api health](https://fxsentinel-api.onrender.com/api/health) once before a live demo.

Canonical deep-dives: [`docs/GENERAL_SYSTEM_ARCHITECTURE.md`](docs/GENERAL_SYSTEM_ARCHITECTURE.md) · [`docs/FXSENTINEL_CV_AND_CODEBASE_GUIDE.md`](docs/FXSENTINEL_CV_AND_CODEBASE_GUIDE.md)

---

## Tech stack

**Frontend:** React 19, Vite 7, React Router, Firebase Auth, Framer Motion, lightweight-charts  
**Backend:** Python, Flask, Gunicorn  
**AI:** OpenAI GPT, Google Gemini  
**Data / infra:** Firebase (Auth, Firestore/Realtime), Stripe, Resend, Redis (optional)  
**Hosting:** Vercel (frontend) · Render (API, live-lite)

---

## Repo map

| Path | Role |
|------|------|
| `src/` | React app (landing, dashboard, blog) |
| `backend/` | Flask API + services |
| `backend/services/` | News, AI, calendar, markets, payments |
| `docs/` | Architecture, runbooks, product notes |
| `config/env.example` | Env var names (no secrets) |
| `render.yaml` | Render blueprint for live-lite API |

---

## Run locally

**Frontend**

```bash
npm install
npm run dev
```

**Backend**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# copy config/env.example → backend/.env and fill keys locally
LIVE_LITE_MODE=true python3 main.py
```

Never commit `.env`, service-account JSON, or Telegram `.session` files. See [`docs/LIVE_LITE_SECURITY_ROTATION.md`](docs/LIVE_LITE_SECURITY_ROTATION.md) and [`SECURITY.md`](SECURITY.md).

---

## Status

| Surface | State |
|---------|--------|
| Landing + auth | Live on Vercel |
| Dashboard Overview (news / calendar / sentiment) | Served by Render API |
| AI Analyze | Works when OpenAI/Gemini keys are configured on Render |
| Alerts tab | Hidden in live-lite (no worker) |
| Stripe checkout | Soft-disabled on demo host |

---

## License

All rights reserved © Kavi C.  
This repository is published for **portfolio and educational visibility**. You may view and learn from the code; you may not redistribute or operate it as a competing commercial service without written permission.

---

## Contact

Built by **Kavi C** — [github.com/kavi936](https://github.com/kavi936) · live product: [fxsentinel.io](https://fxsentinel.io)
