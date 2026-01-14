# Prediction Markets Hybrid API Implementation Plan

## Overview

Implement hybrid approach for prediction markets:
- **Polymarket CLOB API (Direct)** - Primary source for Polymarket markets
- **DOME API** - Secondary source for Kalshi markets (only accessible option from UAE)

## Goals

1. **Increase Data Volume:** Fetch 1,000 markets per request (vs 100 with DOME)
2. **Remove Rate Limit Restrictions:** No 10 req/10sec limit for Polymarket
3. **Better Forex Coverage:** Expected 6.4% forex-relevant (vs 0.6% with DOME)
4. **Maintain Kalshi Access:** Keep DOME API for Kalshi (only option)
5. **Backward Compatibility:** Keep DOME API as fallback option

---

## Implementation Plan

### Phase 1: Add Direct Polymarket CLOB Fetcher

**File:** `backend/services/prediction_markets_service.py`

**New Method:** `_fetch_polymarket_clob_direct()`
- Fetch directly from `https://clob.polymarket.com/markets`
- Support pagination with cursor
- Handle rate limiting (respectful delays, no strict limits)
- Return raw market data

**Key Features:**
- Fetch 1,000 markets per request (vs 100 with DOME)
- Use cursor-based pagination
- Add 0.5-1 second delay between requests (respectful)
- Handle errors gracefully

### Phase 2: Update Service Architecture

**Changes to `PredictionMarketsService`:**

1. **Add Configuration:**
   ```python
   self.use_direct_clob = os.getenv('USE_DIRECT_CLOB', 'true').lower() == 'true'
   ```

2. **Update `_fetch_polymarket_markets()`:**
   - Check `use_direct_clob` flag
   - If True: Use `_fetch_polymarket_clob_direct()`
   - If False: Use existing DOME API method (fallback)

3. **Keep DOME API for Kalshi:**
   - Continue using `_fetch_kalshi_markets()` via DOME API
   - No changes needed (only option from UAE)

### Phase 3: Update Data Normalization

**New Method:** `_normalize_clob_market_data()`
- Handle CLOB API data structure differences:
  - Uses `question` instead of `title`
  - Uses `tokens` array for prices
  - Uses `end_date_iso` for resolution dates
  - Uses `condition_id` for market ID

**Key Differences:**
- CLOB: `question` field
- CLOB: `tokens` array with `outcome` and `price`
- CLOB: `end_date_iso` (ISO string)
- CLOB: `active`, `closed`, `archived` boolean fields

### Phase 4: Update Filtering Logic

**Changes to `_filter_economic_markets()`:**
- Handle both DOME and CLOB data structures
- Check for `question` or `title` field
- Extract prices from `tokens` array or `side_a`/`side_b`
- Parse dates from `end_date_iso` or Unix timestamps

### Phase 5: Add Configuration & Environment Variables

**New Environment Variables:**
- `USE_DIRECT_CLOB=true` - Enable direct CLOB API (default: true)
- `CLOB_MAX_PAGES=3` - Max pages to fetch from CLOB (default: 3 = 3,000 markets)
- `CLOB_REQUEST_DELAY=0.5` - Delay between CLOB requests (default: 0.5s)

**Keep Existing:**
- `DOME_API_KEY` - Still needed for Kalshi
- `FETCH_MARKET_PRICES` - Still applies

### Phase 6: Testing & Validation

**Test Cases:**
1. Fetch Polymarket markets via CLOB (direct)
2. Fetch Kalshi markets via DOME API
3. Combine both sources
4. Verify filtering works with both structures
5. Verify normalization produces consistent output
6. Test fallback to DOME if CLOB fails

---

## Implementation Details

### CLOB API Data Structure

```json
{
  "data": [
    {
      "question": "Will the Fed raise rates...",
      "description": "...",
      "condition_id": "0x...",
      "active": true,
      "closed": false,
      "archived": false,
      "accepting_orders": true,
      "end_date_iso": "2024-02-01T00:00:00Z",
      "tokens": [
        {"outcome": "Yes", "price": 0.65},
        {"outcome": "No", "price": 0.35}
      ],
      "tags": ["politics", "economics"]
    }
  ],
  "next_cursor": "...",
  "limit": 1000,
  "count": 1000
}
```

### Normalization Mapping

