# Background Worker Deployment Guide

## Why Update the Worker?

We've made critical fixes to the alert system that require the worker to be updated:

1. **New Persistent Deduplication Service** - Worker needs access to `persistent_alert_deduplication.py`
2. **Improved Filtering Logic** - Worker now uses sophisticated `is_forex_high_impact()` filtering
3. **Removed In-Memory Deduplication** - Worker no longer uses `processed_news_ids` set

## Files Changed in Worker

The following files are used by the worker and have been updated:

- ✅ `backend/services/background_alert_worker.py` - Updated filtering and removed in-memory dedup
- ✅ `backend/services/persistent_alert_deduplication.py` - NEW file (must be deployed)
- ✅ `backend/services/news_alert_trigger.py` - Updated (used by worker for filtering)
- ✅ `backend/worker_app.py` - Entry point (no changes, but uses updated services)

## Deployment Steps

### Option 1: Railway CLI (Recommended)

Based on your setup, the worker is deployed via Railway CLI:

```bash
# Navigate to backend directory
cd backend

# Make sure you're logged into Railway
railway login

# Link to the background worker service (if not already linked)
railway link

# Select the background worker service when prompted
# Or specify directly:
railway link --service fxsentinel-background-worker

# Deploy the worker
railway up

# Or force a fresh deployment (clears cache)
railway up --detach
```

### Option 2: Git Push (If Auto-Deploy is Enabled)

If your Railway worker service is connected to GitHub:

```bash
# Commit all changes
git add .
git commit -m "Fix alert system: persistent deduplication and improved filtering"

# Push to trigger deployment
git push origin main
```

**Note**: Make sure the worker service in Railway is configured to:
- **Root Directory**: `backend`
- **Start Command**: `python3 worker_app.py`

### Option 3: Railway Dashboard

1. Go to Railway Dashboard
2. Select your background worker service (`fxsentinel-background-worker`)
3. Go to **Settings** → **Deploy**
4. Click **Redeploy** or **Deploy Latest**

## Verify Deployment

### 1. Check Worker Logs

```bash
railway logs --service fxsentinel-background-worker
```

**Look for**:
- ✅ "Persistent Alert Deduplication Service initialized"
- ✅ "Background worker imported successfully"
- ✅ "Found X high-impact forex news items" (new filtering)
- ❌ Any import errors or Firebase connection errors

### 2. Check Worker Health

```bash
# Get worker URL
railway domain --service fxsentinel-background-worker

# Test health endpoint
curl https://your-worker-url.railway.app/api/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "background-worker",
  "worker_running": true,
  "timestamp": 1234567890
}
```

### 3. Monitor Alert Activity

Watch the logs for alert activity:

```bash
railway logs --service fxsentinel-background-worker --follow
```

**Look for**:
- ✅ "Checking for news alerts..."
- ✅ "Found X high-impact forex news items"
- ✅ "Processing X new high-impact news items"
- ✅ "News alert triggered successfully"

## Environment Variables Required

Make sure these are set in Railway for the worker service:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
API_BASE_URL=https://your-main-app.railway.app

# Firebase (for persistent deduplication)
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_REALTIME_URL=https://your-project-default-rtdb.firebaseio.com

# Optional but recommended
FLASK_ENV=production
OPENAI_API_KEY=your_openai_key  # If worker needs AI analysis
```

## What to Expect After Deployment

### Before Fixes
- ❌ Only `impact == 'high'` news caught
- ❌ Duplicates after restarts
- ❌ Inconsistent filtering

### After Fixes
- ✅ More alerts caught (sophisticated filtering)
- ✅ No duplicates (persistent deduplication)
- ✅ Consistent filtering with main app

## Troubleshooting

### Issue: Worker fails to start

**Check**:
1. All required files are in `backend/services/`
2. `persistent_alert_deduplication.py` exists
3. Environment variables are set
4. Firebase credentials are correct

**Solution**:
```bash
railway logs --service fxsentinel-background-worker
# Look for import errors or missing files
```

### Issue: Firebase connection errors

**Check**:
- `FIREBASE_PROJECT_ID` is set correctly
- `FIREBASE_REALTIME_URL` is set (or uses default)
- Firebase database rules allow read/write

**Solution**:
- Verify Firebase credentials in Railway dashboard
- Check Firebase console for database access

### Issue: Worker not catching alerts

**Check**:
- Worker is running: `railway logs --service fxsentinel-background-worker`
- Look for "Checking for news alerts..." messages
- Verify filtering is working (should see "Found X high-impact forex news items")

**Solution**:
- Check worker logs for errors
- Verify `API_BASE_URL` points to correct main app
- Test main app `/api/news` endpoint

## Rollback Plan

If something goes wrong, you can rollback:

```bash
# In Railway Dashboard:
# 1. Go to your worker service
# 2. Go to Deployments
# 3. Find previous working deployment
# 4. Click "Redeploy"
```

Or redeploy previous commit:
```bash
git checkout <previous-commit-hash>
git push origin main --force
```

## Post-Deployment Checklist

- [ ] Worker starts successfully (check logs)
- [ ] Health endpoint returns 200
- [ ] No import errors in logs
- [ ] Firebase connection works (check for 401 errors)
- [ ] Worker is checking for alerts (check logs)
- [ ] Alerts are being sent (monitor for 24 hours)
- [ ] No duplicates (test by sending same alert twice)

## Next Steps

After deploying the worker:

1. **Monitor for 24 hours** - Watch alert volume and check for duplicates
2. **Check Firebase** - Verify deduplication records are being created
3. **User feedback** - Ask users if they're receiving alerts correctly
4. **Compare metrics** - More alerts should be sent (better filtering)

## Support

If you encounter issues:

1. **Collect logs**: `railway logs --service fxsentinel-background-worker > worker.log`
2. **Check Firebase**: Verify deduplication records in Firebase console
3. **Test endpoints**: Verify main app `/api/news` and `/api/alerts/trigger` work
4. **Review changes**: Check that all modified files are deployed

