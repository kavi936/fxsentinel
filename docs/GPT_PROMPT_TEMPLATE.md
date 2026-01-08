# GPT Prompt Template - Complete Structure (Production-Optimized)

This document shows the **complete prompt** that GPT receives for economic event analysis. All variables and field names are clearly marked.

**Last Updated**: 2026-01-08 - Production-optimized version with consolidated instructions and reduced hallucination risk

---

## Prompt Structure Overview

```
1. Role Definition
2. EVENT DETAILS
3. ECONOMIC CONTEXT FOR {currency} (conditional)
4. MARKET CONTEXT
5. ADDITIONAL MARKET CONTEXT
6. ECONOMIC CONTEXT USAGE REQUIREMENTS (conditional)
7. EVENT TIMING INSTRUCTIONS (conditional)
8. ANALYSIS REQUIREMENTS
9. JSON RESPONSE FORMAT
10. CRITICAL QUALITY STANDARDS
```

---

## Complete Prompt Template

```
You are a senior macro analyst specializing in forex markets with deep expertise in economic indicators, central bank policy, and market dynamics. Provide a comprehensive, data-driven analysis for this economic event.



EVENT DETAILS:
- Title: {event_title}
- Currency: {currency}
- Impact Level: {impact}
- Previous: {previous}
- Expected: {expected}
- Actual: {actual}
- Analysis Type: {analysis_type}

{ECONOMIC_CONTEXT_SECTION}

MARKET CONTEXT:
{MARKET_CONTEXT_SECTION}

ADDITIONAL MARKET CONTEXT:
{ADDITIONAL_CONTEXT_SECTION}

{ECONOMY_CONTEXT_INSTRUCTIONS}

{EVENT_TIMING_INSTRUCTIONS}

ANALYSIS REQUIREMENTS:

1. FORWARD SCENARIOS: Provide specific probability percentages (must sum to ~100%):
   - Base probabilities on event data, economic context, policy pressure, and market conditions
   - Include specific price levels and targets for each scenario
   - Explain the reasoning using economic context data (current indicators, policy targets, trends)

2. VOLATILITY EXPECTATIONS: Consider:
   - Active trading sessions (London-NY overlap = highest volatility, Asian sessions = lower volatility)
   - VIX level (high VIX >25 = elevated fear/volatility, low VIX <15 = calm markets)
   - Risk appetite (low risk appetite = safe haven demand, high risk appetite = risk-on flows)
   - Event impact level and historical volatility patterns

3. POLICY IMPLICATIONS: Must reference:
   - Current central bank rate and trend direction
   - Policy pressure analysis (if provided)
   - How event data relates to central bank targets
   - Potential policy trajectory implications

4. ECONOMIC CONTEXT: Must include:
   - Current indicator values and how event compares
   - Statistical context (averages, trends, deviations)
   - Historical patterns and position relative to norms
   - Economic trajectory implications

5. TRADING INTELLIGENCE: Provide:
   - Specific currency pairs most affected (use pairs sentiment data)
   - Key price levels based on current market context
   - Position sizing considerations based on volatility
   - Risk management strategies

Please provide analysis in the following JSON format:
{
    "headline": "Compelling headline summarizing the key takeaway",
    "key_takeaway": "Main insight in 1-2 sentences",
    "forward_scenarios": {
        "bullish": "Bullish scenario description with specific probability percentage (e.g., '60% probability: Above key resistance at [level], target [level]. Reason: [driver]')",
        "bearish": "Bearish scenario description with specific probability percentage (e.g., '30% probability: Below key support at [level], target [level]. Reason: [driver]')", 
        "neutral": "Neutral scenario description with specific probability percentage (e.g., '10% probability: Range trading between [level] and [level] if no breakout')"
    },
    "event_summary": {
        "release": "Event description",
        "outcome": "{OUTCOME_TEXT}",
        "previous": "{previous}",
        "expected": "{expected}",
        "actual": "{actual}"
    },
    "market_reaction": {
        "price_action": "Specific expected price action with currency pairs and levels (reference pairs sentiment data)",
        "volatility": "Volatility expectations with reasoning (reference trading sessions, VIX, risk appetite)",
        "reason": "Why this reaction is expected (reference economic context, policy pressure, current indicators)"
    },
    "implications_takeaways": {
        "economic_context": "Economic implications - MUST reference current indicator values, statistical context, and trends from ECONOMIC CONTEXT above",
        "policy_implications": "Central bank policy implications - MUST reference current rate, trend, policy pressure, and targets from ECONOMIC CONTEXT above",
        "market_bias": "Overall market bias with specific reasoning based on economic context",
        "risk_level": "Risk assessment considering current economic conditions and policy environment"
    },
    "trading_plan": {
        "best_approach": "Recommended trading approach",
        "avoid_strategies": "Strategies to avoid",
        "key_levels": "Important price levels",
        "position_sizing": "Position sizing recommendations",
        "next_catalysts": "Upcoming events to watch"
    },
    "big_picture": {
        "economic_outlook": "Economic outlook implications - reference current economic indicators, trends, and statistical context",
        "medium_term_direction": "Medium-term market direction based on economic trajectory and policy context",
        "policy_trajectory": "Policy trajectory implications - reference current policy pressure, rate trends, and central bank targets",
        "forward_focus": "What to focus on going forward - specific indicators and data points to monitor"
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

CRITICAL QUALITY STANDARDS:
- Your analysis MUST be data-driven with specific numbers and comparisons
- You MUST demonstrate you've read and understood the ECONOMIC CONTEXT provided above
- Avoid generic phrases like "potential headwinds" or "dovish stance" - use specific data points instead
- Reference actual values: "Current unemployment at 3.8% (below Fed's 4.0% target)" not "low unemployment"
- Compare event data to current indicators: "Expected 57K NFP vs current 119K and historical average of 185K"
- Use policy pressure analysis: "Moderate hawkish pressure as unemployment below target"
- Incorporate statistical context: "Current value is 35% below historical average, showing decreasing trend"

Your analysis must be sophisticated, professional, and demonstrate deep understanding of the economic context provided. Generic analysis without specific data references will be considered inadequate.
```

