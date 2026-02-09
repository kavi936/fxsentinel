# AI Analysis Usage: Tracking, Billing UI, and OpenAI Dashboard

This document analyses and evaluates how the codebase tracks AI analysis usage, shows it in the profile billing section, and surfaces it in OpenAI’s API usage platform.

---

## 1. Architecture Overview

There are **three separate but related systems**:

| System | Purpose | Where it lives |
|--------|--------|----------------|
| **Billing / quota** | Enforce and display free (15/month) and premium (50/day) limits | `stripe_service`, Firestore `users` doc fields: `monthly_analysis_count`, `daily_analysis_count`, reset fields |
| **Analytics / logging** | Log who used AI, when, and what type (for feedback, analytics) | `ai_usage_tracker`, Firestore `ai_usage_logs` + `users` (e.g. `total_ai_analyses`, `daily_ai_usage.{date}`) |
| **OpenAI usage dashboard** | Per-user usage in OpenAI’s UI (platform.openai.com/usage) | OpenAI API `user` parameter set in `gpt_ai_analysis.py` and `mvp_news_analyzer.py` |

Billing counts and analytics both write to the same Firestore **`users`** collection (by `user_id`). Billing uses `monthly_analysis_count` / `daily_analysis_count`; analytics uses `total_ai_analyses`, `last_ai_usage`, `daily_ai_usage.{date}`, etc.

---

## 2. Tracking User AI Analysis Usage

### 2.1 Entry points

AI analysis is triggered from two places; both track usage and support OpenAI’s `user` parameter.

- **Economic calendar**  
  - Route: `POST /api/enhanced-analysis/<news_id>` (or GET with event from calendar).  
  - Frontend: `Overview.jsx` (sends `Authorization: Bearer <idToken>` and optionally body `user_id` / `user_email`).  
  - Backend: `app.py` → `_extract_user_from_token()` then token (or body) → `user_info` → `gpt_ai_analyzer.analyze_macro_event(..., user_info=user_info)`.

- **Live news (dashboard)**  
  - Route: `GET /api/analysis/<news_id>`.  
  - Frontend: `LiveNewsFeed.jsx` (sends `Authorization: Bearer <idToken>`).  
  - Backend: `app.py` → `generate_news_analysis()` → `_extract_user_from_token()` → `mvp_news_analyzer.analyze_news(..., user_info=token_user_info)`.

So **user identity is taken from the Firebase ID token first**; body is only a fallback for calendar. That way the backend uses a verified identity for tracking and for the OpenAI `user` parameter.

### 2.2 What gets written

**Billing (StripeService)**  
- `stripe_service.increment_analysis_count(user_id, email)` is called:
  - In **enhanced-analysis** (in `app.py` after GPT analysis, when `user_info` exists).
  - In **live news** (in `app.py` after `generate_news_analysis`, when `token_user_info` and analysis succeeded).
- It updates the Firestore `users/<user_id>` doc:
  - **Premium**: `daily_analysis_count` += 1, `last_daily_reset` = today if new day.
  - **Free**: `monthly_analysis_count` += 1, `last_monthly_reset` = current month start if new month.
- Developers (by email) are skipped and not incremented.

**Analytics (AIUsageTracker)**  
- `ai_usage_tracker.track_analysis_usage(user_info, analysis_type, event_id, model_used, cost_estimate, cache_hit)`:
  - In **enhanced-analysis**: called in `app.py` with `user_info`, `analysis_type`, `event_id`, `model_used`, `cost_estimate`, `cache_hit`.
  - In **live news**: called inside `mvp_news_analyzer.analyze_news()` when a GPT call is made (with `user_info`).
- It:
  - Appends a document to **`ai_usage_logs`** (per-request log).
  - Updates **`users`** (by `user_id` or `email_<hash>`): `last_ai_usage`, `last_ai_usage_type`, `total_ai_analyses` += 1, `daily_ai_usage.<date>` += 1.

