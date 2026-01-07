# Duplicate Alert Debug Logging - Implementation Summary

**Date**: January 2026  
**Status**: ✅ Implemented

---

## Changes Implemented

### 1. Removed Aggressive Global Deduplication Check ✅

**File**: `backend/services/unified_alert_processor.py`

**Change**: Removed the global content hash check that was blocking per-user processing. The global check now only happens inside `should_send_news_alert()` as an optimization, not as a blocker.

**Before**:
```python
# Filter news items by global content hash (one check per news item)
news_items_to_process = []
for news_item in high_impact_filtered[:3]:
    content_hash = dedup._get_news_content_hash(news_item)
    if content_hash:
        if dedup._check_global_content_hash(content_hash):
            news_items_to_process.append(news_item)
        else:
            # BLOCKED - already sent globally
            logger.debug(f"Skipping news item (already sent globally)...")
```

**After**:
```python
# Don't filter by global hash here - let per-user deduplication handle it
# Global hash is checked inside should_send_news_alert() for optimization
news_items_to_process = high_impact_filtered[:3]  # Max 3 items
```

**Why**: The global check was too aggressive - if a news item was sent to ANY user, it blocked sending to ALL other users. Now per-user deduplication handles it properly.

---

### 2. Added Detailed Logging Throughout Alert Flow ✅

#### A. Entry Point Logging

**File**: `backend/services/unified_alert_processor.py`

**Location**: `_send_alert_to_user()` method start

**Added**:
```python
logger.info(f"🔍 _send_alert_to_user called for user {user_id}: {news_title}...")
```

**Purpose**: Track when alert processing starts for each user.

---

#### B. Deduplication Check Logging

**File**: `backend/services/unified_alert_processor.py`

**Location**: Before and after `should_send_news_alert()` call

**Added**:
```python
logger.info(f"🔍 Checking deduplication for user {user_id}: {news_title}...")
should_send = should_send_news_alert(news_item, user_id)
logger.info(f"🔍 Deduplication result for user {user_id}: should_send={should_send}")
```

**Purpose**: Track deduplication decisions for each user.

---

#### C. Global Hash Check Logging

**File**: `backend/services/persistent_alert_deduplication.py`

**Location**: `should_send_news_alert()` method

**Added**:
```python
global_check_result = self._check_global_content_hash(content_hash)
logger.info(f"🔍 Global hash check for user {user_id}: hash={content_hash[:16]}..., result={global_check_result}, title={news_title}")

if not global_check_result:
    logger.warning(f"🚫 Global duplicate prevented for user {user_id}: {news_title}")
else:
    logger.info(f"✅ Global hash check passed for user {user_id}: {news_title}")
```

**Purpose**: Track global deduplication decisions.

---

#### D. Global Content Hash Firebase Check Logging

**File**: `backend/services/persistent_alert_deduplication.py`

**Location**: `_check_global_content_hash()` method

**Added**:
```python
if existing_hash and isinstance(existing_hash, dict):
    # ... existing logic ...
    logger.info(f"🚫 Global content hash EXISTS (not expired): {content_hash[:16]}...")
else:
    logger.info(f"✅ Global content hash NEW (not found in Firebase): {content_hash[:16]}...")
```

**Purpose**: Track Firebase global hash lookups.

---

#### E. Atomic Check-and-Reserve Logging

**File**: `backend/services/persistent_alert_deduplication.py`

**Location**: `_check_and_reserve_alert()` method

**Added**:
```python
logger.info(f"🔍 _check_and_reserve_alert attempt {attempt + 1}/{max_retries} for user {user_id}: {alert_type}, key={alert_key[:32]}...")
existing_alert = self.firebase._make_request('GET', alert_path)
logger.info(f"🔍 Existing alert check result: {existing_alert is not None} for user {user_id}")
```

**Purpose**: Track atomic reservation attempts and results.

---

#### F. History Logging Result Logging