---

## Variable Definitions

### EVENT DETAILS Variables

| Variable | Source | Example Value | Description |
|----------|--------|---------------|-------------|
| `{event_title}` | `event.get('title', 'Unknown Event')` | `"Non-Farm Employment Change"` | Title of the economic event |
| `{currency}` | `event.get('currency', 'USD')` | `"USD"` | Currency code (USD, EUR, GBP, JPY, etc.) |
| `{impact}` | `event.get('impact', 'medium')` | `"high"` | Impact level: 'low', 'medium', 'high' |
| `{previous}` | `event.get('previous', 'N/A')` | `"64K"` | Previous release value |
| `{expected}` | `event.get('expected') or event.get('forecast') or 'N/A'` | `"57K"` | Expected/forecast value (handles both field names) |
| `{actual}` | `event.get('actual', 'N/A')` | `"TBD"` or `"200K"` | Actual value (TBD for pre-event) |
| `{analysis_type}` | Function parameter | `"pre-event"` or `"post-event"` | Analysis timing |

### ECONOMIC CONTEXT Section (Conditional)

**Only included if:**
- Event title matches an event type in `EVENT_TYPE_MAPPING`
- Currency is supported (USD, EUR, GBP, JPY)
- Economy context data is available

**Structure:**
```
ECONOMIC CONTEXT FOR {currency}:
- Central Bank Rate: {cbr_value}% (Trend: {cbr_trend})
- Current {indicator_label}: {current_value} (Average: {avg}, Range: {range}, Trend: {trend}) - Position: {position} ({deviation} from avg, {percent_deviation}%)

POLICY TARGET ANALYSIS:
{policy_indicator_type} Policy Pressure: {pressure_level}
  - Current: {current_value}%
  - Target: {target_value}%
  - Deviation: {deviation}pp ({deviation_percent}%)
```

**Variables:**

