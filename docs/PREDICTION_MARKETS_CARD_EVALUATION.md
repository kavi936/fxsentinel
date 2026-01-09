# Prediction Markets Card - Feature Evaluation

## Executive Summary

This document evaluates the feasibility and implementation approach for adding a "Prediction Markets" card to the Overview page that displays retail trader predictions for currency movements from platforms like Kalshi and Polymarket.

## 1. Feasibility Assessment

### API Availability ✅

**Kalshi API:**
- REST API available for market data access
- Provides order books, market statistics, trades, and portfolios
- Requires API authentication (API keys + RSA-PSS signatures)
- Official Python SDK available
- Documentation: https://docs.kalshi.com
- **Test Result**: Requires account setup and authentication - cannot test without credentials

**Polymarket API:**
- ✅ **REST API accessible** - No authentication required for public data
- ✅ **CLOB API**: `https://clob.polymarket.com/markets` - Returns 1000+ markets per page
- ✅ **Gamma API**: `https://gamma-api.polymarket.com/markets` - Returns market metadata
- ✅ **Test Result**: Successfully fetched 5,000+ markets, found 570+ economic-related markets
- ✅ **Ready to use immediately** - No setup required
- Documentation: https://docs.polymarket.com

**Unified API Options:**
- **Predexon**: Unified API for prediction market data, aggregates Polymarket and Kalshi data
  - Cross-platform market matching
  - Single API key access
  - Documentation: https://docs.predexon.com

- **PolyRouter**: Standardized interface for normalized prediction market data
  - Supports Kalshi, Polymarket, and others
  - Single API key
  - Website: https://www.polyrouter.io

- **Dome**: Unified API for prediction markets
  - Live and historical data across multiple platforms
  - YC-backed company

### Technical Feasibility: HIGH

Both platforms and unified APIs are accessible, making integration technically feasible.

## 2. Current Architecture Analysis

### Existing Card Patterns

The Overview page follows a consistent card structure:
- `cards-grid-container` and `cards-grid-container-second` for layout
- Cards include:
  - Header with title and InfoIcon
  - Controls (refresh buttons, filters)
  - Content sections with data visualization
  - Loading and error states

### Existing Data Fetching Patterns

Current backend endpoints follow this pattern:
- `/api/market-sentiment` - Market sentiment analysis
- `/api/forex-prices` - Real-time forex prices
- `/api/economic-calendar` - Economic calendar events
- `/api/economy-indicators/<country>` - Economic indicators

All endpoints:
- Handle CORS preflight requests
- Return JSON with status/data structure
- Include error handling and fallback mechanisms
- Support caching strategies

### Frontend Data Fetching

Frontend uses:
- Custom hooks (`useForexPrices`, `useMarketSentiment`)
- Config-based endpoint management (`src/config.js`)
- React state management with loading/error states
- Automatic refresh capabilities

## 3. Implementation Approach

### Recommended Architecture

**Option A: Direct API Integration (Per Platform)**
```
Frontend → Backend Endpoint → Kalshi/Polymarket APIs → Response
```
- Pros: Direct control, no third-party dependencies
- Cons: Multiple API integrations, more maintenance

**Option B: Unified API Integration**
```
Frontend → Backend Endpoint → Predexon/PolyRouter → Multiple Platforms → Response
```
- Pros: Single integration point, normalized data format
- Cons: Additional third-party dependency, potential cost

**Recommendation: Start with Polymarket (Direct Integration)**
- ✅ **No authentication required** - Can start building immediately
- ✅ **5,000+ markets available** - Rich economic data (Fed, inflation, indicators)
- ✅ **REST API** - Easy integration with existing Python `requests` library
- ✅ **Tested and working** - Successfully fetched real market data
- Can add Kalshi or unified APIs later if needed

### Data Structure Considerations

**Prediction Market Data Points:**
1. **Market Information**
   - Market ID/Title
   - Currency pair (e.g., "EUR/USD will be above 1.10")
   - Resolution date/time
   - Current probability/price

2. **Market Statistics**
   - Total volume
   - Open interest
   - Yes/No prices
   - Last trade price

