# Alert System Diagnosis - No Alerts Since Deployment

## Issue Summary
No alerts have been received since deployment yesterday. This document identifies potential causes.

## Critical Issues Found

### 1. ⚠️ Worker Not Using Deduplication (But This Shouldn't Block Alerts)

**Location**: `backend/services/background_alert_worker.py:130-140`

**Problem**: The worker imports `should_send_news_alert` but **never actually calls it**. It just appends all filtered news items without checking deduplication.

**Code**:
```python
from services.persistent_alert_deduplication import should_send_news_alert

new_news_items = []
for news_item in high_impact:
    news_id = news_item.get('id') or news_item.get('url') or news_item.get('title')
    if news_id:
        # Check persistent deduplication (works across restarts)
        # Note: We check without user_id here since we're filtering at worker level
        # The main app will do user-specific deduplication
        # For now, we'll use a generic check - the main app handles per-user deduplication
        new_news_items.append(news_item)  # ❌ Never calls should_send_news_alert!
```

**Impact**: 
- Worker doesn't filter duplicates at worker level (but main app does per-user, so this is OK)
- **However**: If Firebase is failing and blocking everything, this could be an issue

**Status**: This is actually OK - deduplication happens at main app level per-user. But we should verify Firebase isn't blocking.

---

### 2. 🔴 Firebase Connection May Be Failing (CRITICAL)

**Location**: `backend/services/persistent_alert_deduplication.py`

**Problem**: If Firebase connection is failing (401 Unauthorized), the deduplication service might be blocking alerts.

**Current Behavior**: 
- The code has "fail-open" logic (allows alerts if Firebase fails)
- BUT: If Firebase is consistently failing, it might be causing issues

**Check Needed**:
- Verify Firebase credentials in Railway
- Check if `FIREBASE_PROJECT_ID` and `FIREBASE_REALTIME_URL` are set
- Look for 401 errors in logs

---

### 3. ⚠️ Filtering May Be Too Strict

**Location**: `backend/services/news_alert_trigger.py:93-141`

**Problem**: The `is_forex_high_impact()` function requires specific keywords. If news doesn't contain these keywords, it won't be caught.

**Required Keywords**:
- Central banks: 'fed', 'federal reserve', 'ecb', 'boe', etc.
- Economic indicators: 'nfp', 'cpi', 'inflation', 'gdp', etc.
- Market events: 'breaking', 'urgent', 'crisis', etc.
- Currency terms: 'dollar', 'euro', 'pound', 'yen', etc.

**Impact**: 
- News without these keywords won't trigger alerts
- This might be too restrictive

**Check Needed**:
- Review recent news items to see if they contain required keywords
- Check if news items have proper `title`, `content`, and `source` fields

---

### 4. 🔴 Worker May Not Be Running

**Check Needed**:
- Verify worker is running in Railway
- Check worker logs for errors
- Verify worker is checking for news every 60 seconds

**Commands**:
```bash
railway logs --service fxsentinel-background-worker
# Look for:
# - "Checking for news alerts..."
# - "Found X high-impact forex news items"
# - Any errors
```

---

### 5. ⚠️ API Connection Issue

**Location**: `backend/services/background_alert_worker.py:105`

**Problem**: Worker calls `/api/news` endpoint. If this fails, no alerts.

**Check Needed**:
- Verify `API_BASE_URL` is set correctly in Railway
- Test `/api/news` endpoint manually
- Check for connection errors in worker logs

---

### 6. 🔴 Main App Deduplication May Be Blocking Everything

**Location**: `backend/services/news_alert_trigger.py:360`

**Problem**: If Firebase is failing and deduplication is blocking, all alerts might be marked as duplicates.

**Current Logic**:
```python
if not should_send_news_alert(news_item, user_id):
    logger.debug(f"Duplicate news alert prevented...")
    return False
```

**Check Needed**:
- Verify Firebase connection is working
- Check if deduplication is incorrectly marking new alerts as duplicates
- Review logs for "Duplicate news alert prevented" messages

---

## Diagnostic Checklist