| Variable | Source | Example | Description |
|----------|--------|---------|-------------|
| `{currency}` | From event | `"USD"` | Currency code |
| `{cbr_value}` | `economy_context['central_bank_rate']['value']` | `3.75` | Central bank rate value |
| `{cbr_trend}` | `economy_context['central_bank_rate']['trend']` | `"down"` | Rate trend: 'down', 'stable', 'up' |
| `{indicator_label}` | Mapped from indicator ID | `"Unemployment Rate"` | Human-readable indicator name |
| `{current_value}` | `ind_data.get('currentValue')` | `"4.6%"` | Current indicator value |
| `{avg}` | Calculated from `chartData` | `4.12` | Historical average |
| `{range}` | Calculated from `chartData` | `"3.70 - 4.60"` | Min - Max range |
| `{trend}` | Calculated from `chartData` | `"increasing"` | Trend: 'increasing', 'decreasing', 'stable' |
| `{position}` | Calculated | `"above average"` | Position: 'above average', 'below average', 'near average' |
| `{deviation}` | Calculated | `+0.48` | Deviation from average |
| `{percent_deviation}` | Calculated | `+11.6` | Percentage deviation from average |
| `{pressure_level}` | From policy pressure calculation | `"moderate hawkish pressure"` | Policy pressure level |
| `{target_value}` | From `POLICY_TARGETS` | `4.0` | Central bank target |
| `{deviation}` (policy) | Calculated | `+0.60` | Deviation from target in percentage points |
| `{deviation_percent}` (policy) | Calculated | `+15.0` | Percentage deviation from target |

**Indicator Labels Mapping:**
- `'interest-rate'` → `"Interest Rate"`
- `'inflation-YoY'` → `"CPI (YoY)"`
- `'core-inflation-YoY'` → `"Core CPI (YoY)"`
- `'gdp-growth'` → `"GDP Growth"`
- `'unemployment'` → `"Unemployment Rate"`
- `'nonfarm-payrolls'` → `"Non-Farm Payrolls"`

### MARKET CONTEXT Section

**Always Included:**
```
- Current Prices: {current_prices}
- Recent Volatility: {recent_volatility}
- Market Sentiment: {market_sentiment}
```

**Conditionally Included (only if not None):**
```
- Bond Yields: {bond_yields}
- Equity Indices: {equity_indices}
- Commodity Prices: {commodity_prices}
- Key Technical Levels: {key_levels}
- Retail Sentiment: {retail_sentiment}
- Futures Positioning: {futures_positioning}
- Institutional Flow: {institutional_flow}
```

**Variables:**

| Variable | Source | Example Value | Description |
|----------|--------|---------------|-------------|
| `{current_prices}` | `market_context.current_prices` | `{'EURUSD': 1.0850, 'GBPUSD': 1.2650, ...}` | Dict of pair prices |
| `{recent_volatility}` | `market_context.recent_volatility` | `{'EURUSD': 'moderate', ...}` | Dict of volatility levels |
| `{market_sentiment}` | `market_context.market_sentiment` | `{'EURUSD': 'neutral', ...}` | Dict of sentiment levels |
| `{bond_yields}` | `market_context.bond_yields` | `{'US_10Y': 4.2, ...}` or `None` | Bond yields (optional) |
| `{equity_indices}` | `market_context.equity_indices` | `{'SPX': 4500, ...}` or `None` | Equity indices (optional) |
| `{commodity_prices}` | `market_context.commodity_prices` | `{'GOLD': 2000, ...}` or `None` | Commodity prices (optional) |
| `{key_levels}` | `market_context.key_levels` | `{...}` or `None` | Technical levels (optional) |
| `{retail_sentiment}` | `market_context.retail_sentiment` | `{...}` or `None` | Retail sentiment (optional) |
| `{futures_positioning}` | `market_context.futures_positioning` | `{...}` or `None` | Futures positioning (optional) |
| `{institutional_flow}` | `market_context.institutional_flow` | `{...}` or `None` | Institutional flow (optional) |

### ADDITIONAL MARKET CONTEXT Section

**Market Status Warning (if markets closed):**
```
⚠️ MARKET STATUS: Markets are currently CLOSED (weekend/holiday). 
Any analysis should consider that trading will resume when markets reopen. 
Price movements may be limited or non-existent until markets reopen.
```

