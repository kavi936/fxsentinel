# US NFP System Flow - Complete Holistic Explanation

## Overview
This document explains the complete end-to-end flow for analyzing a "US Non-Farm Payrolls" (NFP) economic event, from user click to GPT response display.

---

## 1. USER INTERACTION

### 1.1 User Clicks on Event
**Location**: `src/components/Overview.jsx`

**Event Data Structure** (from economic calendar):
```javascript
{
  id: "12345",
  title: "US Non-Farm Payrolls",
  currency: "USD",
  date: "2026-01-10",
  time: "08:30",
  impact: "high",
  previous: "150K",
  expected: "180K",
  actual: "200K"  // If post-event
}
```

**Action**: `handleEventClick()` sets state to `'pending'` and stores `selectedEvent`

---

## 2. USER CONFIRMS ANALYSIS

### 2.1 Confirm Button Click
**Location**: `src/components/Overview.jsx`

**Action**: `handleConfirmAnalysis()` calls:
```javascript
const analysis = await generateEventAnalysis(selectedEvent);
```

**API Call**: `GET /api/enhanced-analysis/<news_id>`

---

## 3. BACKEND API ENDPOINT

### 3.1 API Route Handler
**Location**: `backend/app.py`

**Function**: `get_enhanced_analysis(news_id)`

**Steps**:
1. Fetch event from calendar service
2. Create initial `MarketContext` object
3. Call `gpt_analyzer.analyze_macro_event(event, market_context, analysis_type)`

---

## 4. GPT ANALYSIS SERVICE - MAIN FLOW

### 4.1 Entry Point: `analyze_macro_event()`
**Location**: `backend/services/gpt_ai_analysis.py`

**Complete Flow**:

```
analyze_macro_event()
  ├─ Step 1: Validate Event Data
  │   └─ economic_data_validator.validate_event_data(event)
  │       └─ Returns: validated_event, validation_errors
  │
  ├─ Step 2: Fetch Live Market Data
  │   └─ live_market_data_service.get_live_market_data()
  │       └─ TradingView API → Current prices, volatility, sentiment
  │
  ├─ Step 3: Create Enhanced Market Context
  │   └─ _create_enhanced_market_context(market_context, live_data)
  │       └─ Merges live data with original context
  │
  ├─ Step 4: Check Cache
  │   └─ _get_cached_analysis(cache_key)
  │       └─ Redis/in-memory cache lookup
  │
  ├─ Step 5: Rate Limiting Check
  │   └─ _check_rate_limit()
  │
  ├─ Step 6: Select GPT Model
  │   └─ _select_model(event)
  │       └─ Returns: "gpt-4o-mini" or "gpt-4o" based on impact
  │
  ├─ Step 7: Generate GPT Analysis
  │   └─ _generate_enhanced_gpt_analysis()
  │       └─ Builds prompt → Calls GPT → Parses response
  │
  ├─ Step 8: Cache Result
  │   └─ _cache_analysis(cache_key, result)
  │
  └─ Step 9: Return GPTAnalysisResult
```

---

## 5. DATA COLLECTION & MAPPING

### 5.1 Event Data (Input)
**Source**: Economic Calendar (Hybrid Calendar Service)

**For US NFP**:
```python
event = {
    'id': '12345',
    'title': 'US Non-Farm Payrolls',
    'currency': 'USD',
    'date': '2026-01-10',
    'time': '08:30',
    'impact': 'high',
    'previous': '150K',
    'expected': '180K',
    'actual': '200K'  # Post-event
}
```

### 5.2 Live Market Data
**Source**: TradingView API (`live_market_data_service`)

**Data Retrieved**:
```python
live_market_data = {
    'current_prices': {
        'EURUSD': 1.0850,
        'GBPUSD': 1.2650,
        'USDJPY': 148.50,
        # ... all major pairs
    },
    'recent_volatility': {
        'EURUSD': 'moderate',
        'GBPUSD': 'moderate',
        # ...
    },
    'market_sentiment': {
        'EURUSD': 'neutral',
        'GBPUSD': 'neutral',
        # ...
    },
    'change_percent': {
        'EURUSD': -0.15,
        'GBPUSD': -0.25,
        # ...
    },
    # Note: bond_yields, equity_indices, commodity_prices, key_levels = None
    # (removed inaccurate/estimated data)
}
```

