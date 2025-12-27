# Live News Feed System - Complete Explanation

This document provides a comprehensive explanation of the entire live news feed system, including all components, data flow, logic, caching strategy, and recent improvements.

## Table of Contents

1. [System Overview](#system-overview)
2. [Frontend Components](#frontend-components)
3. [Backend API Endpoint](#backend-api-endpoint)
4. [Data Sources](#data-sources)
5. [Caching System](#caching-system)
6. [Data Flow](#data-flow)
7. [Deduplication Logic](#deduplication-logic)
8. [Timestamp Preservation](#timestamp-preservation)
9. [Refresh Mechanism](#refresh-mechanism)
10. [Recent Improvements](#recent-improvements)

---

## System Overview

The live news feed system aggregates forex-related news from multiple sources (RSS feeds, alternative sources, Telegram channels), caches it persistently, and serves it to the frontend. The system is designed to:

- **Fetch news** from RSS feeds, alternative sources, and Telegram channels
- **Cache news** persistently in Firebase Realtime Database
- **Merge fresh and cached** news while preserving timestamps
- **Deduplicate** news items across sources
- **Serve news** quickly to the frontend (even stale cache for instant loading)
- **Update cache** every 5 minutes or on manual refresh

---

## Frontend Components

### LiveNewsFeed.jsx

**Location**: `src/components/LiveNewsFeed.jsx`

**Purpose**: Main React component that displays the live news feed to users.

**Key Features**:
- Fetches news from `/api/news` endpoint
- Auto-refreshes every 5 minutes
- Manual refresh button (force refresh)
- Filtering by impact level (all, high, medium, low)
- AI analysis integration
- News history tracking

**State Management**:
```javascript
const [news, setNews] = useState([]);              // News items array
const [loading, setLoading] = useState(true);      // Loading state
const [error, setError] = useState(null);          // Error state
const [filter, setFilter] = useState('all');       // Impact filter
const [forceRefreshing, setForceRefreshing] = useState(false); // Refresh state
```

**Auto-Refresh Mechanism**:
- Fetches news on component mount
- Sets up interval to fetch every 5 minutes
- Backend handles fetching new news and merging with cache

**Manual Refresh**:
- User clicks refresh button
- Calls `fetchNews(true)` with `forceRefresh=true`
- Frontend sends request to `/api/news?force_refresh=true`
- Backend skips cache and fetches fresh news
- Same fetch logic as automatic 5-minute fetch

**Timeout Handling**:
- Normal requests: 15-second timeout
- Force refresh: 30-second timeout
- Prevents hanging requests

---

## Backend API Endpoint

### `/api/news` Endpoint

**Location**: `backend/app.py`

**Purpose**: Main endpoint that handles news fetching, caching, and serving.

**Query Parameters**:
- `force_refresh` (optional): If `true`, skips cache and fetches fresh news

**Request Flow**:

#### 1. Initial Setup
```
Request arrives → Check force_refresh parameter
```

#### 2. Cache Loading (if not force refresh)
```python
if not force_refresh:
    cached_news = news_cache.load_news(allow_stale=True)  # Load cache (even if stale)
    should_fetch_new = news_cache.should_fetch_new_news(fetch_interval_minutes=5)
```

**Key Decision Points**:
- `allow_stale=True`: Returns cached news even if expired (>15 minutes old) for faster UI
- `should_fetch_new_news()`: Checks if last fetch was >5 minutes ago

#### 3. Immediate Cache Return (Optimization)
```python
if cached_news and not force_refresh:
    if not should_fetch_new:
        # Cache is fresh (< 5 minutes) - return immediately
        return cached_news
    else:
        # Cache is stale - return it immediately for fast UI
        # Fresh fetch happens in background (user gets it on next request)
        return cached_news (with cache_status: "cached_stale")
```

**Why this optimization?**
- UI loads instantly with cached news
- User doesn't wait for API calls
- Fresh news is fetched in background
- Next request (or refresh) gets fresh news

#### 4. Force Refresh Handling
```python
if force_refresh:
    cached_news = None              # Skip cache
    should_fetch_new = True         # Always fetch fresh
    # Uses same fetch logic as regular fetch below
```

**Simplification**:
- Force refresh now uses the **same fetch logic** as regular 5-minute fetch
- No separate `force_refresh_news_internal()` function
- More reliable and consistent

#### 5. Fresh News Fetching
```python
if should_fetch_new or force_refresh:
    # Fetch from multiple sources in parallel:
    - RSS Feeds (Bloomberg, CNBC, MarketWatch, FXStreet, ForexLive, etc.)
    - Alternative Sources (FXStreet, ForexLive, MarketWatch)
    - Telegram (WatcherGuru channels)
```

**Parallel Fetching**:
- Uses `ThreadPoolExecutor` for concurrent requests
- 10-second timeout per source
- Continues even if some sources fail

**RSS Feed Improvements**:
- Checks up to **20 entries** per feed (increased from 10)
- No longer stops after 5 articles (checks all entries)
- Finds more recent articles that might be further down in feeds

**Telegram Improvements**:
- Includes **gold and silver news** (marked as high impact)
- Deduplicates across channel variants (@WatcherGuru vs WatcherGuru)
- Uses enhanced forex filter for better accuracy

#### 6. Merging Fresh + Cached News

**Step 1: Deduplicate Fresh News**
```python
fresh_news = remove_duplicate_news_simple(fresh_news)
# Removes duplicates within fresh news itself
```

**Step 2: Load Cached News for Merging**
```python
if force_refresh and not cached_news:
    cached_news = news_cache.load_news(allow_stale=True)
    # Load cached news to preserve added_to_feed_at timestamps
```

**Step 3: Merge and Preserve Timestamps**
```python
if cached_news:
    # Create map of cached items by title+source
    cached_items_map = {key: item for item in cached_news}
    
    # Add fresh news, preserving added_to_feed_at from cache
    for item in fresh_news:
        if item exists in cached_items_map:
            item['added_to_feed_at'] = cached_item['added_to_feed_at']  # Preserve!
        else:
            item['added_to_feed_at'] = current_time  # New item
    
    # Add cached items that aren't in fresh news
    all_news = fresh_news + (cached_items_not_in_fresh)
else:
    # No cache - use only fresh news
    all_news = fresh_news
```

**Step 4: Sort by added_to_feed_at**
```python
all_news.sort(key=lambda x: x.get('added_to_feed_at'), reverse=True)
# Newest items first (based on when first added to feed, not published date)
```

#### 7. Saving to Cache

**Critical Logic**:
```python
if cached_news and (should_fetch_new or force_refresh):
    # IMPORTANT: Pass only fresh_news, not all_news
    news_cache.save_news(fresh_news, append=True)
else:
    # First time or no cache
    news_cache.save_news(all_news, append=False)
```

**Why `append=True` with only `fresh_news`?**
- `save_news` with `append=True`:
  1. Loads existing cache
  2. Compares `fresh_news` against existing cache
  3. Adds only truly new items (preserving `added_to_feed_at` from existing)
  4. Merges: new items on top, existing items below

- If we passed `all_news` (fresh + cached), it would see everything as existing and add nothing!

**Why this matters**:
- New news items are correctly added to cache
- Existing items keep their original `added_to_feed_at` timestamps
- Cache grows correctly over time

#### 8. Return Response
```python
return {
    "news": all_news,                    # Merged list (fresh + cached)
    "last_updated": datetime.now(),      # Current time
    "sources": sources_used,             # ["RSS Feeds", "Telegram", etc.]
    "total_articles": len(all_news),
    "cache_status": "fresh" or "cached" or "cached_stale"
}
```

---

## Data Sources

### 1. RSS Feeds (news_aggregator.py)

**Sources**:
- Bloomberg: `https://feeds.bloomberg.com/markets/news.rss`
- CNBC: `https://www.cnbc.com/id/100003114/device/rss/rss.html`
- MarketWatch: `https://feeds.marketwatch.com/marketwatch/marketpulse/`
- FXStreet: `https://www.fxstreet.com/rss`
- ForexLive: `https://www.forexlive.com/feed/`

**Fetching Process**:
1. Fetches RSS feed using `requests.get()` with 8-second timeout
2. Parses feed using `feedparser`
3. Checks **up to 20 entries** per feed (recent improvement)
4. Filters for forex-related articles using `enhanced_forex_filter`
5. Parses articles into standard format with:
   - `id`: Hash of title + source + date
   - `title`: Article title
   - `summary`: Article summary (up to 800 chars)
   - `source`: Source name (e.g., "Bloomberg")
   - `url`: Article URL
   - `published_at`: Original publication date from RSS
   - `added_to_feed_at`: When added to our system (set on first fetch)
   - `impact`: "high", "medium", or "low"
   - `currency_pairs`: Detected currency pairs
   - `type`: "RSS_FEED"

**Improvements**:
- Increased from 10 to 20 entries checked per feed
- Removed early stop after 5 articles
- Now finds articles that might be further down in feeds

### 2. Alternative Sources (alternative_news_sources.py)

**Sources**:
- ForexLive
- FXStreet
- MarketWatch

**Fetching Process**:
Similar to RSS feeds, but uses different filtering logic.

**Improvements**:
- Increased from 15 to 25 entries checked per feed

### 3. Telegram Channels (telegram_sync_wrapper.py)

**Channels**:
- WatcherGuru (main channel)
- @WatcherGuru (variant - deduplicated)

**Fetching Process**:
1. Creates isolated Telegram client session
2. Fetches messages from channels (up to 20 messages, max 10 per channel)
3. Filters for forex-related messages
4. **Now includes gold/silver news** (marked as high impact)
5. Parses into standard format

**Filtering**:
- Uses `enhanced_forex_filter` for better accuracy
- Includes commodity keywords (gold, silver, precious metals)
- Marks gold/silver as high impact (they're safe-haven assets)

**Deduplication**:
- Removes duplicates between @WatcherGuru and WatcherGuru
- Uses channel ID to detect same channel with different names

---

## Caching System

### PersistentNewsCache (persistent_news_cache.py)

**Storage**: Firebase Realtime Database

**Purpose**: 
- Persist news across server restarts
- Enable sharing cache across multiple instances
- Survive deployments

**Cache Structure**:
```
news_cache/current/
  - timestamp: When cache was last updated
  - news_count: Number of articles
  - news: Array of news items
  - max_age_hours: 0.25 (15 minutes)
  - last_fetch: When news was last fetched
```

**Key Methods**:

#### `load_news(allow_stale=True)`
- Loads cache from Firebase
- Checks if cache is too old (>15 minutes)
- If `allow_stale=True`: Returns cache even if expired (for faster UI)
- If `allow_stale=False`: Returns None if expired

**Recent Improvement**:
- `allow_stale=True` by default for faster UI loading
- Cache is returned even if expired
- Fresh fetch happens in background

#### `save_news(news_items, append=False)`
- Saves news items to Firebase
- If `append=True`:
  1. Loads existing cache (with `allow_stale=True`)
  2. Compares `news_items` against existing cache
  3. Preserves `added_to_feed_at` from existing items
  4. Adds only truly new items
  5. Merges: new items first, then existing items
  6. Limits to 200 items (newest first)
- If `append=False`:
  1. Replaces entire cache
  2. Adds all items to history

**Recent Improvements**:
- Uses `title+source` as key for better matching
- Preserves `added_to_feed_at` from existing items correctly
- Loads cache with `allow_stale=True` to get all items

#### `should_fetch_new_news(fetch_interval_minutes=5)`
- Checks `last_fetch` timestamp in cache
- Returns `True` if last fetch was >5 minutes ago
- Returns `False` if last fetch was <5 minutes ago

---

## Data Flow

### Complete Flow Diagram

```
User Opens Page / Clicks Refresh
         |
         v
Frontend: fetchNews(forceRefresh)
         |
         v
GET /api/news?force_refresh=true (if manual refresh)
         |
         v
Backend: /api/news endpoint
         |
    [Check force_refresh]
         |
    ┌────┴────┐
    |         |
  false     true
    |         |
    v         v
Load Cache  Skip Cache
    |         |
    v         |
Check if should_fetch_new
    |         |
    v         |
[Return cached immediately?]
    |         |
    └────┬────┘
         |
         v
Fetch Fresh News (if should_fetch_new or force_refresh)
    |
    ├──> RSS Feeds (parallel)
    ├──> Alternative Sources (parallel)
    └──> Telegram (sequential)
         |
         v
Deduplicate Fresh News
    |
    v
Merge with Cached News
    - Preserve added_to_feed_at from cached items
    - Set added_to_feed_at for new items
    |
    v
Sort by added_to_feed_at (newest first)
    |
    v
Save to Cache (append=True, only fresh_news)
    - save_news merges with existing cache
    - Preserves timestamps
    - Adds only new items
    |
    v
Return merged news to frontend
    |
    v
Frontend displays news
```

### Example Timeline

**T=0:00** - Initial Load
- Cache empty
- Fetch fresh news from all sources
- Save to cache with `append=False`
- Return news to frontend

**T=0:05** - 5 Minutes Later (Auto-refresh)
- Load cache (18 items, fresh)
- `should_fetch_new` = True (>5 minutes)
- Fetch fresh news (3 new items found)
- Merge: 3 new + 18 cached = 21 items
- Save with `append=True` (only 3 new items passed)
- Cache now has 21 items (3 new added)
- Return 21 items to frontend

**T=0:10** - User Clicks Refresh (Force)
- Skip cache check
- Fetch fresh news (0 new items, same as cache)
- Load cached news for merging
- Merge: 0 new + 21 cached = 21 items
- Save with `append=True` (0 new items, nothing added)
- Return 21 items to frontend

**T=0:15** - New News Published
- Auto-refresh triggers
- Fetch fresh news (2 new items found)
- Merge: 2 new + 21 cached = 23 items
- Save with `append=True` (2 new items passed)
- Cache now has 23 items
- Return 23 items to frontend

---

## Deduplication Logic

### Multi-Level Deduplication

#### Level 1: Within Fresh News
```python
# Deduplicate fresh news itself (multiple sources may have same article)
def remove_duplicate_news_simple(news_list):
    seen = {}
    unique_news = []
    for item in news_list:
        key = f"{item.get('title', '')}_{item.get('source', '')}"
        if key not in seen:
            seen[key] = item
            unique_news.append(item)
    return unique_news
```

#### Level 2: Fresh vs Cached (During Merge)
```python
# When merging fresh + cached
cached_items_map = {f"{item.title}_{item.source}": item for item in cached_news}

for item in fresh_news:
    key = f"{item.title}_{item.source}"
    if key in cached_items_map:
        # Item exists in cache - preserve its added_to_feed_at
        item['added_to_feed_at'] = cached_item['added_to_feed_at']
    else:
        # New item - set added_to_feed_at to current time
        item['added_to_feed_at'] = current_time
```

#### Level 3: During Cache Save (append=True)
```python
# In save_news with append=True
existing_news = load_news(allow_stale=True)
existing_by_key = {f"{item.title}_{item.source}": item for item in existing_news}

for item in news_items:  # Only fresh_news passed here
    key = f"{item.title}_{item.source}"
    if key in existing_by_key:
        # Item exists - don't add (will be included from existing_news)
        pass
    else:
        # New item - add to new_items list
        new_items.append(item)

# Merge: new_items first, then existing_news
merged_news = new_items + existing_news
```

**Why Three Levels?**
1. **Level 1**: Removes duplicates within fresh news (e.g., same article from RSS and Alternative)
2. **Level 2**: Preserves timestamps when merging for display
3. **Level 3**: Ensures cache only gets truly new items, preserves existing timestamps

---

## Timestamp Preservation

### The `added_to_feed_at` Field

**Purpose**: Track when a news item was **first added to our feed**, not when it was published.

**Why This Matters**:
- Users see "3 hours ago" based on when we first saw the article
- Not based on when it was originally published (could be days old)
- Consistent timestamps across page refreshes

### How It's Preserved

#### 1. When News is First Fetched
```python
# In news_aggregator.py, alternative_news_sources.py, telegram_sync_wrapper.py
added_to_feed_at = datetime.now().isoformat()  # Set to current time
```

#### 2. When Merging Fresh + Cached
```python
if item exists in cached_items_map:
    # Preserve original timestamp from cache
    item['added_to_feed_at'] = cached_item['added_to_feed_at']
else:
    # New item - set to current time
    item['added_to_feed_at'] = current_time
```

#### 3. When Saving to Cache (append=True)
```python
# In persistent_news_cache.py save_news()
if item_key in existing_keys:
    # Item exists in cache - preserve its added_to_feed_at
    # Don't add to new_items (will be included from existing_news)
    pass
else:
    # New item - set added_to_feed_at if not already set
    item['added_to_feed_at'] = current_time
    new_items.append(item)
```

**Result**: 
- Items keep their original `added_to_feed_at` timestamp across fetches
- Only new items get new timestamps
- Frontend displays consistent "time ago" values

---

## Refresh Mechanism

### Automatic Refresh (Every 5 Minutes)

**Frontend**:
```javascript
useEffect(() => {
    fetchNews();  // Initial fetch
    const interval = setInterval(fetchNews, 5 * 60 * 1000);  // Every 5 minutes
    return () => clearInterval(interval);
}, []);
```

**Backend**:
- Checks `should_fetch_new_news(fetch_interval_minutes=5)`
- Returns `True` if last fetch was >5 minutes ago
- Fetches fresh news and merges with cache

### Manual Refresh (Force Refresh)

**Frontend**:
```javascript
const fetchNews = async (forceRefresh = false) => {
    const url = forceRefresh 
        ? `${config.API_BASE_URL}/api/news?force_refresh=true`
        : config.endpoints.news;
    // ... fetch with 30-second timeout
}
```

**Backend**:
```python
if force_refresh:
    cached_news = None           # Skip cache
    should_fetch_new = True      # Always fetch fresh
    # Uses same fetch logic as regular fetch
```

**Key Point**: Force refresh uses the **exact same fetch logic** as automatic refresh, just skips the cache check.

### Cache Behavior

**Regular Request (no force_refresh)**:
1. Load cache (even if stale)
2. Return cache immediately if fresh (<5 minutes)
3. Return stale cache immediately if expired (optimization)
4. Fetch fresh news in background (for next request)

**Force Refresh**:
1. Skip cache entirely
2. Always fetch fresh news
3. Load cache for merging (to preserve timestamps)
4. Merge fresh + cached
5. Save fresh news to cache
6. Return merged news

---

## Recent Improvements

### 1. Increased RSS Feed Checking (December 2025)

**Before**:
- Checked only first 10 entries per feed
- Stopped after finding 5 forex articles
- Missed articles further down in feeds

**After**:
- Checks up to 20 entries per feed
- Checks all entries (no early stop)
- Finds more recent articles

**Impact**: More news articles discovered, especially newer ones

### 2. Gold/Silver News Inclusion (December 2025)

**Before**:
- Gold/silver news filtered out (not in keyword list)
- Telegram messages about gold/silver were ignored

**After**:
- Gold/silver added to forex keywords
- Marked as high impact (safe-haven assets)
- Included in news feed

**Impact**: Precious metals news now appears in feed

### 3. Cache Stale Return Optimization (December 2025)

**Before**:
- If cache expired (>15 minutes), returned empty
- User saw "No News Available"
- Had to wait for fresh fetch

**After**:
- Returns stale cache immediately (for fast UI)
- Fresh fetch happens in background
- Next request gets fresh news

**Impact**: Instant UI loading, no empty states

### 4. Force Refresh Simplification (December 2025)

**Before**:
- Used separate `force_refresh_news_internal()` function
- Cleared cache before fetching
- Complex error handling
- Often failed or returned empty

**After**:
- Uses same fetch logic as regular refresh
- Skips cache but still merges for timestamps
- Simpler and more reliable

**Impact**: Force refresh now works consistently

### 5. Timestamp Preservation Fix (December 2025)

**Before**:
- `added_to_feed_at` was overwritten on each fetch
- Timestamps showed "now" instead of when first added

**After**:
- `added_to_feed_at` preserved from cache
- Only new items get new timestamps
- Consistent timestamps across fetches

**Impact**: Correct "time ago" display, proper sorting

### 6. Cache Save Logic Fix (December 2025)

**Before**:
- Passed `all_news` (fresh + cached) to `save_news(append=True)`
- Everything appeared as existing, nothing added
- New news not saved to cache

**After**:
- Pass only `fresh_news` to `save_news(append=True)`
- `save_news` correctly identifies new items
- New news saved to cache correctly

**Impact**: New news correctly added to persistent cache

---

## Common Issues and Solutions

### Issue: "No News Available" Message

**Cause**: Cache expired and no cached news to return

**Solution**: 
- Cache now returns even if stale (`allow_stale=True`)
- Always returns news if cache exists
- Only shows empty if truly no news

### Issue: New News Not Appearing

**Cause**: 
- RSS feeds not checking enough entries
- Cache save logic passing wrong data

**Solution**:
- Increased RSS checking from 10 to 20 entries
- Fixed cache save to pass only fresh_news

### Issue: Refresh Button Doesn't Work

**Cause**: Separate force refresh function failing

**Solution**:
- Simplified to use same fetch logic as regular refresh
- More reliable and consistent

### Issue: Dates Keep Changing

**Cause**: `added_to_feed_at` not preserved from cache

**Solution**:
- Fixed timestamp preservation in merge logic
- Fixed cache save to preserve timestamps

---

## Performance Characteristics

### Response Times

**With Fresh Cache** (<5 minutes old):
- Response time: ~50-100ms (Firebase read)
- User experience: Instant

**With Stale Cache** (>5 minutes old):
- Response time: ~50-100ms (Firebase read)
- Fresh fetch: Happens in background
- User experience: Instant (sees stale cache), fresh on next request

**Force Refresh**:
- Response time: ~3-5 seconds (RSS + Telegram fetching)
- User experience: Shows loading, then fresh news

### Cache Size

**Maximum Items**: 200 articles
- Newest items kept (oldest removed)
- Prevents cache from growing too large

**Typical Size**: 20-50 articles
- Depends on how much forex news is published
- Grows over time as new articles added

---

## Summary

The live news feed system is designed to:

1. **Aggregate** news from multiple sources (RSS, Alternative, Telegram)
2. **Filter** for forex-relevant content (including gold/silver)
3. **Cache** persistently in Firebase (survives restarts)
4. **Merge** fresh and cached news intelligently
5. **Preserve** timestamps for consistent display
6. **Serve** news quickly (even stale cache for instant UI)
7. **Update** automatically every 5 minutes or on manual refresh

The system has been optimized for:
- **Speed**: Instant UI loading with stale cache
- **Reliability**: Same logic for auto and manual refresh
- **Accuracy**: Proper deduplication and timestamp preservation
- **Completeness**: Checks more feed entries, includes gold/silver

All components work together to provide a seamless, efficient news feed experience.

