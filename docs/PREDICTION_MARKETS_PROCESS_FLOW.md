# Prediction Markets Process Flow

## Complete Process: From API Call to Display

### Overview
The prediction markets system uses a **hybrid approach**:
- **Polymarket**: Direct CLOB API (better rate limits, more data)
- **Kalshi**: DOME API (only option from UAE)

---

## Step-by-Step Process

### 1. **Service Initialization** (`PredictionMarketsService.__init__`)

**Location:** `backend/services/prediction_markets_service.py`

**What happens:**
- Reads configuration from environment variables:
  - `USE_DIRECT_CLOB=true` (default: use CLOB API for Polymarket)
  - `CLOB_MAX_PAGES=3` (max pages to fetch = 3,000 markets)
  - `DOME_API_KEY` (required for Kalshi)
- Determines tier (free vs paid) based on API key
- Sets up rate limiters and caching

**Configuration:**
```python
# Free Tier:
- Max 2 pages per platform (DOME API)
- Max 3 pages from CLOB (3,000 markets)
- 30-minute cache expiration
- No price fetching via API

# Paid Tier:
- More pages allowed
- 10-minute cache expiration
- Can fetch individual prices
```

---

### 2. **Market Fetching** (`_do_refresh()`)

**Location:** `backend/services/prediction_markets_service.py:1791`

**Process:**

#### 2a. **Polymarket Markets** (`_fetch_polymarket_markets()`)

**If `USE_DIRECT_CLOB=true` (default):**
- Calls `_fetch_polymarket_clob_direct()`
- **API Endpoint:** `https://clob.polymarket.com/markets`
- **Parameters:**
  - `limit=1000` (per request)
  - `cursor` (for pagination)
- **Rate Limiting:** 0.5s delay between requests
- **Early Stopping:** Stops at threshold (400 markets default)
- **Result:** ~1,000-3,000 raw markets

**If `USE_DIRECT_CLOB=false`:**
- Uses DOME API SDK or HTTP fallback
- **API Endpoint:** `https://api.domeapi.io/v1/markets`
- **Parameters:**
  - `limit=100` (per request)
  - `offset` (for pagination)
- **Rate Limiting:** 1 request/second (free tier)
- **Result:** ~200 raw markets (free tier)

#### 2b. **Kalshi Markets** (`_fetch_kalshi_markets()`)

- Always uses DOME API (only option from UAE)
- **API Endpoint:** `https://api.domeapi.io/v1/kalshi/markets`
- **Parameters:**
  - `limit=100` (per request)
  - `offset` (for pagination)
- **Rate Limiting:** 1 request/second (free tier)
- **Result:** ~200-400 raw markets (free tier)

**Combined Result:** ~1,400 raw markets (free tier)

---

### 3. **Data Normalization** (During Filtering)

**Location:** `_filter_economic_markets()` - happens inline

**What happens for each market:**

#### 3a. **Structure Detection**
- Detects if market is from CLOB API (`_source == "clob_direct"` or has `question` field)
- Detects platform (Polymarket vs Kalshi)

#### 3b. **Data Extraction**
- **Title/Question:**
  - CLOB: Uses `question` field
  - DOME: Uses `title` field
  - Removes "arch" prefix if present (archived markets)

- **Status:**
  - CLOB: Uses `active`, `closed`, `archived` (booleans or strings)
  - DOME: Uses `status` field ("open" or "closed")

- **Dates:**
  - CLOB: Uses `end_date_iso` (ISO string format)
  - DOME: Uses `end_time` or `close_time` (Unix timestamp)

- **Prices:**
  - CLOB: Extracted from `tokens` array
  - DOME: Extracted from `side_a`/`side_b` or `last_price`

---

### 4. **Filtering Process** (`_filter_economic_markets()`)

**Location:** `backend/services/prediction_markets_service.py:936`

**Filtering Steps (in order):**

#### Step 1: **Deduplication**
- Checks market ID (condition_id for Polymarket, market_ticker for Kalshi)
- Skips duplicates

#### Step 2: **Archived Markets**
- Filters out markets with `archived=True`
- Filters out markets with questions starting with "arch"

#### Step 3: **Resolved Markets**
- Checks `winning_side` (Polymarket) or `result` (Kalshi)
- Checks if token prices are 1.0/0.0 (resolved)
- **Skips ALL resolved markets** (no exceptions)

#### Step 4: **Closed Markets**
- Checks `closed=True` (CLOB) or `status="closed"` (DOME)
- **Skips ALL closed markets**

#### Step 5: **Date Filtering** ⚠️ **RELAXED FILTER**
- Checks `end_date_iso` (CLOB) or `end_time`/`close_time` (DOME)
- **Shows markets with:**
  - **Future resolution dates** (preferred)
  - **OR recently resolved** (within last 30 days)
- **Skips markets resolved more than 30 days ago**
- **Reason:** Most API markets are historical, so we show recent ones to ensure users see data

#### Step 6: **Economic Keywords**
- Searches title/question and tags for forex-relevant keywords:
  - **Central Banks:** Fed, FOMC, ECB, BOE, BOJ, RBA, RBNZ, BOC, SNB
  - **Economic Data:** CPI, inflation, GDP, employment, NFP, unemployment
  - **Forex Pairs:** EUR/USD, GBP/USD, USD/JPY, etc.
  - **Geopolitics:** Sanctions, Brexit, etc.

- **Scoring:**
  - High relevance: Multiple keywords + economic tags
  - Medium relevance: Single keyword match
  - Low relevance: Weak match

#### Step 7: **Price Availability**
- Checks if market has embedded prices (for free tier prioritization)
- CLOB: Checks `tokens[].price`
- DOME: Checks `side_a.price`, `side_b.price`, or `last_price`

**Result:** Only markets that pass ALL filters are included

