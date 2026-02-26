# Live News Time Display – Accuracy Fix

## Problem

Users saw times like **"14:17 GST • 4 hrs ago"** for items that had only just appeared in the Live News card (e.g. a few minutes ago). The displayed time did not match when the event was first shown in the app.

## Root Cause

The UI shows **when the item entered our feed** using `added_to_feed_at`. When that field was missing (e.g. legacy cached items or older Firebase data), the backend used **`published_at`** (the article’s original publication time) as a fallback. So the card showed the article’s age (“4 hrs ago”) instead of when we first added it to the feed (“Just now” / “2 mins ago”).

## Changes Made

### Backend (`backend/app.py`)

- **Fallback for missing `added_to_feed_at`**: All places that build the `/api/news` response now use **current time** (`datetime.now().isoformat()`) when `added_to_feed_at` is absent, instead of `published_at`.
- **Merge logic**: When merging fresh and cached news, if a cached item has no `added_to_feed_at`, we use the current merge time instead of the cached item’s `published_at`.
- **Save path**: When replacing the cache, items without `added_to_feed_at` get the current time before save so future responses show a sensible “in feed” time.

**Result**: Legacy items no longer show article publish time. They show “Just now” or “X mins ago” based on when we’re serving them (or when we first set the fallback), so the time is consistent with “when we’re showing it” rather than “when the article was published”.

### Frontend

- The card still displays `formatTime(newsItem.added_to_feed_at || newsItem.published_at)`. With the backend fix, `added_to_feed_at` is now always set (or fallback is “now”), so the time reflects feed appearance, not publication.

## Intended Meaning of the Displayed Time

- **Primary**: “When this item first entered our live news feed” (`added_to_feed_at`), which aligns with when it could first appear in the app.
- **Fallback**: If the backend ever omits `added_to_feed_at`, the frontend falls back to `published_at`; after this fix, the backend no longer sends article publish time in place of feed time.

## Optional Future Improvements

- **Client-side “first seen”**: To show “when this user first saw this item,” the client could store a `first_seen_at` per `newsItem.id` (e.g. in sessionStorage or state) and display that when available.
- **Tooltip**: A tooltip like “In feed: 2 mins ago” vs “Published: 4 hrs ago” could show both feed time and publish time if both are available.