### 5.3 Trading Sessions Data
**Source**: `_get_trading_sessions()` (calculated from current time)

**For US NFP (08:30 ET = 13:30 UTC)**:
```python
trading_sessions = {
    'active_sessions': ['New York', 'London'],  # Overlap period
    'volatility_implication': 'High volatility expected (London-NY overlap)',
    'market_status': 'open'  # or 'closed' if weekend/holiday
}
```

### 5.4 Market Sentiment Data
**Source**: `market_sentiment_service` (`_get_market_sentiment_data()`)

**Data Retrieved**:
```python
sentiment_data = {
    'vix': {
        'value': 15.2,
        'change': +0.5,
        'level': 'low'  # low/medium/high
    },
    'risk_appetite': {
        'level': 'high',  # high/medium/low
        'percentage': 75,
        'safe_havens': 'None'  # or list of safe havens if risk-off
    }
}
```

### 5.5 Pairs Sentiment Data (Top 3 Most Important Pairs)
**Source**: `_get_pairs_sentiment_data(currency, event, market_context)`

**For USD NFP Event**:
```python
# Step 1: Identify top 3 pairs
top_3_pairs = _get_top_3_pairs_for_currency('USD')
# Returns: ['EURUSD', 'USDJPY', 'GBPUSD']

# Step 2: Get sentiment for each pair
pairs_sentiment = [
    {
        'pair': 'EURUSD',
        'sentiment': 'bearish',  # bullish/bearish/neutral
        'daily_change': -0.15,  # percentage
        'rsi': 48.2,  # Relative Strength Index
        'volatility': 0.04  # percentage
    },
    {
        'pair': 'USDJPY',
        'sentiment': 'neutral',
        'daily_change': -0.05,
        'rsi': 47.5,
        'volatility': 0.05
    },
    {
        'pair': 'GBPUSD',
        'sentiment': 'bearish',
        'daily_change': -0.25,
        'rsi': 40.4,
        'volatility': 0.15
    }
]
```

**How Top 3 Pairs Are Selected**:
```python
def _get_top_3_pairs_for_currency(currency: str) -> List[str]:
    """
    Returns the 3 most important pairs for a currency
    
    For USD:
    1. EURUSD (most liquid, major pair)
    2. USDJPY (major pair, high volume)
    3. GBPUSD (major pair, high volume)
    
    Logic: Prioritizes major pairs with highest trading volume
    """
```

### 5.6 Economy Context Data (NEW - Phase 1 Integration)
**Source**: Static JSON (`src/data/economyIndicators.json`) via `economy_context_service`

**Step 1: Event Type Matching (Approach 4)**
```python
# Event title: "US Non-Farm Payrolls"
relevant_indicator_ids = _get_relevant_indicators("US Non-Farm Payrolls")
# Returns: ['interest-rate', 'unemployment', 'nonfarm-payrolls']

# Mapping Logic:
EVENT_TYPE_MAPPING = {
    'nfp': ['unemployment', 'nonfarm-payrolls'],
    'employment': ['unemployment', 'nonfarm-payrolls'],
    # ... always includes 'interest-rate' for policy context
}
```

**Step 2: Load Economy Context**
```python
economy_context = economy_context_service.get_economy_context('USD')
# Maps USD → US (country code)

# Returns:
{
    'currency': 'USD',
    'country_code': 'US',
    'central_bank_rate': {
        'value': 3.75,
        'trend': 'down',
        'bank_name': 'Fed',
        'as_of': '2025-12-10'
    },
    'indicators': {
        # Filtered to only relevant indicators:
        'interest-rate': {
            'currentValue': '3.75%',
            'asOf': '2025-12-10',
            # ... chart data, source, etc.
        },
        'unemployment': {
            'currentValue': '3.8%',
            'asOf': '2025-11-01',
            # ...
        },
        'nonfarm-payrolls': {
            'currentValue': '119K',
            'asOf': '2025-11-01',
            # ...
        }
    }
}
```

