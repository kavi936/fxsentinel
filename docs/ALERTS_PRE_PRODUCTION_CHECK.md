# Alerts System Pre-Production Check

**Date:** February 2026  
**Status:** Ready for production with minor notes

---

## 1. Import & Module Verification

| Module | Status |
|--------|--------|
| `persistent_alert_deduplication` | OK |
| `unified_alert_processor` | OK |
| `news_alert_trigger` | OK |
| `economic_calendar_alerts` | OK |
| `alert_service` | OK |

---

## 2. Fixes Verification

| Fix | Status | Notes |
|-----|--------|-------|
| Deterministic news IDs (hashlib.md5) | OK | `news_aggregator`, `alternative_news_sources`, `telegram_sync_wrapper` |
| Reserve flow for Path 2 | OK | `news_alert_trigger._send_alert_to_user` uses `reserve_news_alert` before send |
| Firebase error handling | OK | `{}` response → fail closed; exception in `_check_alert_only` → fail closed |
| Missing expires_at | OK | Block when `status` sent/reserved but no `expires_at` |
| user_data passed to process_alert | OK | Path 2 and economic alerts pass `user_data` for `chat_id` |

---

## 3. Flow Verification

### Path 1 (UnifiedAlertProcessor)
- Quick check → lock → double-check → reserve → mark (before send) → send → mark (after, global hash)
- Lock released in `finally` block
- Per-user+news lock key: `(user_id, news_id)`

### Path 2 (news_alert_trigger / trigger API)
- Check → reserve → send → mark (on success)
- No lock (relies on Firebase reserve)

### Economic Calendar
- `should_send_economic_alert` → send → `mark_economic_alert_sent`
- Uses `persistent_alert_deduplication` (Firebase-backed)

---

## 4. Potential Issues (Non-Blocking)

### 4.1 Inconsistent fail-open in should_send_news_alert
- **Location:** `persistent_alert_deduplication.py` line 381
- **Issue:** On exception, `should_send_news_alert` returns `True` (allow), while `_check_alert_only` returns `False` (block)
- **Impact:** Low – exceptions in `_check_alert_only` are caught there and return False; the outer `should_send_news_alert` exception would only fire if `_get_news_content_hash` or `_get_news_content_string` fails
- **Recommendation:** Consider changing to `return False` for consistency

### 4.2 _check_and_reserve_alert does not handle Firebase `{}` explicitly
- **Location:** `persistent_alert_deduplication.py` line 406
- **Issue:** On `existing_alert == {}`, we enter `if existing_alert and isinstance(existing_alert, dict)` (True for `{}`). We then get `status='sent'`, `expires_at_str=''`, and hit the `else` block → return False. So we do block.
- **Status:** Correct behavior

### 4.3 Duplicate log line in _check_and_reserve_alert
- **Location:** `persistent_alert_deduplication.py` lines 403–404
- **Issue:** Same `logger.info` line appears twice
- **Impact:** Cosmetic only

---

## 5. Environment Checklist

Before deploying, ensure:

| Variable | Required | Purpose |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | Required for sending alerts |
| `FIREBASE_REALTIME_URL` | Yes | Users, settings, dedup state |
| `FIREBASE_PROJECT_ID` | Optional | Defaults from URL |

---

## 6. Health Endpoints

After deploy, verify:

- `GET /api/health` – General health
- `GET /api/health/alerts` – Should show `unified_processor_running: true` when main app is running
- `GET /api/health/unified-alert-processor` – Processor status

---

## 7. Post-Deploy Verification

1. **Webhook:** Ensure Telegram webhook is set to `https://YOUR_DOMAIN/api/telegram/webhook`
2. **User setup:** At least one user with `telegram_chat_id` and Telegram enabled
3. **Trigger:** Call `GET /api/news` or `POST /api/news?force_refresh=true` to trigger alert check
4. **Logs:** Look for `DEDUP_ALLOW`, `DEDUP_BLOCK`, `RESERVED`, `SENT` in logs

---

## 8. Summary

| Category | Status |
|----------|--------|
| Imports | Pass |
| Dedup logic | Pass |
| Reserve flow | Pass |
| Lock release | Pass |
| Error handling | Pass (minor inconsistency noted) |
| Economic alerts | Pass |

**Conclusion:** The alerts system is ready for production. The fixes for duplicate alerts are in place. Run the health checks after deploy and monitor logs for the first few alerts.
