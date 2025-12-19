# Caching System - How It Works

## Overview

The Economies tab uses a **two-layer caching system** to optimize performance and reduce API calls to Google Sheets:

1. **Backend Cache** (Server-side): Caches Google Sheets API responses
2. **Frontend Cache** (Client-side): Prevents duplicate API requests

---

## Backend Caching (Google Sheets Service)

### How It Works

**Location:** `backend/services/google_sheets_service.py`

**Storage:**
- `self.cache`: Dictionary storing cached data
- `self.cache_timestamps`: Dictionary storing when each cache entry was created
- Cache key format: `indicators_{country_code}` (e.g., `indicators_US`)

**Cache TTL (Time To Live):**
- **Default:** 30 seconds (recently changed from 5 minutes)
- **Configurable:** Via `GOOGLE_SHEETS_CACHE_TTL` environment variable
- **Purpose:** Balance between data freshness and API rate limits

### Cache Flow

```
1. Request comes in for /api/economy-indicators/US
   ↓
2. Check cache: Does 'indicators_US' exist in cache?
   ↓
3. If exists:
   - Check timestamp: Is it less than 30 seconds old?
   - If YES → Return cached data immediately (no API call)
   - If NO → Cache expired, continue to step 4
   ↓
4. If not exists OR expired:
   - Fetch fresh data from Google Sheets API
   - Store in cache with current timestamp
   - Return fresh data
```

### Code Implementation

```python
# Check cache first
cache_key = f"indicators_{country_code}"

if self._is_cache_valid(cache_key):
    logger.debug(f"Returning cached data for {country_code}")
    return self.cache[cache_key]  # Return cached data, skip API call

# Cache miss or expired - fetch fresh data
indicators = fetch_from_google_sheets()

# Store in cache
self.cache[cache_key] = indicators
self.cache_timestamps[cache_key] = datetime.now()

return indicators
```

### Cache Validation

```python
def _is_cache_valid(self, cache_key: str) -> bool:
    # Check if cache entry exists
    if cache_key not in self.cache:
        return False
    
    # Check if timestamp exists
    timestamp = self.cache_timestamps.get(cache_key)
    if not timestamp:
        return False
    
    # Check if cache is still fresh (less than TTL seconds old)
    age_in_seconds = (datetime.now() - timestamp).total_seconds()
    return age_in_seconds < self.cache_ttl  # 30 seconds default
```

### Cache Bypass

**Force Refresh:**
- Add `?refresh=true` to API URL
- Backend clears cache for that country
- Forces fresh fetch from Google Sheets

```python
if force_refresh:
    # Clear cache for this country
    if cache_key in self.cache:
        del self.cache[cache_key]
    if cache_key in self.cache_timestamps:
        del self.cache_timestamps[cache_key]
    logger.info(f"🔄 Cache cleared for {country_code}, forcing fresh fetch")
```

---

## Frontend Caching (React Component)

### How It Works

**Location:** `src/components/Economies.jsx`

**Storage:**
- `fetchedCountriesRef`: Map storing country codes and timestamps
- Format: `Map<countryCode, timestamp>`
- Example: `{ 'US': 1703001234567, 'EUR': 1703001237890 }`

**Refetch Interval:**
- **Default:** 30 seconds
- **Purpose:** Prevent excessive API calls when switching between economies

### Cache Flow

```
1. User selects economy (e.g., switches to EUR)
   ↓
2. Check frontend cache: Was EUR fetched recently?
   ↓
3. If fetched within last 30 seconds:
   - Skip API call
   - Use existing data in state
   ↓
4. If not fetched OR more than 30 seconds ago:
   - Make API request to backend
   - Store timestamp in fetchedCountriesRef
   - Update state with new data
```

### Code Implementation

```javascript
// Check if we recently fetched this economy
const lastFetchTime = fetchedCountriesRef.current.get(selectedEconomy);
const now = Date.now();
const timeSinceLastFetch = lastFetchTime ? now - lastFetchTime : Infinity;
const REFETCH_INTERVAL = 30000; // 30 seconds

// Skip if recently fetched (unless forcing refresh)
if (!forceRefresh && lastFetchTime && timeSinceLastFetch < REFETCH_INTERVAL) {
  return; // Use cached data, don't make API call
}

// Fetch fresh data
const response = await fetch(apiUrl);

// Store timestamp
fetchedCountriesRef.current.set(selectedEconomy, now);
```

### Cache Bypass

**Force Refresh:**
- Add `?refresh=true` to page URL
- Frontend bypasses cache check
- Forces API request even if recently fetched

```javascript
const urlParams = new URLSearchParams(window.location.search);
const forceRefresh = urlParams.get('refresh') === 'true';

if (!forceRefresh && lastFetchTime && timeSinceLastFetch < REFETCH_INTERVAL) {
  return; // Skip if not forcing refresh
}
```

---

## Two-Layer Cache Interaction

### Example Scenario

**User switches from US → EUR → US:**

```
1. User selects US (first time)
   - Frontend: No cache → API request
   - Backend: No cache → Fetch from Google Sheets (takes 2 seconds)
   - Backend: Store in cache, return data
   - Frontend: Store timestamp, display data

2. User switches to EUR (within 30 seconds)
   - Frontend: No EUR cache → API request
   - Backend: No EUR cache → Fetch from Google Sheets (takes 2 seconds)
   - Backend: Store EUR in cache, return data
   - Frontend: Store EUR timestamp, display data

3. User switches back to US (within 30 seconds)
   - Frontend: US cache exists, but less than 30 seconds old → Skip API call
   - Uses existing data in React state (instant)

4. User switches to EUR again (after 35 seconds)
   - Frontend: EUR cache expired → API request
   - Backend: EUR cache still valid (only 35 seconds old, < 30s TTL... wait, that's wrong)
   - Actually: Backend cache is 30 seconds, so it's expired
   - Backend: Fetch fresh from Google Sheets
   - Frontend: Update timestamp, display fresh data
```

