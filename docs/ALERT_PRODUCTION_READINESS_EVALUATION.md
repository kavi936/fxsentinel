# Alert system – production readiness evaluation

**Date:** Re-evaluation before production push  
**Scope:** Duplicate alerts + alert spam fixes

---

## 1. Problem recap

| Issue | What you saw | Root cause |
|-------|----------------|------------|
| **Duplicate alerts** | Same alert sent twice in a row after a “recheck”; other checks did not resend | Not enough time for “sent” to be visible; reserve PUT could overwrite “sent” with “reserved” |
| **Alert spam** | After 5‑min check, 5 alerts delivered back‑to‑back to one user | Multiple (user, news) tasks in parallel; no spacing between sends per user |

---

## 2. Fixes verified in codebase

### 2.1 Dedup: do not overwrite “sent” (`persistent_alert_deduplication.py`)

- **Re-GET before reserve PUT** (lines 426–445): Immediately before writing a reservation we GET again. If `status == 'sent'` and not expired, we return `False` and **do not PUT**, so we never overwrite “sent” with “reserved”.
- **Step numbering:** Step 1 (initial check) → Step 2 (re-check before reserve) → Step 3 (build reserve) → Step 4 (PUT) → Step 5 (verify). Logic is consistent.
- **Duplicate log line** removed (single “Existing alert check result” log).

### 2.2 Per-user lock + spacing (`unified_alert_processor.py`)

- **Per-user lock** (lines 337–342): We acquire `_user_send_locks[user_id]` at the start of `_send_alert_to_user` (before quick check). Only one send runs per user at a time.
- **15s delay after successful send** (lines 562–566): After a successful send we `time.sleep(_min_seconds_between_alerts_per_user)` (15s) before releasing the user lock. Next alert to that user is delayed by at least 15s.
- **Config** (line 65): `_min_seconds_between_alerts_per_user = 15` (configurable 10–20).
- **1s propagation delay** (lines 424–426): After `mark_news_alert_sent(..., mark_global_hash=False)` we sleep 0.2s + 1.0s before proceeding, so “sent” has time to propagate before we release the (user, news) lock.

### 2.3 Lock release and safety

- **`finally` block** (lines 558–568): Always runs. Releases `processing_lock` only if `processing_lock_acquired and processing_lock is not None`. Then, if `sent_success`, sleeps 15s. Then **always** releases `user_lock`.
- **Early returns** (e.g. after quick check): We never acquire `processing_lock` in those paths; `processing_lock_acquired` stays `False`, so we don’t release it. We always release `user_lock` in `finally`.
- **No deadlock:** We acquire user lock → then processing lock. We release processing lock → then user lock. We never wait for another user’s lock while holding one.

---

## 3. Entry points and coverage

| Entry point | Path | Dedup (re-GET) | Per-user spacing |
|-------------|------|----------------|-------------------|
| Main app: `check_news_alerts_async(fresh_news)` | UnifiedAlertProcessor._send_alert_to_user | ✅ (via reserve_news_alert) | ✅ |
| Main app: `process_news_for_alerts(fresh_news)` (e.g. force refresh) | NewsAlertTrigger._send_alert_to_user | ✅ | N/A (one news → many users, sequential) |
| API: POST `/api/alerts/trigger` (worker) | NewsAlertTrigger._send_alert_to_user | ✅ | N/A (one news → many users, sequential) |

- **Duplicate fix** applies to all paths (shared `persistent_alert_deduplication`).
- **Spacing fix** applies where multiple news items can hit the same user in parallel (UnifiedAlertProcessor). Other paths send one news item to many users, so no per-user burst.

---

## 4. Edge cases checked

- **Empty `news_id`:** `lock_key = (user_id, '')` for items without `id`. All such items for one user share the same per-news lock and are serialized with 15s gap after each send. Acceptable and consistent with “no spam” goal.
- **Exception during send:** Exception is caught; `sent_success` stays `False`; `finally` releases locks without sleeping. User lock is always released.
- **Firebase errors:** Reserve/sent writes can fail. We still release locks in `finally`. Dedup may allow a rare retry; we do not deadlock.

---

## 5. Production checklist

- [x] Re-GET before reserve implemented and not overwriting “sent”
- [x] Per-user lock and 15s delay implemented in UnifiedAlertProcessor
- [x] Lock release in all paths (early return, success, exception)
- [x] No deadlock (single lock order, no cross-user wait)
- [x] API and process_news_for_alerts paths use same dedup (re-GET)
- [x] Configurable gap (`_min_seconds_between_alerts_per_user = 15`)
- [x] Documentation: `ALERT_DEDUP_AND_SPACING_FIX.md` and this evaluation

---

## 6. Recommendation

**Ready to push to production** for the duplicate and spam fixes, with the following in mind:

1. **Monitor after deploy:** Watch logs for `DEDUP_BLOCK`, `Duplicate prevented`, and `Waiting 15s before next alert` to confirm behavior.
2. **Optional:** If you want a 10s or 20s gap instead of 15s, change `_min_seconds_between_alerts_per_user` in `UnifiedAlertProcessor.__init__`.
3. **Firebase:** Ensure `FIREBASE_REALTIME_URL` (and credentials) are set in production so dedup state is shared across instances.

No code changes required for production based on this evaluation.