### Step 1: Check Worker Status
```bash
# Check if worker is running
railway logs --service fxsentinel-background-worker --tail 100

# Look for:
# ✅ "BackgroundAlertWorker started"
# ✅ "Checking for news alerts..."
# ✅ "Found X high-impact forex news items"
# ❌ Any errors or exceptions
```

### Step 2: Check Main App Status
```bash
# Check main app logs
railway logs --service cheerful-vitality --tail 100

# Look for:
# ✅ "/api/alerts/trigger" requests
# ✅ "Alert trigger received"
# ✅ "Successfully sent alert to user"
# ❌ Any errors
```

### Step 3: Test News Endpoint
```bash
# Get your main app URL
railway domain --service cheerful-vitality

# Test news endpoint
curl https://your-app.railway.app/api/news

# Check response:
# - Does it return news items?
# - Do news items have proper structure?
# - Do news items have required keywords?
```

### Step 4: Check Firebase Connection
```bash
# Check environment variables in Railway
railway variables --service fxsentinel-background-worker
railway variables --service cheerful-vitality

# Verify:
# - FIREBASE_PROJECT_ID is set
# - FIREBASE_REALTIME_URL is set (or uses default)
```

### Step 5: Test Alert Trigger Manually
```bash
# Test alert trigger endpoint
curl -X POST https://your-app.railway.app/api/alerts/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "type": "news",
    "data": {
      "id": "test_manual_123",
      "title": "Fed Raises Interest Rates - Test",
      "summary": "Federal Reserve announces rate changes",
      "source": "Test",
      "impact": "high"
    }
  }'

# Check response:
# - Does it return success?
# - How many alerts_sent?
# - Any errors?
```

### Step 6: Check User Settings
- Verify users have Telegram enabled
- Verify users have `liveNews` alerts enabled
- Verify users have valid chat IDs in Firebase
- Check subscription status

---

## Most Likely Causes (Priority Order)

### 1. 🔴 Firebase Connection Failing (HIGH PROBABILITY)
- If Firebase credentials are wrong or missing
- Deduplication might be blocking everything
- **Fix**: Verify Firebase credentials in Railway

### 2. 🔴 Worker Not Running or Crashing (HIGH PROBABILITY)
- Worker might have crashed on startup
- Import errors might prevent worker from starting
- **Fix**: Check worker logs for errors

### 3. ⚠️ Filtering Too Strict (MEDIUM PROBABILITY)
- News items might not contain required keywords
- Filtering logic might be too restrictive
- **Fix**: Review news items and adjust filtering if needed

### 4. ⚠️ API Connection Issue (MEDIUM PROBABILITY)
- Worker can't reach main app `/api/news` endpoint
- `API_BASE_URL` might be incorrect
- **Fix**: Verify API_BASE_URL and test endpoint

### 5. ⚠️ No High-Impact News (LOW PROBABILITY)
- Legitimately no high-impact forex news
- **Fix**: Test with manual alert trigger

---

## Immediate Actions Required

1. **Check Worker Logs** - Most important first step
   ```bash
   railway logs --service fxsentinel-background-worker --tail 200
   ```

2. **Check Main App Logs** - See if alerts are being triggered
   ```bash
   railway logs --service cheerful-vitality --tail 200 | grep -i alert
   ```

3. **Test News Endpoint** - Verify news is available
   ```bash
   curl https://your-app.railway.app/api/news | jq '.news | length'
   ```

4. **Test Manual Alert** - Bypass worker and test directly
   ```bash
   # Use the curl command from Step 5 above
   ```

5. **Check Firebase** - Verify credentials and connection
   - Go to Railway dashboard
   - Check environment variables
   - Test Firebase connection

---

## Next Steps

After running diagnostics:

1. **If worker is not running**: Fix startup errors
2. **If Firebase is failing**: Fix credentials
3. **If filtering is too strict**: Adjust filtering logic
4. **If API connection fails**: Fix API_BASE_URL
5. **If no news available**: Check news aggregator

**DO NOT make changes yet** - gather diagnostic information first, then we'll fix the root cause.

