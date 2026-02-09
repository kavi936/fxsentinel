# Usage Billing Fix Summary & Rate Limiting

Summary of the **usage/billing fix** (now working locally) and what remains for **rate limiting**.

---

## 1. What Was Fixed (Usage Updates Successfully Locally)

### Problem

- **Firestore rejected `datetime.date`**: Firestore only accepts `datetime.datetime` (or timestamp types), not Python `datetime.date`.
- The code wrote `last_daily_reset` and `last_monthly_reset` as `date` objects, causing:
  - `Error ensuring user doc exists: ('Cannot convert to a Firestore Value', datetime.date(...), 'Invalid type' ...)`
  - `Error incrementing analysis count: ...`
  - `Error checking analysis permission: ...`
- Result: user docs could not be created/updated, analysis count did not increment, and the billing UI did not update (e.g. stayed at 0/15).

### Fix (in `backend/services/stripe_service.py`)

1. **`_date_to_firestore(d)`**  
   Converts a Python `date` to a timezone-aware `datetime` at start-of-day UTC before any Firestore write.

2. **`_firestore_to_date(v)`**  
   Converts a value read from Firestore (e.g. `DatetimeWithNanoseconds` or datetime) to a `date` so comparisons like `last_daily_reset != today` work correctly.

3. **All writes** of date/time fields now use:
   - `_date_to_firestore(today)` / `_date_to_firestore(current_month_start)` for `last_daily_reset` and `last_monthly_reset`.
   - `datetime.now(timezone.utc)` (or `datetime.fromtimestamp(..., tz=timezone.utc)`) for timestamp fields (e.g. `account_created`, `webhook_processed_at`).

4. **All reads** that compare to `today` or `current_month_start` use `_firestore_to_date(...)` so stored datetimes are compared as dates.

5. **Places updated**: `_ensure_user_doc_exists`, `create_customer`, `can_perform_analysis`, `increment_analysis_count`, `handle_subscription_created`, `handle_subscription_updated`, `handle_subscription_deleted`, `handle_payment_succeeded`, `handle_payment_failed`.

### Outcome

- User documents are created and updated without Firestore type errors.
- Analysis count increments correctly after each analysis (e.g. 0/15 → 1/15).
- Subscription status and check-analysis-permission work; the billing section in the profile popup updates as expected locally.

### Related Docs

- **Troubleshooting**: `docs/AI_ANALYSIS_BILLING_AND_OPENAI_USAGE_ANALYSIS.md` (sections 8 and 7).
- **Architecture**: same doc, sections 1–3 (tracking, billing UI, Firestore).

---

## 2. Rate Limiting: Current State

### 2.1 Flask-Limiter (API-level)

- **Library**: `flask-limiter`; key function: `get_remote_address` (IP-based).
- **Default limits**: `200 per day`, `50 per hour` (app-wide when no per-route limit).
- **Storage**: `memory://` (in-process; not shared across workers or instances).

| Endpoint / area              | Limit              | Notes                          |
|-----------------------------|--------------------|---------------------------------|
| `GET /api/analysis/<id>`    | 5 per minute       | Live news analysis              |
| `GET/POST /api/enhanced-analysis/<id>` | Default only (50/hour, 200/day) | No per-route decorator |
| Stripe checkout             | 10 per minute      |                                |
| Coupon / verify              | 20 per minute      |                                |
| Portal / email / refund      | 3–5 per minute/hour |                                |
| Health / webhooks / many internal | Exempt            |                                |

So:

- **Live news analysis** is rate limited per IP (5/min).
- **Enhanced (calendar) analysis** has no per-route limit beyond the default 50/hour, 200/day per IP.
- Limits are **per IP**, not per user; one user behind one IP shares the same bucket with others on that IP.

### 2.2 In-analyzer rate limiting (OpenAI)

