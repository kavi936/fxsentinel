# Alert System Testing Guide

## Overview

This guide provides comprehensive testing instructions for the alert system fixes. Test both unit tests and integration tests to verify all fixes are working correctly.

## Prerequisites

1. **Firebase Configuration**: Ensure Firebase Realtime Database is configured
   - Set `FIREBASE_PROJECT_ID` environment variable
   - Set `FIREBASE_REALTIME_URL` environment variable (or it will use default)

2. **Flask App Running** (for integration tests):
   ```bash
   cd backend
   python3 app.py
   ```

3. **Python Dependencies**:
   ```bash
   pip install requests
   ```

## Test Files

### 1. Unit Tests (`tests/test_alert_system_fixes.py`)

Tests individual components:
- Persistent deduplication
- Filtering logic
- Async handling
- Worker consistency

**Run Unit Tests**:
```bash
cd tests
python3 test_alert_system_fixes.py
```

### 2. Integration Tests (`tests/test_alert_integration.py`)

Tests the full alert flow:
- Alert trigger endpoint
- Duplicate prevention
- Health checks

**Run Integration Tests**:
```bash
cd tests
python3 test_alert_integration.py [base_url]
# Default: http://localhost:5001
# Example: python3 test_alert_integration.py http://your-app.railway.app
```

## Manual Testing Steps

### Test 1: Verify Deduplication Works

1. **Send a test alert**:
   ```bash
   curl -X POST http://localhost:5001/api/alerts/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "type": "news",
       "data": {
         "id": "test_123",
         "title": "Test Alert",
         "summary": "Testing deduplication",
         "source": "Test",
         "impact": "high"
       }
     }'
   ```

2. **Check response** - should show alerts sent

3. **Send same alert again** (same ID):
   ```bash
   curl -X POST http://localhost:5001/api/alerts/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "type": "news",
       "data": {
         "id": "test_123",
         "title": "Test Alert",
         "summary": "Testing deduplication",
         "source": "Test",
         "impact": "high"
       }
     }'
   ```

4. **Expected**: `alerts_sent: 0` (duplicate prevented)

### Test 2: Verify Filtering Catches More Alerts

1. **Send medium-impact forex news**:
   ```bash
   curl -X POST http://localhost:5001/api/alerts/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "type": "news",
       "data": {
         "id": "test_medium_1",
         "title": "ECB Discusses Monetary Policy",
         "summary": "European Central Bank considers policy changes",
         "source": "Bloomberg",
         "impact": "medium"
       }
     }'
   ```

2. **Expected**: Alert should be sent (even though impact is "medium", it's forex-relevant)

### Test 3: Verify Persistence After Restart

1. **Send an alert** (note the ID)

2. **Restart Flask app**:
   ```bash
   # Stop Flask app (Ctrl+C)
   # Start Flask app again
   python3 app.py
   ```

3. **Send same alert again** (same ID)

4. **Expected**: Duplicate should still be prevented (persisted in Firebase)

### Test 4: Check Firebase Deduplication Records

1. **Go to Firebase Console**
2. **Navigate to**: `alert_deduplication/alerts`
3. **Verify**: You should see records of sent alerts
4. **Check**: Each record should have:
   - `alert_type`
   - `user_id`
   - `sent_at`
   - `expires_at`

## Testing in Production (Railway)

### Step 1: Deploy Changes

```bash
# Commit changes
git add .
git commit -m "Fix alert system: persistent deduplication and improved filtering"
git push origin main

# Main app auto-deploys via GitHub
# Worker deploys via Railway CLI
cd backend
railway push
```

### Step 2: Monitor Logs

**Main App Logs**:
```bash
railway logs --service cheerful-vitality
```

**Worker Logs**:
```bash
railway logs --service fxsentinel-background-worker
```

**Look for**:
- ✅ "Persistent Alert Deduplication Service initialized"
- ✅ "Found X high-impact forex news items"
- ✅ "Duplicate alert prevented for user..."
- ❌ Any errors related to Firebase or async handling

### Step 3: Test Production Endpoint

```bash
# Get your Railway URL
railway domain

# Test alert trigger
curl -X POST https://your-app.railway.app/api/alerts/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "type": "news",
    "data": {
      "id": "prod_test_1",
      "title": "Production Test Alert",
      "summary": "Testing in production",
      "source": "Test",
      "impact": "high"
    }
  }'
```

### Step 4: Verify Deduplication Stats

Check deduplication statistics:
```bash
# Add this endpoint to your app if needed
# GET /api/alerts/deduplication/stats
```

Or check Firebase directly:
- Go to Firebase Console
- Navigate to `alert_deduplication/alerts`
- Count records (should increase as alerts are sent)

## Expected Results

### Before Fixes
- ❌ Many alerts missed (only `impact == 'high'` caught)
- ❌ Duplicates sent after restarts
- ❌ Inconsistent filtering between worker and main app
- ❌ Async errors causing silent failures

### After Fixes
- ✅ More alerts caught (sophisticated filtering)
- ✅ No duplicates (persistent deduplication)
- ✅ Consistent filtering everywhere
- ✅ Reliable async handling

## Troubleshooting

### Issue: Tests fail with Firebase connection error

**Solution**: 
- Check `FIREBASE_REALTIME_URL` environment variable
- Verify Firebase project ID is correct
- Check Firebase database rules allow read/write

### Issue: Duplicates still being sent

**Solution**:
- Check Firebase connection is working
- Verify `persistent_alert_deduplication.py` is being imported
- Check logs for deduplication errors

### Issue: No alerts being sent

**Solution**:
- Check worker is running: `railway logs --service fxsentinel-background-worker`
- Verify news items have proper structure
- Check filtering logic is catching news (check logs)

### Issue: Async errors in logs

**Solution**:
- Verify Flask app is using updated `app.py` with fixed async handling
- Check for "RuntimeError: asyncio.run()" errors
- If errors persist, check event loop handling code

## Success Criteria

✅ All unit tests pass
✅ All integration tests pass
✅ No duplicates sent (even after restart)
✅ More alerts being sent (better filtering)
✅ No async errors in logs
✅ Firebase deduplication records visible

## Next Steps After Testing

1. **Monitor for 24 hours** - Check alert volume and duplicate rate
2. **Review logs** - Look for any errors or warnings
3. **Check Firebase** - Verify deduplication records are being created
4. **User feedback** - Ask users if they're receiving alerts correctly

## Reporting Issues

If tests fail or issues are found:

1. **Collect logs**:
   ```bash
   railway logs --service cheerful-vitality > main_app.log
   railway logs --service fxsentinel-background-worker > worker.log
   ```

2. **Check Firebase**:
   - Screenshot of `alert_deduplication/alerts` in Firebase
   - Count of records

3. **Test results**:
   - Output from unit tests
   - Output from integration tests

4. **Environment**:
   - Railway service URLs
   - Firebase project ID
   - Any error messages