### Cache Timing Diagram

```
Time 0s:   User selects US
           ↓ Frontend: No cache → API call
           ↓ Backend: No cache → Google Sheets API (2s)
           ↓ Backend: Cache US (expires at 30s)
           ↓ Frontend: Cache US timestamp

Time 5s:   User switches to EUR
           ↓ Frontend: No EUR cache → API call
           ↓ Backend: No EUR cache → Google Sheets API (2s)
           ↓ Backend: Cache EUR (expires at 35s)
           ↓ Frontend: Cache EUR timestamp

Time 10s:  User switches back to US
           ↓ Frontend: US cache valid (10s < 30s) → Skip API
           ↓ Uses React state data (instant)

Time 40s:  User switches to EUR
           ↓ Frontend: EUR cache expired (35s > 30s) → API call
           ↓ Backend: EUR cache expired (35s > 30s) → Google Sheets API
           ↓ Backend: Cache EUR fresh (expires at 70s)
           ↓ Frontend: Update EUR timestamp
```

---

## Cache Benefits

### Performance
- **Reduced API Calls:** Google Sheets API calls are expensive (rate limits, latency)
- **Faster Response:** Cached data returns instantly
- **Lower Latency:** No network round-trip for cached data

### Cost Optimization
- **API Quota:** Google Sheets API has daily quotas
- **Rate Limits:** Prevents hitting rate limits
- **Server Load:** Reduces backend processing

### User Experience
- **Instant Updates:** Switching between recently-viewed economies is instant
- **Smooth Navigation:** No loading spinners for cached data
- **Fresh Data:** 30-second TTL ensures data is reasonably fresh

---

## Cache Invalidation

### Automatic Invalidation
- **Time-based:** Cache expires after TTL (30 seconds)
- **Automatic:** No manual intervention needed

### Manual Invalidation

**Backend:**
```bash
# Add ?refresh=true to API URL
GET /api/economy-indicators/US?refresh=true
```

**Frontend:**
```bash
# Add ?refresh=true to page URL
http://localhost:5173/dashboard?refresh=true
```

### When Cache Clears

**Backend Cache Clears:**
- After TTL expires (30 seconds)
- On server restart
- When `?refresh=true` is used

**Frontend Cache Clears:**
- After 30 seconds (refetch interval)
- On page refresh
- When `?refresh=true` is used

---

## Configuration

### Backend Cache TTL

**Environment Variable:**
```bash
GOOGLE_SHEETS_CACHE_TTL=30  # seconds
```

**Recommended Values:**
- **Development:** 30 seconds (frequent updates)
- **Production:** 60-120 seconds (balance freshness vs API limits)
- **Very Active Data:** 30 seconds (maximum freshness)

### Frontend Refetch Interval

**Hardcoded in Component:**
```javascript
const REFETCH_INTERVAL = 30000; // 30 seconds
```

**To Change:**
- Edit `src/components/Economies.jsx`
- Modify `REFETCH_INTERVAL` constant

---

## Cache Statistics

### What Gets Cached

**Backend Caches:**
- Full indicator data for each country
- Includes: currentValue, chartData, chartDates, metadata
- Key: `indicators_{country_code}`

**Frontend Caches:**
- Timestamp of last fetch per country
- Key: Country code (US, EUR, GBP, JPY)
- Value: Timestamp (milliseconds since epoch)

### Cache Size

**Backend:**
- In-memory dictionary
- Typically small (< 1MB for all countries)
- Cleared on server restart

**Frontend:**
- Map with 4 entries (one per country)
- Minimal memory footprint (< 1KB)

---

## Troubleshooting

### Issue: Data Not Updating

**Symptoms:** Changes in Google Sheets don't appear

**Solutions:**
1. Wait 30 seconds for cache to expire
2. Use `?refresh=true` to force refresh
3. Restart backend server to clear cache
4. Hard refresh browser (Cmd+Shift+R)

### Issue: Too Many API Calls

**Symptoms:** Hitting Google Sheets API rate limits

**Solutions:**
1. Increase `GOOGLE_SHEETS_CACHE_TTL` (e.g., 60-120 seconds)
2. Increase frontend `REFETCH_INTERVAL` (e.g., 60 seconds)
3. Check for unnecessary refreshes

### Issue: Stale Data

**Symptoms:** Data seems outdated

**Solutions:**
1. Decrease `GOOGLE_SHEETS_CACHE_TTL` (e.g., 15-30 seconds)
2. Decrease frontend `REFETCH_INTERVAL`
3. Use `?refresh=true` for immediate updates

---

## Summary

**Backend Cache:**
- ✅ Stores Google Sheets API responses
- ✅ 30-second TTL (configurable)
- ✅ Reduces API calls to Google Sheets
- ✅ Can be bypassed with `?refresh=true`

**Frontend Cache:**
- ✅ Prevents duplicate API requests
- ✅ 30-second refetch interval
- ✅ Uses React refs (persists during component lifetime)
- ✅ Can be bypassed with `?refresh=true`

**Together:**
- ✅ Optimize performance
- ✅ Reduce API costs
- ✅ Improve user experience
- ✅ Balance freshness with efficiency

The caching system ensures that data is fresh enough for real-time updates while preventing excessive API calls and providing fast, responsive user experience.

