# Live News System - Complete Explanation

## Overview

The live news system fetches news from multiple sources (RSS feeds, alternative sources, Telegram), caches it persistently in Firebase, and displays it in the frontend with filtering and deduplication.

---

## System Architecture

```
┌─────────────────┐
│   Frontend      │
│ LiveNewsFeed.jsx│
└────────┬────────┘
         │ HTTP GET /api/news
         ▼
┌─────────────────┐
│   Backend API   │
│   /api/news     │
└────────┬────────┘
         │
         ├─► Check Cache (Firebase)
         ├─► Check if should fetch new (5 min interval)
         ├─► Fetch RSS News
         ├─► Fetch Alternative News
         ├─► Fetch Telegram News
         ├─► Merge & Deduplicate
         ├─► Save to Cache (Firebase)
         └─► Return to Frontend
```

---

## 1. Frontend Component (LiveNewsFeed.jsx)

### Initialization
- **Location**: `src/components/LiveNewsFeed.jsx`
- **State Variables**:
  - `news`: Array of news items to display
  - `loading`: Loading state
  - `filter`: Filter type ('all', 'high', 'medium', 'low')
  - `activeTab`: 'live' or 'history'

### Auto-Refresh
```javascript
useEffect(() => {
  fetchNews();
  // Auto-refresh every 5 minutes
  const interval = setInterval(fetchNews, 5 * 60 * 1000);
  return () => clearInterval(interval);
}, []);
```

**Behavior**: Fetches news on mount, then every 5 minutes automatically.

### Fetching News
```javascript
const fetchNews = async (forceRefresh = false) => {
  if (forceRefresh) {
    response = await fetch(`${config.API_BASE_URL}/api/news?force_refresh=true`);
  } else {
    response = await fetch(config.endpoints.news);
  }
  
  const data = await response.json();
  setNews(data.news || []);
}
```

**Parameters**:
- `forceRefresh=false`: If true, bypasses cache and fetches fresh news
- Regular calls: Uses cached news if available

### Filtering Logic

**Filter Types**:
1. **'all'**: Shows all forex-relevant news (passes `isForexRelevant()`)
2. **'high'**: Shows only high-impact forex news (passes `isHighImpactForex()`)
3. **'medium'**: Shows medium-impact forex news
4. **'low'**: Shows low-impact forex news

**Forex Relevance Check** (`isForexRelevant`):
```javascript
const isForexRelevant = (item) => {
  const text = `${title} ${summary}`.toLowerCase();
  
  // Core keywords: 'fed', 'ecb', 'forex', 'currency', etc.
  const coreForexKeywords = ['fed', 'ecb', 'boj', 'forex', 'currency', ...];
  
  // Economic terms: 'inflation', 'cpi', 'interest rate', etc.
  const forexRelevantTerms = ['inflation', 'cpi', 'economic', ...];
  
  return hasCoreForex || hasForexRelevant;
}
```

**High Impact Check** (`isHighImpactForex`):
- Requires multiple high-impact keywords
- More strict for non-credible sources
- Keywords: 'fed', 'ecb', 'interest rate', 'cpi', 'nfp', etc.

### Display Logic

1. **Remove Duplicates**: Based on title similarity
2. **Apply Filter**: Based on filter type and forex relevance
3. **Sort**: By `added_to_feed_at` (newest first)
4. **Render**: News items with source, time, impact badge, summary

---

## 2. Backend API Endpoint (`/api/news`)

### Location
`backend/app.py` - `@app.route('/api/news')`

### Request Flow

#### Step 1: Check Parameters
```python
force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
```

#### Step 2: Load Cache
```python
if not force_refresh:
    cached_news = news_cache.load_news()  # From Firebase
```

#### Step 3: Check if Should Fetch New
```python
if cached_news:
    should_fetch_new = news_cache.should_fetch_new_news(fetch_interval_minutes=5)
```

**Logic**:
- Checks `last_fetch` timestamp in cache
- If > 5 minutes ago → `should_fetch_new = True`
- If < 5 minutes ago → `should_fetch_new = False`

#### Step 4: Serve Cached News (If Available and Fresh)
```python
if cached_news and not should_fetch_new:
    # Return cached news immediately (fast response)
    return jsonify({
        "news": cached_news,
        "cache_status": "cached"
    })
```

