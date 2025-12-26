# News Accumulation System - 5-Minute Refresh

## Overview

The news system now works as follows:
- **Every 5 minutes**, the system checks for new news
- **New news is appended** to the persistent cache (not replaced)
- **New news appears on top** of existing news
- **News accumulates** over time (up to 200 items)
- **Cache persists** across restarts

---

## How It Works

### 1. Frontend Behavior
- Calls `/api/news` every **5 minutes** (changed from 2 minutes)
- Displays all cached news immediately
- New news automatically appears when fetched

### 2. Backend Behavior

#### Initial Request (No Cache)
1. No cache exists
2. Fetch fresh news from all sources
3. Save to cache (replace mode)
4. Return news to frontend

#### Subsequent Requests (< 5 minutes since last fetch)
1. Cache exists and is valid
2. **Serve cached news immediately** (fast response)
3. **Do NOT fetch new news** (saves API calls)
4. Return cached news to frontend

#### Requests After 5 Minutes
1. Cache exists
2. **Serve cached news immediately** (non-blocking)
3. **Fetch new news in background**
4. **Merge new news with cached news** (new on top)
5. **Deduplicate** to avoid duplicates
6. **Save merged news** to cache (append mode)
7. Return merged news to frontend

---

## Key Features

### Append Mode
- New news is **appended** to existing cache
- New items appear **on top** (newest first)
- Existing items remain in cache
- **Deduplication** prevents duplicates

### Cache Limits
- Maximum **200 items** in cache
- Oldest items removed when limit exceeded
- Keeps most recent news

### Deduplication
- Based on **news ID** and **title**
- Prevents same news appearing twice
- Works across multiple sources

### Persistence
- Cache persists across **app restarts**
- Cache persists across **deployments**
- Uses Firebase Realtime Database

---

## Code Changes

### Backend Changes

1. **`persistent_news_cache.py`**:
   - Added `append` parameter to `save_news()` method
   - Added `should_fetch_new_news()` method (checks last fetch time)
   - Added `last_fetch` timestamp tracking

2. **`app.py`** (`/api/news` endpoint):
   - Checks cache age using `should_fetch_new_news()`
   - Fetches new news every 5 minutes
   - Merges new news with cached news
   - Uses append mode when merging

### Frontend Changes

1. **`LiveNewsFeed.jsx`**:
   - Changed refresh interval from **2 minutes to 5 minutes**
   - Matches backend fetch interval

---

## Flow Diagram

```
Frontend Request → Backend
    ↓
Check Cache
    ↓
Cache exists?
    ├─ No → Fetch fresh news → Save (replace) → Return
    └─ Yes → Check last_fetch time
              ↓
         > 5 minutes?
              ├─ No → Return cached news (fast)
              └─ Yes → Return cached news immediately
                        ↓
                   Fetch new news
                        ↓
                   Merge: new + cached
                        ↓
                   Deduplicate
                        ↓
                   Save (append mode)
                        ↓
                   Return merged news
```

---

## Benefits

✅ **Fast Response**: Cached news served immediately
✅ **Fresh Content**: New news fetched every 5 minutes
✅ **Accumulation**: News builds up over time
✅ **Persistence**: Survives restarts and deployments
✅ **Efficient**: Only fetches when needed (every 5 min)
✅ **No Duplicates**: Deduplication prevents duplicates

---

## Configuration

### Fetch Interval
- **Default**: 5 minutes
- **Configurable**: Change `fetch_interval_minutes` parameter
- **Location**: `news_cache.should_fetch_new_news(fetch_interval_minutes=5)`

### Cache Size Limit
- **Default**: 200 items
- **Configurable**: Change limit in `save_news()` append logic
- **Location**: `persistent_news_cache.py` line ~81

### Cache TTL
- **Default**: 15 minutes (0.25 hours)
- **Purpose**: Determines when cache expires (not used for fetch timing)
- **Location**: `persistent_news_cache.py` line ~22

---

## Testing

### Test Accumulation
1. Call `/api/news` - should fetch fresh news
2. Wait 5 minutes
3. Call `/api/news` again - should fetch new news and append
4. Verify new news appears on top
5. Verify no duplicates

### Test Persistence
1. Cache some news
2. Restart app
3. Verify cache still exists
4. Verify news is still there

### Test Deduplication
1. Fetch news (creates cache)
2. Fetch same news again (should not duplicate)
3. Verify no duplicate items in cache

---

## Troubleshooting

### Issue: News not accumulating

**Check**:
- `last_fetch` timestamp in Firebase
- Time since last fetch
- Logs for "should fetch new news" messages

**Solution**:
- Verify `should_fetch_new_news()` is working
- Check Firebase connection
- Review logs for errors

### Issue: Duplicates appearing

**Check**:
- Deduplication logic
- News IDs and titles
- Merge logic

**Solution**:
- Verify deduplication is working
- Check ID generation
- Review merge logic

### Issue: Cache not persisting

**Check**:
- Firebase connection
- Cache save operations
- Firebase structure

**Solution**:
- Verify Firebase credentials
- Check Firebase console
- Review save operations

---

## Summary

The news system now:
- ✅ Fetches new news every 5 minutes
- ✅ Appends new news to existing cache
- ✅ Displays new news on top
- ✅ Accumulates news over time
- ✅ Persists across restarts
- ✅ Deduplicates automatically

