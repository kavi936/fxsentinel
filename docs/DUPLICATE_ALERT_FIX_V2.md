# Duplicate Alert Fix V2 - Enhanced Race Condition Prevention

**Date**: January 2026  
**Issue**: Duplicate alerts still occurring in pairs (race condition)  
**Status**: ✅ Enhanced Fix Applied

---

## Problem Analysis

### Root Cause: Firebase Eventual Consistency

Even with atomic reservation, duplicates were still occurring because:

1. **Firebase Realtime Database has eventual consistency**
   - Writes may not be immediately visible to other readers
   - Two threads can both see "no record" and both create reservations

2. **Timing Window**
   - Thread A: Check → No record → Reserve → Send
   - Thread B: Check → No record (before A's write is visible) → Reserve → Send
   - Result: Both send the alert

3. **No Verification After Reservation**
   - Original code didn't verify the reservation was actually ours
   - Could overwrite another thread's reservation

---

## Enhanced Solution

### 1. Retry Logic with Verification ✅

**New Approach**: Retry up to 3 times with verification

```python
def _check_and_reserve_alert(self, alert_type, content, user_id):
    for attempt in range(3):
        # 1. Check if exists
        # 2. Try to reserve
        # 3. Verify we got the reservation (check reserved_at timestamp)
        # 4. If verification fails, retry with delay
```

**Benefits**:
- Handles Firebase eventual consistency
- Verifies we actually got the reservation
- Retries if verification fails

---

### 2. Timestamp-Based Verification ✅

**New Feature**: Use unique timestamp to identify our reservation

```python
our_reserved_at = now.isoformat()  # Unique timestamp
reserve_record = {
    'status': 'reserved',
    'reserved_at': our_reserved_at,  # Our unique identifier
    ...
}

# Verify: Check if reserved_at matches ours
if verify_reserved_at == our_reserved_at:
    # We got it!
    return True
else:
    # Someone else got it first
    return False
```

**Benefits**:
- Can distinguish our reservation from others
- Prevents false positives in verification
- More reliable than just checking status

---

### 3. Increased Delay After Reservation ✅

**Before**: 200ms delay  
**After**: 300ms delay + 200ms in verification

**Total**: ~500ms delay to allow Firebase to propagate

**Benefits**:
- More time for Firebase to propagate writes
- Reduces race condition window
- Better for high-concurrency scenarios

---

### 4. Retry on Verification Failure ✅

**New Feature**: Retry if verification fails

```python
if verify_status != 'reserved' or verify_reserved_at != our_reserved_at:
    if attempt < max_retries - 1:
        time.sleep(0.15)  # Wait before retry
        continue  # Retry
```

**Benefits**:
- Handles transient Firebase issues
- Gives Firebase time to propagate
- More resilient to network delays

---

## Workflow (Enhanced)

### Before (Race Condition)
```
T+0ms: Thread A: Check → No record
T+0ms: Thread B: Check → No record (A's write not visible yet)
T+10ms: Thread A: Reserve → Success
T+10ms: Thread B: Reserve → Success (overwrites A's reservation)
T+20ms: Thread A: Send alert
T+20ms: Thread B: Send alert (DUPLICATE!)
```

### After (Race Condition Prevented)
```
T+0ms: Thread A: Check → No record
T+0ms: Thread B: Check → No record
T+10ms: Thread A: Reserve → Success (reserved_at: T+10ms)
T+10ms: Thread B: Reserve → Success (reserved_at: T+10ms, but different timestamp)
T+200ms: Thread A: Verify → reserved_at matches → Proceed
T+200ms: Thread B: Verify → reserved_at doesn't match → Abort
T+300ms: Thread A: Send alert (only one!)
```

---

## Key Improvements

### 1. Atomic Check-and-Reserve with Verification
- Single operation checks and reserves
- Verifies we got the reservation
- Retries if verification fails

### 2. Timestamp-Based Identification
- Each reservation has unique timestamp
- Can distinguish our reservation from others
- Prevents false positives

### 3. Retry Logic
- Up to 3 attempts
- 150ms delay between retries
- Handles transient Firebase issues

### 4. Increased Propagation Delay
- 300ms delay after reservation
- 200ms delay in verification
- Total ~500ms for Firebase to propagate

---

## Testing Recommendations

### 1. Monitor Reserved Alerts
```bash
python3 scripts/diagnose_duplicate_alerts.py
```

Look for:
- Reserved alerts count (should be 0 or very low)
- Multiple reservations with different timestamps (indicates race condition)

### 2. Check Logs
Look for:
- "Successfully reserved alert" messages
- "Alert already reserved by another instance" messages
- "Reservation verification failed" messages

### 3. Test High Concurrency
- Process same news item for multiple users simultaneously
- Verify only one alert is sent per user
- Check for duplicate reservations

---

## Expected Behavior

### Normal Flow
1. Thread checks deduplication → No record
2. Thread reserves alert → Success
3. Thread verifies reservation → Matches → Proceed
4. Thread sends alert
5. Thread marks as sent

### Race Condition (Prevented)
1. Thread A checks → No record
2. Thread B checks → No record
3. Thread A reserves → Success (timestamp: T1)
4. Thread B reserves → Success (timestamp: T2)
5. Thread A verifies → Matches T1 → Proceed
6. Thread B verifies → Doesn't match T1 → Abort
7. Only Thread A sends alert

---

## Performance Impact

### Delays Added
- Reservation verification: ~200ms
- Post-reservation delay: ~300ms
- Total: ~500ms per alert

### Trade-offs
- **Pro**: Prevents duplicates
- **Con**: Slightly slower alert delivery
- **Acceptable**: 500ms delay is negligible for alert delivery

---

## Monitoring

### Key Metrics
1. **Reserved Alerts**: Should be 0 or very low
   - High count = send failures or race conditions

2. **Verification Failures**: Should be 0
   - High count = Firebase consistency issues

3. **Retry Count**: Should be low
   - High count = Firebase performance issues

### Alerts to Watch
- Multiple reservations for same alert
- Verification failures
- Retry attempts

---

## Rollback Plan

If issues occur, can disable verification by:
```python
# In _check_and_reserve_alert, remove verification step
# Just return True after PUT succeeds
```

---

## Conclusion

The enhanced fix addresses Firebase eventual consistency by:
- ✅ Retry logic with verification
- ✅ Timestamp-based reservation identification
- ✅ Increased propagation delays
- ✅ Better error handling

This should eliminate duplicate alerts even under high concurrency and Firebase consistency delays.

