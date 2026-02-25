# FXSentinel Alerts System – Analysis & Recommendations

**Date**: February 2025  
**Purpose**: Understand the current alerts system, why it’s broken, and whether to keep Telegram or adopt a different approach.

---

## 1. How the alerts system works (high level)

### 1.1 Architecture

The system is **event-driven**: alerts are triggered when news is fetched by the main app, not by a separate polling worker.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MAIN APP (Flask)                                                        │
│  • /api/news → fetches/returns news, then triggers alert check           │
│  • UnifiedAlertProcessor started on app startup (background thread)      │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │  When news is returned (fresh or cached):
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  unified_alert_processor.check_news_alerts_async(news_items)              │
│  • Runs in a separate thread (non-blocking)                              │
│  • Filters high-impact forex news (news_alert_trigger)                   │
│  • Gets all users with alerts from Firebase                              │
│  • For each (user × news) pair: per-user deduplication → send via Telegram│
└─────────────────────────────────────────────────────────────────────────┘
         │
         ├──► persistent_alert_deduplication.should_send_news_alert()
         ├──► alert_service.process_alert() → send_telegram_alert()
         └──► robust_telegram_service (circuit breaker, retries, DLQ)
```

**Important**: There is no separate “alert worker” process in the main path. The **Unified Alert Processor** runs inside the main app as a background thread. Alerts run only when the main app serves `/api/news` (or similar) and then calls `check_news_alerts_async(fresh_news)`.

Other workers (`BackgroundAlertWorker`, `production_alert_worker`, `independent_worker`) still exist in code but are **obsolete** for the primary flow; they were replaced by the unified processor.

### 1.2 Main components

| Component | Role |
|----------|------|
| **UnifiedAlertProcessor** | Background thread; on news fetch, filters high-impact items and fans out to users. |
| **NewsAlertTrigger** | Decides if a news item is “high-impact forex” and builds alert content (incl. optional AI analysis). |
| **PersistentAlertDeduplication** | Per-user + global (hint) deduplication in Firebase so the same story isn’t sent twice. |
| **AlertService** | User preferences (impact, types, quiet hours), then sends via Telegram (and stub email). |
| **RobustTelegramService** | Sends to Telegram API with rate limiting, retries, invalid-chat handling. |
| **Firebase Realtime** | User alert settings, `telegram_chat_id`, deduplication state, history. |
| **Circuit breaker + DLQ** | In `alert_service.send_telegram_alert`: if Telegram is failing, open circuit and put failed alerts in dead-letter queue. |

### 1.3 Data flow (news → Telegram)

1. **Trigger**: Any code path that returns news calls `get_unified_processor().check_news_alerts_async(fresh_news)` (e.g. in `app.py` around 973, 1117, 1406, 1446, 1538).
2. **Filter**: Only items passing `news_alert_trigger.is_forex_high_impact()` are considered.
3. **Users**: `FirebaseRealtimeStorage.get_all_users_with_alerts()` returns list of `{ user_id, settings, telegram_chat_id }`.
4. **Per-user**: For each user and each news item, `should_send_news_alert(news_item, user_id)` is used (per-user + global-hint deduplication).
5. **Send**: `alert_service.process_alert(alert_data, user_settings, user_id, user_data)` checks preferences and quiet hours, then `send_telegram_alert(chat_id, message, ...)`.
6. **Telegram**: `robust_telegram_service` (or direct Bot API) sends the message; circuit breaker and DLQ handle failures.

---

## 2. What’s broken or fragile

### 2.1 Alerts only run when news is fetched

- Alert checks are **only** triggered from the main app when it serves news (e.g. `/api/news`).
- If nobody calls `/api/news` (or the path that triggers the check), **no alert run happens**.
- There is no standalone “wake up every N minutes and check news” in the main app; the old workers that did that are deprecated.

**Effect**: Low traffic or no frontend polling → no alerts.

### 2.2 Firebase user_id vs safe_user_id (hash)

- Firebase paths use a **hashed** user id: `safe_user_id = md5(user_id).hexdigest()`, e.g. `alerts/users/{safe_user_id}/settings` and `telegram_chat_id`.
- `get_all_users_with_alerts()` returns `user_id: safe_user_id` (the hash), not the original Firebase Auth UID.
- The rest of the pipeline (e.g. `process_alert`, deduplication) uses this same value, so **sending and deduplication are consistent** as long as everyone uses this “user_id” consistently.
- But: any code that assumes `user_id` is the **real** Firebase UID (e.g. for logging, support, or history by “real” user) is wrong. There is no reverse mapping from hash → real UID in this flow.

**Effect**: Architecture is consistent for sending; confusing or wrong if you need to correlate alerts to real user identities elsewhere.

### 2.3 Global deduplication (historical / config)

- Earlier evaluation (e.g. `COMPREHENSIVE_ALERT_SYSTEM_EVALUATION.md`) reported **global content hash blocking all alerts** (“all already sent globally”).
- In **current** code, global hash is only a **hint**: if the global hash exists, the code still runs **per-user** deduplication (`should_send_news_alert`). So global hash alone should not block everyone.
- Remaining risks:
  - **TTL**: Global and per-user state use `alert_ttl_hours` (e.g. 0.5 h) and cleanup; if Firebase has very long-lived or stale content hashes, or cleanup fails, you could still see over-deduplication.
  - **Firebase**: If Firebase is down or slow, deduplication can “fail open” (allow send) or behave inconsistently.

**Effect**: If alerts are still “blocked”, the next place to look is Firebase content-hash cleanup and TTL, and whether something else is filtering out all users (e.g. no `telegram_chat_id` or Telegram disabled).

### 2.4 User configuration and Telegram

- Users must have **Telegram enabled** in settings (`telegram_enabled`, or `channels.telegram.enabled`) and a valid **telegram_chat_id** (stored under `alerts/users/{safe_user_id}/telegram_chat_id`).
- If `get_all_users_with_alerts()` does not return a `telegram_chat_id` (e.g. not set after bot `/start`), or Telegram is disabled in settings, that user never gets alerts.
- Test/placeholder chat IDs (e.g. `123456789`, `987654321`) are rejected by `_validate_chat_id` on **save**; existing bad data in Firebase can still cause send failures.

**Effect**: “Alerts broken” can simply be “no users with valid Telegram + chat_id” or “Telegram disabled in settings”.

### 2.5 Multiple workers and dead code

- **BackgroundAlertWorker**, **production_alert_worker**, **independent_worker** still exist and can be started (e.g. `worker_app.py`). They poll news and trigger alerts themselves.
- Running them **together** with the main app’s unified processor can cause duplicate processing or confusion about who is responsible for alerts.
- The main app’s **single** source of alert triggering is the unified processor started in `initialize_unified_alert_processor()`.

**Effect**: If you run a separate worker, you must be clear it’s either the only runner or that deduplication makes duplicates rare; otherwise prefer “main app only” and turn off extra workers.

### 2.6 Email and other channels

- **Email**: `send_email_alert` is a stub (logs only). No real email sending.
- **Other channels**: No Discord, Slack, or generic webhook in the alert pipeline. Only Telegram is implemented for real delivery.

**Effect**: Today the system is “Telegram-only” for real notifications.

---

## 3. Should you keep Telegram or switch to something else?

### 3.1 Why Telegram fits this product

- **Already built**: Bot setup, webhook, chat_id storage, rate limiting, circuit breaker, DLQ.
- **UX**: Users get instant push on their phone; no need to open an app or rely on email.
- **Cost**: Telegram Bot API is free; no per-message cost.
- **Landing/marketing**: The product is already described as “Telegram alerts” (e.g. LandingPage), so changing channel would need copy and user expectation updates.

### 3.2 When to consider adding another channel

- **Email**: Useful for “digest” or users who don’t use Telegram. Requires an email provider (SendGrid, Postmark, etc.) and more design (rate limits, bounces, unsubscribes).
- **Discord/Slack**: Good if your users are already in a server/workspace; need bot + channel ID and possibly different formatting.
- **Push (web)**: Good for in-app only; doesn’t replace “not in app” alerts.

**Recommendation**: **Keep Telegram as the primary alert channel.** It’s the only one fully implemented and matches current positioning. If you want a second channel, add **email** (or a simple webhook) behind the same `process_alert` flow so one alert can go to Telegram + email (or webhook) based on user settings.

---

## 4. Recommended approach to “fix” the system

### 4.1 Short term (prove it works)

1. **Confirm who should get alerts**
   - In Firebase Realtime: `alerts/users` → each user with `settings` and `telegram_chat_id`.
   - Ensure at least one real user has:
     - Valid `telegram_chat_id` (saved after Telegram bot `/start`),
     - Telegram enabled in `settings` (e.g. `channels.telegram.enabled` or `telegram_enabled`),
     - Preferences that allow `liveNews` (and impact levels you’re testing with).

2. **Trigger a run**
   - Call `/api/news` (or the exact path that triggers `check_news_alerts_async`) so the unified processor runs with recent news.
   - Check logs for: “Processing alerts for N users”, “Alert approved for user …”, “Telegram alert sent to …” or errors (e.g. “no Telegram chat ID”, “Telegram disabled”, “Duplicate prevented”).

3. **Don’t run two systems**
   - Either run **only** the main app (unified processor) and no separate worker, or run **only** one worker that triggers alerts; avoid both main app and worker doing it unless you’re sure deduplication is correct.

4. **Optional: force-send test**
   - In `PersistentAlertDeduplication`, `force_send_mode = True` bypasses deduplication (for testing only). Use once to confirm Telegram and routing work, then turn off.

### 4.2 Medium term (stability and clarity)

1. **Deduplication**
   - Ensure `_cleanup_expired_content_hashes()` and cleanup of per-user records run regularly (already tied to operation count; consider a time-based cleanup as well).
   - If you still see “all already sent globally” in logs, add a small admin or script to clear or shorten TTL for `alert_deduplication/content_hashes` in Firebase (or reduce `alert_ttl_hours` and confirm cleanup runs).

2. **User identity**
   - Store the **real** Firebase Auth UID in each user’s alert document (e.g. `alerts/users/{safe_user_id}/auth_uid`) when saving settings or chat_id, and return it from `get_all_users_with_alerts()` as e.g. `auth_uid`. Use `auth_uid` for logging and support; keep using `safe_user_id` for Firebase paths and deduplication keys so behaviour stays consistent.

3. **Deprecate old workers**
   - Remove or clearly disable `BackgroundAlertWorker` / `production_alert_worker` from deployment and docs so the “single path” (unified processor in main app) is the only one.

4. **Monitoring**
   - Log or expose: number of users with alerts, number with `telegram_chat_id`, and per-run “alerts sent” vs “skipped (duplicate / no chat_id / Telegram disabled)”. This will make “alerts are broken” debuggable in minutes.

### 4.3 If you want a second channel (e.g. email)

- Add a real implementation in `alert_service.send_email_alert` (provider + template).
- Keep the same flow: `process_alert` already branches on `channels.telegram` and `channels.email`; you only need to implement the email send and handle failures (e.g. retries or DLQ) so it’s on par with Telegram.

---

## 5. Summary

| Aspect | Status | Action |
|--------|--------|--------|
| Architecture | Event-driven, unified processor in main app | Keep; ensure no duplicate worker is running. |
| Trigger | Only when news is fetched (e.g. `/api/news`) | Accept or add a minimal scheduler that hits that path periodically. |
| Telegram | Implemented with retries, circuit breaker, DLQ | Keep as primary channel; verify token and webhook. |
| Deduplication | Per-user + global hint in Firebase | Ensure cleanup runs; fix TTL/cleanup if “blocking” persists. |
| User config | Telegram + chat_id in Firebase | Verify at least one real user has valid chat_id and Telegram enabled. |
| user_id in pipeline | Hash (safe_user_id) used everywhere | Consistent for sending; add auth_uid for support/logging. |
| Email / other channels | Stub or missing | Optional: implement email (or webhook) in same `process_alert` flow. |

**Bottom line**: The design is sound and Telegram is the right primary channel. “Broken” is likely due to (a) alerts only running when news is fetched, (b) no/few users with valid Telegram + chat_id and enabled settings, or (c) over-aggressive or stale deduplication. Fix those first; then add monitoring and optional second channel (e.g. email) if needed.
