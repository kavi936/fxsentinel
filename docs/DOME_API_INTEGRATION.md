# Dome API Integration for Prediction Markets

## Overview

The prediction markets service has been updated to use the Dome API instead of directly accessing the Polymarket CLOB API. This provides better rate limiting, more structured data, and access to additional features.

## Changes Made

### 1. Environment Configuration
- Added `DOME_API_KEY` to `backend/env.example.secure`
- Service loads API key from environment variables on initialization

### 2. Dependencies
- Added `dome-api-sdk>=1.0.0` to `backend/requirements.txt`
- Service uses SDK with fallback to direct HTTP requests if SDK not available

### 3. Service Updates (`backend/services/prediction_markets_service.py`)

#### API Integration
- **`_fetch_polymarket_markets()`**: Updated to use Dome API SDK
  - Uses `DomeClient` from `dome_api_sdk` package
  - Calls `dome_client.polymarket.markets.get_markets()`
  - Implements pagination with `limit` and `offset` parameters
  - Fetches up to 5000 markets (50 pages × 100 markets per page)
  - Falls back to direct HTTP requests if SDK not available

#### Data Structure Handling
- **`_filter_economic_markets()`**: Updated to work with Dome API structure
  - Uses `title` instead of `question`
  - Uses `status` field ("open"/"closed") instead of boolean `active`/`closed`
  - Handles Unix timestamp `end_time` instead of ISO date strings
  - Extracts volume data directly from API response

#### Price Extraction
- **`_extract_prices_from_dome_market()`**: New method to extract prices
  - Handles `side_a` and `side_b` structure with token IDs
  - Attempts to fetch prices via `_fetch_token_price()` method
  - Falls back to 50/50 for open markets if prices unavailable
  - Uses `winning_side` for resolved markets

- **`_fetch_token_price()`**: New method to fetch individual token prices
  - Uses SDK: `dome_client.polymarket.markets.get_market_price()`
  - Falls back to direct HTTP requests if SDK not available
  - Handles cases where price endpoint may not be available
  - Returns `None` if prices cannot be fetched

#### Data Normalization
- **`_normalize_market_data()`**: Updated to map Dome API fields
  - Maps `title` → `question`
  - Converts Unix timestamps to ISO format
  - Extracts volume data from `volume_total` or `volume_1_week`
  - Handles `side_a`/`side_b` structure for price extraction

## API Differences

### Polymarket CLOB API (Old)
```json
{
  "question": "Will the Fed...",
  "active": true,
  "closed": false,
  "end_date_iso": "2024-01-15T00:00:00Z",
  "tokens": [
    {"outcome": "Yes", "price": 0.65},
    {"outcome": "No", "price": 0.35}
  ]
}
```

### Dome API (New)
```json
{
  "title": "Will the Fed...",
  "status": "open",
  "end_time": 1705276800,
  "side_a": {"id": "...", "label": "Yes"},
  "side_b": {"id": "...", "label": "No"},
  "volume_total": 12345.67,
  "winning_side": null
}
```

## Configuration

### Required Environment Variable
```bash
DOME_API_KEY=your_dome_api_key_here
```

### Setting Up
1. Install the Dome API SDK:
   ```bash
   pip install dome-api-sdk
   ```
   Or install all requirements:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Add `DOME_API_KEY` to your `.env` file in the `backend/` directory:
   ```bash
   DOME_API_KEY=your_dome_api_key_here
   ```

3. For production (Railway), add the variable in Railway dashboard

4. Restart the backend service

**Note:** The service will automatically fall back to direct HTTP requests if the SDK is not installed, but using the SDK is recommended for better error handling and maintainability.

## Testing

### Test the Integration
1. Set `DOME_API_KEY` in your environment
2. Make a request to `/api/prediction-markets?refresh=true`
3. Check logs for:
   - "Fetching fresh prediction markets data from Dome API"
   - Number of markets fetched
   - Any API errors

### Expected Behavior
- Service fetches markets from Dome API
- Filters for economic/forex relevance
- Returns normalized market data
- Falls back to cached data if API fails
- Uses 50/50 price fallback if prices unavailable

## Known Limitations

### Price Fetching
- Current implementation attempts to fetch prices but may fall back to 50/50 for open markets
- Price endpoint structure may need adjustment based on actual Dome API documentation
- Resolved markets use `winning_side` to determine final prices

### Rate Limiting
- Dome API has tiered rate limits (Free: 1 QPS, Dev: 100 QPS)
- Current implementation fetches prices individually (may hit rate limits)
- Consider batching price requests if available in Dome API

## Future Improvements

1. **Price Fetching Optimization**
   - Investigate batch price endpoints
   - Cache prices separately
   - Use WebSocket for real-time prices if available

2. **Error Handling**
   - Better handling of rate limit errors
   - Retry logic with exponential backoff
   - Graceful degradation when API is unavailable

3. **Data Enrichment**
   - Use volume data for market prioritization
   - Add liquidity metrics if available
   - Include market images from Dome API response

## Troubleshooting

### No Markets Returned
- Check `DOME_API_KEY` is set correctly
- Verify API key has proper permissions
- Check backend logs for API errors
- Test API key with curl command

### Prices Show as 50/50
- Price fetching may not be working
- Check if price endpoint structure is correct
- Verify token IDs are valid
- Consider using fallback logic until prices can be fetched

### Rate Limit Errors
- Reduce number of markets fetched
- Increase cache expiration time
- Consider upgrading Dome API tier
- Implement request throttling

## Migration Notes

- Old cache files will be invalidated on first refresh
- No frontend changes required (data format is normalized)
- Existing filtering logic remains the same
- Volume data is now available (previously was None)

