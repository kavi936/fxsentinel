# Prediction Markets API Decision Guide

## Test Results Summary

Based on comprehensive testing of available prediction market APIs, here are the findings and recommendations for implementing the Prediction Markets card in FXSentinel.

---

## API Test Results

### ✅ Polymarket - RECOMMENDED FOR MVP

**Status**: ✅ **Fully Accessible - No Authentication Required**

**Endpoints Available**:
1. **CLOB API**: `https://clob.polymarket.com/markets`
   - Returns paginated market data (1000 markets per page)
   - Includes: question, description, active status, condition_id, order book data
   - **Total Markets Found**: 5000+ (tested first 5 pages)

2. **Gamma API**: `https://gamma-api.polymarket.com/markets`
   - Returns market metadata
   - Includes: question, category, liquidity, end date
   - **Total Markets Found**: 20+ (may be paginated)

**Currency-Related Markets Found**:
- **570 markets** from CLOB API (includes Fed, inflation, economic indicators)
- **4 markets** from Gamma API
- Many markets relate to:
  - Federal Reserve interest rate decisions
  - Inflation/CPI data
  - Economic indicators (GDP, employment)
  - Crypto prices (USD-denominated)

**Pros**:
- ✅ No authentication required for public data
- ✅ REST API (easy to integrate)
- ✅ Large number of markets
- ✅ Good coverage of economic events
- ✅ Real-time data available
- ✅ Well-structured JSON responses

**Cons**:
- ⚠️ Many markets are not directly forex-related (need filtering)
- ⚠️ Some false positives in keyword matching (e.g., "CAD" matches "Academy")
- ⚠️ Need to filter by relevance and liquidity

**Best Use Cases**:
- Federal Reserve interest rate predictions
- Inflation/CPI predictions
- Economic indicator forecasts
- Market sentiment around economic events

---

### ⚠️ Kalshi - Requires Setup

**Status**: ⚠️ **Requires Authentication**

**Findings**:
- API endpoint: `https://api.kalshi.com/trade-api/v2`
- All tested endpoints returned authentication errors or connection issues
- Requires:
  - Account registration
  - API key generation
  - RSA-PSS signature authentication (complex)

**Pros**:
- ✅ Official Python SDK available
- ✅ Well-documented REST API
- ✅ US-regulated platform
- ✅ Official support

**Cons**:
- ❌ Complex authentication (RSA-PSS)
- ❌ Requires account setup
- ❌ Cannot test without credentials
- ❌ More setup time required

**Best Use Cases**:
- Production use with official support
- When you need US-regulated data
- When you want official SDK support

---

### ❓ Unified APIs (Predexon, PolyRouter)

**Predexon**:
- Status: Endpoint accessible but requires authentication
- Documentation: https://docs.predexon.com
- Would need to contact for API access and pricing

**PolyRouter**:
- Status: Requires authentication
- Website: https://www.polyrouter.io
- Would need to contact for API access and pricing

**Best Use Cases**:
- When you need multiple platforms aggregated
- When you want normalized data across platforms
- If managing multiple APIs becomes burdensome

---

## Recommendation: Start with Polymarket

### Why Polymarket?

1. **Immediate Implementation**: No authentication required, can start building immediately
2. **Rich Economic Data**: Many markets related to Fed decisions, inflation, economic indicators
3. **Easy Integration**: Simple REST API, standard JSON responses
4. **Good Coverage**: 5000+ markets available
5. **Real-time Data**: Live market data accessible

### Implementation Strategy

#### Phase 1: MVP with Polymarket (Week 1-2)

**Backend Service** (`backend/services/prediction_markets_service.py`):
```python
# Fetch from Polymarket CLOB API
# Filter for relevant markets:
# - Federal Reserve decisions
# - Inflation/CPI data
# - Economic indicators
# - Filter by liquidity/volume
```

**Key Filters to Implement**:
1. **Economic Events**: Fed rate decisions, CPI releases, GDP data
2. **Liquidity Threshold**: Only show markets with sufficient liquidity
3. **Active Markets**: Only show markets that are currently active
4. **Time Filter**: Show markets resolving in next 1-4 weeks

