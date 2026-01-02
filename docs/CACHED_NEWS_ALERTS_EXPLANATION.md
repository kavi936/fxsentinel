# How Alerts Handle Cached News Events - Simple Explanation
**Date**: January 2, 2026  
**Purpose**: Explain how alerts distinguish between fresh and cached news

---

## The Key Question

**"When news is fetched, some is fresh (new) and some is cached (old). How does the system know which alerts to send?"**

---

## Simple Answer 🎯

The robot is **super smart**! It:
1. ✅ Only sends alerts for **FRESH news** (newly fetched)
2. ✅ **Skips cached news** (already in the system)
3. ✅ Uses **memory** to prevent sending alerts for news that was already sent

---

## How It Works (Step-by-Step)

### Step 1: News is Fetched 📰

When the `/api/news` endpoint is called:

```
Fresh News (just fetched):
  - News A: "Fed raises rates" (NEW!)
  - News B: "CPI data released" (NEW!)

Cached News (already in system):
  - News C: "GDP growth" (from yesterday)
  - News D: "Unemployment data" (from yesterday)
```

### Step 2: Robot Separates Fresh from Cached 🧠

The robot knows:
- **Fresh News** = Just fetched (might be new, might be duplicate)
- **Cached News** = Already in system (definitely old)

### Step 3: Robot Only Checks Fresh News for Alerts ⚡

**IMPORTANT**: Robot only checks **fresh_news** for alerts, NOT cached_news!

```python
# In backend/app.py
unified_processor.check_news_alerts_async(fresh_news)  # Only fresh_news!
```

**Why?**
- Cached news is already in the system (old)
- If cached news was important, alerts were already sent
- We only want to send alerts for NEW news

### Step 4: Robot Checks Its Memory 🧠

For each fresh news item, robot checks:

1. **Global Memory**: "Did I already send THIS news to anyone?"
   - If YES → Skip! (Already sent)
   - If NO → Continue!

2. **Per-User Memory**: "Did I already send THIS news to Person A?"
   - If YES → Skip Person A! (Already sent to them)
   - If NO → Send to Person A!

### Step 5: Only NEW Fresh News Gets Alerts ✅

**Result**:
- Fresh news that's **truly new** → Alerts sent! ✅
- Fresh news that's **already sent** → Skipped! ❌
- Cached news → **Never checked** (already old) ❌

---

## Example Scenario

### Scenario: News Fetch at 10:00 AM

**Fresh News Fetched**:
1. "Fed raises rates" (published 9:55 AM) - **NEW!**
2. "CPI data released" (published 9:50 AM) - **NEW!**
3. "GDP growth" (published yesterday) - **DUPLICATE** (already in cache)

**Cached News** (already in system):
1. "Unemployment data" (from yesterday)
2. "Trade balance" (from yesterday)

### What Happens:

1. **Robot checks only fresh_news**:
   - "Fed raises rates" → Check memory → NEW! → Send alerts! ✅
   - "CPI data released" → Check memory → NEW! → Send alerts! ✅
   - "GDP growth" → Check memory → Already sent! → Skip! ❌

2. **Robot ignores cached_news**:
   - "Unemployment data" → Not checked (cached, old)
   - "Trade balance" → Not checked (cached, old)

3. **Result**:
   - ✅ 2 alerts sent (for new fresh news)
   - ❌ 0 alerts for cached news (correctly skipped)

---

## Edge Case: What If Cached News Was Never Sent?

**Question**: "What if cached news is important but was never sent as an alert?"

**Answer**: This shouldn't happen because:
1. When news was first fetched (when it was fresh), alerts were sent
2. If alerts weren't sent, it means:
   - News wasn't high-impact (filtered out)
   - Or there was an error (rare)

