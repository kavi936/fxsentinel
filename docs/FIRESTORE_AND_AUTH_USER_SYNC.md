# Firestore and syncing Auth users

## What Firestore is used for in FXSentinel

Your production Firestore database is used for:

| Use | Collection / fields | Purpose |
|-----|---------------------|--------|
| **Billing / usage** | `users/<uid>`: `subscription_status`, `monthly_analysis_count`, `daily_analysis_count`, `last_monthly_reset`, `last_daily_reset`, `stripe_customer_id` | Free vs premium limits, Stripe linkage, usage quotas |
| **Analytics** | `users/<uid>`: `total_ai_analyses`, `last_ai_usage`, `daily_ai_usage.{date}`; `ai_usage_logs` | Who used AI, when, and how much |
| **Profile / identity** | `users/<uid>`: `user_email`, `user_name`, `account_created` | Optional display and audit (set when doc is created or updated) |

Firebase **Authentication** holds who can sign in (email, password, providers, UID). Firestore **users** holds app-level state: tier, counts, and optional profile. They are linked by **UID**: `users/<uid>` in Firestore should use the same `uid` as in Firebase Auth.

## Why some users have no Firestore doc

A `users/<uid>` document is created **lazily** when:

- The user opens the subscription/billing UI (backend calls `get_subscription_status` → `_ensure_user_doc_exists`), or
- The user runs an AI analysis (billing calls `increment_analysis_count` or usage tracker creates/updates the doc).

So anyone who **only** signed up (Firebase Auth) and never hit billing or AI analysis has **no** `users/<uid>` document. For those users, the app still works: the first time they hit subscription status or run an analysis, the doc is created. Until then, subscription status defaults to “free” with 0 usage in code, but having a doc in Firestore gives you a single source of truth and consistent behavior (e.g. Billing tab shows 0/15).

## What you can do

1. **One-time backfill**  
   Run the script that syncs **all** Firebase Auth users into Firestore: for each Auth user, if `users/<uid>` does not exist, create it with free-tier defaults and (optionally) email/display name from Auth. That way every existing Auth user has a Firestore doc even if they never opened Billing or ran analysis.

2. **Rely on lazy creation (no script)**  
   Do nothing: when a user first hits subscription status or AI analysis, the backend already creates `users/<uid>`. Existing users will get a doc on first use.

3. **Use Firestore for more**  
   You can extend `users/<uid>` (or add other collections) for:
   - Preferences (timezone, theme, default pairs)
   - Feature flags or onboarding state
   - Notifications / alert settings
   - Audit trail of important actions

Recommendation: run the one-time backfill so all current Auth users have a Firestore doc; then keep relying on lazy creation for new signups.

## Running the backfill script

From the repo root (or backend):

```bash
cd backend
python scripts/sync_auth_users_to_firestore.py
```

The script uses the same Firebase Admin setup as `list_firebase_users.py` (e.g. `backend/firebase-service-account.json` or env). It will:

- List all users from Firebase Authentication (paginated).
- For each UID, check if `users/<uid>` exists in Firestore.
- If it does **not** exist, create it with:
  - `subscription_status`: `'free'`
  - `monthly_analysis_count` / `daily_analysis_count`: `0`
  - `last_monthly_reset` / `last_daily_reset`: current month/day (UTC)
  - `account_created`: now
  - `user_email` / `user_name`: from Auth (when available)

It will **not** overwrite existing `users/<uid>` documents (no Stripe or usage data is changed).
