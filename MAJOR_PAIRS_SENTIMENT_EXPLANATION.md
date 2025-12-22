# Major Pairs Sentiment Cards - Complete Explanation

## Overview

The Major Pairs Sentiment cards display real-time sentiment analysis for the 4 major currency pairs: **EUR/USD**, **GBP/USD**, **USD/JPY**, and **USD/CHF**. Each card shows sentiment direction, strength, daily price change, RSI, and volatility.

---

## Data Flow

### 1. Data Source: TradingView API

**Location**: `backend/app.py` → `get_tradingview_prices()`

**API Endpoint**: `https://scanner.tradingview.com/forex/scan`

**Data Retrieved**:
- **Price**: Current close price
- **Change**: Absolute change (e.g., +0.0012 for EUR/USD)
- **Change Percent**: Percentage change (e.g., +0.11%)

**Pairs Fetched**: All 15 supported pairs, but only 4 major pairs are displayed:
- EUR/USD
- GBP/USD  
- USD/JPY
- USD/CHF

**Update Frequency**: Every time market sentiment is calculated (every 15 minutes by default)

**Data Structure**:
```python
{
    'EURUSD': {
        'price': 1.0923,
        'change': 0.0012,
        'changePercent': 0.11,
        'lastUpdate': '2024-01-15T10:30:00',
        'source': 'TradingView'
    },
    # ... other pairs
}
```

---

## Calculation Process

### Location: `backend/services/market_sentiment_service.py` → `_calculate_pairs_sentiment()`

### Step-by-Step Calculation:

#### 1. **Fetch Forex Data**
```python
forex_data = get_tradingview_prices()
```
- Gets real-time data from TradingView API
- Falls back to default values if API fails

#### 2. **Process Each Major Pair**

For each of the 4 major pairs:

##### A. **Extract Price Change Data**
```python
price_change_percent = data.get('changePercent', 0)  # e.g., 0.11 (0.11%)
price_change = data.get('change', 0)                  # e.g., 0.0012
```

##### B. **Calculate Sentiment** (Bullish/Bearish/Neutral)

**Logic**:
- **Bullish**: `changePercent > 0.1%` (price moving up)
- **Bearish**: `changePercent < -0.1%` (price moving down)
- **Neutral**: `-0.1% ≤ changePercent ≤ 0.1%` (minimal movement)

**Example**:
- EUR/USD: `changePercent = +0.15%` → **Bullish**
- GBP/USD: `changePercent = -0.25%` → **Bearish**
- USD/JPY: `changePercent = +0.05%` → **Neutral**

##### C. **Calculate Sentiment Percentage** (0-100%)

**Formula**:
- **Bullish**: `percentage = min(85, 50 + abs(changePercent) × 50)`
- **Bearish**: `percentage = max(15, 50 - abs(changePercent) × 50)`
- **Neutral**: `percentage = 50`

**Examples**:
- `changePercent = +0.2%` → `percentage = min(85, 50 + 0.2 × 50) = min(85, 60) = 60%`
- `changePercent = -0.3%` → `percentage = max(15, 50 - 0.3 × 50) = max(15, 35) = 35%`
- `changePercent = +0.05%` → `percentage = 50%`

**Visual Representation**:
- 0-15%: Very bearish (red bar, mostly empty)
- 15-50%: Bearish (red bar, partially filled)
- 50%: Neutral (yellow/orange bar, half filled)
- 50-85%: Bullish (green bar, mostly filled)
- 85-100%: Very bullish (green bar, almost full)

##### D. **Calculate RSI (Relative Strength Index)**

**Formula**:
- **Strong Bullish** (`changePercent > 0.2%`): 
  ```
  RSI = min(100, 70 + (changePercent - 0.2) × 100)
  ```
- **Strong Bearish** (`changePercent < -0.2%`): 
  ```
  RSI = max(0, 30 + (changePercent + 0.2) × 100)
  ```
- **Neutral** (`-0.2% ≤ changePercent ≤ 0.2%`): 
  ```
  RSI = 50 + (changePercent × 100)
  ```

**Examples**:
- `changePercent = +0.3%` → `RSI = min(100, 70 + (0.3 - 0.2) × 100) = min(100, 80) = 80`
- `changePercent = -0.4%` → `RSI = max(0, 30 + (-0.4 + 0.2) × 100) = max(0, 10) = 10`
- `changePercent = +0.1%` → `RSI = 50 + (0.1 × 100) = 60`

**RSI Interpretation**:
- **0-30**: Oversold (bearish)
- **30-50**: Weak bearish
- **50**: Neutral
- **50-70**: Weak bullish
- **70-100**: Overbought (bullish)

**Note**: This is a simplified RSI calculation based on daily change. A true RSI requires historical price data over multiple periods (typically 14 periods).

##### E. **Calculate Volatility**

**Formula**:
```
volatility = abs(changePercent) × 10
```

**Examples**:
- `changePercent = +0.15%` → `volatility = 0.15 × 10 = 1.5%`
- `changePercent = -0.30%` → `volatility = 0.30 × 10 = 3.0%`
- `changePercent = +0.05%` → `volatility = 0.05 × 10 = 0.5%`