So **usage is tracked in two ways**: quota (billing) and analytics (logs + aggregates). Both use the same `users` collection keyed by the same `user_id` when the user is logged in via Firebase.

---

## 3. Displaying Usage in the Billing Section (Profile Popup)

### 3.1 Data sources

The profile popup uses two API calls:

1. **Subscription and counts**  
   - **Endpoint**: `GET /api/subscription-status/<uid>?email=...`  
   - **Handler**: `stripe_service.get_subscription_status(user_id, email)`  
   - **Returns**: `status`, `monthly_analysis_count`, `daily_analysis_count`, `monthly_limit`, `daily_limit`, `stripe_customer_id`, `is_developer`, etc.  
   - **UI**: Stored in `subscriptionStatus`. The **billing section uses this** to show plan (Free/Premium), limits (e.g. 15 or 50), and **usage counts** (e.g. “5/15”, “12/50”) and the progress bar.

2. **Permission and usage (for notifications)**  
   - **Endpoint**: `GET /api/check-analysis-permission/<uid>?email=...`  
   - **Handler**: `stripe_service.can_perform_analysis(user_id, email)`  
   - **Returns**: `can_perform`, `daily_usage`, `monthly_usage`, `daily_limit`, `monthly_limit`, `status`.  
   - **UI**: Stored in `usageData`. Used for **usage notifications** (e.g. limit reached, low remaining), not for the main billing numbers.

Both endpoints read the same Firestore `users` document, so the numbers are consistent. The visible “X / limit” in the billing tab comes from **subscription-status** (`subscriptionStatus.monthly_analysis_count` / `subscriptionStatus.daily_analysis_count`).

### 3.2 Where it’s shown in the UI

- **ProfilePopup.jsx**  
  - **Billing tab** (`activeTab === 'billing'`):  
    - Free: “Monthly Limit: {monthly_analysis_count}/15”, progress bar, “X remaining this month”.  
    - Premium: “Daily Limit: {daily_analysis_count}/50”, progress bar, “X remaining today”.  
  - **Notifications**: `useEffect` on `usageData` and `subscriptionStatus` calls `addUsageNotification('usage_limit_reached' | 'usage_warning', ...)` so the user sees when they’re at or near the limit.

So: **tracking** is done when an analysis runs (increment in backend); **display** is done by the profile popup reading subscription-status (and check-analysis-permission for notifications). No separate “usage API” is needed for the main billing numbers.

---

## 4. Seeing Usage in OpenAI’s API Usage Platform