- **MVP News Analyzer** (`backend/services/mvp_news_analyzer.py`): `_check_rate_limit()` caps calls per hour (e.g. `max_calls_per_hour`); when exceeded, falls back to non-GPT analysis. Resets on the hour.
- **GPT AI Analysis** (`backend/services/gpt_ai_analysis.py`): Similar `_check_rate_limit()` to avoid exceeding OpenAI usage; can fall back to a lighter analysis.
- These protect **OpenAI cost and quota**, not per-user abuse (they are process-wide, not per user).

### 2.3 Other services

- **Prediction markets**: `dome_api_rate_limiter` (e.g. 1 req/s, 10 per 10s) for external APIs.
- **TradingView**: 429 handling and backoff in the backend.

---

## 3. What Needs to Be Done for Rate Limiting

If the goal is to **harden abuse prevention and align limits with your product** (free 15/month, premium 50/day), consider the following.

### 3.1 Per-user rate limiting (recommended)

- **Current**: Quota is enforced in business logic (`can_perform_analysis` + `increment_analysis_count`); API limits are per IP.
- **Gap**: A single IP could hit the analysis endpoints many times (e.g. many users on same network, or one user with multiple tabs), and the only cap is the global/IP limit (e.g. 5/min for `/api/analysis`) or default 50/hour for enhanced-analysis.
- **Options**:
  - Use a **per-user key** for the limiter when a valid Firebase token is present (e.g. `key_func` that returns `user_id` from token when available, else `get_remote_address`). Then apply limits **per user** (e.g. 10 analysis requests per minute per user) so heavy users cannot starve others on the same IP.
  - Keep **quota** (15/month, 50/day) as the main product limit; use **per-user rate limits** to smooth traffic (e.g. max N analyses per minute per user) and avoid bursts that look like abuse.

### 3.2 Apply a limit to enhanced-analysis

- **Current**: `/api/enhanced-analysis/<news_id>` has no `@limiter.limit(...)`.
- **Todo**: Add a per-route limit, e.g. `@limiter.limit("10 per minute")` (or use the same per-user key as above so it’s 10 per minute per user). This avoids one client hammering the endpoint within the default 50/hour.

### 3.3 Check analysis permission before running analysis

- **Current**: Permission is checked in the frontend and via `/api/check-analysis-permission`; the analysis endpoints may still run the analysis and then increment. Ensure **both** live news and enhanced-analysis call `stripe_service.can_perform_analysis(...)` **before** running the expensive analysis and return 429 or a clear “limit reached” response when `can_perform` is False. That way quota and rate limiting are enforced at the API layer.

### 3.4 Production: shared storage for limits

- **Current**: `storage_uri="memory://"` — limits are per process; multiple workers or instances do not share counters.
- **Todo**: For production, use a shared backend (e.g. **Redis**): `storage_uri="redis://..."`. Then rate limits apply across all app instances and restarts.

### 3.5 Optional: stricter defaults

- Tighten default app-wide limits (e.g. 30/hour instead of 50) if you want a harder cap for unauthenticated or misbehaving clients; keep exempt routes (health, webhooks) as they are.

---

## 4. Summary Table

| Item | Status | Action |
|------|--------|--------|
| Usage/billing Firestore date fix | Done | — |
| User doc creation for new users | Done | — |
| Analysis count increment | Done | — |
| Billing UI updating locally | Done | — |
| Per-user rate limiting | Done | `_rate_limit_key()` in `app.py`: user_id from token when present, else IP; limiter uses it |
| Limit on `/api/enhanced-analysis` | Done | `@limiter.limit("10 per minute")` on route |
| Check `can_perform_analysis` before analysis | Done | Both `/api/analysis` and `/api/enhanced-analysis` call it first and return 429 with `analysis_limit_reached` when `can_perform` is False |
| Redis (or shared) storage for limiter | Not done | Set `storage_uri="redis://..."` in production when scaling to multiple workers |
| In-analyzer OpenAI rate limits | Done | Already protect cost; optional: tune or expose config |

This doc can sit alongside `AI_ANALYSIS_BILLING_AND_OPENAI_USAGE_ANALYSIS.md` and `AI_ANALYSIS_USAGE_SYSTEM_ANALYSIS.md` for a single place to see what was fixed and what remains for rate limiting.
