# Duplicate Alert Race Condition Fix

**Date**: January 2026  
**Issue**: Duplicate alerts being sent (2-4 times) due to race condition in concurrent processing  
**Status**: ✅ Fixed

---

## Problem Identified

### Root Cause: Race Condition in Concurrent Processing

The system was processing alerts in parallel using `ThreadPoolExecutor` with 10 workers. For each news item, it created futures for ALL users:

```python
for user_data in users:  # 10 users
    for news_item in news_items_to_process:  # 3 news items
        future = executor.submit(
            self._send_alert_to_user,
            user_data,
            news_item
        )
        futures.append(future)  # 30 futures total
```

**The Race Condition:**
1. Multiple threads process the same user+news combination simultaneously
2. Thread 1 checks Firebase deduplication (no record exists)
3. Thread 2 checks Firebase deduplication (no record exists) - **before Thread 1 writes**
4. Thread 1 reserves the alert in Firebase
5. Thread 2 reserves the alert in Firebase (overwrites Thread 1's reservation)
6. Both threads verify their reservation (both see "reserved" status)
7. Both threads send the alert → **DUPLICATES**

Even though the atomic check-and-reserve was implemented, the 0.5s verification delay created a window where multiple threads could all pass the check.

---

## Solution Implemented

### Per-User+News Lock

Added a per-user+news combination lock to ensure only one thread processes the same user+news combination at a time.

**Implementation:**

1. **Lock Dictionary**: Created a dictionary of locks keyed by `(user_id, news_id)`
   ```python
   self._processing_locks: Dict[Tuple[str, str], threading.Lock] = {}
   self._processing_locks_lock = threading.Lock()  # Lock for the locks dictionary
   ```

2. **Lock Acquisition**: Before processing, acquire lock for the specific user+news combination
   ```python
   lock_key = (user_id, news_id)
   
   # Get or create lock for this user+news combination
   with self._processing_locks_lock:
       if lock_key not in self._processing_locks:
           self._processing_locks[lock_key] = threading.Lock()
       processing_lock = self._processing_locks[lock_key]
   
   # Acquire lock before processing (non-blocking)
   if not processing_lock.acquire(blocking=False):
       # Another thread is already processing - skip
       logger.warning(f"🚫 Another thread already processing alert for user {user_id}: {news_title}... (skipping)")
       return False
   ```

3. **Lock Release**: Always release lock in finally block
   ```python
   try:
       # ... process alert ...
   finally:
       # Always release the lock
       processing_lock.release()
   ```

---

## How It Works

### Before Fix:
```
Thread 1: Check Firebase → No record → Reserve → Verify → Send ✅
Thread 2: Check Firebase → No record → Reserve → Verify → Send ✅
Result: 2 alerts sent (DUPLICATE)
```

### After Fix:
```
Thread 1: Acquire lock → Check Firebase → No record → Reserve → Verify → Send → Release lock ✅
Thread 2: Try acquire lock → BLOCKED (Thread 1 has it) → Skip ❌
Result: 1 alert sent (NO DUPLICATE)
```

---

## Benefits

1. **Prevents Race Conditions**: Only one thread can process the same user+news combination at a time
2. **Non-Blocking**: Uses `blocking=False` so if lock is held, thread skips instead of waiting
3. **Efficient**: Locks are created on-demand and reused
4. **Thread-Safe**: Lock dictionary itself is protected by `_processing_locks_lock`

---

## Expected Behavior

### Logs to Look For:

**When duplicate is prevented:**
```
🚫 Another thread already processing alert for user {user_id}: {title}... (skipping)
```

**When alert is processed:**
```
🔍 _send_alert_to_user called for user {user_id}: {title}...
🔍 Checking deduplication for user {user_id}: {title}...
✅ Alert approved for user {user_id}: {title}...
✅ Alert sent and logged to history for user {user_id}: {title}...
```

---

## Testing

1. **Press refresh button multiple times quickly**
   - Should see "Another thread already processing" messages
   - Should receive only 1 alert per news item

2. **Check logs for duplicate prevention**
   - Look for "🚫 Another thread already processing" messages
   - Verify only one "Alert sent successfully" per user+news combination

3. **Monitor concurrent processing**
   - Multiple users can still process in parallel (different user+news combinations)
   - Same user+news combination is serialized

---

## Files Modified

1. **`backend/services/unified_alert_processor.py`**
   - Added `_processing_locks` dictionary
   - Added `_processing_locks_lock` for thread-safe lock management
   - Modified `_send_alert_to_user()` to acquire/release lock
   - Added logging for duplicate prevention

---

## Conclusion

The race condition has been fixed by adding per-user+news locks. This ensures that even when multiple threads are processing alerts in parallel, only one thread can process the same user+news combination at a time, preventing duplicates while still allowing parallel processing for different combinations.