**Data Points to Display**:
- Market question/title
- Current probability (Yes/No prices)
- Volume/Liquidity
- Resolution date
- Sentiment (bullish/bearish based on probability)

#### Phase 2: Enhanced Filtering (Week 3)

- Improve keyword matching (reduce false positives)
- Add sentiment analysis based on market probabilities
- Integrate with economic calendar (link markets to events)
- Add caching (5-10 minute intervals)

#### Phase 3: Additional Sources (Future)

- Add Kalshi if needed (after account setup)
- Consider unified APIs if scaling becomes an issue
- Add more platforms as they become available

---

## Simple Decision Tree

```
Do you want to start immediately?
├─ YES → Use Polymarket (no auth required)
└─ NO → Do you need official support?
    ├─ YES → Set up Kalshi account
    └─ NO → Consider unified APIs (Predexon/PolyRouter)
```

---

## Next Steps

### Immediate Actions (This Week)

1. **Create Backend Service**
   - File: `backend/services/prediction_markets_service.py`
   - Fetch from `https://clob.polymarket.com/markets`
   - Filter for economic/forex-related markets
   - Implement caching (10-minute intervals)

2. **Create API Endpoint**
   - File: `backend/app.py` (add new route)
   - Endpoint: `/api/prediction-markets`
   - Return filtered, normalized market data

3. **Test Market Filtering**
   - Focus on: Fed decisions, inflation, economic indicators
   - Filter by liquidity threshold
   - Test with real data

### Week 2 Actions

4. **Create Frontend Component**
   - Add card to `cards-grid-container-second`
   - Display markets with probabilities
   - Add refresh button
   - Show loading/error states

5. **Integrate with Existing Features**
   - Link to economic calendar events
   - Compare with market sentiment card
   - Use in AI analysis prompts

---

## Market Filtering Strategy

### High-Value Markets for FX Trading

1. **Federal Reserve Decisions**
   - Interest rate changes
   - FOMC meeting outcomes
   - Fed policy statements

2. **Economic Indicators**
   - CPI/Inflation data
   - GDP releases
   - Employment data (NFP)
   - Retail sales

3. **Central Bank Actions**
   - ECB decisions
   - Bank of England decisions
   - BOJ decisions

### Filtering Keywords (Refined)

**Primary Keywords**:
- "Federal Reserve", "Fed", "FOMC", "interest rate"
- "inflation", "CPI", "consumer price"
- "GDP", "gross domestic product"
- "employment", "non-farm payrolls", "NFP"
- "ECB", "European Central Bank"
- "Bank of England", "BOE"
- "Bank of Japan", "BOJ"

**Avoid False Positives**:
- "CAD" (matches "Academy" - use "Canadian dollar" instead)
- "Fed" (matches "Federal" in non-economic contexts - use "Federal Reserve" or "FOMC")
- "USD" (matches crypto prices - filter by category)

---

## Data Structure for Frontend

```json
{
  "status": "success",
  "data": {
    "markets": [
      {
        "id": "string",
        "platform": "polymarket",
        "question": "Will the Fed increase interest rates by 25 bps?",
        "category": "economic",
        "yes_price": 0.65,
        "no_price": 0.35,
        "liquidity": 12345,
        "volume": 50000,
        "resolution_date": "2024-02-01T00:00:00Z",
        "sentiment": "bullish",
        "relevance": "high",
        "related_event": "FOMC Meeting"
      }
    ],
    "summary": {
      "total_markets": 10,
      "last_updated": "2024-01-09T12:00:00Z"
    }
  }
}
```

---

## Conclusion

**RECOMMENDATION: Start with Polymarket**

Polymarket provides the best balance of:
- ✅ Ease of implementation (no auth required)
- ✅ Rich economic data (Fed, inflation, indicators)
- ✅ Large market coverage (5000+ markets)
- ✅ Real-time data access

You can build the MVP immediately and add Kalshi or unified APIs later if needed.

---

## Testing Scripts Created

1. `scripts/test_prediction_markets_apis.py` - Comprehensive API testing
2. `scripts/test_polymarket_endpoints.py` - Detailed endpoint testing
3. `scripts/find_currency_markets.py` - Market discovery and filtering
4. `scripts/test_predexon_api.py` - Unified API testing

All test results saved to `data/` directory.

