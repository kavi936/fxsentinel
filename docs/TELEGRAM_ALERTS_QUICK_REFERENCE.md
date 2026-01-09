# Telegram Alerts System - Quick Reference Guide

**Quick decision guide for implementing improvements**

---

## Critical Issues & Solutions (At a Glance)

| Issue | Severity | Recommended Solution | Time | Risk |
|-------|----------|---------------------|------|------|
| Global Deduplication Blocking | 🔴 Critical | Reduce TTL + Hybrid Approach | 4-6h | Low |
| Complex Chat ID Lookup | 🟡 High | Gradual Migration + Validation | 3-4h | Low |
| Inconsistent Settings | 🟡 High | API Normalization + Migration | 3-4h | Low |
| Error Recovery | 🟡 Moderate | Circuit Breaker + Metrics | 5-7h | Low |

---

## Quick Start: Phase 1 (4-6 hours)

### 1. Reduce Deduplication TTL (30 min)
```python
# backend/services/persistent_alert_deduplication.py
self.alert_ttl_hours = 0.5  # Change from 2 to 0.5
```

### 2. Add Settings Normalization on GET
```python
# backend/app.py - /api/alerts/user-settings GET endpoint
settings = firebase_storage.get_user_alert_settings(user_id)
normalized = normalize_settings(settings)  # Add this line
return jsonify({"success": True, "settings": normalized})
```

### 3. Add Chat ID Validation
```python
# backend/services/firebase_realtime_storage.py
def save_telegram_chat_id(self, user_id, chat_id):
    if not self._validate_chat_id(chat_id):
        return False
    # ... rest of code
```

### 4. Verify Circuit Breaker
```python
# backend/services/alert_service.py
# Already implemented, just verify it's working
circuit_breaker = get_telegram_circuit_breaker()
if circuit_breaker.get_stats()['state'] == 'open':
    # Handle appropriately
```

---

## Implementation Checklist

### Phase 1: Quick Wins
- [ ] Reduce deduplication TTL to 30 minutes
- [ ] Add settings normalization on GET
- [ ] Add chat ID validation
- [ ] Verify circuit breaker integration
- [ ] Test all changes

### Phase 2: Core Fixes
- [ ] Implement hybrid deduplication
- [ ] Complete chat ID migration
- [ ] Run settings migration script
- [ ] Add basic metrics collection
- [ ] Test all changes

### Phase 3: Enhancements
- [ ] Enhance dead letter queue
- [ ] Add metrics dashboard
- [ ] Add admin notifications
- [ ] Remove backward compatibility
- [ ] Test all changes

---

## Key Files to Modify

1. **`backend/services/persistent_alert_deduplication.py`**
   - Reduce TTL
   - Implement hybrid deduplication

2. **`backend/services/firebase_realtime_storage.py`**
   - Add chat ID validation
   - Implement gradual migration

3. **`backend/app.py`**
   - Add normalization on GET
   - Add metrics endpoint

4. **`backend/services/alert_service.py`**
   - Verify circuit breaker
   - Add metrics recording

5. **New: `backend/services/alert_metrics.py`**
   - Create metrics service

---

## Testing Checklist

- [ ] Alerts not blocked incorrectly
- [ ] Chat IDs migrate correctly
- [ ] Settings normalize correctly
- [ ] Circuit breaker works
- [ ] Metrics accurate
- [ ] No regressions

---

## Rollback Plan

All changes are reversible:
- TTL: Simple constant change
- Normalization: Additive, safe
- Migration: Gradual, can rollback
- Metrics: Additive, safe

---

## Estimated Timeline

- **Week 1**: Phase 1 (4-6 hours)
- **Week 2**: Phase 2 (10-12 hours)
- **Week 3**: Phase 3 (8-10 hours)

**Total**: 22-28 hours over 3 weeks

---

## Success Criteria

✅ No alerts blocked by deduplication  
✅ Single source of truth for chat IDs  
✅ Consistent settings format  
✅ Metrics visible  
✅ Circuit breaker working  

---

For detailed information, see: `TELEGRAM_ALERTS_IMPROVEMENTS_SUMMARY.md`