**Interpretation**:
- **< 1%**: Low volatility
- **1-2%**: Moderate volatility
- **> 2%**: High volatility

**Note**: This is a simplified volatility measure. True volatility typically uses standard deviation of returns over multiple periods.

#### 3. **Create PairSentiment Object**

```python
PairSentiment(
    pair='EURUSD',
    sentiment='bullish',
    percentage=60.0,
    price_change=0.15,  # percentage
    rsi=65.0,
    volatility=1.5,
    support=None,  # Not currently calculated
    resistance=None  # Not currently calculated
)
```

---

## Frontend Display

### Location: `src/components/Overview.jsx` → Lines 2632-2662

### Display Components:

#### 1. **Pair Name**
- Shows the currency pair (e.g., "EURUSD")
- Displayed at the top of each card

#### 2. **Daily Change**
- Shows the percentage change with +/- sign
- Color-coded:
  - **Green** (`positive`): Positive change (price up)
  - **Red** (`negative`): Negative change (price down)
- Format: `+0.15%` or `-0.25%`

#### 3. **Sentiment Gauge Bar**
- Visual bar showing sentiment strength
- **Width**: Based on `percentage` (0-100%)
- **Color**: Based on `sentiment`:
  - **Green**: Bullish
  - **Red**: Bearish
  - **Yellow/Orange**: Neutral
- **Gradient**: Fades from solid to 80% opacity

#### 4. **RSI Metric**
- Displays: `RSI: 65` (rounded to nearest integer)
- Shows relative strength/weakness

#### 5. **Volatility Metric**
- Displays: `Vol: 1.5%` (rounded to 1 decimal)
- Shows market volatility level

---

## Complete Example

### Input Data (from TradingView):
```python
{
    'EURUSD': {
        'price': 1.0923,
        'change': 0.0012,
        'changePercent': 0.11  # 0.11%
    }
}
```

### Calculations:
1. **Sentiment**: `0.11% > 0.1%` → **Bullish**
2. **Percentage**: `min(85, 50 + 0.11 × 50) = min(85, 55.5) = 55.5%`
3. **RSI**: `50 + (0.11 × 100) = 61`
4. **Volatility**: `0.11 × 10 = 1.1%`

### Frontend Display:
```
┌─────────────────────┐
│ EURUSD              │
│ Daily Change: +0.11%│
│ ████████░░░░░░░░░░  │ (55.5% green bar)
│ RSI: 61             │
│ Vol: 1.1%           │
└─────────────────────┘
```

---

## Current Limitations & Notes

### 1. **Simplified RSI**
- Current RSI is based only on daily change
- True RSI requires 14-period historical data
- Considered a "pseudo-RSI" or momentum indicator

### 2. **Simplified Volatility**
- Based only on absolute daily change
- True volatility uses standard deviation over multiple periods
- More of a "volatility proxy"

### 3. **No Support/Resistance**
- `support` and `resistance` fields exist but are `None`
- Would require historical price data and technical analysis
- Could be added using pivot points or technical levels

### 4. **No Historical Context**
- Only uses current day's change
- Doesn't consider trends over time
- Could be enhanced with moving averages or trend analysis

### 5. **Fixed Thresholds**
- Sentiment thresholds are fixed at ±0.1%
- Could be dynamic based on pair's typical volatility
- Some pairs (like USD/JPY) are naturally more volatile

---

## Potential Enhancements

1. **True RSI Calculation**
   - Fetch historical price data (14 periods minimum)
   - Calculate using standard RSI formula
   - More accurate overbought/oversold signals

2. **Support/Resistance Levels**
   - Calculate pivot points from recent highs/lows
   - Identify key psychological levels
   - Display on cards

3. **Trend Analysis**
   - Compare current change to recent averages
   - Identify if movement is accelerating/decelerating
   - Add trend indicators (↑↓→)

4. **Pair-Specific Thresholds**
   - Adjust sentiment thresholds per pair
   - USD/JPY typically more volatile than EUR/USD
   - More accurate sentiment classification

5. **Volatility Calculation**
   - Use standard deviation of returns over 20 periods
   - Compare to historical volatility
   - Show volatility percentile

---

## Data Refresh

- **Backend**: Calculated every 15 minutes (or when cache expires)
- **Frontend**: Updates when market sentiment data refreshes
- **API**: TradingView data is real-time (fetched on each calculation)

---

## Error Handling

- **API Failure**: Falls back to default neutral values
- **Missing Data**: Uses default `PairSentiment` objects
- **Invalid Values**: Clamped to valid ranges (RSI: 0-100, Percentage: 15-85)

---

## Summary

The Major Pairs Sentiment cards provide a quick visual overview of:
- **Direction**: Bullish/Bearish/Neutral
- **Strength**: Percentage bar (15-85%)
- **Momentum**: RSI indicator
- **Volatility**: Daily volatility measure
- **Price Change**: Daily percentage change

All calculations are based on real-time TradingView data and update automatically with market sentiment refreshes.