**File**: `backend/services/unified_alert_processor.py`

**Location**: History logging section

**Added**:
```python
logger.info(f"🔍 Attempting to log alert to history for user {user_id}: {alert_title[:50]}...")
history_logged = firebase_storage.log_alert_history(user_id, history_data)
logger.info(f"🔍 History logging result: {history_logged} for user {user_id}")
```

**Purpose**: Track history logging success/failure.

---

## Expected Log Flow

When an alert is processed, you should see logs in this order:

1. `🔍 _send_alert_to_user called for user {user_id}: {title}...`
2. `🔍 Checking deduplication for user {user_id}: {title}...`
3. `🔍 Global hash check for user {user_id}: hash={hash}..., result={result}, title={title}`
   - If global check fails: `🚫 Global duplicate prevented for user {user_id}: {title}`
   - If global check passes: `✅ Global hash check passed for user {user_id}: {title}`
4. `🔍 _check_and_reserve_alert attempt 1/3 for user {user_id}: news, key={key}...`
5. `🔍 Existing alert check result: {True/False} for user {user_id}`
6. `✅ Successfully reserved alert for user {user_id}: news` (if successful)
7. `🔍 Deduplication result for user {user_id}: should_send={True/False}`
8. `✅ Alert approved for user {user_id}: {title}` (if should_send=True)
9. `🔍 Attempting to log alert to history for user {user_id}: {title}...`
10. `🔍 History logging result: {True/False} for user {user_id}`
11. `✅ Logged alert to history for user {user_id}: {title}...` (if successful)
12. `✅ Alert sent and logged to history for user {user_id}: {title}...`
13. `Alert sent successfully to user {user_id}`

---

## Debugging Duplicate Alerts

### If you see duplicates:

1. **Check for multiple "Alert approved" messages** for the same user and title
   - This means deduplication is failing
   - Look for the reservation logs to see if atomic check-and-reserve is working

2. **Check for "Global duplicate prevented" followed by "Alert approved"**
   - This shouldn't happen - global check should block per-user check
   - Indicates a logic error

3. **Check for multiple reservation attempts**
   - If you see multiple "attempt 1/3" for the same user and key, it means retries are happening
   - Check if reservation verification is failing

4. **Check for "Alert already reserved by another instance"**
   - This is good - it means the atomic reservation is working
   - But if you still see duplicates, the reservation might not be preventing sends

---

## Debugging Missing History

### If history is not appearing:

1. **Check for "History logging result: False"**
   - This means `log_alert_history()` returned False
   - Check Firebase connection and permissions

2. **Check for "Error logging alert to history"**
   - This means an exception occurred
   - Check the exception details in the logs

3. **Check for "Alert sent but history logging failed"**
   - Alert was sent but history wasn't logged
   - Check Firebase storage service

4. **Verify history endpoint is working**
   - Check `/api/alerts/history` endpoint
   - Verify it's reading from the correct Firebase path

---

## Next Steps

1. **Monitor logs** for the new debug messages
2. **Track duplicate patterns** - look for same user + title appearing multiple times
3. **Verify history logging** - check if "History logging result: True" appears
4. **Check Firebase** - verify records are being created in Firebase
5. **Test with refresh button** - press multiple times and watch logs

---

## Files Modified

1. `backend/services/unified_alert_processor.py`
   - Removed aggressive global deduplication check
   - Added entry point logging
   - Added deduplication result logging
   - Enhanced history logging with result tracking

2. `backend/services/persistent_alert_deduplication.py`
   - Added global hash check logging
   - Added Firebase global hash lookup logging
   - Added atomic check-and-reserve attempt logging
   - Added existing alert check result logging

---

## Conclusion

All logging has been added to track the complete alert flow from entry point to history logging. The aggressive global deduplication check has been removed to allow proper per-user processing. The logs will now show exactly where duplicates are occurring and why history might not be logging.

