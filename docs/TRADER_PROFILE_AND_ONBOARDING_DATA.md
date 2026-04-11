# Trader profile & onboarding data

This document describes where onboarding and trading-preference data lives, how it is accessed, and how you can use it for product behavior, analysis, and marketing.

## Storage (Firestore)

All of this is stored on the **same document** as billing and other app state:

| Location | Description |
|----------|-------------|
| Collection | `users` |
| Document ID | Firebase Auth **UID** (same as `users/{uid}` used for Stripe, usage counts, etc.) |

Writes use **`set(..., merge=True)`**, so existing fields such as `subscription_status`, `monthly_analysis_count`, or `stripe_customer_id` are **not** wiped when saving `trader_profile` or onboarding timestamps.

### Fields at document root (`users/{uid}`)

| Field | Type | Purpose |
|-------|------|---------|
| `trader_profile` | `map` | See below — main preference payload |
| `onboarding_survey_completed_at` | `timestamp` | Set when the user **completes** the survey (full submit) |
| `onboarding_survey_skipped_at` | `timestamp` | Set when the user taps **Skip for now** (no `trader_profile` required) |
| `onboarding_survey_version` | `number` | Schema version (currently `1`); bump if you add breaking survey changes |
| `user_email` | `string` | Optional; may be set on merge when saving from the API |

If **both** `onboarding_survey_completed_at` and `onboarding_survey_skipped_at` are absent, the app treats the user as **needing the onboarding survey** (`needs_survey: true` from the API).

### Map: `trader_profile`

| Field | Type | Notes |
|-------|------|--------|
| `trading_style` | `string` | One of: `day`, `swing`, `both`, `unsure` |
| `experience_level` | `string` | One of: `beginner`, `intermediate`, `advanced` |
| `primary_pairs` | `array<string>` | Up to **24** instruments, each `BASE/QUOTE` (e.g. `EUR/USD`, `XAU/USD`, `US500/USD`). Validated server-side. |
| `marketing_opt_in` | `boolean` | Product tips / occasional offers by email |
| `primary_goal` | `string` | One of: `stay_informed`, `analysis_workflow`, `alerts`, `learning`, `other` |
| `referral_source` | `string` | One of the allowed slugs (search, social platforms, friend, etc.) — see backend `REFERRAL_SOURCES` |
| `updated_at` | `timestamp` | Set on full profile save (not on skip-only) |

Canonical validation and allowed enums live in:

- `backend/services/user_trader_profile.py` (`TRADING_STYLES`, `EXPERIENCE_LEVELS`, `PRIMARY_GOALS`, `REFERRAL_SOURCES`, `INSTRUMENT_PATTERN`, `MAX_PAIRS`)

Frontend labels for goals and referral (must stay in sync with backend slugs):

- `src/constants/onboardingSurveyOptions.js`

Instrument presets (UI only; stored values are still `BASE/QUOTE` strings):

- `src/constants/forexPairs.js` (`PRESET_MARKET_INSTRUMENTS`)

---

## HTTP API

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/api/user/trader-profile` | `Authorization: Bearer <Firebase ID token>` |
| `PUT` | `/api/user/trader-profile` | Same |

Implemented in `backend/app.py` (`api_user_trader_profile`). The same route exists when running `scripts/main_app.py` (mirrored for local dev).

### `GET` response (conceptual)

- `needs_survey` — `true` if the user has not completed or skipped onboarding (and read succeeded).
- `trader_profile` — object with the fields above (nulls if never set).
- `onboarding_survey_completed_at`, `onboarding_survey_skipped_at` — ISO strings or `null`.
- `onboarding_survey_version`
- `firestore_available` — `false` if Firestore could not be read (degraded behavior).

### `PUT` body

**Skip onboarding**

```json
{ "skipped": true }
```

**Complete or update preferences** (validation requires all fields below)

```json
{
  "skipped": false,
  "trading_style": "day",
  "experience_level": "intermediate",
  "primary_pairs": ["EUR/USD", "XAU/USD"],
  "marketing_opt_in": false,
  "primary_goal": "stay_informed",
  "referral_source": "search"
}
```

---

## Where users see and edit this data

| Surface | Purpose |
|---------|---------|
| **Onboarding survey** (`/onboarding-survey`) | Multi-step flow after sign-in; writes via `PUT`. |
| **Profile → Trading preferences** (`ProfilePopup`) | Same payload; users can change answers later. |
| **Firebase Console** | Browse `users` → document by UID to inspect raw fields for support or one-off analysis. |

---

## How to use this data (current and future)

### Already wired

- **Onboarding gating**: `needs_survey` drives redirect to `/onboarding-survey` until complete or skip (`TraderProfileGate`, `OnboardingSurvey`).
- **Persistence**: All fields above are saved to Firestore when the user completes the survey or updates Profile.

### Natural next steps (not automatically connected today)

These are intentional integration points — implement when you prioritize them:

| Data | Possible use |
|------|----------------|
| `experience_level` | Softer vs denser copy in tooltips, AI prompts, or education modules. |
| `primary_pairs` | Prioritize calendar rows, news tags, or default alert pairs (align with `preferences.currencyPairs` in alert settings if you sync). |
| `trading_style` | Session-focused vs swing-focused defaults or ordering in the UI. |
| `primary_goal` | First-run emphasis (e.g. calendar vs alerts vs learning). |
| `referral_source` | Marketing attribution, channel ROI, cohort reports. |
| `marketing_opt_in` | ESP segments (only email users who opted in; respect unsubscribes in the mail tool). |

### Analysis and reporting

- **Firestore exports / BigQuery** (if linked): aggregate `trader_profile.*` and referral counts by `referral_source`.
- **Internal scripts**: Use Admin SDK to list `users` and read `trader_profile` (read-only analytics — follow privacy policy).
- **Product analytics**: Fire events with **non-sensitive** buckets (e.g. `experience_level`, `primary_goal`) if your analytics stack allows; avoid sending raw email in custom dimensions unless required.

### Privacy & compliance

- Treat `trader_profile` as **personal data** tied to UID (and often email on the same doc).
- Use `marketing_opt_in` only for the purposes described at collection time.
- `referral_source` is low sensitivity but still useful for internal metrics.

---

## Implementation reference (code)

| Piece | Location |
|-------|----------|
| Firestore read/write + validation | `backend/services/user_trader_profile.py` |
| Flask routes | `backend/app.py` (`/api/user/trader-profile`) |
| Lazy Firestore client | `UserTraderProfileStore._ensure_client()` — avoids connecting before Firebase Admin init |
| Survey UI | `src/components/OnboardingSurvey.jsx` |
| Profile editing | `src/components/ProfilePopup.jsx` |
| Instrument input parsing (client) | `src/utils/instrumentInput.js` |

---

## Related docs

- `docs/FIRESTORE_AND_AUTH_USER_SYNC.md` — how `users/{uid}` relates to Auth and billing.
