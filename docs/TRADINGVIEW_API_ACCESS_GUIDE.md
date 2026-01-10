# TradingView API & Data Access Guide

## Overview

TradingView does **not offer an official public REST API** for programmatic data access. However, there are several ways to access TradingView data and functionality, ranging from free to paid options.

---

## Free Access Options

### 1. Scanner API (Currently Used - Undocumented)
**Endpoint**: `https://scanner.tradingview.com/forex/scan`

**What's Available**:
- Real-time forex prices
- Price changes (absolute and percentage)
- Multiple currency pairs in a single request

**Limitations**:
- **Undocumented** - No official documentation
- **No rate limit guarantees** - Limits may be enforced without notice
- **No authentication** - Public endpoint, may be restricted
- **Limited data columns** - Only basic price data available

**Current Usage in FXSentinel**:
```python
# backend/app.py - get_tradingview_prices()
url = "https://scanner.tradingview.com/forex/scan"
# Returns: close price, change, change_abs for forex pairs
```

**Status**: ⚠️ **Use with caution** - This is an undocumented endpoint that could be restricted or removed at any time.

---

### 2. TradingView Chart Widgets (Free)
**Access**: Embeddable chart widgets for websites

**What's Available**:
- Interactive charts (free tier)
- Basic technical indicators
- Multiple chart types (candlestick, line, area, etc.)
- Symbol search and display

**How to Use**:
```html
<!-- TradingView Widget -->
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
  "autosize": true,
  "symbol": "FX:EURUSD",
  "interval": "D",
  "timezone": "Etc/UTC",
  "theme": "light",
  "style": "1",
  "locale": "en",
  "toolbar_bg": "#f1f3f6",
  "enable_publishing": false,
  "hide_top_toolbar": true,
  "hide_legend": true,
  "save_image": false,
  "container_id": "tradingview_chart"
});
</script>
```

**Limitations**:
- Free widgets show TradingView branding
- Limited customization options
- Requires internet connection to TradingView servers
- May have usage restrictions

**Documentation**: https://www.tradingview.com/widget-docs/

---

### 3. TradingView Lightweight Charts (Open Source - Free)
**Access**: Open-source charting library (MIT License)

**What's Available**:
- Full-featured charting library
- No TradingView branding required
- Customizable and embeddable
- Works offline (once loaded)

**How to Use**:
```bash
npm install lightweight-charts
```

```javascript
import { createChart } from 'lightweight-charts';

const chart = createChart(document.getElementById('chart'), {
  width: 600,
  height: 300,
});
const candlestickSeries = chart.addCandlestickSeries();
candlestickSeries.setData([
  { time: '2024-01-01', open: 1.08, high: 1.09, low: 1.07, close: 1.085 },
  // ... more data
]);
```

**GitHub**: https://github.com/tradingview/lightweight-charts

**Limitations**:
- **No data included** - You must provide your own price data
- Charting library only, not a data source
- Requires data from other sources (APIs, databases, etc.)

---

## Paid Access Options

### TradingView Subscription Plans

#### 1. Essential Plan - $14.95/month
**Web Platform Features**:
- 2 charts per tab
- 5 indicators per chart
- 10,000 historical bars
- 20 price alerts
- Ad-free experience
- Real-time data for 100+ exchanges

**API Access**: ❌ No additional API access beyond free options

---

#### 2. Plus Plan - $29.95/month
**Web Platform Features**:
- 4 charts per tab
- 10 indicators per chart
- 10,000 historical bars
- 100 price alerts
- Custom timeframes
- Multiple watchlists
- Advanced screener functionality

**API Access**: ❌ No additional API access beyond free options

---

#### 3. Premium Plan - $59.95/month
**Web Platform Features**:
- 8 charts per tab
- 25 indicators per chart
- 20,000 historical bars
- 400 price alerts
- Volume Profile
- Custom range bars
- Advanced chart types (Renko, Kagi, etc.)

**API Access**: ❌ No additional API access beyond free options

---

#### 4. Expert Plan - $199.95/month
**Web Platform Features**:
- All Premium features
- Priority customer support
- Professional-grade market data feeds

**API Access**: ❌ No additional API access beyond free options

---

#### 5. Ultimate Plan - $239.95/month
**Web Platform Features**:
- All Expert features
- Maximum charting capabilities
- Highest priority support

**API Access**: ❌ No additional API access beyond free options

---

## Additional Data Fees

Some real-time data feeds require **additional fees** (separate from subscription):

- **Nasdaq**: $3/month
- **NYSE**: $3/month
- **Arca**: $9/month
- **Other exchanges**: Varies by exchange

These fees are mandated by exchanges and passed through TradingView.

---

## How to Upgrade

1. **Log in** to your TradingView account
2. Navigate to: https://www.tradingview.com/pricing/
3. Select your desired plan
4. Complete the subscription process
5. Add any additional data feeds if needed

**Discounts Available**:
- Annual subscriptions offer discounts vs monthly
- Promotions during events (Black Friday, etc.)
- 30-day free trial available for paid plans

---

## Current FXSentinel Implementation

### What We're Using

**Endpoint**: `scanner.tradingview.com/forex/scan`
- **Type**: Undocumented public API
- **Cost**: Free
- **Data**: Real-time forex prices
- **Rate Limits**: Unknown (no official documentation)

### Recommendations

1. **Monitor for Rate Limits**: Watch logs for 429 errors from TradingView
2. **Have Fallback Ready**: Already implemented - falls back to cached/mock data
3. **Consider Alternatives**: 
   - Implement server-side caching (5-10 second cache)
   - Consider paid data providers if TradingView restricts access
   - Use TradingView widgets for charts (free, but requires internet)

### Potential Issues

- ⚠️ **No official API** - Endpoint could be restricted or removed
- ⚠️ **Unknown rate limits** - May hit limits without warning
- ⚠️ **No support** - Can't contact TradingView for API issues
- ⚠️ **No guarantees** - Service could change at any time

---

## Alternative Data Sources

If TradingView becomes unavailable or restricted, consider:

1. **Finnhub** - Already integrated in FXSentinel
   - Free tier: 60 API calls/minute
   - Paid tiers available

2. **Alpha Vantage** - Already integrated in FXSentinel
   - Free tier: 5 API calls/minute, 500/day
   - Paid tiers available

3. **Polygon.io** - Documented in codebase
   - Paid service: $50/month
   - Professional-grade data

4. **ExchangeRate-API** - Currently used as fallback
   - Free tier available
   - Paid tiers for higher limits

---

## Summary

| Feature | Free Access | Paid Access |
|---------|-------------|-------------|
| **Scanner API** | ✅ Yes (undocumented) | ❌ No official API |
| **Chart Widgets** | ✅ Yes (with branding) | ✅ Yes (less branding) |
| **Lightweight Charts** | ✅ Yes (open source) | ✅ Yes (same) |
| **Real-time Data** | ⚠️ Limited | ✅ Yes (with subscription) |
| **Historical Data** | ⚠️ Limited | ✅ Yes (more bars) |
| **API Access** | ⚠️ Undocumented only | ❌ No official API |
| **Support** | ❌ No | ✅ Yes (with paid plans) |

**Key Takeaway**: TradingView's primary value is in their **web platform and charting tools**, not in programmatic API access. For API access, you're limited to undocumented endpoints or need to use alternative data providers.

---

## References

- TradingView Pricing: https://www.tradingview.com/pricing/
- TradingView Widget Docs: https://www.tradingview.com/widget-docs/
- Lightweight Charts: https://github.com/tradingview/lightweight-charts
- Current Implementation: `backend/app.py` - `get_tradingview_prices()`

