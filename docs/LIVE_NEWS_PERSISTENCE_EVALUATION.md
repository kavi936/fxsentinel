# Live News Persistence Evaluation

## Problem Summary

Live news events disappear when a new app instance is created (git push, Railway restart, deployment). This is the same type of issue we fixed with alert deduplication - data stored in ephemeral storage that doesn't survive restarts.

## Root Cause Analysis

### 1. 🔴 News Cache Uses Local JSON Files (CRITICAL)

**Location**: `backend/services/news_cache.py`

**Problem**: News cache stores data in local JSON files:
- `news_cache.json` - Current news cache (15 minute TTL)
- `news_history.json` - News history (last 100 items)

**Code**:
```python
def save_news(self, news_items: List[Dict[str, Any]]) -> bool:
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'news_count': len(news_items),
        'news': news_items
    }
    
    with open(self.cache_file, 'w', encoding='utf-8') as f:  # ❌ Local file
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
```

**Impact**: 
- On Railway restart/deployment, filesystem is reset
- All cached news is lost
- News history is lost
- Users see empty feed until new news is fetched

---

### 2. ⚠️ Frontend State is In-Memory

**Location**: `src/components/LiveNewsFeed.jsx:8`

**Problem**: Frontend uses React `useState` which is lost on page refresh:
```javascript
const [news, setNews] = useState([]);  // ❌ Lost on page refresh
```

**Impact**:
- Page refresh clears news display
- User has to wait for API call to repopulate
- No offline/persistent state

**Note**: This is less critical since frontend can refetch, but the backend cache loss is the main issue.

---

### 3. ⚠️ Cache TTL is Very Short

**Location**: `backend/services/news_cache.py:15`

**Problem**: Cache expires after 15 minutes (`max_age_hours: int = 0.25`)

**Impact**:
- Even if cache survives restart, it expires quickly
- Forces frequent refetching
- Not ideal for persistence

---

## Current Flow

### Before Restart
```
1. News fetched from RSS feeds
2. Saved to news_cache.json (local file)
3. Added to news_history.json (local file)
4. Served to frontend via /api/news
5. Frontend displays news
```

### After Restart
```
1. Railway restarts app
2. Filesystem reset → news_cache.json deleted ❌
3. Filesystem reset → news_history.json deleted ❌
4. /api/news called → no cache found
5. Must fetch fresh news (slow, API rate limits)
6. Frontend shows empty/loading state
```

---

## Comparison: Deduplication vs News Cache

| Feature | Alert Deduplication (Fixed) | News Cache (Current) |
|---------|------------------------------|----------------------|
| Storage | Firebase Realtime Database ✅ | Local JSON files ❌ |
| Persists on restart | Yes ✅ | No ❌ |
| Survives deployment | Yes ✅ | No ❌ |
| Cross-instance | Yes ✅ | No ❌ |
| TTL | 24 hours ✅ | 15 minutes ⚠️ |

---

## Solution Approach (Similar to Deduplication Fix)

### Option 1: Firebase Realtime Database (Recommended)

**Similar to**: `persistent_alert_deduplication.py`

**Benefits**:
- ✅ Persists across restarts
- ✅ Survives deployments
- ✅ Works across multiple instances
- ✅ Already using Firebase for alerts
- ✅ Consistent with existing architecture

**Implementation**:
- Create `persistent_news_cache.py` using Firebase Realtime Database
- Store news cache and history in Firebase
- Replace `news_cache.py` usage with persistent version
- Keep same API interface for backward compatibility

**Firebase Structure**:
```
news_cache/
  current/
    timestamp: "2024-12-23T..."
    news: [...]
  history/
    {news_id}/
      title: "..."
      source: "..."
      cached_at: "..."
      ...
```

---

### Option 2: Extend Cache TTL + Better Error Handling

**Benefits**:
- ✅ Simpler implementation
- ✅ No new dependencies

**Drawbacks**:
- ❌ Still loses data on restart
- ❌ Doesn't solve root problem
- ❌ Temporary fix only

---

## Recommended Solution

### Create Persistent News Cache Service

**File**: `backend/services/persistent_news_cache.py`

**Features**:
1. **Firebase-backed storage** - Same pattern as `persistent_alert_deduplication.py`
2. **Backward compatible API** - Same methods as `NewsCache` class
3. **Extended TTL** - 24 hours instead of 15 minutes
4. **History persistence** - Store last 500 items (instead of 100)
5. **Automatic cleanup** - Remove expired items

**Key Methods**:
- `save_news(news_items)` - Save to Firebase
- `load_news()` - Load from Firebase (with TTL check)
- `get_recent_history(hours)` - Get history from Firebase
- `clear_cache()` - Clear Firebase cache

---

## Impact Assessment

### Before Fix
- ❌ News disappears on every restart
- ❌ Users see empty feed after deployment
- ❌ Must wait for fresh fetch (slow)
- ❌ History lost on restart

### After Fix
- ✅ News persists across restarts
- ✅ Users see cached news immediately
- ✅ History preserved
- ✅ Consistent with alert deduplication pattern

---

## Implementation Considerations

### 1. Backward Compatibility
- Keep same API interface as `NewsCache`
- Can replace `news_cache` import with `persistent_news_cache`
- No changes needed in `app.py` (just import change)

### 2. Migration Path
- Old cache files will be ignored
- New system starts fresh (no migration needed)
- Firebase will build cache over time

### 3. Performance
- Firebase reads are fast (cached)
- Writes are async (non-blocking)
- Better than file I/O in some cases

### 4. Cost
- Firebase Realtime Database has free tier
- News cache is small data (few KB per item)
- Should be well within limits

---

## Files That Need Changes

### New Files
- `backend/services/persistent_news_cache.py` - New persistent cache service

### Modified Files
- `backend/app.py` - Change import from `news_cache` to `persistent_news_cache`
- Potentially: `backend/services/news_aggregator.py` - If it uses cache directly

### No Changes Needed
- `src/components/LiveNewsFeed.jsx` - Frontend doesn't need changes (uses API)
- Other components using `/api/news` endpoint

---

## Testing Plan

1. **Test Cache Persistence**:
   - Save news to cache
   - Restart app (simulate)
   - Verify cache still exists
   - Verify news loads from cache

2. **Test History Persistence**:
   - Add news to history
   - Restart app
   - Verify history still exists
   - Verify `/api/news-history` works

3. **Test TTL**:
   - Save news with old timestamp
   - Verify cache expires correctly
   - Verify fresh fetch happens

4. **Test Performance**:
   - Compare Firebase vs file I/O speed
   - Verify no degradation

---

## Next Steps

1. **Review this evaluation** - Confirm approach
2. **Create persistent_news_cache.py** - Similar to persistent_alert_deduplication.py
3. **Update app.py** - Replace news_cache import
4. **Test locally** - Verify functionality
5. **Deploy** - Test in production

---

## Questions to Consider

1. **Cache Size**: How many news items to keep? (Currently 100, suggest 500)
2. **TTL**: How long should cache be valid? (Currently 15 min, suggest 24 hours)
3. **History Size**: How many historical items? (Currently 100, suggest 500)
4. **Cleanup**: When to remove old items? (Automatically on save)

---

## Conclusion

The issue is identical to the deduplication problem we just fixed:
- **Root cause**: Ephemeral storage (local files) that doesn't survive restarts
- **Solution**: Use Firebase Realtime Database for persistence
- **Pattern**: Same approach as `persistent_alert_deduplication.py`

This is a straightforward fix that will significantly improve user experience by ensuring news persists across deployments and restarts.