**Trading Sessions:**
```
- Active Trading Sessions: {active_sessions}
- Volatility Implication: {volatility_implication}
```

**VIX Fear Indicator:**
```
- VIX Fear Indicator: {vix_value} ({vix_change:+.1f}, Level: {vix_level})
```

**Risk Appetite:**
```
- Risk Appetite: {risk_level} ({risk_percentage}%) - Safe Havens: {safe_havens}
```

**Pairs Sentiment (Top 3):**
```
RELEVANT CURRENCY PAIRS SENTIMENT (Daily Change):
- {pair}: {sentiment} ({daily_change:+.2f}% daily change), RSI: {rsi:.1f}, Volatility: {volatility:.2f}%
- {pair}: {sentiment} ({daily_change:+.2f}% daily change), RSI: {rsi:.1f}, Volatility: {volatility:.2f}%
- {pair}: {sentiment} ({daily_change:+.2f}% daily change), RSI: {rsi:.1f}, Volatility: {volatility:.2f}%
```

**Variables:**

| Variable | Source | Example | Description |
|----------|--------|---------|-------------|
| `{active_sessions}` | `trading_sessions.get('active_sessions', [])` | `['New York', 'London']` | List of active trading sessions |
| `{volatility_implication}` | `trading_sessions.get('volatility_implication')` | `"High volatility expected (London-NY overlap)"` | Volatility implication text |
| `{vix_value}` | `sentiment_data['vix']['value']` | `15.2` | VIX value |
| `{vix_change}` | `sentiment_data['vix']['change']` | `+0.5` | VIX change |
| `{vix_level}` | `sentiment_data['vix']['level']` | `'low'` | VIX level: 'low', 'medium', 'high' |
| `{risk_level}` | `sentiment_data['risk_appetite']['level']` | `'HIGH'` | Risk appetite level (uppercase) |
| `{risk_percentage}` | `sentiment_data['risk_appetite']['percentage']` | `75` | Risk appetite percentage |
| `{safe_havens}` | `sentiment_data['risk_appetite']['safe_havens']` | `'None'` | Safe haven currencies |
| `{pair}` | `pair_data['pair']` | `'EUR/USD'` | Currency pair |
| `{sentiment}` | `pair_data['sentiment'].upper()` | `'BEARISH'` | Pair sentiment (uppercase) |
| `{daily_change}` | `pair_data['daily_change']` | `-0.15` | Daily change percentage |
| `{rsi}` | `pair_data['rsi']` | `48.2` | RSI value |
| `{volatility}` | `pair_data['volatility']` | `0.04` | Volatility percentage |

### ECONOMIC CONTEXT USAGE REQUIREMENTS (Conditional)

**Only included if `economy_context_section` exists (i.e., event maps to indicators)**

**Static Text:**
```
CRITICAL: ECONOMIC CONTEXT USAGE REQUIREMENTS
You MUST incorporate the ECONOMIC CONTEXT data provided above in your analysis. This is mandatory, not optional.

1. REFERENCE SPECIFIC VALUES: Cite exact current values from the economic context:
   - Current unemployment rate, NFP, CPI, GDP, interest rates with specific numbers
   - Compare event data to these current values (e.g., "Current unemployment at 3.8% vs Fed target of 4.0%")
   - Reference central bank rate and trend direction (e.g., "Fed rate at 3.75%, trending down from peak")

2. USE STATISTICAL CONTEXT: Incorporate statistical information when provided:
   - Compare current values to historical averages (e.g., "Current NFP of 119K is below historical average of 185K")
   - Reference trend direction (increasing/decreasing/stable)
   - Mention position relative to average (above/below/near average)
   - Cite deviations and percentages when available

3. POLICY PRESSURE ANALYSIS: If POLICY TARGET ANALYSIS is provided, you MUST use it:
   - Reference policy pressure level (hawkish/dovish/near target)
   - Explain how current values compare to central bank targets
   - Connect policy pressure to potential central bank actions

4. DATA-DRIVEN ANALYSIS: Your analysis must be specific and quantitative:
   - Use actual numbers, not vague terms like "potential headwinds" or "dovish stance"
   - Compare event expectations to current economic conditions
   - Explain how the event data relates to current indicators and policy targets

5. ECONOMIC CONTEXT INTEGRATION: Weave economic context throughout your analysis:
   - Headline: Reference current economic conditions
   - Key Takeaway: Compare event to current indicators
   - Policy Implications: Use policy pressure analysis
   - Economic Context: Reference statistical trends and comparisons
   - Big Picture: Connect to current economic trajectory

FAILURE TO USE ECONOMIC CONTEXT WILL RESULT IN GENERIC, LOW-VALUE ANALYSIS. You must demonstrate you've read and understood the economic context provided above.
```

