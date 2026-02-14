# Live News: Fetching, Caching, Persistent Storage & Layering — Evaluation

## 1. System Overview

### 1.1 Data flow (high level)

```
[RSS] + [Alternative] + [Telegram]  →  dedupe & filter  →  merge with existing cache  →  Firebase
         (parallel)                      (title+source)      (new on top, cap 200)         (current + history)
                                                                                               ↓
Client  ←  GET /api/news  ←  return cache immediately (or return fresh after fetch)  ←  load_news()
```

- **Fetch**: Every 5 minutes (or on force refresh), the backend fetches from three sources in parallel.
- **Cache**: “Current” feed is stored in Firebase at `news_cache/current` (single JSON object: `timestamp`, `news_count`, `news[]`, `last_fetch`).
- **History**: Individual items are stored under `news_cache/history/{news_id}` (up to 500 items); used for the History tab and for looking up a story by ID.
- **Layering**: New items are **prepended** to existing cache; combined list is **capped at 200**; that list is written back as the new “current” cache. So you get a rolling window of the 200 most recent items.

---

## 2. Fetching

**Where**: `backend/app.py` `get_news()` and `_news_scheduler_loop()`.

- **Triggers**: (1) **Periodic scheduler**: a daemon thread started at app load runs every 5 minutes (`_NEWS_FETCH_INTERVAL_SECONDS = 300`) and calls `_maybe_start_background_news_fetch()`, so the cache is updated continuously regardless of traffic. (2) **Request-driven**: when a request finds cache stale (`should_fetch_new_news(5, last_fetch)`), it returns cache immediately and starts a background fetch; when `force_refresh=true` the request runs the fetch (and with `wait_fresh=true` returns the fresh result).
- **Sources** (parallel, `ThreadPoolExecutor(max_workers=3)`):
  - RSS: `news_aggregator.get_recent_news(hours=24)` (timeout 10s)
  - Alternative: `alternative_news_sources.get_alternative_news(hours=24)` (timeout 10s)
  - Telegram: `telegram_sync.get_recent_telegram_news(hours=24)` (timeout 15s)
- **Deduplication**: By `title + source` (and later by `id` when merging with cache).
- **Filtering**: Hardcoded phrase (e.g. “Gold rises, according to FXStreet data”) and economic-calendar detection (clear cache if Finnhub/economic events found in cache).

**Strengths**: Parallel fetch, timeouts, single hardcoded filter.

**Gaps**: No per-source circuit breaker; no retries; filter list is not configurable.

---

## 3. Caching (in-memory vs persistent)

- **No in-memory cache**: Each request that needs news calls Firebase (or triggers a fetch then returns).
- **Persistent cache**: Firebase Realtime Database at `news_cache/current`:
  - One document with `news` (array of items), `timestamp`, `news_count`, `last_fetch`, `max_age_hours`.
  - **TTL**: `max_age_hours = 0.25` (15 min) is used only to decide “is this stale?”; **stale is still returned** for fast UI (`allow_stale=True`). Fresh fetch runs when `last_fetch` is older than 5 minutes.

So “caching” is really: **persistent store + 5‑minute fetch interval + “return stale then refresh”**.

---

## 4. Persistent storage (Firebase)

**Current cache** (`news_cache/current`):

- Single PUT of the full object: `{ timestamp, news_count, news[], max_age_hours, last_fetch }`.
- **Max 200 items** in `news[]`; each item has `id`, `title`, `summary`, `source`, `url`, `published_at`, `added_to_feed_at`, `impact`, etc.

**History** (`news_cache/history`):

- One node per item: `news_cache/history/{news_id}` → one object per story.
- **Max 500 items**; cleanup removes oldest by `cached_at` when over limit.
- Used by: History tab (`get_recent_history(hours)`), `get_news_by_id()`, and when saving after merge.

**Write pattern on merge**:

1. Load existing cache (GET).
2. Merge: `merged_news = new_items + existing_news`, then `merged_news = merged_news[:200]`.
3. Single PUT to `news_cache/current` with the new 200-item list.
4. For history: only items not already in history get a PUT to `news_cache/history/{id}` (one PUT per new item).

So “layering 100 events on top” is: **new batch + existing list, sort by `added_to_feed_at`, keep newest 200, write that back**.

---

## 5. Layering (merge) logic

**Where**: `PersistentNewsCache.save_news(..., append=True)` and `get_news()` in `app.py`.

