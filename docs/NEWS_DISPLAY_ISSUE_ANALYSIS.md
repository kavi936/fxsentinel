# News Display Issue Analysis

## Diagnostic Results

### Issues Found

1. **Cache Save Failed (Local)**
   - Firebase 401 errors (expected - credentials only in production)
   - In production, cache should save successfully

2. **Telegram News Not Available (Local)**
   - Requires interactive authentication
   - In production, Telegram should work

3. **Frontend Filtering**
   - `isForexRelevant()` function may be filtering out news
   - Need to check if news items pass this filter

4. **API Would Return 16 Items**
   - After deduplication: 16 items
   - All items have required fields
   - Impact distribution: 1 high, 4 medium, 11 low

## Potential Causes

### 1. Frontend Filtering Too Strict

The `isForexRelevant()` function checks for forex keywords. If news items don't contain these keywords, they won't be displayed.

**Check**: Does the WatcherGuru news about Trump/Fed contain forex keywords?

### 2. Cache Not Saving in Production

If Firebase connection fails in production, cache won't save and news won't persist.

**Check**: Verify Firebase credentials in Railway

### 3. API Not Being Called with Force Refresh

If frontend calls API without `force_refresh=true`, it might return cached (empty) data.

**Check**: Verify refresh buttons are working

### 4. News Items Missing Required Fields

If news items are missing `id`, `title`, `source`, etc., they might not display.

**Check**: Verify all news items have required fields

## Next Steps

1. **Check Production Logs**: See if cache is saving successfully
2. **Check Frontend Console**: See if news is being filtered out
3. **Test API Directly**: Call `/api/news?force_refresh=true` and see response
4. **Check Filtering Logic**: Verify `isForexRelevant()` isn't too strict