### EVENT TIMING INSTRUCTIONS (Conditional)

**Pre-Event (if `is_pre_event == True`):**
```
PRE-EVENT ANALYSIS GUIDELINES:
- The actual value is TBD (To Be Determined) - this is a PRE-EVENT analysis
- DO NOT state that data "came in" or "missed expectations" - the data hasn't been released yet
- Focus on what the expected value means relative to current economic conditions
- Compare the expected value to current indicators and historical averages
- Explain potential market reactions based on different outcome scenarios
- Reference how the expected value relates to policy targets and current trends
```

**Post-Event (if `is_pre_event == False`):**
```
POST-EVENT ANALYSIS GUIDELINES:
- The actual value has been released - analyze what happened vs expectations
- Compare actual vs expected vs previous values
- Explain how the actual result relates to current economic indicators
- Reference policy implications based on how actual compares to targets
- Analyze market reaction potential based on the surprise magnitude
```

**Variable:**
- `is_pre_event` = `actual in ['N/A', 'TBD', '', None] or actual == 'TBD'`

### JSON RESPONSE FORMAT Variables

**In JSON Template:**

| Field | Variable/Text | Description |
|-------|---------------|-------------|
| `"outcome"` | Conditional based on `is_pre_event` | Pre-event: "Expected outcome analysis..."<br>Post-event: "What happened vs expectations..." |
| `"previous"` | `{previous}` | Previous value from event |
| `"expected"` | `{expected}` | Expected value from event |
| `"actual"` | `{actual}` | Actual value from event |

**All other fields are static instructions/descriptions.**

---

## Example: Complete Prompt for "Non-Farm Employment Change"

