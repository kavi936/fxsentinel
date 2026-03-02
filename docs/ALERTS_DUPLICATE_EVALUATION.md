# Alert Duplicate Evaluation – Root Cause Analysis

This document evaluates why duplicate alerts are still being sent after several days of testing, including across app restarts.

---

## Executive Summary

Several issues can cause duplicate alerts. The most likely root causes are:

1. **Non-deterministic news IDs** (high impact) – `hash()` in Python 3 is randomized across runs
2. **Two alert paths without reserve** (high impact) – `news_alert_trigger._send_alert_to_user` does not use reserve/lock
3. **Multiple trigger points** (medium impact) – Same news can be processed by several entry points
4. **Firebase error handling** (medium impact) – Fail-open on errors can allow duplicates
5. **`should_send_alert` gap** (low impact) – Records with `status=sent` but no `expires_at` are treated as new

---

## 1. Non-Deterministic News IDs (HIGH IMPACT)

### Location
- `backend/services/news_aggregator.py` line 157
- `backend/services/alternative_news_sources.py` line 141

### Problem
Article IDs are generated with Python’s built-in `hash()`:

```python
article_id = hash(f"{source_name}_{title}_{pub_date.isoformat()}")
```

In Python 3, `hash()` for strings is randomized per process (PYTHONHASHSEED). The same article can get different IDs across restarts or different processes.

### Impact
- Dedup uses `news:{news_id}` when `id` is present
- Same article with different IDs → different dedup keys → different Firebase records
- Result: same story can be sent again after restart or when re-parsed

### Example
- Run 1: Article A → `id=12345` → sent → Firebase: `news:12345`
- Restart / new fetch: Article A → `id=67890` → check `news:67890` → no record → sent again

### Fix
Use deterministic hashing (e.g. `hashlib.md5` or `hashlib.sha256`) instead of `hash()`:

```python
import hashlib
article_id = int(hashlib.md5(f"{source_name}_{title}_{pub_date.isoformat()}".encode()).hexdigest()[:12], 16)
```

---

## 2. Two Alert Paths – One Without Reserve (HIGH IMPACT)

### Path 1: UnifiedAlertProcessor (has reserve + lock)
- Entry: `check_news_alerts_async()` from `/api/news`, scheduler, etc.
- Flow: `should_send` → lock → `reserve_news_alert` → `mark_news_alert_sent` (before send) → send → `mark_news_alert_sent` (after)
- Uses per-user+news lock and atomic reserve in Firebase

### Path 2: news_alert_trigger._send_alert_to_user (no reserve)
- Entry: `/api/alerts/trigger` (from background_alert_worker), `process_news_for_alerts` (force refresh)
- Flow: `should_send_news_alert` → send → `mark_news_alert_sent`
- No reserve, no lock

### Problem
Between `should_send` and `mark_news_alert_sent`, another caller can also pass `should_send` and send. Both can send before either marks.

### Scenario
- T=0: Path 1 checks (no record), reserves, sends, marks
- T=0: Path 2 checks (no record yet), sends, marks
- If Path 2’s check happens before Path 1’s mark is visible (e.g. Firebase latency), both send.

### Fix
Path 2 should use the same reserve pattern as Path 1:

1. `should_send_news_alert` (check only)
2. `reserve_news_alert` (atomic reserve)
3. Send
4. `mark_news_alert_sent` (update reserved → sent)

---

## 3. Multiple Trigger Points (MEDIUM IMPACT)

### Entry points for news alerts

