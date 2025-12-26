# News Cache TTL Fix - Why New News Wasn't Displaying

## Problem Identified

After implementing persistent news cache, users reported that new news wasn't being displayed. Investigation revealed:

### Root Cause
- **Cache TTL was set to 24 hours** (vs 15 minutes for old file cache)
- Frontend calls `/api/news` every 2 minutes
- Backend checks cache first - if cache exists and is valid (< 24 hours old), it returns cached news
- **Fresh news is NEVER fetched until cache expires (24 hours later!)**
- Users see stale news for up to 24 hours

### Impact
- New news not displayed for up to 24 hours
- Users see outdated information
- Only manual refresh (`force_refresh=true`) fetches fresh news

---

## Solution

### Change Made
Reduced cache TTL from **24 hours to 15 minutes** (0.25 hours) to match old file cache behavior.

### Why This Works
- **Cache still persists across restarts** (main benefit of persistent cache)
- **Fresh news fetched every 15 minutes** (matches old behavior)
- **Best of both worlds**: Persistence + Fresh content

### Code Change
```python
# Before
def __init__(self, max_age_hours: float = 24.0):

# After  
def __init__(self, max_age_hours: float = 0.25):  # 15 minutes
```

---

## Behavior Comparison

### Before Fix (24-hour TTL)
1. News cached at 9:00 AM
2. Frontend calls API every 2 minutes
3. Backend returns cached news (still valid)
4. **Fresh news NOT fetched until 9:00 AM next day**
5. Users see stale news for 24 hours

### After Fix (15-minute TTL)
1. News cached at 9:00 AM
2. Frontend calls API every 2 minutes
3. Backend returns cached news (valid for 15 minutes)
4. **At 9:15 AM, cache expires**
5. **Fresh news fetched automatically**
6. Users see fresh news every 15 minutes

---

## Benefits Maintained

✅ **Cache persists across restarts** (main benefit)
✅ **Cache persists across deployments** (main benefit)
✅ **Fresh news fetched regularly** (fixed)
✅ **No breaking changes** (same API)

---

## Testing

### Verify Fix
1. **Check cache TTL**: Should be 15 minutes (0.25 hours)
2. **Cache some news**: Call `/api/news` to populate cache
3. **Wait 15 minutes**: Cache should expire
4. **Call `/api/news` again**: Should fetch fresh news
5. **Restart app**: Cache should still exist (persistence)

### Expected Behavior
- Cache expires after 15 minutes
- Fresh news fetched automatically when cache expires
- Cache persists across restarts
- Users see fresh news regularly

---

## Related Files

- `backend/services/persistent_news_cache.py` - TTL changed from 24.0 to 0.25
- `scripts/diagnose_news_cache_issue.py` - Diagnostic script created

---

## Summary

**Problem**: 24-hour cache TTL prevented fresh news from being fetched
**Solution**: Reduced TTL to 15 minutes (matches old behavior)
**Result**: Cache persists across restarts + fresh news fetched regularly

