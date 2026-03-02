# FXSentinel Alerts System – Current Implementation (Pre-Duplicate Fixes)

This document captures the alert system implementation as it existed before the duplicate-alert fixes applied in February 2026. Use it as a reference for rollback or comparison.

---

## 1. Architecture Overview

### Components

| Component | Purpose |
|-----------|---------|
| **UnifiedAlertProcessor** | Main alert processor; runs in background thread. Handles news alerts (Path 1), economic calendar, post-news analysis. |
| **news_alert_trigger** | Creates alert content, triggers AI analysis, sends via alert_service. Used by both Path 1 and Path 2. |
| **persistent_alert_deduplication** | Firebase-backed dedup; stores `alert_deduplication/alerts/{alert_key}` and `content_hashes/{hash}`. |
| **alert_service** | Formats messages, sends via Telegram (robust_telegram_service). |
| **background_alert_worker** | Standalone worker loop; fetches news, POSTs to `/api/alerts/trigger`. |
| **Firebase Realtime Storage** | Users, settings, chat_id, dedup state. |

### Two Alert Paths for Live News

**Path 1 – UnifiedAlertProcessor (has reserve + lock)**  
- Entry: `check_news_alerts_async()` from `/api/news`, scheduler.  
- Flow: `should_send_news_alert` → per-user+news lock → `reserve_news_alert` → `mark_news_alert_sent` (before send) → send → `mark_news_alert_sent` (after, with `mark_global_hash=True`).  
- Uses `_recently_checked` (in-memory, 5 min) to skip same news within window.

**Path 2 – news_alert_trigger._send_alert_to_user (no reserve)**  
- Entry: `/api/alerts/trigger` (from background_alert_worker), `process_news_for_alerts` (force refresh).  
- Flow: `should_send_news_alert` → send → `mark_news_alert_sent`.  
- No reserve, no lock.

---

## 2. Entry Points for News Alerts

| Location | Trigger | Path |
|----------|---------|------|
| app.py ~974 | Background fetch | UnifiedAlertProcessor |
| app.py ~1123 | Cached news served | UnifiedAlertProcessor |
| app.py ~1410 | Fresh news fetched | UnifiedAlertProcessor |
| app.py ~1423 | Fresh news (cache save fail) | UnifiedAlertProcessor |
| app.py ~1450 | All news saved | UnifiedAlertProcessor |
| app.py ~1462 | All news (cache save fail) | UnifiedAlertProcessor |
| app.py ~1545 | No fresh news, cached only | UnifiedAlertProcessor |
| app.py ~1855 | Force refresh | process_news_for_alerts (Path 2) |
| app.py ~6790 | run_alert_check | background_worker → /api/alerts/trigger (Path 2) |
| app.py ~7235 | Scheduled task | background_worker → /api/alerts/trigger (Path 2) |

---

## 3. News ID Generation

### Current Implementation (Non-Deterministic)

**news_aggregator.py** (line 157):
```python
article_id = hash(f"{source_name}_{title}_{pub_date.isoformat()}")
return {'id': abs(article_id), ...}
```

**alternative_news_sources.py** (line 141):
```python
article_id = hash(f"{source_name}_{title}_{pub_date.isoformat()}")
return {'id': abs(article_id), ...}
```

**telegram_sync_wrapper.py** (line 303):
```python
article_id = hash(f"telegram_isolated_{channel_name}_{message.id}_{message_date.isoformat()}")
# ...
'id': abs(article_id),
```

**Problem:** Python 3’s `hash()` for strings is randomized per process (PYTHONHASHSEED). Same article can get different IDs across restarts → different dedup keys → duplicates.

---

## 4. Deduplication Logic

### Content String (Per-User)

- With `news_id`: `news:{news_id}`  
- Without: `news:{normalized_title}|{source}` (title normalized: lowercase, whitespace collapsed, special chars removed)

### Firebase Paths

- Per-user: `alert_deduplication/alerts/{md5(alert_type:content:user_id)}`  
- Global hint: `alert_deduplication/content_hashes/{md5(content)}`