| Location        | Trigger                    | Path                          |
|----------------|----------------------------|-------------------------------|
| app.py ~974    | Background fetch           | UnifiedAlertProcessor         |
| app.py ~1123   | Cached news served         | UnifiedAlertProcessor         |
| app.py ~1410   | Fresh news fetched         | UnifiedAlertProcessor         |
| app.py ~1423   | Fresh news (cache save fail) | UnifiedAlertProcessor       |
| app.py ~1450   | All news saved             | UnifiedAlertProcessor         |
| app.py ~1462   | All news (cache save fail) | UnifiedAlertProcessor         |
| app.py ~1545   | No fresh news, cached only | UnifiedAlertProcessor         |
| app.py ~1855   | Force refresh              | process_news_for_alerts (Path 2) |
| app.py ~6790   | run_alert_check            | background_worker → /api/alerts/trigger (Path 2) |
| app.py ~7235   | Scheduled task             | background_worker → /api/alerts/trigger (Path 2) |

### Problem
A single `/api/news` request can trigger `check_news_alerts_async` multiple times with overlapping news (e.g. fresh_news and all_news_to_save). Each call starts a new thread. `_recently_checked` helps, but it is in-memory and lost on restart.

### Impact
- More concurrent processing of the same news
- Higher chance of races, especially with Path 2

---

## 4. Firebase Error Handling (MEDIUM IMPACT)

### Location
- `backend/services/firebase_realtime_storage.py` line 61–67
- `backend/services/persistent_alert_deduplication.py` lines 123–128, 154–156

### Problem
- On `RequestException`, `_make_request` returns `{}`
- `should_send_alert`: `if existing_alert is None: return True` (allow) – only handles `None`, not `{}`
- For `existing_alert = {}`: `status='sent'`, `expires_at_str=''`; the `if expires_at_str` block is skipped, so the function falls through and returns `True` (allow)
- On errors, behavior is effectively fail-open → duplicates possible

### Fix
- Treat `{}` as an error (e.g. block or retry) instead of allowing
- Or: on any Firebase error, fail closed (return `False`) to avoid duplicates

---

## 5. should_send_alert Gap for Missing expires_at (LOW IMPACT)

### Location
`backend/services/persistent_alert_deduplication.py` lines 131–152

### Problem
If a record has `status in ['sent','reserved']` but no `expires_at`, the code never returns `False`. It falls through to `return True` and allows the alert.

### Impact
Old or malformed records without `expires_at` could be treated as new → duplicates.

### Fix
Block when status is `sent` or `reserved`, even if `expires_at` is missing:

```python
if status in ['sent', 'reserved']:
    if expires_at_str:
        # existing logic
    else:
        return False  # Block - record exists, treat as duplicate
```

---

## 6. _recently_checked Is In-Memory (LOW IMPACT)

### Location
`backend/services/unified_alert_processor.py` lines 51–53

### Problem
`_recently_checked` is in-memory. On restart it is empty, so the same news can be processed again immediately.

### Impact
Firebase dedup should still block if the content key is stable. The main risk is when the content key changes (e.g. non-deterministic IDs).

---

## Recommended Fix Order

1. **Fix news ID generation** – Use `hashlib.md5` (or similar) instead of `hash()` in `news_aggregator` and `alternative_news_sources`.
2. **Align Path 2 with Path 1** – Add reserve + mark flow to `news_alert_trigger._send_alert_to_user` and `/api/alerts/trigger`.
3. **Harden Firebase error handling** – Treat `{}` and other error responses as failures and fail closed for dedup.
4. **Handle missing expires_at** – Block when status is `sent`/`reserved` even if `expires_at` is absent.

---

## Files Modified (Fixes Applied)

| File                               | Changes Applied                                                         |
|------------------------------------|-------------------------------------------------------------------------|
| `news_aggregator.py`               | Replaced `hash()` with `hashlib.md5` for article IDs                   |
| `alternative_news_sources.py`     | Same as above                                                           |
| `telegram_sync_wrapper.py`         | Same as above (Telegram news IDs)                                       |
| `news_alert_trigger.py`            | Added `reserve_news_alert` before send in `_send_alert_to_user`; pass `user_data` to `process_alert` |
| `persistent_alert_deduplication.py` | Treat `{}` as Firebase error → fail closed; block when `status` sent/reserved but no `expires_at`; fail closed on exception |
