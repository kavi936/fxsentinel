# Deployment Checklist - Persistent News Cache

## Pre-Deployment Verification

### ✅ Code Changes Complete
- [x] `persistent_news_cache.py` created
- [x] All imports in `app.py` updated (11 locations)
- [x] Test script created (`scripts/test_persistent_news_cache.py`)
- [x] No linter errors
- [x] Error handling improved

### ✅ Files Ready for Deployment
- `backend/services/persistent_news_cache.py` - New persistent cache service
- `backend/app.py` - Updated to use persistent cache
- `scripts/test_persistent_news_cache.py` - Test script (optional)

---

## Deployment Steps

### Step 1: Commit Changes
```bash
git add backend/services/persistent_news_cache.py
git add backend/app.py
git add scripts/test_persistent_news_cache.py
git add docs/
git commit -m "Implement persistent news cache using Firebase Realtime Database"
```

### Step 2: Push to GitHub
```bash
git push origin main
```

**Note**: According to your deployment setup, the main app ("cheerful-vitality") is automatically updated by pushing to GitHub.

### Step 3: Monitor Deployment
1. Go to Railway dashboard
2. Watch deployment logs for "cheerful-vitality" service
3. Look for: `"Persistent News Cache Service initialized (TTL: 24.0h)"`
4. Check for any Firebase connection errors

---

## Post-Deployment Verification

### Step 4: Check Firebase Connection
1. Open Firebase Console: https://console.firebase.google.com/
2. Navigate to: Realtime Database → Data
3. Look for `news_cache` structure:
   ```
   news_cache/
     current/
       timestamp: "..."
       news_count: ...
       news: [...]
     history/
       {news_id_1}/...
       {news_id_2}/...
   ```

### Step 5: Test API Endpoints

#### Test `/api/news` Endpoint
```bash
curl https://your-app.railway.app/api/news
```
**Expected**: Returns news items (may be empty initially)

#### Test `/api/cache-status` Endpoint
```bash
curl https://your-app.railway.app/api/cache-status
```
**Expected**: Returns cache status with `exists`, `is_valid`, `news_count`, etc.

#### Test `/api/news-history` Endpoint
```bash
curl https://your-app.railway.app/api/news-history
```
**Expected**: Returns news history array

### Step 6: Verify Cache Persistence
1. **Trigger news fetch**: Call `/api/news` endpoint (or wait for scheduled fetch)
2. **Check Firebase**: Verify `news_cache/current` exists in Firebase
3. **Restart app**: Trigger a new deployment or restart
4. **Verify cache persists**: Call `/api/news` again - should return cached data
5. **Check logs**: Should see "Loaded X news items from Firebase cache"

---

## Monitoring Checklist

### Immediate (First Hour)
- [ ] Deployment successful
- [ ] No errors in Railway logs
- [ ] Firebase connection working
- [ ] Cache structure visible in Firebase console
- [ ] `/api/news` endpoint working

### Short-term (First Day)
- [ ] News cache persists across restarts
- [ ] News history accumulating in Firebase
- [ ] No Firebase errors in logs
- [ ] Users seeing cached news after restart
- [ ] Performance acceptable

### Long-term (First Week)
- [ ] Cache TTL working (24 hours)
- [ ] History cleanup working (500 item limit)
- [ ] No memory leaks or performance issues
- [ ] User feedback positive (no empty feeds)

---

## Troubleshooting

### Issue: Firebase 401 Unauthorized

**Symptoms**:
- Logs show: `401 Client Error: Unauthorized`
- Cache not saving to Firebase

**Solution**:
1. Check Railway environment variables:
   - `FIREBASE_PROJECT_ID` should be set
   - `FIREBASE_REALTIME_URL` should be set
2. Verify Firebase Realtime Database rules allow read/write
3. Check Firebase project settings

### Issue: Cache Not Persisting

**Symptoms**:
- News disappears after restart
- Cache status shows `exists: false`

**Check**:
1. Firebase connection in logs
2. Firebase console for `news_cache` data
3. Error messages in Railway logs

**Solution**:
- Verify Firebase credentials in Railway
- Check Firebase database rules
- Review `persistent_news_cache.py` error handling

### Issue: Cache Too Old

**Symptoms**:
- Cache exists but is ignored
- Fresh news fetched every time

**Check**:
- Cache TTL is 24 hours (configurable)
- Timestamp in cache data

**Solution**:
- This is expected behavior
- Cache refreshes automatically
- Can adjust `max_age_hours` if needed

### Issue: History Not Loading

**Symptoms**:
- `/api/news-history` returns empty
- History disappears after restart

**Check**:
- Firebase structure: `news_cache/history/{news_id}`
- Firebase read permissions
- Logs for errors

**Solution**:
- Verify Firebase structure
- Check `_add_to_history()` method
- Review Firebase write permissions

---

## Success Criteria

✅ **Deployment Successful**
- No errors in Railway logs
- App starts successfully
- "Persistent News Cache Service initialized" in logs

✅ **Firebase Connection Working**
- `news_cache` structure visible in Firebase console
- No 401 errors in logs
- Cache operations succeed

✅ **Cache Persistence Verified**
- News cache survives app restart
- News history persists across deployments
- Users see cached news immediately after restart

✅ **Performance Acceptable**
- Fast reads from Firebase (<100ms)
- No performance degradation
- No memory leaks

---

## Rollback Plan (If Needed)

If issues occur, you can temporarily revert to the old file cache:

1. **Revert imports in app.py**:
   ```python
   # Change back to:
   from services.news_cache import news_cache
   ```

2. **Redeploy**:
   ```bash
   git commit -m "Revert to file cache temporarily"
   git push origin main
   ```

3. **Note**: Old file cache will work but won't persist across restarts (original issue)

---

## Next Steps After Successful Deployment

1. **Monitor for 24-48 hours** - Ensure stability
2. **User feedback** - Verify no empty feeds
3. **Performance monitoring** - Check Firebase usage/quota
4. **Optional cleanup** - Remove old `news_cache.py` file if desired
5. **Documentation** - Update any relevant docs

---

## Related Documentation

- `docs/PERSISTENT_NEWS_CACHE_IMPLEMENTATION.md` - Implementation details
- `docs/CONTEXT_AND_NEXT_STEPS.md` - Full context and next steps
- `scripts/test_persistent_news_cache.py` - Test script

---

## Environment Variables Required

These should already be set in Railway (same as alert deduplication):

- `FIREBASE_PROJECT_ID` - Firebase project ID (e.g., "fxsentinel")
- `FIREBASE_REALTIME_URL` - Firebase Realtime Database URL

**No new environment variables needed** - uses existing Firebase setup.