**Step 3: Policy Target Analysis (Approach 6)**
```python
# For NFP (employment event), calculate unemployment policy pressure
policy_pressure = _get_policy_pressure('USD', 'unemployment', 3.8)

# Returns:
{
    'target': 4.0,  # Fed's "natural rate"
    'current': 3.8,
    'deviation': -0.2,  # Below target
    'deviation_percent': -5.0,
    'pressure_level': 'moderate hawkish pressure',  # Below target = hawkish
    'indicator_type': 'unemployment',
    'central_bank': 'Federal Reserve'
}
```

---

## 6. PROMPT CONSTRUCTION

### 6.1 Prompt Structure
**Location**: `_create_analysis_prompt()` in `gpt_ai_analysis.py`

**Complete Prompt for US NFP**:

```
Analyze the following economic event and provide comprehensive market analysis:

EVENT DETAILS:
- Title: US Non-Farm Payrolls
- Currency: USD
- Impact Level: high
- Previous: 150K
- Expected: 180K
- Actual: 200K
- Analysis Type: post_event

ECONOMIC CONTEXT FOR USD:
- Central Bank Rate: 3.75% (Trend: down)
- Current Interest Rate: 3.75%
- Current Unemployment Rate: 3.8%
- Current Non-Farm Payrolls: 119K

POLICY TARGET ANALYSIS:
Unemployment Policy Pressure: moderate hawkish pressure
  - Current: 3.80%
  - Target: 4.00%
  - Deviation: -0.20pp (-5.0%)

MARKET CONTEXT:
- Current Prices: {'EURUSD': 1.0850, 'GBPUSD': 1.2650, 'USDJPY': 148.50, ...}
- Recent Volatility: {'EURUSD': 'moderate', 'GBPUSD': 'moderate', ...}
- Market Sentiment: {'EURUSD': 'neutral', 'GBPUSD': 'neutral', ...}

ADDITIONAL MARKET CONTEXT:
- Active Trading Sessions: New York, London
- Volatility Implication: High volatility expected (London-NY overlap)
- VIX Fear Indicator: 15.2 (+0.5, Level: low)
- Risk Appetite: HIGH (75%) - Safe Havens: None

RELEVANT CURRENCY PAIRS SENTIMENT (Daily Change):
- EURUSD: BEARISH (-0.15% daily change), RSI: 48.2, Volatility: 0.04%
- USDJPY: NEUTRAL (-0.05% daily change), RSI: 47.5, Volatility: 0.05%
- GBPUSD: BEARISH (-0.25% daily change), RSI: 40.4, Volatility: 0.15%

IMPORTANT: For forward_scenarios, provide specific probability percentages for each scenario (bullish, bearish, neutral). 
The probabilities should sum to approximately 100% and reflect the likelihood of each outcome based on the event data, 
market context, and historical patterns. Include key price levels and reasoning for each scenario.

When considering volatility expectations, take into account:
- Active trading sessions (London-NY overlap = highest volatility, Asian sessions = lower volatility)
- VIX level (high VIX >25 = elevated fear/volatility, low VIX <15 = calm markets)
- Risk appetite (low risk appetite = safe haven demand, high risk appetite = risk-on flows)

Please provide analysis in the following JSON format:
{
    "headline": "Compelling headline summarizing the key takeaway",
    "key_takeaway": "Main insight in 1-2 sentences",
    "forward_scenarios": {
        "bullish": "Bullish scenario description with specific probability percentage...",
        "bearish": "Bearish scenario description with specific probability percentage...", 
        "neutral": "Neutral scenario description with specific probability percentage..."
    },
    "event_summary": {
        "release": "Event description",
        "outcome": "What happened vs expectations",
        "previous": "150K",
        "expected": "180K",
        "actual": "200K"
    },
    "market_reaction": {
        "price_action": "Expected price action",
        "volatility": "Volatility expectations",
        "reason": "Why this reaction is expected"
    },
    "implications_takeaways": {
        "economic_context": "Economic implications",
        "policy_implications": "Central bank policy implications",
        "market_bias": "Overall market bias",
        "risk_level": "Risk assessment"
    },
    "trading_plan": {
        "best_approach": "Recommended trading approach",
        "avoid_strategies": "Strategies to avoid",
        "key_levels": "Important price levels",
        "position_sizing": "Position sizing recommendations",
        "next_catalysts": "Upcoming events to watch"
    },
    "big_picture": {
        "economic_outlook": "Economic outlook implications",
        "medium_term_direction": "Medium-term market direction",
        "policy_trajectory": "Policy trajectory implications",
        "forward_focus": "What to focus on going forward"
    },
    "positioning_context": {
        "retail_sentiment": "Retail trader sentiment",
        "institutional_flow": "Institutional flow analysis",
        "market_bias": "Overall market bias"
    },
    "next_catalysts": [
        "Upcoming event 1",
        "Upcoming event 2",
        "Upcoming event 3"
    ]
}

Provide sophisticated, professional analysis that would be valuable for forex traders.
```