OpenAI’s dashboard (e.g. https://platform.openai.com/usage) can show usage **per user** if the API is called with the optional **`user`** parameter.

### 4.1 How it’s set

- **Economic calendar (GPT)**  
  - **File**: `backend/services/gpt_ai_analysis.py`.  
  - **Logic**: `openai_user = user_info.get('user_email') or user_info.get('user_id')`. If present, `api_params["user"] = openai_user` is set before `client.chat.completions.create(**api_params)`.  
  - So the same identifier (email or uid) is sent to OpenAI and used in their “Users” view.

- **Live news (MVP)**  
  - **File**: `backend/services/mvp_news_analyzer.py`.  
  - **Logic**: Same idea — `openai_user = user_info.get('user_email') or user_info.get('user_id')`, then `api_params["user"] = openai_user` on the completion call.

So **both analysis paths** send a stable user identifier to OpenAI when `user_info` is present. That identifier is what appears in the OpenAI usage platform under “Users”.

### 4.2 What the user (you) sees

- In **OpenAI dashboard** → Usage: you can filter or group by **Users**. Each value you pass as `user` (e.g. email or Firebase uid) shows up there, so you can see usage per end-user of your app.  
- This is **independent** of your own app’s billing UI: the app’s billing section is driven by Firestore counts; OpenAI’s dashboard is driven by the `user` parameter on each API call.

### 4.3 When it might not show per-user

- **No token / no user_info**: If the frontend doesn’t send `Authorization: Bearer <idToken>` or the backend can’t extract the user, `user_info` is missing and `user` is not set; usage then appears under your API key only, not per user.  
- **Cached responses**: Cached analyses don’t call the OpenAI API, so they don’t create new usage entries in the OpenAI dashboard. They still increment your app’s billing count (see below).

---

## 5. Evaluation and Potential Issues

### 5.1 Strengths

- **Single source of truth for billing**: One `users` document per user holds both subscription state and usage counts; subscription-status and check-analysis-permission both read from it, so the profile popup stays consistent.  
- **Token-first identity**: User is taken from the Firebase token (and only fallback to body for calendar), which is good for security and for correct attribution in OpenAI.  
- **Dual tracking**: Billing (quota) and analytics (logs + aggregates) are both implemented; you can enforce limits and also analyse behaviour.  
- **OpenAI `user` parameter**: Used in both GPT and MVP analyzers so usage is visible per user in the OpenAI dashboard.  
- **Clear separation**: Billing logic in `stripe_service`, analytics in `ai_usage_tracker`, and OpenAI attribution in the analyzers; no circular dependencies.

### 5.2 Cache hits and billing count

- **Current behaviour**: In `app.py`, after enhanced-analysis, `stripe_service.increment_analysis_count(...)` is called whenever `user_info` exists, **regardless of `cache_hit`**. So a cached analysis (no OpenAI call) still increases the user’s quota (e.g. 1 more of 15 or 50).  
- **Implication**: From the **product** perspective this can be intentional (“one analysis consumed from the user’s allowance”). From a **cost** perspective, cache hits don’t cost OpenAI money, so you could argue they shouldn’t count.  
- **Recommendation**: Decide explicitly:  
  - If “quota = number of analyses shown to the user”, keep current behaviour.  
  - If “quota = number of billable OpenAI calls”, only call `increment_analysis_count` when `cache_hit` is false (and similarly in live news if you add caching there).

### 5.3 Live news: no cache_hit check for billing

- For live news, `increment_analysis_count` is called whenever the analysis succeeds; the MVP analyzer may or may not use caching. If you introduce caching there, consider only incrementing when the request actually hit the API (e.g. when not a cache hit), to align with the policy you choose above.

### 5.4 Document ID consistency (analytics)

- **AIUsageTracker** uses `doc_id = user_id if user_id else ('email_' + hashlib.sha256(user_email).hexdigest()[:28])` for the `users` document.  
- **StripeService** uses `user_id` (Firebase uid) from the token.  
- So for **logged-in users** (token present), both use the same Firebase uid and the same document. For **anonymous or token-less** requests, the tracker might create/update an `email_xxx` document while Stripe still uses `user_id`; in practice, analysis is gated by login and token, so this is mostly theoretical.

### 5.5 Profile: two requests for overlapping data

- The popup calls both **subscription-status** and **check-analysis-permission**. They return overlapping usage info (subscription-status has the counts the UI uses; check-analysis-permission has `can_perform` and usage for notifications). This is a small redundancy but keeps permission logic and display logic clear; acceptable unless you want to reduce round-trips.

### 5.6 Developer / beta handling

- Developers are excluded from `increment_analysis_count` (by email). They still get Firestore analytics and OpenAI `user` if they’re logged in. So their usage is visible in OpenAI and in `ai_usage_logs`, but not in the billing quota. That’s consistent with “developer = unlimited quota”.

---

## 6. Summary Table

| Question | Answer |
|----------|--------|
| Where is AI analysis usage tracked? | On each analysis: `stripe_service.increment_analysis_count()` (billing) and `ai_usage_tracker.track_analysis_usage()` (analytics). Both use Firestore `users` (and `ai_usage_logs` for logs). |
| Where is it shown in the app? | Profile popup → Billing tab. Counts come from `GET /api/subscription-status/<uid>`. Notifications use `GET /api/check-analysis-permission/<uid>`. |
| How does it show in OpenAI’s platform? | Backend sets `user` on OpenAI API calls (in `gpt_ai_analysis.py` and `mvp_news_analyzer.py`) to email or Firebase uid. Usage then appears per user in https://platform.openai.com/usage (Users). |
| What could be improved? | (1) Decide whether cache hits should count toward quota and, if not, only increment when `cache_hit` is false. (2) If live news gets caching, apply the same rule there. |

---

## 7. Key code references

- **Billing increment**: `backend/services/stripe_service.py` — `increment_analysis_count()`, `can_perform_analysis()`, `get_subscription_status()`.  
- **Analytics**: `backend/services/ai_usage_tracker.py` — `track_analysis_usage()`, `get_user_usage_stats()`, `get_active_users()`.  
- **OpenAI `user`**: `backend/services/gpt_ai_analysis.py` (around line 1226–1256), `backend/services/mvp_news_analyzer.py` (around 572–593).  
- **API usage wiring**: `backend/app.py` — enhanced-analysis (e.g. 2082–2294), analysis for news (e.g. 1825–1835), `check_analysis_permission` (5443), `get_subscription_status` (5404).  
- **Profile UI**: `src/components/ProfilePopup.jsx` — `fetchSubscriptionStatus()`, `fetchUsageData()`, billing tab rendering and usage notifications.  
- **Token sending**: `src/components/Overview.jsx`, `src/components/LiveNewsFeed.jsx` — `Authorization: Bearer ${authToken}` with `currentUser.getIdToken()`.

This should give you a full picture of how tracking, billing UI, and OpenAI usage fit together and where to adjust behaviour (e.g. cache hits) if needed.

---

## 8. Troubleshooting

### Billing section not updating (always 0/15 for another user)

**Cause**: The Firestore document `users/<user_id>` did not exist for new users. It was only created when going through Stripe checkout, so free users who never clicked “Upgrade” had no document. `increment_analysis_count` returned early when the doc was missing, and `get_subscription_status` always returned default 0.

**Fix (implemented)**: The backend now creates the user document when it is missing:
- In `get_subscription_status`: create doc with 0 counts when the user opens the profile (Billing tab).
- In `can_perform_analysis`: create doc with 0 counts when checking permission (e.g. before analysis).
- In `increment_analysis_count`: create doc with count 1 when the user’s first analysis runs and no doc existed yet.

So the first time a new user opens Billing or runs an analysis, their `users` doc is created and subsequent usage is counted and shown correctly.

### OpenAI usage dashboard shows only one user (e.g. only “Kavi Choudhary”)

**Causes**:
1. **No token sent** – Backend needs `Authorization: Bearer <idToken>`. If the header is missing, for **GET** requests (e.g. Live News analysis) there is no user identity, so usage is not attributed to a user. For **POST** (Economic calendar) the body still has `user_id` / `user_email`, so attribution can work if the backend uses that (it does).
2. **Token invalid or wrong project** – If the backend’s Firebase Admin is initialized with a different project than the one that issued the token, `verify_id_token` fails and the backend gets no user. Then for GET there is no user; for POST the body fallback still applies.
3. **Live News uses GET** – There is no body, so user identity comes only from the token. If the token is missing or invalid, that request is not attributed to any user.

**What to do**:
- In the browser: DevTools → Network → select the analysis request and confirm the request has header `Authorization: Bearer <long string>`.
- In backend logs: look for “Extracted user from token: …” (success) or “Could not extract user from token” / “Using user from request body (no valid token)” (token missing or invalid).
- Ensure the backend’s Firebase project (e.g. `firebase-service-account.json` or `GOOGLE_APPLICATION_CREDENTIALS`) is the **same** project as the one used by the frontend (Firebase config). Otherwise tokens from the app will not verify and only the POST body (calendar) will carry user identity.
- For **Economic calendar** the frontend sends POST with `user_id` and `user_email` in the body, so even if the token fails, that user can still be used for billing and for the OpenAI `user` parameter. For **Live News** the request is GET with no body, so a valid token is required for per-user attribution.
