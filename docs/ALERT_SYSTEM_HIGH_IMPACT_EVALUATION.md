# High-Impact Alerts Evaluation (March 1–7)

Evaluation of why high-impact economic calendar alerts may not have been received, and fixes applied.

---

## Summary of issues found and fixed

### 1. **Critical: Economic calendar datetime not parsed (FIXED)**

**Problem:** The unified alert processor gets events from `hybrid_economic_calendar.get_economic_events()`, which returns events with `date` in **YYYY-MM-DD** (e.g. `2026-03-06`) and `time` in **"HH:MM UTC"**. The economic calendar alerts service’s `_parse_event_datetime()` did **not** handle that combination. It only supported formats like `"Mon, Jan 15 14:30 UTC"` or regex for `"Wed, Mar 04"`. So for hybrid calendar events, `_parse_event_datetime()` returned `None`, and `_send_pre_event_alert()` exited early without sending.

**Fix:** In `economic_calendar_alerts.py`, `_parse_event_datetime()` now handles **YYYY-MM-DD** plus **HH:MM UTC** first, so hybrid calendar events are parsed correctly and alerts can be sent.

---

### 2. **Critical: Timezone mismatch (FIXED)**

**Problem:** Event times are stored as **"HH:MM UTC"**, but the code compared them to `datetime.now()` (server local time). So:

- On a server in UTC: behaviour was correct.
- On a server in EST/PST/etc.: “minutes until event” could be wrong and events could fall outside the 10min / 1h / 2h windows, so no alerts were sent.

**Fix:** In `unified_alert_processor.py`, “now” and event time are both treated as **UTC**:

- `now = datetime.now(timezone.utc)`
- Event datetime is built with `tzinfo=timezone.utc`

So regardless of server timezone, alert windows are evaluated correctly.

---

### 3. **High-impact weekend events dropped (FIXED)**

**Problem:** In `economic_calendar_alerts._validate_event_data()`, any event on Saturday/Sunday was rejected unless the title contained “speech”, “meeting”, or “conference”. March 1 (Sunday) and March 7 (Saturday) high-impact events were therefore filtered out.

**Fix:** The weekend rule now applies only to **non–high-impact** events. High-impact events are always allowed, so weekend high-impact releases can trigger alerts.

---

## Other factors (no code change)

### 4. **Narrow timing windows and 5‑minute check**

Alerts are sent only when “minutes until event” falls in:

- **10 min:** 5–15 min before
- **1 h:** 50–65 min before  
- **2 h:** 110–125 min before

The processor runs economic calendar checks every **5 minutes**. So:

- Each window is hit at most twice per event.
- If the process is down or an exception happens during the only check that would have fallen in the window, that event is missed.

**Recommendation:** Keep an eye on logs (e.g. “Sending economic alert for: …”) and consider slightly wider windows (e.g. 3–18 min for “10 min before”) if you see missed alerts.

---

### 5. **Background thread must be running**

Alerts depend on the **Unified Alert Processor** background thread (started in `initialize_unified_alert_processor()` on app startup). If the app runs in a serverless or short-lived process, or the thread is not started, economic calendar checks never run.

**Recommendation:** Ensure the main app process is long-lived (e.g. always-on Railway/web process) and that startup logs show “Unified alert processor started in background”.

---

### 6. **User preferences**

Users only get economic calendar alerts if:

- **Pre-news / economic calendar** is enabled (`preNews` or equivalent in `alertTypes` / economic calendar settings).
- **Telegram** is enabled and linked (valid `telegram_chat_id`).
- **High impact** is enabled in impact level preferences (default is on).
- They are **not** in quiet hours.

If you’re testing with a single account, confirm in the app that Pre-News / Economic Calendar and Telegram are on and that quiet hours are not blocking the event time.

---

## Flow recap

1. **Unified Alert Processor** (background thread) runs **every 5 minutes**.
2. It loads events from **hybrid_economic_calendar.get_economic_events(start_date, end_date)**.
3. It keeps only **high-impact** events with status **upcoming** or **today**.
4. For each, it computes “minutes until event” in **UTC** and, if in one of the three windows, calls **`_send_economic_alert(event)`**.
5. That loads users from Firebase, filters by pre-news + Telegram + impact + quiet hours, then for each user calls **economic_calendar_alerts.send_pre_event_alert(user_data, event)**.
6. **economic_calendar_alerts** parses the event datetime (now supports **YYYY-MM-DD** + **HH:MM UTC**), checks deduplication, then uses **alert_service.process_alert()** to send via Telegram.

The two critical bugs (datetime parsing and timezone) would have prevented step 6 from sending for hybrid calendar events; the weekend filter would have blocked March 1 and 7. With the fixes above, high-impact events for March 1–7 and beyond should be eligible to trigger alerts as long as the processor is running, user settings allow it, and the event falls in one of the timing windows.

---

## Files changed

| File | Change |
|------|--------|
| `backend/services/economic_calendar_alerts.py` | Parse **YYYY-MM-DD** + **HH:MM UTC** in `_parse_event_datetime()`; allow high-impact events on weekends in `_validate_event_data()`. |
| `backend/services/unified_alert_processor.py` | Use **UTC** for `now` and event datetime in `_check_economic_calendar_alerts()` and `_send_economic_alert_to_user()`. |
