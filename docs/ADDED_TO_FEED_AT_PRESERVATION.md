# Preserving Original `added_to_feed_at` Timestamp

## Problem

When news is re-fetched and merged with cached news, the `added_to_feed_at` timestamp was being updated to the current time instead of preserving the original time when it was first fetched.

### Example of the Problem

**Incorrect behavior**:
- News published at 9:00 AM
- First fetched at 10:00 AM → `added_to_feed_at` = 10:00 AM ✅
- Displayed: "10:00 AM" ✅
- Re-fetched at 10:05 AM → `added_to_feed_at` = 10:05 AM ❌
- Displayed: "10:05 AM" ❌ (should still be 10:00 AM)

**Correct behavior**:
- News published at 9:00 AM
- First fetched at 10:00 AM → `added_to_feed_at` = 10:00 AM ✅
- Displayed: "10:00 AM" ✅
- Re-fetched at 10:05 AM → `added_to_feed_at` = 10:00 AM ✅ (preserved)
- Displayed: "10:00 AM" ✅

## Solution

### Changes Made

1. **Create cache map before processing**:
   - Map cached items by key (title + source)
   - This allows us to look up original `added_to_feed_at` values

2. **Preserve cached timestamps**:
   - When processing merged news, check if item exists in cache
   - If it exists, use the cached item's `added_to_feed_at`
   - Only set `added_to_feed_at` to current time for truly new items

3. **Deduplication prefers cached items**:
   - In deduplication, prefer items with existing `added_to_feed_at` (from cache)
   - This ensures cached items are kept over fresh duplicates

### Code Changes

**Before**:
```python
# Set added_to_feed_at for all items without it
for item in all_news:
    if 'added_to_feed_at' not in item:
        item['added_to_feed_at'] = current_time
```

**After**:
```python
# Create map of cached items to preserve their added_to_feed_at
cached_items_map = {}
if cached_news:
    for item in cached_news:
        key = f"{item.get('title', '')}_{item.get('source', '')}"
        if key not in cached_items_map:
            cached_items_map[key] = item

# Preserve cached added_to_feed_at, only set for new items
for item in all_news:
    key = f"{item.get('title', '')}_{item.get('source', '')}"
    if key in cached_items_map:
        # Item exists in cache - preserve original added_to_feed_at
        cached_item = cached_items_map[key]
        if 'added_to_feed_at' in cached_item:
            item['added_to_feed_at'] = cached_item['added_to_feed_at']
    elif 'added_to_feed_at' not in item:
        # New item - set to current time
        item['added_to_feed_at'] = current_time
```

## Result

- ✅ `added_to_feed_at` preserves the original time when news was first fetched
- ✅ Re-fetched news keeps the original timestamp
- ✅ Only truly new items get current time as `added_to_feed_at`
- ✅ Display shows consistent timestamps (e.g., "10:00 AM" stays "10:00 AM")

## Flow

1. **First fetch (10:00 AM)**:
   - Fetch news from sources
   - Set `added_to_feed_at` = 10:00 AM (current time)
   - Save to cache
   - Display: "10:00 AM"

2. **Re-fetch (10:05 AM)**:
   - Fetch fresh news (has `added_to_feed_at` = 10:05 AM)
   - Load cached news (has `added_to_feed_at` = 10:00 AM)
   - Merge: fresh + cached
   - **Preserve**: Items in cache keep `added_to_feed_at` = 10:00 AM
   - **Set**: New items get `added_to_feed_at` = 10:05 AM
   - Deduplicate: Prefer cached items (with 10:00 AM timestamp)
   - Save to cache
   - Display: "10:00 AM" (preserved) for cached items, "10:05 AM" for new items

