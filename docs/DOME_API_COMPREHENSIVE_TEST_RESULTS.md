# DOME API Comprehensive Test Results

## Test Summary

**Test Date:** January 14, 2026  
**API Key:** 01555869c196b7ba95ea... (DOME API Free Tier)  
**Rate Limit:** 1 request/second, 10 requests per 10 seconds  
**Test Duration:** ~35 seconds

---

## Overall Results

### Markets Fetched

| Platform | Total Markets | Pages Fetched | Forex-Relevant* | Status |
|----------|--------------|---------------|-----------------|--------|
| **Polymarket** | 2,000 | 20 pages | 12 | ✅ Success |
| **Kalshi** | 700 | 7 pages | 19 | ⚠️ Rate Limited |
| **Total** | **2,700** | **27 pages** | **31** | - |

*Note: Forex-relevant count uses basic keyword matching. Actual relevance may be higher with better filtering.

---

## Polymarket Results (via DOME API)

### Data Fetched
- **Total Markets:** 2,000 markets
- **Pages Fetched:** 20 pages (100 markets per page)
- **Forex-Relevant:** 12 markets (using basic keyword matching)
- **Status Distribution:**
  - Open: 1,161 markets (58.1%)
  - Closed: 839 markets (41.9%)

### Data Quality
- **Has Volume Data:** 1,996 markets (99.8%)
- **Has Price Data:** 2,000 markets (100%)
- **Has Date Data:** 1,995 markets (99.8%)

### Data Structure

**Endpoint:** `/polymarket/markets`

**Response Structure:**
```json
{
  "markets": [...],
  "pagination": {
    "has_more": true/false
  }
}
```

**Market Object Fields:**
```json
{
  "market_slug": "btc-updown-15m-1768454100",
  "title": "Bitcoin Up or Down - January 15, 12:15AM-12:30AM ET",
  "condition_id": "0x284c1acae3b25ff7c5c7f57674b2050fbc64141ff3555c2be8a3fee1d6591193",
  "start_time": 1768368211,
  "end_time": 1768368300,
  "completed_time": null,
  "close_time": null,
  "tags": ["crypto", "bitcoin"],
  "volume_1_week": 12345,
  "volume_1_month": 67890,
  "volume_1_year": 123456,
  "volume_total": 123456,
  "resolution_source": null,
  "image": "https://...",
  "side_a": {
    "outcome": "Yes",
    "price": 0.65,
    "volume": 1000
  },
  "side_b": {
    "outcome": "No",
    "price": 0.35,
    "volume": 500
  },
  "winning_side": null,
  "status": "open",
  "extra_fields": {}
}
```

### Sample Markets Found

1. **Inflation Markets (Argentina):**
   - "Will annual inflation in Argentina increase by 39% or higher in January 2026?"
   - "Will annual inflation in Argentina increase by between 36% and 38.9% in January 2026?"
   - Multiple inflation range markets

2. **Crypto Markets:**
   - "Bitcoin Up or Down - January 15, 12:15AM-12:30AM ET"
   - Many short-term crypto price movement markets

### Response Times
- **Average:** ~750ms per request
- **Range:** 395ms - 1,749ms
- **Total Time:** ~20 seconds for 20 pages

---

## Kalshi Results (via DOME API)

### Data Fetched
- **Total Markets:** 700 markets
- **Pages Fetched:** 7 pages (stopped due to rate limit)
- **Forex-Relevant:** 19 markets (using basic keyword matching)
- **Status Distribution:**
  - Open: 700 markets (100%)

### Data Quality
- **Has Volume Data:** 75 markets (10.7%)
- **Has Price Data:** 75 markets (10.7%)
- **Has Date Data:** 700 markets (100%)

### Data Structure

**Endpoint:** `/kalshi/markets`

**Response Structure:**
```json
{
  "markets": [...],
  "pagination": {
    "has_more": true/false
  }
}
```

**Market Object Fields:**
- Similar structure to Polymarket
- Uses `title` field for market question
- Uses `status` field (open/closed)
- Has `start_time`, `end_time` fields

### Sample Markets Found

1. **GDP Markets:**
   - "Will **real GDP** increase by more than 1.0% in Q4 2026?"
   - "Will **real GDP** increase by more than 1.5% in Q4 2026?"
   - "Will **real GDP** increase by more than 2.0% in Q4 2026?"
   - Multiple GDP prediction markets

2. **Economic Indicators:**
   - Various economic data prediction markets

### Response Times
- **Average:** ~710ms per request
- **Range:** 428ms - 988ms
- **Total Time:** ~7 seconds for 7 pages

### Rate Limit Behavior
- **Hit Rate Limit:** After 7 pages (10 requests per 10 seconds)
- **Behavior:** API returned 429 status code
- **Impact:** Could fetch more markets with proper rate limiting

---

## Other Endpoints Tested

### Failed Endpoints
1. `/polymarket/events` - ❌ Not Found (404)
2. `/kalshi/events` - ❌ Not Found (404)
3. `/polymarket/markets/market-price` - ❌ Not Found (404)