```
You are a senior macro analyst specializing in forex markets with deep expertise in economic indicators, central bank policy, and market dynamics. Provide a comprehensive, data-driven analysis for this economic event.

EVENT DETAILS:
- Title: Non-Farm Employment Change
- Currency: USD
- Impact Level: high
- Previous: 64K
- Expected: 57K
- Actual: TBD
- Analysis Type: pre-event

ECONOMIC CONTEXT FOR USD:
- Central Bank Rate: 3.75% (Trend: down)
- Current Interest Rate: 3.75% (Average: 4.25, Range: 3.75 - 5.50, Trend: decreasing) - Position: below average (-0.50 from avg, -11.8%)
- Current Unemployment Rate: 4.6% (Average: 4.12, Range: 3.70 - 4.60, Trend: increasing) - Position: above average (+0.48 from avg, +11.6%)
- Current Non-Farm Payrolls: 119K (Average: 185.5K, Range: 119K - 315K, Trend: decreasing) - Position: below average (-66.5K from avg, -35.8%)

POLICY TARGET ANALYSIS:
Unemployment Policy Pressure: moderate hawkish pressure
  - Current: 4.60%
  - Target: 4.00%
  - Deviation: +0.60pp (+15.0%)

MARKET CONTEXT:
- Current Prices: {'EURUSD': 1.0850, 'GBPUSD': 1.2650, 'USDJPY': 148.50, 'USDCHF': 0.8750, 'AUDUSD': 0.6650, 'USDCAD': 1.3450, 'NZDUSD': 0.6250, 'EURGBP': 0.8570, 'EURJPY': 161.12, 'GBPJPY': 187.85}
- Recent Volatility: {'EURUSD': 'moderate', 'GBPUSD': 'moderate', 'USDJPY': 'moderate', 'USDCHF': 'moderate', 'AUDUSD': 'moderate', 'USDCAD': 'moderate', 'NZDUSD': 'moderate', 'EURGBP': 'moderate', 'EURJPY': 'moderate', 'GBPJPY': 'moderate'}
- Market Sentiment: {'EURUSD': 'neutral', 'GBPUSD': 'neutral', 'USDJPY': 'neutral', 'USDCHF': 'neutral', 'AUDUSD': 'neutral', 'USDCAD': 'neutral', 'NZDUSD': 'neutral', 'EURGBP': 'neutral', 'EURJPY': 'neutral', 'GBPJPY': 'neutral'}

ADDITIONAL MARKET CONTEXT:
- Active Trading Sessions: New York, London
- Volatility Implication: High volatility expected (London-NY overlap)
- VIX Fear Indicator: 15.2 (+0.5, Level: low)
- Risk Appetite: HIGH (75%) - Safe Havens: None

RELEVANT CURRENCY PAIRS SENTIMENT (Daily Change):
- EUR/USD: BEARISH (-0.15% daily change), RSI: 48.2, Volatility: 0.04%
- USD/JPY: NEUTRAL (-0.05% daily change), RSI: 47.5, Volatility: 0.05%
- GBP/USD: BEARISH (-0.25% daily change), RSI: 40.4, Volatility: 0.15%

CRITICAL: ECONOMIC CONTEXT USAGE REQUIREMENTS
You MUST incorporate the ECONOMIC CONTEXT data provided above in your analysis. This is mandatory, not optional.

1. REFERENCE SPECIFIC VALUES: Cite exact current values from the economic context:
   - Current unemployment rate, NFP, CPI, GDP, interest rates with specific numbers
   - Compare event data to these current values (e.g., "Current unemployment at 3.8% vs Fed target of 4.0%")
   - Reference central bank rate and trend direction (e.g., "Fed rate at 3.75%, trending down from peak")

2. USE STATISTICAL CONTEXT: Incorporate statistical information when provided:
   - Compare current values to historical averages (e.g., "Current NFP of 119K is below historical average of 185K")
   - Reference trend direction (increasing/decreasing/stable)
   - Mention position relative to average (above/below/near average)
   - Cite deviations and percentages when available

3. POLICY PRESSURE ANALYSIS: If POLICY TARGET ANALYSIS is provided, you MUST use it:
   - Reference policy pressure level (hawkish/dovish/near target)
   - Explain how current values compare to central bank targets
   - Connect policy pressure to potential central bank actions

4. DATA-DRIVEN ANALYSIS: Your analysis must be specific and quantitative:
   - Use actual numbers, not vague terms like "potential headwinds" or "dovish stance"
   - Compare event expectations to current economic conditions
   - Explain how the event data relates to current indicators and policy targets

5. ECONOMIC CONTEXT INTEGRATION: Weave economic context throughout your analysis:
   - Headline: Reference current economic conditions
   - Key Takeaway: Compare event to current indicators
   - Policy Implications: Use policy pressure analysis
   - Economic Context: Reference statistical trends and comparisons
   - Big Picture: Connect to current economic trajectory

FAILURE TO USE ECONOMIC CONTEXT WILL RESULT IN GENERIC, LOW-VALUE ANALYSIS. You must demonstrate you've read and understood the economic context provided above.

PRE-EVENT ANALYSIS GUIDELINES:
- The actual value is TBD (To Be Determined) - this is a PRE-EVENT analysis
- DO NOT state that data "came in" or "missed expectations" - the data hasn't been released yet
- Focus on what the expected value means relative to current economic conditions
- Compare the expected value to current indicators and historical averages
- Explain potential market reactions based on different outcome scenarios
- Reference how the expected value relates to policy targets and current trends

ANALYSIS REQUIREMENTS:

1. FORWARD SCENARIOS: Provide specific probability percentages (must sum to ~100%):
   - Base probabilities on event data, economic context, policy pressure, and market conditions
   - Include specific price levels and targets for each scenario
   - Explain the reasoning using economic context data (current indicators, policy targets, trends)

2. VOLATILITY EXPECTATIONS: Consider:
   - Active trading sessions (London-NY overlap = highest volatility, Asian sessions = lower volatility)
   - VIX level (high VIX >25 = elevated fear/volatility, low VIX <15 = calm markets)
   - Risk appetite (low risk appetite = safe haven demand, high risk appetite = risk-on flows)
   - Event impact level and historical volatility patterns

3. POLICY IMPLICATIONS: Must reference:
   - Current central bank rate and trend direction
   - Policy pressure analysis (if provided)
   - How event data relates to central bank targets
   - Potential policy trajectory implications

4. ECONOMIC CONTEXT: Must include:
   - Current indicator values and how event compares
   - Statistical context (averages, trends, deviations)
   - Historical patterns and position relative to norms
   - Economic trajectory implications

5. TRADING INTELLIGENCE: Provide:
   - Specific currency pairs most affected (use pairs sentiment data)
   - Key price levels based on current market context
   - Position sizing considerations based on volatility
   - Risk management strategies

Please provide analysis in the following JSON format:
{
    "headline": "Compelling headline summarizing the key takeaway",
    "key_takeaway": "Main insight in 1-2 sentences",
    "forward_scenarios": {
        "bullish": "Bullish scenario description with specific probability percentage (e.g., '60% probability: Above key resistance at [level], target [level]. Reason: [driver]')",
        "bearish": "Bearish scenario description with specific probability percentage (e.g., '30% probability: Below key support at [level], target [level]. Reason: [driver]')", 
        "neutral": "Neutral scenario description with specific probability percentage (e.g., '10% probability: Range trading between [level] and [level] if no breakout')"
    },
    "event_summary": {
        "release": "Event description",
        "outcome": "Expected outcome analysis (compare expected value to current indicators and policy targets)",
        "previous": "64K",
        "expected": "57K",
        "actual": "TBD"
    },
    "market_reaction": {
        "price_action": "Specific expected price action with currency pairs and levels (reference pairs sentiment data)",
        "volatility": "Volatility expectations with reasoning (reference trading sessions, VIX, risk appetite)",
        "reason": "Why this reaction is expected (reference economic context, policy pressure, current indicators)"
    },
    "implications_takeaways": {
        "economic_context": "Economic implications - MUST reference current indicator values, statistical context, and trends from ECONOMIC CONTEXT above",
        "policy_implications": "Central bank policy implications - MUST reference current rate, trend, policy pressure, and targets from ECONOMIC CONTEXT above",
        "market_bias": "Overall market bias with specific reasoning based on economic context",
        "risk_level": "Risk assessment considering current economic conditions and policy environment"
    },
    "trading_plan": {
        "best_approach": "Recommended trading approach",
        "avoid_strategies": "Strategies to avoid",
        "key_levels": "Important price levels",
        "position_sizing": "Position sizing recommendations",
        "next_catalysts": "Upcoming events to watch"
    },
    "big_picture": {
        "economic_outlook": "Economic outlook implications - reference current economic indicators, trends, and statistical context",
        "medium_term_direction": "Medium-term market direction based on economic trajectory and policy context",
        "policy_trajectory": "Policy trajectory implications - reference current policy pressure, rate trends, and central bank targets",
        "forward_focus": "What to focus on going forward - specific indicators and data points to monitor"
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

CRITICAL QUALITY STANDARDS:
- Your analysis MUST be data-driven with specific numbers and comparisons
- You MUST demonstrate you've read and understood the ECONOMIC CONTEXT provided above
- Avoid generic phrases like "potential headwinds" or "dovish stance" - use specific data points instead
- Reference actual values: "Current unemployment at 3.8% (below Fed's 4.0% target)" not "low unemployment"
- Compare event data to current indicators: "Expected 57K NFP vs current 119K and historical average of 185K"
- Use policy pressure analysis: "Moderate hawkish pressure as unemployment below target"
- Incorporate statistical context: "Current value is 35% below historical average, showing decreasing trend"

Your analysis must be sophisticated, professional, and demonstrate deep understanding of the economic context provided. Generic analysis without specific data references will be considered inadequate.
```

