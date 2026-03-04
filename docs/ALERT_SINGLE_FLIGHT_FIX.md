# Alert Single-Flight Fix (Log Analysis)

**Date:** 2026-03-04  
**Log file analyzed:** `data/logs.1772632761061.json`

## Findings from Log Analysis

### 1. Concurrent `check_news_alerts` invocations
Two "Checking 10 news items for alerts..." entries at **the same second** (13:58:41):

```
2026-03-04T13:58:41 | Checking 10 news items for alerts...
2026-03-04T13:58:41 | Checking 10 news items for alerts...
```

**Cause:** Multiple concurrent `/api/news` requests (or different code paths) both call `check_news_alerts_async()` with overlapping news. Each spawns a background thread; both run `_check_news_alerts` in parallel.

### 2. Same user getting many reserves in rapid succession
Example: user `d378ee2732e19a6a` received 5 reserves in ~9 seconds:
- 13:56:57 (UK Energy)
- 13:56:59 (USD/CHF)
- 13:57:02 (Breaking payrolls)
- 13:57:04 (Oil crisis)
- 13:57:06 (EUR/JPY)

**Cause:** Two overlapping alert check runs both submit (user, news) tasks. Per-user lock serializes within one run, but with two runs, each run’s tasks contend and can interleave. Also, failed sends skip the 15s delay, so the next task can run soon after.

### 3. Dedup is working
No same user + same content reserved twice. Firebase dedup correctly prevents duplicate sends for the same story.

## Fix Applied

**Single-flight lock** in `unified_alert_processor.py`:

- `_news_alerts_check_lock` ensures only one `_check_news_alerts` run at a time.
- If a check is already in progress, new invocations skip with: `"⏭️ Skipping news alert check (N items) - already in progress"`.

This removes the duplicate processing that led to alerts in the same timeframe.

## Files Changed

- `backend/services/unified_alert_processor.py`:
  - Added `_news_alerts_check_lock`
  - In `_check_news_alerts_with_error_handling`, use `acquire(blocking=False)`; if not acquired, return immediately
  - `finally` block releases the lock