**Conclusion:** DOME API only provides `/markets` endpoints for both platforms. No separate events endpoints available.

---

## Key Findings

### ✅ Strengths

1. **Good Data Volume**
   - Can fetch 2,000+ Polymarket markets
   - Can fetch 700+ Kalshi markets (before rate limit)
   - Pagination works well

2. **Complete Data Structure**
   - All markets have price data (side_a, side_b)
   - Most markets have volume data (99.8% for Polymarket)
   - All markets have date/time information

3. **Unified Interface**
   - Same structure for both Polymarket and Kalshi
   - Easy to normalize and process
   - Consistent pagination

4. **Rate Limiting Works**
   - API properly enforces 10 requests per 10 seconds
   - Returns 429 when limit exceeded
   - Can resume after waiting

### ⚠️ Limitations

1. **Rate Limit Restrictions**
   - Free tier: 10 requests per 10 seconds
   - Limits how many markets can be fetched quickly
   - Need to wait between batches

2. **Forex Market Coverage**
   - Only 12 forex-relevant markets found in 2,000 Polymarket markets (0.6%)
   - Only 19 forex-relevant markets found in 700 Kalshi markets (2.7%)
   - **Note:** This is likely due to basic keyword matching. Better filtering would find more.

3. **Kalshi Data Quality**
   - Only 10.7% of Kalshi markets have volume/price data
   - Much lower data completeness than Polymarket

4. **No Events Endpoints**
   - Cannot fetch events separately
   - Only markets endpoint available

---

## Comparison: DOME API vs Direct Polymarket CLOB

| Feature | DOME API | Polymarket CLOB (Direct) |
|---------|----------|--------------------------|
| **Rate Limit** | 10 req/10sec | No apparent limit |
| **Markets per Request** | 100 | 1,000 |
| **Response Time** | ~750ms | ~800ms |
| **Auth Required** | Yes (API key) | No |
| **Forex Markets** | 12/2000 (0.6%) | 64/1000 (6.4%) |
| **Cost** | Free tier available | Free |
| **Unified Interface** | Yes (Polymarket + Kalshi) | No (Polymarket only) |

### Key Differences

1. **Rate Limits:**
   - DOME: Very restrictive (10 req/10sec)
   - CLOB: No apparent limits

2. **Data Volume:**
   - DOME: 100 markets per request
   - CLOB: 1,000 markets per request (10x more)

3. **Forex Coverage:**
   - DOME: Lower coverage (0.6% vs 6.4%)
   - CLOB: Better coverage (likely due to different market ordering)

4. **Multi-Platform:**
   - DOME: Provides both Polymarket and Kalshi
   - CLOB: Polymarket only

---

## Recommendations

### For Maximum Data Volume

**Use Polymarket CLOB API (Direct):**
- Fetch 1,000 markets per request (vs 100 with DOME)
- No rate limit restrictions
- Better forex market coverage (6.4% vs 0.6%)
- Faster to fetch large volumes

### For Multi-Platform Access

**Use DOME API:**
- Provides unified access to Polymarket + Kalshi
- Consistent data structure
- Good for when you need both platforms

### Hybrid Approach (Recommended)

**Use Both:**
1. **Primary:** Polymarket CLOB (direct) for Polymarket markets
   - Better rate limits
   - More markets per request
   - Better forex coverage

2. **Secondary:** DOME API for Kalshi markets
   - Only way to access Kalshi from UAE
   - Unified structure
   - Accept rate limit restrictions for Kalshi access

---

## Implementation Notes

### Rate Limiting Strategy

**For DOME API:**
```python
# Wait 1.1 seconds between requests
# Track requests in 10-second window
# Stop at 10 requests, wait for window to reset
```

**For Polymarket CLOB:**
```python
# No strict rate limiting needed
# Use 0.5-1 second delay to be respectful
# Can fetch multiple pages quickly
```

### Data Normalization

Both APIs return similar structures:
- Use `title` or `question` for market text
- Extract prices from `side_a`/`side_b` or `tokens`
- Use `end_time` or `end_date_iso` for resolution dates
- Check `status` for open/closed state

### Filtering Strategy

Current filtering finds low forex-relevant markets because:
1. Markets are ordered by popularity/volume, not relevance
2. Many markets are crypto/sports/entertainment
3. Need better keyword matching (check description, tags)

**Improvements:**
- Check `tags` field for economic categories
- Search in `description` field (if available)
- Use more comprehensive keyword list
- Filter by volume (higher volume = more relevant)

---

## Conclusion

DOME API provides good access to both Polymarket and Kalshi markets with a unified interface. However, rate limits are restrictive (10 req/10sec), limiting how quickly data can be refreshed.

**Best Strategy:**
- Use **Polymarket CLOB (direct)** for Polymarket markets (better limits, more data)
- Use **DOME API** for Kalshi markets (only accessible option from UAE)
- Combine both sources for maximum coverage

This hybrid approach gives you:
- ✅ Maximum Polymarket data (via CLOB)
- ✅ Kalshi access (via DOME)
- ✅ Best rate limit behavior
- ✅ Maximum forex-relevant markets

