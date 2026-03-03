# Alert deduplication and spacing fix

## Context (user-reported)

1. **Duplicate alerts**: The same alert was sometimes sent twice in a row consecutively after the “recheck for alerts to be sent”. Other checks did not resend the same alert. Hypothesis: the system was not given enough time to record that the alert had already been sent before the next check ran, so the same alert was sent again.

2. **Alert spam**: After the periodic check (e.g. 5 min), several alerts (e.g. 5) could be detected and the user would receive 5 consecutive alerts in quick succession (some same, some different). Desired: a break between each alert (e.g. 10–20 seconds).

## Root causes

### Duplicates

- **Recheck / second trigger**: The same news batch could be passed to `check_news_alerts_async` from more than one place (e.g. after cache save and from another code path), or the same story could be processed again before Firebase had propagated the “sent” state.
- **Reserve overwriting “sent”**: In `_check_and_reserve_alert`, we did a GET (Step 1), then later a PUT to reserve. Another thread could mark the alert as “sent” in between. Our PUT would then overwrite “sent” with “reserved”, so a second sender could think it had won the reservation and send again.
- **No per-user serialization**: Multiple tasks for the same user (e.g. 5 news items → 5 tasks for user A) could run in parallel. Two tasks for the same (user, news) would contend only on the (user_id, news_id) lock; if both passed the initial dedup check before either had written “sent”, we could still get a duplicate after replication lag.

### Spam

- Alerts to the same user were processed in parallel (up to `max_workers`). So when 5 items were eligible, the user could get 5 messages in a short burst.

## Solutions implemented

### 1. Dedup: do not overwrite “sent” when reserving (`persistent_alert_deduplication.py`)

- **Re-GET immediately before PUT** in `_check_and_reserve_alert`: after the initial “can we send?” check, we do a **second GET** right before writing the reservation.
- If that second GET sees `status == 'sent'` and the record is not expired, we **abort** (return `False`) and **do not PUT**. So we never overwrite an existing “sent” with “reserved”, even if the first GET had missed it (e.g. replication lag).
- Removed the duplicate log line in the same block.

### 2. Per-user lock + minimum gap between alerts (`unified_alert_processor.py`)

- **Per-user lock**: Before running the send flow for a user, we acquire a **per-user** lock (`_user_send_locks[user_id]`). Only one alert send runs per user at a time.
- **Minimum gap after a successful send**: After a successful send we call `time.sleep(_min_seconds_between_alerts_per_user)` (default **15 seconds**) before releasing the per-user lock. So the next alert to that user cannot start until after this gap.
- **Effects**:
  - **Dedup**: A “recheck” or second task for the same (user, news) will wait on the per-user lock. By the time it runs, the first send has completed and the 15s delay has passed, so Firebase is very likely to show “sent” and the re-GET-before-reserve will abort.
  - **UX**: Consecutive alerts to the same user are spaced by at least 15 seconds (configurable 10–20s via `_min_seconds_between_alerts_per_user`).

### 3. Extra propagation delay after marking “sent” (`unified_alert_processor.py`)

- After `mark_news_alert_sent(..., mark_global_hash=False)` we already had 0.5s + 0.2s. We added another **1 second** sleep so that before we release the (user, news) lock and proceed to send, the “sent” state has more time to propagate. This reduces the chance that another thread/instance will do a GET and still miss the update.

## Configuration

- **Gap between consecutive alerts (same user)**  
  In `UnifiedAlertProcessor.__init__`:  
  `self._min_seconds_between_alerts_per_user = 15`  
  You can set this to 10–20 seconds as desired (e.g. 10 for faster delivery, 20 for less noise).

## Files changed

| File | Change |
|------|--------|
| `backend/services/persistent_alert_deduplication.py` | Re-GET before reserve PUT; do not overwrite “sent”; remove duplicate log. |
| `backend/services/unified_alert_processor.py` | Per-user lock; 15s delay after successful send; 1s delay after mark_sent. |

## API path (worker → `/api/alerts/trigger`)

- The **re-GET before reserve** in `persistent_alert_deduplication` applies to all callers, including the API trigger path (`news_alert_trigger._send_alert_to_user`). So even when the worker POSTs one news item and the main app sends to many users, we no longer overwrite “sent” with “reserved”.
- The **per-user lock and 15s gap** are only in `UnifiedAlertProcessor` (main app path). The API path sends one news item to many users sequentially, so it does not create multiple alerts in a burst for a single user; the main spam scenario was the main app path with multiple news items per user.

## Testing suggestions

- Trigger a batch that would previously send the same alert twice in a row: confirm only one is sent.
- Trigger a batch that would previously send 5 alerts to one user at once: confirm they are spaced by about 15 seconds (or your configured value).

---

## Update: Same alert still sent twice (content key fix)

**Observed:** The same live news alert (e.g. "Fed's Kashkari: Too soon to know how Iran war will affect inflation", FXStreet, 17:52 UTC) was still delivered twice in a row.

**Root cause:** The dedup key was built from `news:{id}` when `id` was present, and `news:{normalized_title}|{source}` when `id` was missing. The same story can reach the system via two paths (UnifiedAlertProcessor from main app, and API trigger from background worker) with different payload shapes: one path might have an `id` (e.g. from cache), the other might not (or a different `id`). That produced two different Firebase keys, so both sends were allowed.

**Fix (in `persistent_alert_deduplication.py`):** Use a **content-based key only** for news: always build the content string from **normalized title + source** (never from `id`). So the same story always maps to the same dedup key regardless of path or payload shape.

- `_get_news_content_string()` now always returns `news:{normalized_title}|{source}`.
- `_get_news_content_hash()` now hashes that same string (no separate id-based branch).
- `mark_news_alert_sent()` uses `_get_news_content_string()` only (single source of truth).