**Steps**:

1. **Backend** (when there is fresh news):
   - Dedupe fresh batch by `title + source`.
   - Filter unwanted phrase (and economic events).
   - If there is existing cache: build `cached_items_map` by `title + source`; for each fresh item, reuse `added_to_feed_at` if it exists in cache, else set to now; then append cached items not in fresh set → `all_news`.
   - Sort `all_news` by `added_to_feed_at` descending.
   - Call `news_cache.save_news(fresh_news_to_save, append=True)` (with `fresh_news_to_save = fresh_news[:200]`).

2. **PersistentNewsCache.save_news(append=True)**:
   - Load existing cache (`load_news(allow_stale=True)`).
   - Dedupe again by `id` and by `title+source` (lowercase): only items not already in cache go into `new_items`.
   - `merged_news = new_items + existing_news` (new first).
   - If `len(merged_news) > 200`: `merged_news = merged_news[:200]`.
   - PUT full `merged_news` to `news_cache/current`.
   - Add to history only items not already in history (one PUT per new history item).

**Result**: A rolling window of **200 items**, newest first, with stable `added_to_feed_at` for items that were already in cache. No duplicate stories in the feed (by id or title+source).

---

## 6. Frontend

- **Live tab**: `news` from `GET /api/news` → filtered and deduped again (e.g. `removeDuplicateNews`, forex relevance), sorted by `added_to_feed_at`.
- **History tab**: `newsHistory` from `GET /api/news-history?hours=24` → same filtering/sorting; can optionally show only analyzed items.
- **No client-side cap**: The UI shows whatever the backend returns (up to 200 for live; history is whatever is in the 24h window, up to 500).

So “100 events on top of each other” is handled by: **backend cap at 200**, merge order (new on top), and frontend sort by `added_to_feed_at` so the list is always “newest first” without stacking duplicates.

---

## 7. Evaluation and improvements

### 7.1 What works well

- **Persistent cache**: Survives restarts; no loss of feed on deploy.
- **Fast first paint**: Stale cache returned immediately; fetch in background when interval exceeded.
- **Clear layering**: New items prepended, cap at 200, single source of truth in Firebase.
- **Deduplication**: Both by `id` and by `title+source` (backend) and by title/URL (frontend).
- **History separate from cache**: 500-item history for History tab and lookups; 200-item “current” for live feed.

### 7.2 Issues and improvements

| Area | Issue | Improvement |
|------|--------|-------------|
| **Magic numbers** | 200 (cache cap) and 500 (history cap) are hardcoded in multiple places. | Use named constants (e.g. in `persistent_news_cache.py`) or env/config; reference same values in `app.py` when limiting `fresh_news_to_save` / `all_news_to_save`. |
| **History write storm** | When 50+ new items are merged, each new history item is written with a separate PUT. | Batch where possible (e.g. Firebase multi-path update or a small batch endpoint), or at least limit how many new history entries we write per request (e.g. cap at 50 per save). |
| **Stale + background fetch** | ~~Client that triggers a request gets stale data; next request (or 5‑min poll) gets fresh.~~ | **Implemented**: When the backend returns stale cache (`cache_status: cached_stale`), it starts a single background thread that fetches from RSS/alt/Telegram, merges, and saves to Firebase. The next poll (e.g. 5 min) then receives the updated cache. Only one background fetch runs at a time (threading lock). |
| **Filter list** | Unwanted phrase is hardcoded in backend and frontend. | Move to config or DB (e.g. list of filter phrases); apply in one place (backend) and document for frontend. |
| **Dedupe key mismatch** | Backend: `title + source` (lowercase). Frontend: cleaned title (first 5 words) + URL + source. | Prefer backend as source of truth; document dedupe rules. Optionally align frontend key with backend (e.g. same normalisation) to avoid rare duplicates. |
| **Cache TTL vs fetch interval** | `max_age_hours=0.25` (15 min) but fetch every 5 min. So cache is almost always “stale” by TTL but still used. | Either increase `max_age_hours` to match intent (e.g. 1h) or rename to “stale threshold” and keep 15 min; clarify in code comments. |
| **Force refresh UX** | Force refresh returns cached immediately, then fetches; user doesn’t see new data until next load. | Same as “stale + background”: consider short-poll or `wait_fresh` so the client that clicked “Refresh” gets the new 200-item list when ready. |
| **Payload size** | 200 items × ~1–2 KB ≈ 200–400 KB per PUT. Firebase allows it, but growth could hurt. | Keep 200 cap; if adding more fields, consider trimming large fields (e.g. `summary` length) before writing, or compressing. |
| **get_recent_history** | Loads full history (up to 500 items) then filters by `cached_at` in memory. | Acceptable for 500 items; if history grows, consider time-based Firebase query or a small index. |

