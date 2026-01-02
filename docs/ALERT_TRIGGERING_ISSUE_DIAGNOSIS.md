# Alert Triggering Issue Diagnosis
**Date**: January 2, 2026  
**Issue**: Alerts not being sent despite news being available

## Root Causes Identified

### 1. Alerts Only Triggered for Fresh News
**Problem**: The `/api/news` endpoint only triggers alerts when `fresh_news` is saved to cache. If the system serves cached news only (no fresh fetch), no alerts are triggered.

**Current Behavior**:
- When `should_fetch_new_news()` returns `False` (cache is fresh), the system serves cached news
- Alerts are only triggered in the `if save_success:` block (line 1177-1186)
- If no fresh news is fetched, this block never executes

**Fix Applied**: Added code to also trigger alerts for recent cached news (top 10 items) when serving cached news only. This ensures alerts are checked even when no fresh fetch occurs.

### 2. Unified Alert Processor Status
**Problem**: The diagnostic script showed `Running: False`, but production logs show it's starting. This suggests:
- The processor might not be running in all contexts
- Or the diagnostic script is checking a different instance

**Status**: The processor is being initialized in `app.py` at module import time (line 120) and in the `if __name__ == '__main__'` block (line 6430). Production logs confirm it's starting.

### 3. Firebase 401 Errors
**Problem**: Firebase Realtime Database requests are returning `401 Unauthorized` errors for:
- `telegram_mappings/{chat_id}`
- `alert_deduplication/content_hashes/{hash}`
- `alert_deduplication/alerts/{alert_key}`

**Impact**: These errors prevent:
- User lookup by chat_id
- Global content hash deduplication
- Per-user alert deduplication

**Root Cause**: Firebase Realtime Database requires proper authentication. The current implementation might be missing authentication tokens or the database rules might be too restrictive.

**Note**: This is a separate issue that needs to be addressed by:
1. Checking Firebase Realtime Database rules
2. Ensuring proper authentication is configured
3. Verifying environment variables are set correctly

## Fixes Applied

### Fix 1: Trigger Alerts for Cached News
**File**: `backend/app.py` (lines 1213-1226)

Added code to trigger alerts for recent cached news when serving cached news only:

```python
# IMPORTANT: Also trigger alerts for cached news that might not have been sent yet
# This ensures alerts are sent even when serving cached news only
# Only do this if we didn't already trigger alerts for fresh news
if not (save_success and (should_fetch_new or force_refresh)):
    # We're serving cached news only - check if any high-impact items need alerts
    try:
        from services.unified_alert_processor import get_unified_processor
        unified_processor = get_unified_processor()
        # Check only the most recent cached news (top 10) for alerts
        # This prevents checking all 156 items every time
        recent_cached = all_news[:10] if len(all_news) > 10 else all_news
        unified_processor.check_news_alerts_async(recent_cached)
        print(f"✅ Triggered alert check for {len(recent_cached)} recent cached news items (in case alerts were missed)")
    except Exception as e:
        print(f"⚠️  Error triggering alerts for cached news: {e}")
        import traceback
        traceback.print_exc()
```

**Why This Works**:
- When serving cached news only, we now check the top 10 recent items for alerts
- This ensures alerts are sent even if fresh news wasn't fetched
- Deduplication will prevent sending duplicate alerts
- Only checks top 10 to avoid performance issues

## Remaining Issues

### Firebase 401 Errors
**Status**: Needs investigation

**Action Required**:
1. Check Firebase Realtime Database rules in Firebase Console
2. Verify `FIREBASE_REALTIME_URL` environment variable is set correctly
3. Check if authentication tokens are needed for Realtime Database access
4. Review Firebase project settings and permissions

**Impact**: If Firebase 401 errors persist, deduplication won't work, which could lead to:
- Duplicate alerts being sent
- Inability to check if alerts were already sent
- Performance issues from redundant processing

## Testing Recommendations

1. **Test Alert Triggering**:
   - Force a fresh news fetch (`?force_refresh=true`)
   - Verify alerts are triggered for high-impact news
   - Check logs for "Triggered alert check" messages

2. **Test Cached News Alerts**:
   - Wait for cache to be fresh (no fresh fetch)
   - Verify alerts are still triggered for recent cached news
   - Check logs for "Triggered alert check for recent cached news items"

3. **Test Deduplication**:
   - Send the same news item twice
   - Verify only one alert is sent
   - Check Firebase for deduplication records

4. **Monitor Firebase Errors**:
   - Check production logs for 401 errors
   - Verify Firebase rules allow read/write access
   - Test Firebase connection with diagnostic script

## Expected Behavior After Fix

1. **Fresh News Fetch**:
   - Fresh news is fetched and saved
   - Alerts are triggered for high-impact news
   - Deduplication prevents duplicates

2. **Cached News Only**:
   - Cached news is served
   - Top 10 recent items are checked for alerts
   - Alerts are sent if not already sent (deduplication check)

3. **Deduplication**:
   - Global content hash check prevents processing already-sent news
   - Per-user deduplication prevents sending same alert twice to same user
   - Firebase stores deduplication state persistently

## Next Steps

1. Deploy the fix to production
2. Monitor logs for alert triggering messages
3. Test with `/status` command to verify user connection
4. Check Firebase Console for 401 errors and fix authentication
5. Monitor alert delivery and verify users receive alerts