3. **Sentiment Indicators**
   - Retail bias (bullish/bearish)
   - Confidence level (based on volume/liquidity)
   - Time to resolution

**Filtering Strategy:**
- Filter markets by currency pairs (EUR, USD, GBP, JPY, etc.)
- Filter by resolution timeframe (near-term: 1-7 days, medium-term: 1-4 weeks)
- Prioritize markets with higher volume/liquidity
- Focus on directional markets (price above/below thresholds)

### Backend Endpoint Design

**Proposed Endpoint:** `/api/prediction-markets`

**Query Parameters:**
- `refresh` (optional): Force refresh cache
- `currency` (optional): Filter by currency (EUR, USD, GBP, JPY)
- `timeframe` (optional): Filter by resolution timeframe

**Response Structure:**
```json
{
  "status": "success",
  "data": {
    "markets": [
      {
        "id": "string",
        "platform": "kalshi" | "polymarket",
        "title": "string",
        "currency_pair": "EUR/USD",
        "question": "EUR/USD will be above 1.10 by Dec 31",
        "resolution_date": "ISO8601",
        "yes_price": 0.65,
        "no_price": 0.35,
        "volume": 12345,
        "sentiment": "bullish" | "bearish" | "neutral",
        "confidence": 0.85,
        "last_updated": "ISO8601"
      }
    ],
    "summary": {
      "total_markets": 10,
      "platforms": ["kalshi", "polymarket"],
      "last_updated": "ISO8601"
    }
  }
}
```

### Frontend Component Structure

**Component Location:** Add to `cards-grid-container-second` alongside Market Sentiment

**Component Features:**
1. **Header Section**
   - Title: "PREDICTION MARKETS"
   - InfoIcon with tooltip explaining what prediction markets represent
   - Refresh button

2. **Market List Display**
   - Grouped by currency pair
   - Show probability bars (Yes/No prices)
   - Display volume and sentiment indicators
   - Color coding: Green (bullish), Red (bearish), Gray (neutral)

3. **Filters**
   - Currency filter (EUR, USD, GBP, JPY, etc.)
   - Timeframe filter (Near-term, Medium-term)
   - Sort by volume, time to resolution, or sentiment

4. **Empty/Loading States**
   - Loading spinner during fetch
   - Empty state if no markets available
   - Error state with retry button

## 4. Challenges and Solutions

### Challenge 1: Currency Market Filtering

**Problem:** Prediction markets may not always have direct currency pair markets. Markets might be:
- Event-based (e.g., "Fed will raise rates")
- Outcome-based (e.g., "EUR will strengthen")
- Price-threshold based (e.g., "EUR/USD > 1.10")

**Solution:**
- Implement keyword-based filtering
- Map economic events to relevant markets
- Use natural language processing to identify currency-related markets
- Focus on markets with clear currency implications

### Challenge 2: Data Normalization

**Problem:** Kalshi and Polymarket have different data structures

**Solution:**
- Create a unified data model in backend
- Transform platform-specific responses to common format
- Handle missing fields gracefully
- Use adapter pattern for each platform

### Challenge 3: Rate Limiting

**Problem:** API rate limits may restrict frequent updates

**Solution:**
- Implement caching (similar to other endpoints)
- Use reasonable refresh intervals (5-15 minutes)
- Cache in backend to share across users
- Implement exponential backoff for rate limit errors

### Challenge 4: Regulatory Considerations

**Problem:** Prediction markets have varying legal status

**Solution:**
- Display data for informational purposes only
- Add disclaimers about data source
- Ensure compliance with terms of service
- Consider geoblocking if necessary

### Challenge 5: Data Quality and Relevance

**Problem:** Not all markets are relevant or have sufficient liquidity

**Solution:**
- Filter by minimum volume threshold
- Prioritize markets with clear currency implications
- Show confidence indicators based on liquidity
- Allow users to filter by relevance

## 5. Value Proposition

### Benefits for Users

1. **Retail Sentiment Insight**: See what retail traders are betting on, separate from institutional sentiment
2. **Crowd Wisdom**: Leverage collective predictions from active traders
3. **Alternative Data Source**: Complement existing technical and fundamental analysis
4. **Contrarian Indicators**: Identify when retail sentiment diverges from market sentiment