---

## 7. GPT PROCESSING

### 7.1 Model Selection
**Logic**: `_select_model(event)`

**For High-Impact Events (like NFP)**:
- Uses `gpt-4o` (more powerful, better analysis)
- Cost: ~$0.03-0.05 per analysis

**For Medium/Low-Impact Events**:
- Uses `gpt-4o-mini` (faster, cheaper)
- Cost: ~$0.001-0.003 per analysis

### 7.2 GPT Analysis Process
GPT receives the comprehensive prompt and:
1. **Analyzes Event Data**: Compares actual (200K) vs expected (180K) vs previous (150K)
2. **Considers Economic Context**: 
   - Current unemployment (3.8%) vs Fed target (4.0%)
   - Policy pressure (moderate hawkish)
   - Central bank rate trend (down)
3. **Evaluates Market Context**:
   - Current prices, volatility, sentiment
   - Trading sessions (London-NY overlap = high volatility)
   - VIX level (low = calm markets)
   - Risk appetite (high = risk-on)
4. **Assesses Pairs Sentiment**:
   - EURUSD: bearish, RSI 48.2
   - USDJPY: neutral, RSI 47.5
   - GBPUSD: bearish, RSI 40.4
5. **Generates Comprehensive Analysis**: All sections of the JSON response

---

## 8. GPT RESPONSE PARSING

### 8.1 Response Structure
**Location**: `_parse_gpt_response()` in `gpt_ai_analysis.py`