---

## Conditional Sections Summary

| Section | Condition | When Included |
|---------|----------|---------------|
| **ECONOMIC CONTEXT FOR {currency}** | `relevant_indicator_ids` is not empty AND `economy_context` is not None | Event maps to indicators AND currency is supported |
| **POLICY TARGET ANALYSIS** | Event is CPI/inflation OR employment/unemployment related | Within ECONOMIC CONTEXT section |
| **ECONOMIC CONTEXT USAGE REQUIREMENTS** | `economy_context_section` is not empty | Same as ECONOMIC CONTEXT section |
| **PRE-EVENT GUIDELINES** | `is_pre_event == True` | Actual value is TBD/N/A |
| **POST-EVENT GUIDELINES** | `is_pre_event == False` | Actual value has been released |
| **Market Status Warning** | `market_status == 'closed'` | Markets are closed (weekend/holiday) |
| **Bond Yields, Equity Indices, etc.** | Field is not `None` | Only if real data available |

---

## Field Name Reference

### Event Object Fields
- `event['title']` → `event_title`
- `event['currency']` → `currency`
- `event['impact']` → `impact`
- `event['previous']` → `previous`
- `event['expected']` OR `event['forecast']` → `expected`
- `event['actual']` → `actual`

### Market Context Fields
- `market_context.current_prices` (Dict)
- `market_context.recent_volatility` (Dict)
- `market_context.market_sentiment` (Dict)
- `market_context.bond_yields` (Optional Dict or None)
- `market_context.equity_indices` (Optional Dict or None)
- `market_context.commodity_prices` (Optional Dict or None)
- `market_context.key_levels` (Optional Dict or None)
- `market_context.retail_sentiment` (Optional Dict or None)
- `market_context.futures_positioning` (Optional Dict or None)
- `market_context.institutional_flow` (Optional Dict or None)