**But if it happens**:
- The news is already in the cache (old)
- It won't trigger alerts (only fresh news triggers alerts)
- This is correct behavior (we don't want to send alerts for old news)

---

## How Deduplication Prevents Duplicates

### Global Deduplication (First Check)

```
Fresh News: "Fed raises rates"
  ↓
Robot checks global memory: "Did I send this to anyone?"
  ↓
If YES → Skip entirely! (Don't check any users)
If NO → Continue to per-user check
```

**Benefit**: If news was already sent globally, we skip ALL users (saves time!)

### Per-User Deduplication (Second Check)

```
Fresh News: "Fed raises rates" (passed global check)
  ↓
For each user:
  Robot checks: "Did I send this to Person A?"
  ↓
If YES → Skip Person A!
If NO → Send to Person A!
```

**Benefit**: Prevents sending same alert twice to same person

---

## Code Flow (Technical)

### 1. News Fetch (`/api/news` endpoint)

```python
# Fetch fresh news
fresh_news = fetch_from_sources()  # Newly fetched

# Load cached news
cached_news = news_cache.load_news()  # Already in system

# Merge for display (fresh on top)
all_news = merge(fresh_news, cached_news)

# IMPORTANT: Only trigger alerts for fresh_news!
unified_processor.check_news_alerts_async(fresh_news)  # Only fresh!
```

### 2. Alert Processing (`unified_alert_processor.py`)

```python
def _check_news_alerts(self, news_items):  # Only fresh_news!
    # Filter for high-impact
    high_impact = filter_high_impact(news_items)
    
    # Check global deduplication
    for news_item in high_impact:
        if already_sent_globally(news_item):
            skip!  # Already sent, don't check users
        else:
            process_for_users()  # Check each user
```

### 3. Deduplication Check

```python
def should_send_news_alert(news_item, user_id):
    # Check global: "Did I send this to anyone?"
    if already_sent_globally(news_item):
        return False  # Skip!
    
    # Check per-user: "Did I send this to Person A?"
    if already_sent_to_user(news_item, user_id):
        return False  # Skip!
    
    return True  # Send!
```

---

## Summary

### How Alerts Handle Cached News:

1. **Only Fresh News Triggers Alerts** ✅
   - Robot only checks `fresh_news` for alerts
   - Cached news is ignored (already old)

2. **Deduplication Prevents Duplicates** ✅
   - Global check: "Did I send this to anyone?"
   - Per-user check: "Did I send this to YOU?"
   - Both checks prevent duplicates

3. **Cached News Never Triggers Alerts** ✅
   - Cached news is for display only
   - If it was important, alerts were already sent when it was fresh
   - This is correct behavior!

---

## Simple Analogy

Think of it like a **newspaper delivery system**:

- **Fresh News** = New papers just printed
- **Cached News** = Old papers from yesterday

**The delivery person**:
- ✅ Delivers NEW papers (fresh news)
- ❌ Ignores OLD papers (cached news)
- 🧠 Remembers what they already delivered (deduplication)

**Why ignore old papers?**
- If they were important, they were already delivered yesterday
- We don't want to deliver yesterday's papers again!

---

## Key Points

1. **Only fresh_news triggers alerts** (not cached_news)
2. **Deduplication prevents duplicates** (global + per-user)
3. **Cached news is for display only** (never triggers alerts)
4. **This is correct behavior** (we don't want alerts for old news)

---

## Questions?

**Q: What if cached news is important but was never sent?**
A: This shouldn't happen. If it does, the news is already old, so we don't send alerts (correct behavior).

**Q: Can cached news trigger alerts?**
A: No! Only fresh_news triggers alerts. Cached news is ignored.

**Q: How does the system know what's fresh vs cached?**
A: Fresh news is newly fetched. Cached news is loaded from Firebase. They're separate variables in the code.

**Q: What if fresh news is a duplicate of cached news?**
A: Deduplication catches it! Global check sees it was already sent, so it's skipped.

---

## Conclusion

The system is **smart**:
- ✅ Only sends alerts for **fresh news**
- ✅ **Skips cached news** (already old)
- ✅ Uses **deduplication** to prevent duplicates
- ✅ **Fast and accurate**!

This ensures you only get alerts for **new, important news**, not old cached news! 🎉