### Integration with Existing Features

- **Market Sentiment Card**: Compare prediction market sentiment with technical sentiment
- **Economic Calendar**: Link prediction markets to upcoming economic events
- **Live News Feed**: Show how news events correlate with prediction market movements

### Potential Use Cases

1. **Pre-Event Analysis**: Check prediction markets before major economic releases
2. **Sentiment Divergence**: Identify when retail prediction differs from technical indicators
3. **Risk Assessment**: Use prediction market probabilities as risk indicators
4. **Market Timing**: Consider prediction market signals for entry/exit timing

## 6. Implementation Phases

### Phase 1: MVP (Minimum Viable Product) - ✅ READY TO START
- **Polymarket integration** - ✅ Tested and working, no auth required
- Basic market listing with key data points (Fed decisions, inflation, economic indicators)
- Filtering by economic relevance (Fed, inflation, GDP, employment)
- Filter by liquidity threshold and active status
- Basic UI card matching existing design patterns
- **Timeline**: Can be implemented this week

### Phase 2: Enhanced Features
- Add second platform (Kalshi)
- Advanced filtering and sorting
- Sentiment aggregation across platforms
- Historical trend display

### Phase 3: Advanced Features
- Integration with economic calendar events
- Comparison with market sentiment card
- Alert system for significant prediction shifts
- Detailed market analysis popup

## 7. Technical Requirements

### Backend Requirements
- New service module: `backend/services/prediction_markets_service.py`
- API key management for Kalshi/Polymarket
- Caching mechanism (similar to market sentiment)
- Error handling and fallback logic

### Frontend Requirements
- New component or section in Overview.jsx
- Custom hook: `usePredictionMarkets` (optional)
- CSS styling matching existing card designs
- Config endpoint addition

### Dependencies
- Backend: `requests` library (likely already present)
- Optional: GraphQL client for Polymarket (if using GraphQL)
- No new frontend dependencies required

## 8. Recommendations

### Immediate Actions

1. **Start with Polymarket API**
   - Better API documentation available
   - More active markets potentially
   - Can validate concept before adding complexity

2. **Implement Backend Endpoint First**
   - Create `/api/prediction-markets` endpoint
   - Test API connectivity and data extraction
   - Implement filtering and normalization

3. **Design Data Model**
   - Define unified data structure
   - Identify required vs optional fields
   - Plan for multi-platform expansion

4. **Prototype Frontend Component**
   - Add card to Overview page
   - Implement basic market listing
   - Test with real API data

### Long-term Considerations

1. **Data Aggregation**: Consider unified APIs if maintaining multiple integrations becomes burdensome
2. **Machine Learning**: Potentially use prediction market data to improve sentiment analysis
3. **Historical Analysis**: Store historical prediction market data for trend analysis
4. **User Preferences**: Allow users to customize which markets/platforms to display

## 9. Risk Assessment

### Low Risk
- Technical implementation (APIs are available)
- UI/UX design (following existing patterns)
- Backend architecture (consistent with current approach)

### Medium Risk
- Data quality and relevance (requires careful filtering)
- API rate limits (need caching strategy)
- Legal/regulatory compliance (informational use should be fine)

### High Risk
- API stability and availability (third-party dependency)
- Market liquidity (some markets may have low volume)
- User value perception (need to validate user interest)

## 10. Success Metrics

### Quantitative Metrics
- Number of markets displayed
- API response times
- Cache hit rates
- User engagement (clicks, time spent)

### Qualitative Metrics
- User feedback on value
- Accuracy of predictions vs actual outcomes
- Integration with other data sources
- Overall user experience

## Conclusion

The Prediction Markets card is **technically feasible** and **strategically valuable**. It provides a unique data source that complements existing features. The implementation should start with a single platform (Polymarket) as an MVP, then expand based on user feedback and data quality.

The main challenges are filtering relevant markets and normalizing data across platforms, but both are solvable with careful implementation. The feature aligns well with the existing architecture and would enhance the Overview page's value proposition.

**Recommendation: PROCEED with Phase 1 (MVP) implementation.**

