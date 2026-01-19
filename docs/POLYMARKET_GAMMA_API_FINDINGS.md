# Polymarket Gamma API Findings

## API Endpoint Test Results

**Endpoint**: `https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100`

**Date**: January 19, 2026

---

## Key Finding: Active Fed Rate Markets Found! ✅

### Fed January 2026 Meeting Markets

Found **4 active markets** for the January 2026 FOMC meeting:

1. **"No change in Fed interest rates after January 2026 meeting?"**
   - **Yes Price**: 0.9615 (96.15% probability)
   - **No Price**: 0.0385 (3.85% probability)
   - **Volume**: $43,969,922 (very high volume)
   - **Accepting Orders**: ✅ Yes
   - **End Date**: 2026-01-28
   - **Condition ID**: `0xe93c89c41d1bb08d3bb40066d8565df301a696563b2542256e6e8bbbb1ec490d`

2. **"Fed decreases interest rates by 25 bps after January 2026 meeting?"**
   - **Yes Price**: 0.0355 (3.55% probability)
   - **No Price**: 0.9645 (96.45% probability)
   - **Volume**: $42,592,657
   - **Accepting Orders**: ✅ Yes
   - **End Date**: 2026-01-28

3. **"Fed decreases interest rates by 50+ bps after January 2026 meeting?"**
   - **Yes Price**: 0.0025 (0.25% probability)
   - **No Price**: 0.9975 (99.75% probability)
   - **Volume**: $166,529,129 (extremely high volume)
   - **Accepting Orders**: ✅ Yes
   - **End Date**: 2026-01-28

4. **"Fed increases interest rates by 25+ bps after January 2026 meeting?"**
   - **Yes Price**: 0.0015 (0.15% probability)
   - **No Price**: 0.9985 (99.85% probability)
   - **Volume**: $160,914,125 (extremely high volume)
   - **Accepting Orders**: ✅ Yes
   - **End Date**: 2026-01-28

### Market Consensus Interpretation

**Markets are pricing:**
- **96.15% chance of NO CHANGE** (rate hold)
- **3.55% chance of 25bp CUT**
- **0.25% chance of 50bp+ CUT**
- **0.15% chance of 25bp+ HIKE**

This is **exactly the type of data we need** for the Market Expectations Hub!

---

## Other Relevant Markets Found

### Economic/Policy Markets

1. **"Negative GDP growth in 2025?"**
   - Yes: 0.9% | No: 99.1%
   - Volume: $112,147
   - End Date: 2026-01-30

2. **"Will tariffs generate >$250b in 2025?"**
   - Yes: 3.15% | No: 96.85%
   - Volume: $1,063,997
   - End Date: 2026-02-28

3. **"Brazil unemployment below 6.3% for Q4 2025?"**
   - Volume: $217,885
   - End Date: 2026-01-30

### Political Markets (FX-Relevant)

Multiple markets on:
- Federal spending/budget cuts
- Trump policies (deportations, tariffs)
- Elections (UK, Colombia, etc.)

These can impact FX indirectly through policy expectations.

---

## API Structure Analysis

### Event Object Structure
```json
{
  "id": "17823",
  "title": "Event Title",
  "active": true,
  "closed": false,
  "markets": [
    {
      "id": "824952",
      "question": "Market question?",
      "conditionId": "0x...",
      "outcomePrices": "[\"0.23\", \"0.77\"]",
      "volume": "110987.689423",
      "volumeNum": 110987.689423,
      "active": true,
      "closed": false,
      "acceptingOrders": true,
      "endDateIso": "2026-07-01",
      "volume24hr": 3021.805321,
      "volume1wk": 15969.430510999999,
      "oneDayPriceChange": 0.025,
      "oneWeekPriceChange": -0.045
    }
  ]
}
```

### Key Fields Available

- **Prices**: `outcomePrices` array (Yes/No probabilities)
- **Volume**: Multiple timeframes (24hr, 1wk, 1mo, 1yr)
- **Price Changes**: 1 day, 1 week, 1 month deltas
- **Status**: `active`, `closed`, `acceptingOrders`
- **Dates**: `endDateIso` (resolution date)

---

## Integration Opportunity

### Gamma API vs CLOB API

**Gamma API Advantages:**
- ✅ Events-based structure (groups related markets)
- ✅ Includes price deltas (1d, 1wk, 1mo changes)
- ✅ Better organization (events → markets)
- ✅ Volume breakdown by timeframe

**CLOB API** (currently used):
- Direct market access
- More markets (2,000+)
- Simpler structure
- But: Less organized, no event grouping

### Recommendation

**Hybrid Approach:**
1. Use **Gamma API for event discovery** (find Fed/ECB/CPI markets)
2. Use **CLOB API for market details** (get prices, orderbook)
3. Or: Use **Gamma API events endpoint** to identify relevant events, then fetch market details via CLOB

---

## Action Items

### Immediate
1. ✅ **Add Gamma API as data source** in `prediction_markets_service.py`
2. ✅ **Parse Fed markets** from Gamma API
3. ✅ **Match to economic calendar events** (Fed meeting Jan 31)

### Implementation
1. Create method: `_fetch_polymarket_gamma_events()`
2. Filter for economic keywords (Fed, ECB, CPI, etc.)
3. Extract market probabilities
4. Match to upcoming calendar events
5. Display in Market Expectations Hub

### Future
1. Track price changes over time (1d, 1wk deltas)
2. Use volume as conviction indicator
3. Create divergence alerts when PM ≠ FX positioning

---

## Code to Fetch Fed Markets

```python
import requests

def fetch_fed_markets_from_gamma():
    """Fetch Fed rate markets from Gamma API"""
    url = "https://gamma-api.polymarket.com/events"
    params = {
        "active": "true",
        "closed": "false",
        "limit": 200
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    fed_markets = []
    for event in data:
        for market in event.get('markets', []):
            question = market.get('question', '').lower()
            
            # Look for Fed rate markets
            if 'fed' in question and 'interest rate' in question:
                if market.get('active') and not market.get('closed'):
                    # Parse outcome prices
                    prices_str = market.get('outcomePrices', '[]')
                    import ast
                    prices = ast.literal_eval(prices_str)
                    
                    fed_markets.append({
                        'question': market.get('question'),
                        'yes_price': float(prices[0]) if prices else None,
                        'no_price': float(prices[1]) if len(prices) > 1 else None,
                        'volume': market.get('volumeNum'),
                        'endDate': market.get('endDateIso'),
                        'price_change_1d': market.get('oneDayPriceChange'),
                        'price_change_1wk': market.get('oneWeekPriceChange')
                    })
    
    return fed_markets
```

---

## Conclusion

**Good news**: There ARE active economic prediction markets!

The Fed January 2026 meeting has 4 active markets with:
- **High volume** ($40M+ each)
- **Clear probabilities** (96% rate hold)
- **Price deltas available** (can track shifts)

**Next Steps:**
1. Integrate Gamma API into service
2. Match Fed markets to calendar events
3. Display in Market Expectations Hub
4. Compare with FX positioning for divergence detection

This proves the concept works - we just need to use the right API endpoint!