| CLOB Field | DOME Field | Our Field |
|------------|------------|-----------|
| `question` | `title` | `question` |
| `tokens[0].price` | `side_a.price` | `yes_price` |
| `tokens[1].price` | `side_b.price` | `no_price` |
| `end_date_iso` | `end_time` (Unix) | `resolution_date` |
| `condition_id` | `condition_id` | `id` |
| `active` | `status == "open"` | `active` |
| `closed` | `status == "closed"` | `closed` |

### Price Extraction Logic

**CLOB API:**
```python
def extract_clob_prices(tokens):
    yes_price = None
    no_price = None
    
    for token in tokens:
        outcome = token.get("outcome", "").lower()
        price = token.get("price", 0)
        
        if "yes" in outcome:
            yes_price = float(price)
        elif "no" in outcome:
            no_price = float(price)
    
    # Normalize to sum to 1.0
    if yes_price is not None and no_price is not None:
        total = yes_price + no_price
        if total > 0:
            yes_price = yes_price / total
            no_price = no_price / total
    
    return yes_price, no_price
```

---

## Migration Strategy

### Step 1: Add CLOB Fetcher (Non-Breaking)
- Add new method alongside existing DOME method
- Don't change existing behavior yet
- Test CLOB fetcher independently

### Step 2: Add Configuration Flag
- Add `USE_DIRECT_CLOB` environment variable
- Default to `true` (use CLOB)
- Allow fallback to DOME if needed

### Step 3: Update Service Logic
- Check flag in `_fetch_polymarket_markets()`
- Route to appropriate fetcher
- Keep DOME method as fallback

### Step 4: Update Normalization
- Add CLOB-specific normalization
- Detect data source and normalize accordingly
- Ensure consistent output format

### Step 5: Test & Deploy
- Test with production-like data
- Verify filtering works correctly
- Monitor for errors
- Deploy gradually

---

## Expected Improvements

### Data Volume
- **Before:** ~200 markets per refresh (DOME free tier: 2 pages × 100)
- **After:** ~3,000 markets per refresh (CLOB: 3 pages × 1,000)
- **Improvement:** 15x more markets

### Forex Coverage
- **Before:** ~12 forex-relevant markets (0.6% of 2,000)
- **After:** ~192 forex-relevant markets (6.4% of 3,000)
- **Improvement:** 16x more forex-relevant markets

### Refresh Speed
- **Before:** Limited by 10 req/10sec rate limit
- **After:** Can refresh every 1-2 minutes (no strict limits)
- **Improvement:** Much faster refresh capability

### Rate Limit Behavior
- **Before:** 10 requests per 10 seconds (very restrictive)
- **After:** No strict limits (respectful delays only)
- **Improvement:** No rate limit bottlenecks

---

## Risk Mitigation

### Risk 1: CLOB API Changes Structure
**Mitigation:**
- Keep DOME API as fallback
- Add error handling
- Log structure changes
- Test regularly

### Risk 2: CLOB API Rate Limits
**Mitigation:**
- Add respectful delays (0.5-1s)
- Monitor for 429 errors
- Fallback to DOME if rate limited
- Implement exponential backoff

### Risk 3: Data Quality Differences
**Mitigation:**
- Normalize both sources to same format
- Test filtering with both structures
- Verify output consistency
- Monitor data quality metrics

---

## Success Metrics

### Quantitative
- Markets fetched per refresh: Target 3,000+
- Forex-relevant markets: Target 150-200+
- Refresh frequency: Can refresh every 1-2 minutes
- Error rate: <1%

### Qualitative
- Consistent data structure
- No breaking changes
- Backward compatible
- Easy to maintain

---

## Timeline

1. **Phase 1-2:** Add CLOB fetcher and update service (1-2 hours)
2. **Phase 3-4:** Update normalization and filtering (1-2 hours)
3. **Phase 5:** Add configuration (30 minutes)
4. **Phase 6:** Testing and validation (1-2 hours)

**Total Estimated Time:** 3-6 hours

---

## Next Steps

1. ✅ Create implementation plan (this document)
2. ⏭️ Add `_fetch_polymarket_clob_direct()` method
3. ⏭️ Update service to use hybrid approach
4. ⏭️ Add CLOB normalization logic
5. ⏭️ Update filtering for both structures
6. ⏭️ Add configuration flags
7. ⏭️ Test implementation
8. ⏭️ Deploy and monitor

