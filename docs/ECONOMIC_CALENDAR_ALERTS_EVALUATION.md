# Economic calendar alerts – evaluation and fixes

**Scope:** Why high-impact economic calendar events might not trigger alerts. Events and dates/times live in `hybrid_economic_calendar.py` (static events OK for now).

---

## 1. Alert flow (high level)

| Path | Event source | Who runs it | User source |
|------|--------------|-------------|--------------|
| **UnifiedAlertProcessor** | `hybrid_economic_calendar.get_economic_events(start, end)` | Main app background thread (every 5 min) | `get_all_users_with_alerts()`, filter by `preNews` |
| **EconomicCalendarAlerts.process_economic_calendar_for_alerts()** | HTTP `GET /api/economic-calendar` (hybrid) | ProductionAlertWorker, scripts | **Was:** `get_all_users()` (missing) + wrong prefs path |
| **BackgroundAlertWorker** | **Was:** Finnhub when local, API when HTTP | Worker loop | Sends via API trigger (one event at a time) |

---

## 2. Issues found and fixes

### 2.1 **Critical: `get_all_users()` does not exist (economic_calendar_alerts.py)**

- **Issue:** `get_users_to_alert()` called `firebase_storage.get_all_users()`. Firebase only has `get_all_users_with_alerts()`, so this raised `AttributeError` and no users were ever returned for the process_economic_calendar_for_alerts path.
- **Fix:** Use `get_all_users_with_alerts()` and iterate over the returned list. Build user dicts with `user_id`, `settings`, `chat_id`, `telegram_chat_id`.

### 2.2 **Wrong preference path (economic_calendar_alerts.py)**

- **Issue:** Code looked for `settings.alerts.economicCalendar.enabled` and `settings.alerts.channels.telegram.enabled`. The rest of the app uses `settings.preferences.alertTypes.preNews` and `settings.channels.telegram` / `preferences.channels.telegram`, so no users matched.
- **Fix:** Use `settings.preferences.alertTypes.preNews` (default True) with fallback to `alerts.economicCalendar.enabled`. Use the same Telegram checks as unified processor and news alerts. Use `preferences.currencyPairs` (list or dict) and `preferences.impactLevels` / `quietHours`.

### 2.3 **Over-strict validation (economic_calendar_alerts.py)**

- **Issue:** `_validate_event_data` required `raw_data` and `status in ['UPCOMING', 'IMMINENT']`. Hybrid enriched events do have these, but any event without `raw_data` or with `status == 'today'` was rejected.
- **Fix:** Removed the requirement for `raw_data`. Treat missing `status` as upcoming; allow `status` in `['UPCOMING', 'IMMINENT', 'TODAY']` to match unified processor.

### 2.4 **BackgroundAlertWorker used wrong calendar when local (background_alert_worker.py)**

- **Issue:** `_get_economic_calendar_local()` used `finnhub_calendar.get_economic_calendar()` when running in app context. So the worker could send alerts from Finnhub data while the app and API use hybrid; formats and event set differ.
- **Fix:** Use `hybrid_economic_calendar.get_economic_events(start_date, end_date)` in app context (same as main app and API).

### 2.5 **BackgroundAlertWorker timing windows too narrow (background_alert_worker.py)**

- **Issue:** Windows were 8–10 min, 55–60 min, 115–120 min. With a 5‑minute check interval, the 10‑minute window was easy to miss.
- **Fix:** Use the same windows as UnifiedAlertProcessor: 5–15 min, 50–65 min, 110–125 min.

---

## 3. What was already correct

- **UnifiedAlertProcessor:** Uses hybrid, `get_all_users_with_alerts()`, and `preNews`; date/time parsing supports both `YYYY-MM-DD` and `Mon, Oct 13`; status filter `['upcoming', 'today']` matches hybrid’s `_get_status()`.
- **Hybrid:** `get_economic_events()` returns enriched events (with `status`, `raw_data`) via `_enrich_with_alpha_vantage()`. Static events have `date`, `time`, `impact`.
- **API `/api/economic-calendar`:** Returns hybrid events and source `"Hybrid Calendar (ForexFactory)"`, so no false “fallback/mock” skip in economic_calendar_alerts.
- **Dedup:** Economic alerts use `persistent_alert_deduplication.should_send_economic_alert` / `mark_economic_alert_sent` (event + user + alert_timing).

---

## 4. Static event date range

- Hybrid static events are dated roughly Oct 5 – Jan 9 (e.g. in comments). `get_economic_events(start_date, end_date)` only returns events whose date falls in `[start_date, end_date]` (e.g. today to today+7).
- If “today” is outside that range (e.g. March 2026), the hybrid list returns no events and no economic alerts fire. That’s expected until static data is updated or replaced with a feed. No code change for that; just keep event dates in hybrid in sync with the period you care about.

---

## 5. Files changed

| File | Change |
|------|--------|
| `backend/services/economic_calendar_alerts.py` | Use `get_all_users_with_alerts()`; align preferences with app (`preferences.alertTypes.preNews`, Telegram, currencyPairs, impactLevels, quietHours); add `telegram_chat_id` to user dict; make `raw_data` optional and allow status `TODAY` / missing. |
| `backend/services/background_alert_worker.py` | Use `hybrid_economic_calendar.get_economic_events()` in `_get_economic_calendar_local()`; widen timing windows to match unified processor. |

---

## 6. Recommendation

- After these fixes, the main reasons high-impact economic calendar alerts would not send are:
  1. **Date range:** No static events in the requested window (update hybrid dates or use a live feed).
  2. **User preferences:** User has `preNews` off or Telegram off, or no matching currency pairs / impact level.
  3. **Timing:** Check runs every 5 min; events must fall in the 5–15 / 50–65 / 110–125 minute windows. If the run is slightly late, the next run might see the event already in the past (minutes_until_event &lt; 0) and skip it.

- For production: ensure the worker that should send economic alerts actually runs (UnifiedAlertProcessor background thread in main app, and/or ProductionAlertWorker / BackgroundAlertWorker) and that Firebase has the correct user settings under `preferences.alertTypes.preNews` and Telegram.