**GPT Returns JSON**:
```json
{
    "headline": "Strong NFP Surprise: 200K Jobs Added, USD Strengthens",
    "key_takeaway": "NFP significantly exceeded expectations (200K vs 180K expected), indicating robust labor market. Combined with unemployment at 3.8% (below Fed's 4.0% target), this suggests moderate hawkish policy pressure and USD strength.",
    "forward_scenarios": {
        "bullish": "60% probability: USD continues strengthening. EURUSD breaks below 1.08 support, targets 1.0750. USDJPY tests 149.50 resistance. Reason: Strong employment data reinforces Fed's hawkish stance, especially with unemployment below target.",
        "bearish": "25% probability: USD weakens if market interprets data as peak employment. EURUSD bounces from 1.08, targets 1.09. USDJPY retreats to 148.0. Reason: Market may price in 'peak employment' narrative, reducing further hawkish expectations.",
        "neutral": "15% probability: Range trading between key levels. EURUSD 1.08-1.0850, USDJPY 148.0-149.0. Reason: Market consolidates after initial reaction, awaiting Fed communication and next employment data."
    },
    "event_summary": {
        "release": "US Non-Farm Payrolls report for 2026-01-10",
        "outcome": "NFP showed strong employment data (200K vs 180K expected) with high market impact. Significant beat suggests robust labor market conditions.",
        "previous": "150K",
        "expected": "180K",
        "actual": "200K"
    },
    "market_reaction": {
        "price_action": "USD pairs expected to show high volatility with bullish bias. EURUSD and USDJPY primary movers. Initial spike in USD strength likely, followed by potential consolidation.",
        "volatility": "High volatility expected with 30-50 pip movements on data surprise. London-NY overlap period amplifies volatility. VIX at low levels (15.2) suggests calm broader markets, but forex volatility elevated.",
        "reason": "Strong employment data directly impacts Federal Reserve policy expectations and USD strength. Unemployment below Fed target (3.8% vs 4.0%) adds hawkish pressure. High trading session overlap increases volatility."
    },
    "implications_takeaways": {
        "economic_context": "NFP is the most important employment indicator, directly affecting economic growth and inflation expectations. Strong 200K reading suggests robust labor market, supporting economic growth narrative.",
        "policy_implications": "Bullish employment data suggests hawkish Federal Reserve policy bias. Unemployment at 3.8% (below 4.0% target) creates moderate hawkish pressure. Fed may maintain higher rates longer, supporting USD strength.",
        "market_bias": "Bullish - Employment trends suggest bullish USD outlook. Strong data reinforces Fed's hawkish stance, especially with unemployment below natural rate target.",
        "risk_level": "High risk with potential for sharp USD movements. High volatility expected during London-NY overlap. Risk appetite high (75%), suggesting risk-on flows may amplify USD strength."
    },
    "trading_plan": {
        "best_approach": "Range trading with breakout potential. Monitor EURUSD 1.08-1.09 and USDJPY 148.0-149.0 levels. Consider long USD positions on pullbacks, targeting 1.0750 (EURUSD) and 149.50 (USDJPY).",
        "avoid_strategies": "Avoid aggressive positioning before data release. Use tight stops due to volatility. Don't fade initial USD strength without confirmation.",
        "key_levels": "EURUSD: 1.08 support (critical), 1.09 resistance. USDJPY: 148.0 support, 149.0 resistance (key level). GBPUSD: 1.26 support, 1.27 resistance.",
        "position_sizing": "Conservative position sizing recommended due to high volatility. Reduce size by 30% during high volatility periods. Use wider stops (40-50 pips) for major pairs.",
        "next_catalysts": "Federal Reserve FOMC meetings, CPI data releases, Unemployment Rate updates, and other employment indicators (ADP, Initial Jobless Claims)."
    },
    "big_picture": {
        "economic_outlook": "Employment trends suggest bullish economic conditions with implications for growth and inflation. Strong labor market supports economic growth narrative, potentially leading to higher inflation expectations.",
        "medium_term_direction": "USD likely to maintain bullish bias based on employment trends. Fed's hawkish stance supported by unemployment below target, suggesting higher rates for longer.",
        "policy_trajectory": "Federal Reserve policy trajectory influenced by employment data trends. Unemployment below 4.0% target creates moderate hawkish pressure, suggesting Fed may maintain restrictive policy longer than expected.",
        "forward_focus": "Monitor for follow-up employment data and Federal Reserve communications. Key focus: Fed's reaction to strong employment data, next CPI release, and FOMC meeting minutes."
    },
    "positioning_context": {
        "retail_sentiment": "Retail traders showing bullish sentiment toward USD based on strong employment expectations. EURUSD bearish positioning (RSI 48.2) suggests retail expects USD strength.",
        "institutional_flow": "Institutional investors positioning for employment data impact on USD. High risk appetite (75%) suggests risk-on flows may amplify USD strength.",
        "market_bias": "Overall market bias is bullish for USD based on employment trends. Bearish EURUSD and GBPUSD sentiment (RSI 40.4-48.2) supports USD strength narrative."
    },
    "next_catalysts": [
        "Federal Reserve FOMC meetings",
        "CPI and PPI data releases",
        "Unemployment Rate updates",
        "ADP Employment Change",
        "Initial Jobless Claims"
    ]
}
```

