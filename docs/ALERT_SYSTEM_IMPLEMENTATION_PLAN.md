# Alert System Implementation Plan
**Date**: January 2, 2026  
**Goal**: Implement unified alert system with improved performance and efficiency

---

## Overview

This plan implements the unified alert system architecture, merging the background worker into the main app and implementing event-driven alerts with parallel processing.

**Timeline**: 4 phases, ~1 week each  
**Risk Level**: Medium (gradual migration with fallbacks)

---

## Phase 1: Unify Services (Days 1-2)

### Goal
Merge background worker into main app as a background thread, eliminating HTTP overhead.

### Tasks

#### Task 1.1: Create Unified Alert Processor
- [ ] Create `backend/services/unified_alert_processor.py`
- [ ] Move worker logic to unified processor
- [ ] Replace HTTP calls with direct function calls
- [ ] Add thread-safe operations

#### Task 1.2: Integrate into Main App
- [ ] Add background thread initialization in `backend/app.py`
- [ ] Start thread on app startup
- [ ] Add health check endpoint for background thread
- [ ] Test thread lifecycle (start, stop, restart)

#### Task 1.3: Update News Endpoint
- [ ] Add alert trigger to `/api/news` endpoint
- [ ] Implement non-blocking alert processing
- [ ] Test immediate alert triggering

#### Task 1.4: Testing
- [ ] Test background thread starts correctly
- [ ] Test alerts trigger on news fetch
- [ ] Test thread survives app restarts
- [ ] Compare performance with old system

**Deliverable**: Unified service with background thread working

---

## Phase 2: Event-Driven Alerts (Days 3-4)

### Goal
Trigger alerts immediately when news is fetched, eliminating 60-300s delay.

### Tasks

#### Task 2.1: Implement Event-Driven Triggering
- [ ] Modify `/api/news` to trigger alerts immediately
- [ ] Add async alert processing (non-blocking)
- [ ] Implement event queue for coordination
- [ ] Add error handling and retry logic

#### Task 2.2: Coordinate News Fetch and Alerts
- [ ] Ensure alerts trigger after news is saved to cache
- [ ] Add proper sequencing (fetch → save → alert)
- [ ] Test timing and coordination

#### Task 2.3: Update Background Thread
- [ ] Keep background thread for economic calendar only
- [ ] Remove news checking from background thread
- [ ] Update thread to only handle periodic tasks

#### Task 2.4: Testing
- [ ] Test alerts trigger immediately on news fetch
- [ ] Test no duplicate alerts
- [ ] Test error handling
- [ ] Measure latency improvements

**Deliverable**: Event-driven alerts working with immediate triggering

---

## Phase 3: Parallel Processing (Days 5-6)

### Goal
Process users in parallel for 7x faster alert delivery.

### Tasks

#### Task 3.1: Implement Parallel User Processing
- [ ] Add ThreadPoolExecutor to unified processor
- [ ] Process users in parallel batches
- [ ] Add rate limiting for Telegram API
- [ ] Implement proper error handling per user

#### Task 3.2: Thread Safety
- [ ] Ensure thread-safe operations
- [ ] Add proper locking for shared resources
- [ ] Test concurrent access to Firebase
- [ ] Test concurrent Telegram API calls

#### Task 3.3: Rate Limiting
- [ ] Implement Telegram API rate limiting
- [ ] Add retry logic with exponential backoff
- [ ] Monitor API usage
- [ ] Test rate limit handling

#### Task 3.4: Testing
- [ ] Test parallel processing with 7 users
- [ ] Test with 50+ users (simulated)
- [ ] Measure performance improvements
- [ ] Test error handling and recovery

**Deliverable**: Parallel user processing working with rate limiting

---

## Phase 4: Optimize Deduplication (Days 7-8)

### Goal
Efficient deduplication without redundancy.

### Tasks

#### Task 4.1: Global Content Hash Deduplication
- [ ] Implement content hash for news items
- [ ] Add global deduplication check (before user processing)
- [ ] Cache deduplication results
- [ ] Optimize Firebase queries

#### Task 4.2: Per-User Deduplication Optimization
- [ ] Optimize per-user deduplication checks
- [ ] Add caching for user preferences
- [ ] Batch Firebase reads
- [ ] Reduce redundant checks

#### Task 4.3: Testing
- [ ] Test deduplication accuracy
- [ ] Test no duplicate alerts
- [ ] Test performance improvements
- [ ] Monitor Firebase usage

**Deliverable**: Optimized deduplication working efficiently

---

## Migration Strategy

### Step 1: Deploy Unified Service (Parallel Run)
1. Deploy new unified service
2. Run both old and new systems in parallel
3. Monitor both systems
4. Compare results

### Step 2: Gradual Rollout
1. Route 10% traffic to unified service
2. Monitor for 24 hours
3. Route 50% traffic
4. Monitor for 24 hours
5. Route 100% traffic

### Step 3: Decommission Old Worker
1. Verify unified service is stable
2. Stop old background worker service
3. Remove old worker code
4. Update documentation

---

## Testing Checklist

### Functional Tests
- [ ] Alerts trigger on news fetch
- [ ] Alerts sent to all eligible users
- [ ] No duplicate alerts
- [ ] Economic calendar alerts work
- [ ] Post-news analysis works
- [ ] Background thread survives restarts

### Performance Tests
- [ ] Alert latency < 5 seconds
- [ ] User processing < 1 second (7 users)
- [ ] No HTTP overhead
- [ ] CPU usage acceptable
- [ ] Memory usage acceptable

### Integration Tests
- [ ] News fetch → Alert trigger works
- [ ] Firebase state synchronization works
- [ ] Telegram API calls succeed
- [ ] Error handling works correctly

---

## Rollback Plan

If issues occur:
1. **Immediate**: Route traffic back to old system
2. **Short-term**: Fix issues in unified service
3. **Long-term**: Re-evaluate approach if needed

---

## Success Metrics

- ✅ Alert latency: < 5 seconds (from news fetch to delivery)
- ✅ User processing: < 1 second for 7 users
- ✅ Cost reduction: $10-15/month savings
- ✅ Accuracy: 0 duplicate alerts, 0 missed alerts
- ✅ Uptime: 99.9% availability

---

## Next Steps

1. Start with Phase 1: Create unified alert processor
2. Test incrementally after each phase
3. Deploy to staging first
4. Monitor closely during rollout
5. Iterate based on feedback