### Record Structure

```json
{
  "alert_type": "news",
  "user_id": "...",
  "status": "sent" | "reserved",
  "sent_at": "ISO8601",
  "reserved_at": "ISO8601",
  "expires_at": "ISO8601"
}
```

### TTL

- `alert_ttl_hours = 2.0`  
- Reserve window: 10 minutes  
- `_recently_checked` window: 300 seconds (5 min)

### Check Flow (Path 1)

1. `should_send_news_alert` → `_check_alert_only` (read-only, no reserve)  
2. Acquire lock `(user_id, news_id)`  
3. Double-check `should_send_news_alert`  
4. `reserve_news_alert` → `_check_and_reserve_alert` (atomic PUT)  
5. `mark_news_alert_sent` (before send)  
6. Send via `alert_service.process_alert`  
7. `mark_news_alert_sent` (after send, `mark_global_hash=True`)

### Check Flow (Path 2)

1. `should_send_news_alert`  
2. Send  
3. `mark_news_alert_sent`

---

## 5. Firebase Error Handling

### _make_request (firebase_realtime_storage.py)

- On `RequestException`: returns `{}`  
- On success, no data: returns `None` (for null JSON)

### should_send_alert (persistent_alert_deduplication.py)

- `if existing_alert is None`: return `True` (allow) – only handles `None`  
- For `existing_alert = {}` (error): falls through, returns `True` (allow)  
- For `status in ['sent','reserved']` with no `expires_at`: falls through, returns `True` (allow)

---

## 6. Key File Paths

| File | Role |
|------|------|
| `backend/services/unified_alert_processor.py` | Path 1; periodic checks; reserve + lock |
| `backend/services/news_alert_trigger.py` | Alert content; Path 2 send flow |
| `backend/services/persistent_alert_deduplication.py` | Firebase dedup; check/reserve/mark |
| `backend/services/alert_service.py` | Format + send via Telegram |
| `backend/services/firebase_realtime_storage.py` | Firebase REST |
| `backend/services/news_aggregator.py` | RSS parse; `hash()` for ID |
| `backend/services/alternative_news_sources.py` | Alt sources; `hash()` for ID |
| `backend/services/telegram_sync_wrapper.py` | Telegram news; `hash()` for ID |
| `backend/services/background_alert_worker.py` | Worker loop; POSTs to /api/alerts/trigger |
| `backend/app.py` | Routes; trigger points; trigger_alert handler |

---

## 7. Economic Calendar Alerts

- Uses `persistent_alert_deduplication.should_send_economic_alert` and `mark_economic_alert_sent`  
- Content: `economic:{event_id}:{alert_timing}` or `economic:{title}|{time}|{date}|{alert_timing}`  
- Timing windows: 5–15 min, 50–65 min, 110–125 min before event  
- Checked every 5 minutes by UnifiedAlertProcessor

---

## 8. Live News Alert Format (Telegram)

```
<b>{title}</b>

<b>Time:</b> {event_time}
<b>Source:</b> {source}
<b>Currency Pairs:</b> {pairs}

<b>Summary:</b>
{summary}

Check dashboard for detailed analysis
```

---

---

## Post-Script: Fixes Applied (February 2026)

The following fixes were applied to address duplicate alerts:

1. **Deterministic news IDs** – Replaced `hash()` with `hashlib.md5` in `news_aggregator.py`, `alternative_news_sources.py`, and `telegram_sync_wrapper.py`.
2. **Reserve flow for Path 2** – Added `reserve_news_alert` before send in `news_alert_trigger._send_alert_to_user`; pass `user_data` to `process_alert`.
3. **Firebase error handling** – Treat `{}` response as error and fail closed; fail closed on exception in `_check_alert_only` and `should_send_alert`.
4. **Missing expires_at** – Block when `status` is sent/reserved but `expires_at` is missing.

See `ALERTS_DUPLICATE_EVALUATION.md` for full analysis.