### 8.2 Parsing & Validation
**Process**:
1. Extract JSON from GPT response (handles markdown formatting)
2. Validate required fields
3. Create `GPTAnalysisResult` dataclass object
4. Add metadata (timestamp, model used, cost estimate)

---

## 9. RESPONSE TO FRONTEND

### 9.1 API Response
**Format**: JSON serialization of `GPTAnalysisResult`

**Structure**:
```json
{
    "headline": "...",
    "key_takeaway": "...",
    "forward_scenarios": {...},
    "event_summary": {...},
    "market_reaction": {...},
    "implications_takeaways": {...},
    "trading_plan": {...},
    "big_picture": {...},
    "positioning_context": {...},
    "next_catalysts": [...],
    "confidence_score": 85.0,
    "analysis_timestamp": "2026-01-10T13:35:00",
    "event_id": "12345",
    "analysis_type": "post_event",
    "model_used": "gpt-4o",
    "cost_estimate": 0.045,
    "cache_hit": false,
    "data_quality": "validated"
}
```

---

## 10. FRONTEND DISPLAY

### 10.1 State Update
**Location**: `src/components/Overview.jsx`

**Action**: `setAiAnalysis(analysis)` and `setAiAnalysisState('event-analysis')`

### 10.2 UI Rendering
**Sections Displayed**:

1. **Quick-Scan Headline**:
   - Headline text
   - Currency bubble (USD)
   - Key takeaway

2. **AI Overview**:
   - Analysis Confidence (85%)
   - Event Impact (parsed from `risk_level`)
   - Volatility (parsed from `market_reaction.volatility`)
   - Risk Level
   - Market Sentiment (parsed from `market_bias`)

3. **Forward Scenarios**:
   - Bullish scenario card
   - Bearish scenario card
   - Neutral scenario card

4. **Market Positioning**:
   - Retail Sentiment
   - Institutional Flow
   - Market Bias

5. **Expandable Detailed Sections**:
   - Event Summary (Previous, Expected, Actual)
   - Market Reaction (Price Action, Volatility, Reason)
   - Implications & Takeaways (Economic Context, Policy Implications, Risk Level)
   - Trading Plan (Best Approach, Key Levels, Position Sizing)
   - Big Picture (Economic Outlook, Policy Trajectory, Forward Focus)
   - Next Catalysts (list of upcoming events)

---

## 11. DATA FLOW SUMMARY

```
User Click
  ↓
Event Selected (US NFP)
  ↓
User Confirms
  ↓
API Call: /api/enhanced-analysis/<id>
  ↓
Backend: analyze_macro_event()
  ├─ Validate Event Data
  ├─ Fetch Live Market Data (TradingView)
  ├─ Get Trading Sessions
  ├─ Get Market Sentiment (VIX, Risk Appetite)
  ├─ Get Pairs Sentiment (Top 3 pairs: EURUSD, USDJPY, GBPUSD)
  ├─ Get Economy Context (Static JSON)
  │   ├─ Map USD → US
  │   ├─ Filter Indicators (NFP → unemployment, nonfarm-payrolls)
  │   └─ Calculate Policy Pressure (unemployment vs Fed target)
  ├─ Build Comprehensive Prompt
  ├─ Call GPT API (gpt-4o)
  ├─ Parse Response
  ├─ Cache Result
  └─ Return GPTAnalysisResult
  ↓
Frontend Receives Response
  ↓
Display in AI Analysis Card
  ├─ Headline & Key Takeaway
  ├─ Overview Metrics
  ├─ Forward Scenarios
  ├─ Market Positioning
  └─ Detailed Expandable Sections
```

---

## 12. KEY DATA MAPPINGS

### 12.1 Currency → Country Code
```
USD → US
EUR → EUR
GBP → GBP
JPY → JPY
```

### 12.2 Event Type → Relevant Indicators
```
NFP → ['interest-rate', 'unemployment', 'nonfarm-payrolls']
CPI → ['interest-rate', 'inflation-YoY', 'core-inflation-YoY']
GDP → ['interest-rate', 'gdp-growth']
```

