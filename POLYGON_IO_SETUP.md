# Polygon.io API Setup Guide

## Getting Your Polygon.io API Key

1. **Visit Polygon.io**: Go to https://polygon.io/
2. **Sign Up**: Create an account
3. **Choose Plan**: Select the Basic plan ($29/month) for stocks, or upgrade to Basic + Currencies ($50/month) for forex data:
   - **Basic Plan ($29/month)**: Stocks data only
   - **Basic + Currencies ($50/month)**: Stocks + Forex data
   - 100 API calls per day
   - 5 calls per minute
   - Real-time forex data (with Currencies add-on)
   - Historical data access
4. **Get API Key**: Your API key will be provided in your dashboard

## Setting Up the API Key

### Backend Setup
1. **Edit Environment File**: Create or update `.env` file in the `backend/` directory:
   ```env
   POLYGON_API_KEY=your_actual_polygon_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```
   
   **Note**: You need the Basic + Currencies plan ($50/month) to access forex data.

### Frontend Setup (if needed)
1. **Edit Environment File**: Create or update `.env` file in the root directory:
   ```env
   VITE_POLYGON_API_KEY=your_actual_polygon_api_key_here
   VITE_API_URL=http://localhost:8000
   ```

## How It Works

- **Real-time Data**: The app fetches live forex prices from Polygon.io
- **Rate Limiting**: API calls are limited to 5 per minute and 100 per day
- **Fallback Logic**: If API fails or rate limit exceeded, it uses manual time-based logic
- **Visual Indicators**: 
  - 📡 = Using Polygon.io data
  - ⚙️ = Using manual fallback

## API Endpoints Used

### Forex Snapshot API
- **URL**: `https://api.polygon.io/v2/snapshot/locale/global/markets/forex/tickers/{ticker}`
- **Tickers**: 
  - `C:EURUSD` (EUR/USD)
  - `C:USDJPY` (USD/JPY) 
  - `C:GBPUSD` (GBP/USD)
- **Response**: JSON with real-time price data including last price and previous day price

## Rate Limiting Strategy

### Basic + Currencies Plan Limits
- **5 API calls per minute**
- **100 API calls per day**
- **Forex data access** (requires Currencies add-on)

### Implementation
- **Minute-level tracking**: Resets every 60 seconds
- **Daily tracking**: Resets at midnight UTC
- **Graceful degradation**: Falls back to static data when limits exceeded
- **Smart caching**: Reduces unnecessary API calls

## Benefits Over Alpha Vantage

### 1. Better Data Quality
- **Real-time forex data** with millisecond precision
- **Previous day prices** for change calculations
- **More reliable** API with better uptime

### 2. Higher Rate Limits
- **100 calls per day** vs 25 per day (Alpha Vantage free tier)
- **5 calls per minute** vs 5 calls per minute
- **No need for multiple API keys**

### 3. Professional Features
- **WebSocket support** (available in higher tiers)
- **Historical data** access
- **Better documentation** and support

### 4. Cost Efficiency
- **$50/month** for reliable, professional-grade forex data
- **No need to manage multiple free API keys**
- **Predictable pricing** for scaling

## Testing Your Setup

### 1. Test API Key
```bash
curl "https://api.polygon.io/v2/snapshot/locale/global/markets/forex/tickers/C:EURUSD?apikey=YOUR_API_KEY"
```

### 2. Check API Status
```bash
curl http://localhost:8000/api/api-status
```

### 3. Test Forex Prices
```bash
curl http://localhost:8000/api/forex-prices
```

## Troubleshooting

### Common Issues

1. **"API call failed"**: 
   - Check your API key is correct
   - Verify internet connection
   - Check if you've hit rate limits

2. **Rate limit exceeded**: 
   - Wait a few minutes for minute limit to reset
   - Check daily usage in `/api/api-status`
   - App will automatically use fallback data

3. **No data returned**: 
   - Verify ticker symbols are correct
   - Check API key permissions
   - App will use fallback data automatically

### Debug Information

The API status endpoint (`/api/api-status`) provides:
- Current usage statistics
- Rate limit information
- Remaining calls for day/minute
- Last update timestamp

## Migration from Alpha Vantage

### What Changed
1. **API Provider**: Alpha Vantage → Polygon.io
2. **Rate Limits**: 25/day (4 keys) → 100/day (1 key)
3. **Data Quality**: Basic forex → Professional forex data
4. **Cost**: Free → $50/month (Basic + Currencies plan)

### What Stayed the Same
1. **Frontend Interface**: No changes needed
2. **Fallback Logic**: Still works the same way
3. **Error Handling**: Graceful degradation maintained
4. **Caching Strategy**: Still implemented for performance

## Next Steps

1. **Get Polygon.io API Key**: Sign up and get your key
2. **Update Environment Variables**: Add the key to your `.env` files
3. **Test the Integration**: Verify data is flowing correctly
4. **Monitor Usage**: Check `/api/api-status` regularly
5. **Scale as Needed**: Consider upgrading plan if you exceed limits

## Cost Analysis

### Current Setup (Polygon.io Basic + Currencies)
- **Monthly Cost**: $50
- **Daily Calls**: 100
- **Minute Calls**: 5
- **Data Quality**: Professional

### Usage Estimation
- **3 price updates per minute**: 180 calls per hour
- **Daily usage**: ~4,320 calls (exceeds Basic plan)
- **Recommendation**: Consider upgrading to Starter plan ($99/month) for 1,000 calls/day if you need more frequent updates

### Budget Impact
- **Current MRC**: $76/month (including Polygon.io $50)
- **Break-even**: Now needs 4 users (4 × $24.99 = $99.96)
- **Profit margin**: Reduced by $50, but data quality significantly improved 