**When This Happens**:
- Cache exists AND
- Last fetch was < 5 minutes ago
- No force refresh requested

#### Step 5: Fetch Fresh News (If Needed)
```python
if should_fetch_new or force_refresh:
    # Fetch from multiple sources in parallel
    rss_news = news_aggregator.get_recent_news(hours=24)
    alt_news = alternative_news_sources.get_alternative_news(hours=24)
    telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
    
    fresh_news = rss_news + alt_news + telegram_news
```

**Sources**:
1. **RSS Feeds**: Bloomberg, CNBC, FXStreet, ForexLive, MarketWatch, Reuters
2. **Alternative Sources**: Additional RSS feeds and web scraping
3. **Telegram**: WatcherGuru channel via Telethon

#### Step 6: Merge with Cache
```python
if cached_news and should_fetch_new:
    # Combine: fresh news first, then cached news
    all_news = fresh_news + cached_news
else:
    all_news = fresh_news
```

**Why Merge?**
- Preserves old news while adding new news
- Ensures continuity (news doesn't disappear)

#### Step 7: Set Timestamps
```python
# Preserve original added_to_feed_at from cached items
# Set current time for new items
for item in all_news:
    if item in cached_items_map:
        item['added_to_feed_at'] = cached_item['added_to_feed_at']  # Preserve
    else:
        item['added_to_feed_at'] = current_time  # New item
```

**Purpose**: 
- `added_to_feed_at`: When news was first added to our system
- `published_at`: Original publication date
- Display uses `added_to_feed_at` (when we first saw it)

#### Step 8: Sort
```python
# Sort by added_to_feed_at (newest first)
all_news.sort(key=lambda x: x.get('added_to_feed_at') or x.get('published_at'), reverse=True)
```

**Why**: Newly fetched news should appear on top, not sorted by original publication date.

#### Step 9: Deduplicate
```python
def remove_duplicate_news_simple(news_list):
    seen = {}
    for item in news_list:
        key = f"{item.get('title')}_{item.get('source')}"
        if key not in seen:
            seen[key] = item
            unique_news.append(item)
    return unique_news
```

**Deduplication Key**: `title + source`
- Same title from same source = duplicate
- Prefers items with `added_to_feed_at` (from cache)

#### Step 10: Save to Cache
```python
if cached_news and should_fetch_new:
    news_cache.save_news(all_news, append=True)  # Merge mode
else:
    news_cache.save_news(all_news, append=False)  # Replace mode
```

**Append Mode** (`append=True`):
- Loads existing cache
- Adds only truly new items (not in cache)
- Combines: `new_items + existing_items`
- Limits to 200 items total

**Replace Mode** (`append=False`):
- Replaces entire cache
- Used for force refresh or first-time fetch

#### Step 11: Return Response
```python
return jsonify({
    "news": all_news,
    "last_updated": datetime.now().isoformat(),
    "sources": sources_used,
    "total_articles": len(all_news),
    "cache_status": "fresh"
})
```

---

## 3. Persistent News Cache (Firebase)

### Location
`backend/services/persistent_news_cache.py`

### Storage Structure
```
Firebase Realtime Database:
  news_cache/
    current/
      timestamp: "2025-12-26T18:00:00"
      news_count: 20
      news: [...]
      max_age_hours: 0.25
      last_fetch: "2025-12-26T18:00:00"
    history/
      {news_id_1}/
        id: "..."
        title: "..."
        cached_at: "..."
      ...
```

### Key Methods

#### `load_news()`
- Loads from Firebase `news_cache/current`
- Checks TTL (15 minutes = 0.25 hours)
- Returns `None` if cache is too old or missing

#### `save_news(news_items, append=False)`
- **Append Mode** (`append=True`):
  - Loads existing cache
  - Adds only new items (not duplicates)
  - Combines: `new_items + existing_items`
  - Saves merged list
- **Replace Mode** (`append=False`):
  - Replaces entire cache
  - Saves new list directly

#### `should_fetch_new_news(fetch_interval_minutes=5)`
- Checks `last_fetch` timestamp
- Returns `True` if > 5 minutes ago
- Returns `False` if < 5 minutes ago

### Cache TTL
- **Max Age**: 15 minutes (0.25 hours)
- **Purpose**: Ensures cache doesn't get too stale
- **Behavior**: If cache is > 15 minutes old, it's ignored and fresh news is fetched

---

## 4. News Sources

### RSS Feeds
- **Service**: `backend/services/news_aggregator.py`
- **Sources**: Bloomberg, CNBC, FXStreet, ForexLive, MarketWatch, Reuters
- **Method**: RSS feed parsing
- **Filtering**: Only forex-related articles

### Alternative Sources
- **Service**: `backend/services/alternative_news_sources.py`
- **Sources**: Additional RSS feeds and web scraping
- **Method**: Similar to RSS feeds

### Telegram
- **Service**: `backend/services/telegram_sync_wrapper.py`
- **Source**: WatcherGuru Telegram channel
- **Method**: Telethon library (async Telegram client)
- **Authentication**: Uses session files
- **Filtering**: High-impact forex news only

---

## 5. Data Flow Example

### Scenario: User Opens Page

1. **Frontend**: `fetchNews()` called on mount
2. **Backend**: `/api/news` receives request
3. **Backend**: Checks cache → Found, last fetch 2 minutes ago
4. **Backend**: `should_fetch_new = False` (less than 5 minutes)
5. **Backend**: Returns cached news immediately
6. **Frontend**: Receives 20 cached items
7. **Frontend**: Filters by `isForexRelevant()` → 10 items pass
8. **Frontend**: Displays 10 items sorted by `added_to_feed_at`

### Scenario: 5 Minutes Pass

1. **Frontend**: Auto-refresh triggers (5-minute interval)
2. **Backend**: `/api/news` receives request
3. **Backend**: Checks cache → Found, last fetch 6 minutes ago
4. **Backend**: `should_fetch_new = True` (> 5 minutes)
5. **Backend**: Fetches fresh news from all sources
6. **Backend**: Merges: `fresh_news + cached_news`
7. **Backend**: Deduplicates (removes duplicates)
8. **Backend**: Sorts by `added_to_feed_at` (newest first)
9. **Backend**: Saves to cache with `append=True`
10. **Backend**: Returns merged news
11. **Frontend**: Displays new news on top

### Scenario: User Clicks Refresh

1. **Frontend**: `fetchNews(true)` called (force refresh)
2. **Backend**: `/api/news?force_refresh=true` receives request
3. **Backend**: Skips cache check
4. **Backend**: Fetches fresh news immediately
5. **Backend**: Replaces cache (not append)
6. **Backend**: Returns fresh news
7. **Frontend**: Displays fresh news

---

## 6. Common Issues and Solutions

### Issue: Old News Appearing on Top
**Cause**: Sorting by `published_at` instead of `added_to_feed_at`
**Solution**: Sort by `added_to_feed_at` (when first added to system)

### Issue: New News Not Appearing
**Causes**:
1. Cache served before 5 minutes pass
2. New news deduplicated out (same title/source)
3. New news filtered out by `isForexRelevant()`
**Solutions**:
- Use force refresh to bypass cache
- Check deduplication logic
- Check frontend filter

### Issue: Same News Repeated
**Cause**: Deduplication not working (same title from different sources)
**Solution**: Deduplication key is `title + source`, so same title from different sources = different items

### Issue: News Disappears After Refresh
**Cause**: Cache not persisting (Firebase 401 errors)
**Solution**: Fix Firebase rules to allow read/write

---

## 7. Key Timestamps

- **`published_at`**: Original publication date from source
- **`added_to_feed_at`**: When news was first added to our system
- **`last_fetch`**: When cache was last updated
- **`cached_at`**: When item was added to history

**Display Priority**: `added_to_feed_at` > `published_at`

---

## 8. Summary

**Fetching**: Every 5 minutes automatically, or on-demand with force refresh
**Caching**: Firebase Realtime Database (persists across restarts)
**Deduplication**: By title + source
**Filtering**: Frontend filters by forex relevance and impact level
**Sorting**: By `added_to_feed_at` (newest first)
**Display**: Shows filtered, deduplicated, sorted news items

The system is designed to:
- ✅ Show fresh news regularly (every 5 minutes)
- ✅ Persist news across restarts (Firebase)
- ✅ Avoid duplicates (deduplication)
- ✅ Show only relevant news (filtering)
- ✅ Display newest news first (sorting)