---

### 5. **Currency Pair Mapping** (`_get_affected_currency_pairs()`)

**Location:** `backend/services/prediction_markets_service.py:829`

**Process:**
- Analyzes matched keywords
- Maps to affected currency pairs:
  - Fed/FOMC → USD pairs (EUR/USD, GBP/USD, USD/JPY, etc.)
  - ECB → EUR pairs (EUR/USD, EUR/GBP, EUR/JPY)
  - BOE → GBP pairs (GBP/USD, EUR/GBP, GBP/JPY)
  - CPI/GDP/NFP → USD pairs
  - etc.

**Result:** Each market gets `affected_currency_pairs` array

---

### 6. **Sorting** (Frontend)

**Location:** `src/components/Overview.jsx:3407`

**Sort Order:**
1. **Volume** (highest first)
2. **Accepting Orders** (active first)
3. **Future Markets** (future resolution dates first)

---

### 7. **Price Extraction** (`_normalize_market_data()`)

**Location:** `backend/services/prediction_markets_service.py:1840`

**For CLOB Markets:**
- Extracts prices from `tokens` array
- Identifies Yes/No outcomes
- Normalizes to sum to 1.0
- Returns `(yes_price, no_price, price_source)`

**For DOME Markets:**
- Extracts from `side_a`/`side_b` or `last_price`
- May fetch via API if `FETCH_MARKET_PRICES=true` (paid tier)
- Returns `(yes_price, no_price, price_source)`

**Price Sources:**
- `"resolved"`: Market is resolved (1.0/0.0)
- `"api"`: Fetched via API call
- `"embedded"`: From market data
- `"fallback"`: 50/50 estimate

---

### 8. **Caching**

**Location:** `PersistentPredictionMarketsCache`

**Process:**
- Saves filtered markets to Firebase
- Falls back to file cache if Firebase fails
- **TTL:** 30 minutes (free tier), 10 minutes (paid tier)
- Frontend requests refresh every 5 minutes

---

## Current Filtering Statistics

Based on test runs:
- **Raw Markets Fetched:** ~1,400 (1,000 Polymarket + 400 Kalshi)
- **After Filtering:** ~4-7 markets
- **Filtered Out:**
  - ~946 closed/resolved/old markets
  - ~196 markets without economic keywords
  - ~0 excluded by exclude list

**Why So Few Markets?**
1. **Date Filter:** Shows future markets OR recently resolved (within 30 days)
2. **Keyword Matching:** Only forex-relevant markets pass
3. **API Data:** Most markets in CLOB API are historical (checked 5,000 markets, found 0 active future)
4. **Kalshi Markets:** Most active markets come from Kalshi (via DOME API)

**Key Finding:**
- **CLOB API:** Returns mostly historical/closed markets (even in first 5,000)
- **Kalshi API:** Has more active markets with future dates
- **Solution:** Relaxed date filter to show recently resolved markets (within 30 days)

---

## Filtering Criteria Summary

### ✅ **Included Markets Must:**
- Have unique market ID
- Not be archived
- Not be resolved
- Not be closed
- Have **future** resolution date
- Match economic/forex keywords
- Have valid data structure

### ❌ **Excluded Markets:**
- Duplicates
- Archived markets
- Resolved markets (winning_side set or prices 1.0/0.0)
- Closed markets
- **Past due markets** (resolution date in past)
- Markets without economic keywords
- Markets with invalid data

---

## Debugging: Why No Markets Showing?

If you see "No Active Markets", check:

1. **Date Filtering Too Strict?**
   - Current: Only shows markets with **future** resolution dates
   - Many markets might have past dates
   - **Solution:** Could relax to show markets resolved within last 7 days

2. **Keyword Matching Too Strict?**
   - Only forex-relevant keywords pass
   - Many markets might not match
   - **Solution:** Could expand keyword list or lower relevance threshold

3. **All Markets Closed/Resolved?**
   - Most markets in API might be historical
   - **Solution:** Check API directly for active markets

4. **Cache Issue?**
   - Old cached data might be stale
   - **Solution:** Force refresh or clear cache

---

## API Response Examples

### CLOB API Market Structure:
```json
{
  "question": "Will the Fed increase interest rates by 25 bps?",
  "description": "...",
  "active": true,
  "closed": false,
  "archived": false,
  "end_date_iso": "2024-12-31T00:00:00Z",
  "tokens": [
    {"outcome": "Yes", "price": 0.65},
    {"outcome": "No", "price": 0.35}
  ],
  "condition_id": "0x...",
  "volume_total": 50000
}
```

### DOME API Market Structure:
```json
{
  "title": "Will the Fed increase interest rates?",
  "status": "open",
  "end_time": 1733011200,
  "side_a": {"price": 0.65},
  "side_b": {"price": 0.35},
  "volume_total": 50000,
  "tags": ["Economics", "Federal Reserve"]
}
```

---

## Recommendations

### To Show More Markets:

1. **Relax Date Filter:**
   - Show markets resolved within last 7-30 days (not just future)
   - Or show all active markets regardless of date

2. **Expand Keywords:**
   - Add more economic indicators
   - Lower relevance threshold

3. **Check API Directly:**
   - Verify active markets exist in API
   - Check if date filtering is too strict

4. **Add Debug Logging:**
   - Log why each market is filtered out
   - Track filtering statistics

---

## Next Steps

1. **Investigate Date Filtering:**
   - Check if many markets have past dates
   - Consider relaxing to show recently resolved markets

2. **Check API Data:**
   - Query CLOB API directly for active markets
   - Verify markets with future dates exist

3. **Add More Keywords:**
   - Expand economic keyword list
   - Include more forex-related terms

4. **Improve Logging:**
   - Add detailed filtering logs
   - Track why markets are excluded