### 7.3 Recommended next steps (priority)

1. **Introduce constants** for cache cap (200) and history cap (500) in `persistent_news_cache.py` and use them in `app.py` when slicing `fresh_news` / `all_news` before save. Reduces drift and makes “layering 100 events” behavior explicit.
2. **Document** that “layering” = merge new + existing, sort by `added_to_feed_at`, keep newest 200; and that history is a separate 500-item store.
3. **Optional**: Cap new history writes per save (e.g. only add the N newest items that aren’t in history) to avoid a burst of 100+ PUTs in one request.
4. **Optional**: Improve force-refresh UX with a short-poll or `wait_fresh` so the client that requested refresh sees the updated 200-item list without a manual reload.

---

## 8. Multi-user and continuous behaviour

### 8.1 How the cache stays up to date for all users

- **Periodic scheduler**: At app load, a daemon thread starts (`_news_scheduler_loop`) that runs every **5 minutes** (`_NEWS_FETCH_INTERVAL_SECONDS = 300`). Each tick it calls `_maybe_start_background_news_fetch()`, which runs the same fetch+merge+save as a request-driven fetch (RSS + alternative + Telegram → dedupe → merge with cache → save to Firebase). Only one fetch runs at a time per process (threading lock).
- **Effect**: The cache is updated **continuously** every 5 minutes regardless of whether anyone is on the dashboard. New users and existing users who open or refresh the dashboard then read from this shared cache.

### 8.2 User scenarios

| User type | What happens |
|-----------|----------------|
| **New user** (first time opening dashboard) | `GET /api/news` returns whatever is in Firebase (current cache). Cache was last updated by the scheduler or a previous user’s request. If cache is empty (e.g. fresh deploy), that request triggers a fetch and populates the cache. |
| **Existing user** (just opened dashboard again) | Same as above: they get the current cache. The scheduler keeps it at most ~5 minutes old, so they see recently updated news without clicking Refresh. |
| **User already on dashboard** | Frontend polls `GET /api/news` every 5 minutes. Each poll gets the cached list. Because the scheduler (and/or request-driven background fetch) updates the cache every 5 min, the next poll typically gets data that was refreshed since their last poll. No manual refresh needed for incremental updates. |
| **User clicks Refresh** | Request uses `force_refresh=true&wait_fresh=true`, so the server runs a full fetch in that request and returns the new merged list. They see the latest data immediately after the request completes. |

### 8.3 Single shared cache

- All users share the **same** Firebase `news_cache/current`. There is no per-user or per-session cache. So when the scheduler or any request updates the cache, **every** user’s next request sees that update.
- With multiple app workers (e.g. gunicorn with several workers), each worker runs its own scheduler thread. So you may get one fetch per worker per 5 minutes. The lock is per-process, so within one worker only one fetch runs at a time. Redundant fetches across workers are acceptable and keep the cache fresh.

### 8.4 Summary of continuous behaviour

- **Scheduler**: Runs every 5 min in the background so the feed is updated even when no one is polling.
- **Request-driven**: If a request finds cache stale, it still returns cache immediately and can start a background fetch so the next request gets fresh data.
- **Result**: New and existing users see up-to-date live news without relying on manual refresh; the system is continuously working to keep the cache current.

---

## 9. Summary

- **Fetching**: Parallel RSS + alternative + Telegram; triggered every 5 min by the **periodic scheduler** and on demand (stale-cache background fetch or force refresh); dedupe by title+source; one hardcoded filter.
- **Caching**: No in-memory cache; “cache” = Firebase `news_cache/current` (single object, max 200 items).
- **Persistent storage**: Firebase: `current` (one PUT for the full list) and `history/{id}` (one PUT per new history item, max 500).
- **Layering**: New items prepended to existing; combined list capped at 200 and written back; `added_to_feed_at` preserved for existing items so order is stable and “100 events on top” is a rolling window of 200, newest first.

Improvements focus on configurable limits, fewer magic numbers, optional batching/capping of history writes, and better UX when the client triggers a refresh.