### Economy Context Fields
- `economy_context['currency']` → Currency code
- `economy_context['central_bank_rate']['value']` → Rate value
- `economy_context['central_bank_rate']['trend']` → Rate trend
- `economy_context['central_bank_rate']['bank_name']` → Bank name
- `economy_context['central_bank_rate']['as_of']` → Date
- `economy_context['indicators'][indicator_id]['currentValue']` → Current value
- `economy_context['indicators'][indicator_id]['chartData']` → Historical array
- Calculated statistics: `average`, `min`, `max`, `std_deviation`, `trend`, `deviation_from_avg`, `percent_from_avg`, `position`, `range`

### Trading Sessions Fields
- `trading_sessions['market_status']` → 'open' or 'closed'
- `trading_sessions['active_sessions']` → List of session names
- `trading_sessions['volatility_implication']` → Implication text

### Sentiment Data Fields
- `sentiment_data['vix']['value']` → VIX value
- `sentiment_data['vix']['change']` → VIX change
- `sentiment_data['vix']['level']` → VIX level
- `sentiment_data['risk_appetite']['level']` → Risk level
- `sentiment_data['risk_appetite']['percentage']` → Risk percentage
- `sentiment_data['risk_appetite']['safe_havens']` → Safe havens
- `pairs_sentiment[i]['pair']` → Pair name
- `pairs_sentiment[i]['sentiment']` → Sentiment
- `pairs_sentiment[i]['daily_change']` → Daily change %
- `pairs_sentiment[i]['rsi']` → RSI value
- `pairs_sentiment[i]['volatility']` → Volatility %

---

## Notes for Modification

1. **To modify prompt structure**: Edit `_create_analysis_prompt()` function in `backend/services/gpt_ai_analysis.py`
2. **To modify economy context format**: Edit `_format_economy_context_for_prompt()` function
3. **To modify policy analysis**: Edit `_add_policy_context_to_prompt()` function
4. **To modify event matching**: Edit `EVENT_TYPE_MAPPING` constant
5. **To modify policy targets**: Edit `POLICY_TARGETS` constant
6. **To modify statistical calculations**: Edit `_calculate_indicator_statistics()` function

---

## Last Updated
2026-01-08 - Phase 1 Economy Context Integration Complete

