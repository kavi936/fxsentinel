# Local Testing Guide - Unified Alert System
**Date**: January 2, 2026  
**Purpose**: Guide for testing the improved alert system locally

---

## Quick Start

### 1. Run Unit Tests

```bash
python3 scripts/test_unified_alert_system.py
```

This tests:
- ✅ Unified processor import and initialization
- ✅ Processor startup and shutdown
- ✅ Global deduplication
- ✅ User settings caching
- ✅ News alert triggering
- ✅ Deduplication integration
- ✅ Parallel processing
- ✅ Firebase integration

**Expected Result**: All 8 tests should pass ✅

---

## End-to-End Testing

### Step 1: Start Flask App

**Option A: Using the script**
```bash
./scripts/start_app_for_testing.sh
```

**Option B: Manual start**
```bash
cd backend
python3 app.py
```

**Expected Output**:
```
✅ Unified alert processor started in background
✅ Robust alert service started in background
✅ Cost-optimized monitor started
🚀 Starting Flask server on port 5001
```

---

### Step 2: Verify Processor Started

In another terminal, check the health endpoint:

```bash
curl http://localhost:5001/api/health/unified-alert-processor
```

**Expected Response**:
```json
{
  "status": "healthy",
  "processor": {
    "running": true,
    "thread_alive": true,
    ...
  }
}
```

---

### Step 3: Test News Fetch with Alert Triggering

**Option A: Using the test script**
```bash
python3 scripts/test_alert_system_end_to_end.py
```

**Option B: Manual test**
```bash
# Fetch news (should trigger alerts)
curl "http://localhost:5001/api/news?force_refresh=true"
```

**Check Flask app logs for**:
```
✅ Triggered alert check for X fresh news items
Checking X news items for alerts...
Found X high-impact forex news items
Processing X new news items (after global deduplication)
Processing alerts for X users
Alert processing completed: X alerts sent
```

---

### Step 4: Verify Alerts Sent

1. **Check Telegram** - You should receive alerts if:
   - You have Telegram connected
   - You have alerts enabled
   - News items are high-impact forex news

2. **Check Logs** - Look for:
   ```
   Alert sent successfully to user {user_id}
   Alert processing completed: X alerts sent
   ```

3. **Check Deduplication** - Try fetching news again:
   ```bash
   curl "http://localhost:5001/api/news?force_refresh=true"
   ```
   
   **Expected**: No duplicate alerts (check logs for "Duplicate alert prevented")

---

## Testing Checklist

### Basic Functionality
- [ ] Unified processor starts on app startup
- [ ] Health endpoint returns correct status
- [ ] News fetch triggers alert check
- [ ] Alerts are sent to users
- [ ] No duplicate alerts

### Performance
- [ ] Alert latency < 5 seconds
- [ ] User processing < 1 second (7 users)
- [ ] Cache hit rate > 80% (after warmup)
- [ ] Parallel processing works (check logs)

### Deduplication
- [ ] Global content hash prevents duplicates
- [ ] Per-user deduplication works
- [ ] Cache reduces Firebase reads
- [ ] No duplicate alerts sent

### Error Handling
- [ ] Processor handles errors gracefully
- [ ] Thread survives errors
- [ ] Firebase connection failures handled
- [ ] Missing user settings handled

---

## Common Issues

### Issue 1: "Cannot connect to localhost:5001"

**Solution**: Make sure Flask app is running
```bash
python3 backend/app.py
```

---

### Issue 2: "Firebase connection failed"

**Solution**: 
- Check Firebase credentials are configured
- For local testing, this is okay (will work in production)
- Tests will still pass (fail-open mode)

---

### Issue 3: "No users with alerts enabled"

**Solution**:
- Check Firebase: `alerts/users/` path
- Verify users have `settings.preferences.alertTypes.liveNews: true`
- Verify users have Telegram chat IDs

---

### Issue 4: "Processor not running"

**Solution**:
- Check logs for errors
- Verify imports work: `python3 -c "from services.unified_alert_processor import get_unified_processor"`
- Check if thread started: Look for "UnifiedAlertProcessor background thread started"

---

## Performance Testing

### Test Alert Latency

1. Fetch news and measure time to alert:
```bash
time curl "http://localhost:5001/api/news?force_refresh=true"
```

2. Check logs for alert processing time:
```
Alert processing completed: X alerts sent
```

**Expected**: < 5 seconds from news fetch to alert delivery

---

### Test Parallel Processing

1. Add more test users (or simulate)
2. Fetch news
3. Check logs for processing time

**Expected**: Processing time should be ~200ms for 7 users (not 1.4s)

---

### Test Cache Performance

1. Fetch news twice (within 5 minutes)
2. Check logs for cache hits:
```
Using cached settings for user {user_id}
```

**Expected**: Second fetch should use cache (faster)

---

## Debugging

### Enable Debug Logging

Add to `backend/app.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Processor Status

```bash
curl http://localhost:5001/api/health/unified-alert-processor
```

### Check Deduplication Stats

```python
from services.persistent_alert_deduplication import get_deduplication_stats
stats = get_deduplication_stats()
print(stats)
```

---

## Next Steps After Testing

1. **If all tests pass**: Deploy to staging
2. **If issues found**: Fix and re-test
3. **Monitor in production**: Check logs and metrics

---

## Summary

✅ **Unit tests**: `python3 scripts/test_unified_alert_system.py`  
✅ **End-to-end**: Start app + run `scripts/test_alert_system_end_to_end.py`  
✅ **Manual testing**: Use curl commands above

All tests should pass before deploying to production.