### 12.3 Currency → Top 3 Pairs
```
USD → ['EURUSD', 'USDJPY', 'GBPUSD']
EUR → ['EURUSD', 'EURGBP', 'EURJPY']
GBP → ['GBPUSD', 'EURGBP', 'GBPJPY']
JPY → ['USDJPY', 'EURJPY', 'GBPJPY']
```

### 12.4 Policy Targets
```
USD:
  - Inflation: 2.0% (Fed target)
  - Unemployment: 4.0% (Fed's natural rate)
  
EUR:
  - Inflation: 2.0% (ECB target)
  - Unemployment: None
  
GBP:
  - Inflation: 2.0% (BoE target)
  - Unemployment: None
  
JPY:
  - Inflation: 2.0% (BoJ target)
  - Unemployment: None
```

---

## 13. CACHING STRATEGY

### 13.1 Cache Key Generation
**Logic**: `_generate_cache_key(event, analysis_type)`

**Key Components**:
- Event ID
- Event title
- Currency
- Previous/Expected/Actual values
- Analysis type (pre_event/post_event)

**Example**: `"nfp_usd_150k_180k_200k_post_event"`

### 13.2 Cache Duration
- **Redis**: 24 hours (if available)
- **In-Memory**: 1 hour (fallback)

### 13.3 Cache Invalidation
- New event data (different actual value)
- Different analysis type
- Time-based expiration

---

## 14. ERROR HANDLING

### 14.1 Fallback Scenarios
1. **Validation Failed**: Returns fallback analysis with validation errors
2. **API Rate Limit**: Uses fallback analysis (no GPT call)
3. **GPT API Error**: Returns error fallback analysis
4. **Missing Data**: Gracefully handles None values, excludes from prompt
5. **Cache Miss**: Proceeds with GPT call

### 14.2 Data Quality Indicators
- `data_quality`: "validated", "cached", "fallback"
- `validation_status`: "passed", "failed"
- `market_data_source`: "tradingview", "fallback"

---

## 15. COST TRACKING

### 15.1 Cost Calculation
**Logic**: Based on model used and token count

**For US NFP (High Impact)**:
- Model: `gpt-4o`
- Input tokens: ~2,000
- Output tokens: ~1,500
- Cost: ~$0.045 per analysis

**For Medium/Low Impact**:
- Model: `gpt-4o-mini`
- Input tokens: ~1,500
- Output tokens: ~1,000
- Cost: ~$0.002 per analysis

### 15.2 Rate Limiting
- **Free Tier**: 15 analyses/month
- **Premium Tier**: 50 analyses/day
- **Enforcement**: `_check_rate_limit()` before GPT call

---

## 16. IMPROVEMENTS FROM PHASE 1 INTEGRATION

### 16.1 Before Phase 1
- No economy context in prompts
- No policy target analysis
- Generic analysis without economic indicators

### 16.2 After Phase 1
- **Economic Context**: Central bank rates, current indicators (filtered by event type)
- **Policy Target Analysis**: Deviation from central bank targets (inflation/unemployment)
- **Event-Specific Filtering**: Only relevant indicators shown (reduces prompt length)
- **Enhanced Analysis**: GPT can reference current economic conditions and policy pressure

### 16.3 Example Improvement
**Before**: "NFP data suggests USD strength based on employment trends."

**After**: "NFP data (200K) significantly exceeds expectations (180K), combined with unemployment at 3.8% (below Fed's 4.0% target), creating moderate hawkish policy pressure. This reinforces USD strength expectations, especially given the Fed's current rate trend (down from peak but still restrictive)."

---

## CONCLUSION

The system now provides comprehensive, context-aware analysis by:
1. **Collecting** real-time market data, sentiment, and economic indicators
2. **Filtering** relevant data based on event type
3. **Calculating** policy pressure and deviations from targets
4. **Building** comprehensive prompts with all context
5. **Generating** sophisticated GPT analysis
6. **Displaying** results in an intuitive, expandable UI

The integration of economy context (Phase 1) significantly enhances the quality and accuracy of GPT analysis by providing current economic conditions and policy context.

